import guardrails as gd
import dspy
from app.validation.base_validator import BaseValidator
from pydantic import ValidationError
from app.validation.validated_response import ValidatedLLMResponse
from typing import Literal
import logging
import json
import mlflow
from helpers.config import OPENAI_API_KEY, MLFLOW_ENABLED, MLFLOW_EXPERIMENT_NAME

###############################################
############# Semantic validation #############
dspy.settings.configure(lm=dspy.LM(model="gpt-4.1-mini", api_key=OPENAI_API_KEY))

if MLFLOW_ENABLED:
    mlflow.dspy.autolog()

# Define DSPy Signature
class ValidateUserAnswer(dspy.Signature):
    """Validates and formats user responses. Should return 'valid', 'clarify', or 'error'."""

    question: str = dspy.InputField()
    user_answer: str = dspy.InputField()

    status: Literal["valid", "clarify", "error"] = dspy.OutputField(
        desc="Validation status: 'valid', 'clarify', or 'error'. Return 'valid' if the input contains all necessary information."
    )
    feedback: str = dspy.OutputField(
        desc="Explanation if response is incorrect or needs details."
    )
    formatted_answer: str = dspy.OutputField(
        desc="Return the response with proper formatting. Example: "
            "- Emails: Lowercase (e.g., 'John@gmail.com' → 'john@gmail.com'). "
            "- Names: Capitalize first & last name (e.g., 'john doe' → 'John Doe'). "
            "- Addresses: Capitalize & ensure complete info for UK (e.g., '123 high st,london,sw1a 1aa' → '123 High St, London, SW1A 1AA'). "
            "For phone numbers: "
            "- Extract digits, ignoring non-digit characters (e.g., '+447700900123' → '447700900123'). "
            "- If the number starts with '44', it must have exactly 12 digits to be valid (e.g., '447700900123'). Convert to national format by replacing '44' with '0' (e.g., '447700900123' → '07700900123'). Reject if not 12 digits (e.g., '4470442767676' → 13 digits, return 'clarify'). "
            "- After conversion, the number must start with '0'. Reject if it doesn't (e.g., '1234567890' → return 'clarify'). "
            "- Validate as a UK landline (10 digits, starts with '0' but not '07') or mobile (11 digits, starts with '07'). "
            "- Format valid landlines as 0XX XXX XXXX and mobiles as 07XXX XXX XXX. "
            "- Reject invalid formats (e.g., too short, wrong digit count, or non-UK formats) with status='clarify'. "
            "An address must include: house number, street name, town/city, and postcode. House number and street name can be one component. If head starts with Ra, ra, fa, flata, etc, it means Room A or Flat A. 'R' or 'r' in the front means Room; 'F' or f 'f' means Flat"
            "Reject responses that do not meet these formats with status='clarify'. "
            "If the response cannot be formatted, return the original answer."
    )

run_llm_validation = dspy.Predict(ValidateUserAnswer)
#################################################################

#################################################
############# Structural validation #############
guard = gd.Guard.for_pydantic(ValidatedLLMResponse)

####################################################

class DSPyValidator(BaseValidator):
    """Uses DSPy with Guardrails AI for structured validation."""

    def validate(self, question: str, user_answer: str):
        """Validates user response, applies guardrails, and logs to MLflow."""
        try:
            raw_result = run_llm_validation(question=question, user_answer=user_answer)
            structured_validation_output = guard.parse(json.dumps(raw_result.toDict()))
            validated_dict = dict(structured_validation_output.validated_output)

            if MLFLOW_ENABLED:
                mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
                with mlflow.start_run(nested=True):
                    mlflow.log_param("validation_engine", "DSPy + Guardrails AI")
                    mlflow.log_param("question", question)
                    mlflow.log_param("input_answer", user_answer)
                    mlflow.log_param("status", validated_dict["status"])
                    mlflow.log_param(
                        "formatted_answer", validated_dict["formatted_answer"]
                    )

            return {
                "status": validated_dict["status"],
                "feedback": validated_dict["feedback"],
                "formatted_answer": validated_dict["formatted_answer"],
            }

        except ValidationError as ve:
            logging.error(f"Validation error: {str(ve)}")
            return {
                "status": "error",
                "feedback": "Output validation failed.",
                "formatted_answer": user_answer,
            }
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            return {
                "status": "error",
                "feedback": "An error occurred during validation.",
                "formatted_answer": user_answer,
            }