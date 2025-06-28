from app.validation.dspy_validator import DSPyValidator
from app.validation.chatgpt_validator import ChatGPTValidator
from app.helpers.config import VALIDATION_ENGINE


# ValidatorFactory: enables switching between validators, facilitating experimentation.


class ValidatorFactory:
    """Factory class for creating validator instances."""

    _validators = {"dspy": DSPyValidator, "chatgpt": ChatGPTValidator}

    @classmethod
    def create_validator(cls, engine: str):
        """Creates a validator instance dynamically."""
        if engine not in cls._validators:
            raise ValueError(f"Invalid validation engine: {engine}")
        return cls._validators[engine]()



# Application: The app (calling validate_user_input from factory.py) 
# uses these validations to ensure user inputs are correct before proceeding, 
# supporting conditional logic like skipping ask_address.
def validate_user_input(question: str, user_answer: str):
    """Uses the factory to get the appropriate validator."""
    validator = ValidatorFactory.create_validator(VALIDATION_ENGINE)
    return validator.validate(question, user_answer)
