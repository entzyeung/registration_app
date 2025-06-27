from abc import ABC, abstractmethod
from typing import Dict

"""_summary_
Summary: This file establishes BaseValidator as an abstract interface, 
ensuring all validators implement a validate method with a consistent signature. 
It’s used by DSPyValidator and ChatGPTValidator to standardize validation logic.

Declares an abstract method validate that takes:
question: A string (e.g., "What is your email?").
user_answer: A string (e.g., "john@gmail.com").
Returns a dictionary with string keys and values (e.g., {"status": "valid", "feedback": "...", "formatted_answer": "..."}).
"""

class BaseValidator(ABC):
    """Abstract base class for validation strategies."""

    @abstractmethod
    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        """Validate the user input and return a structured response."""
        pass
    

### Example:
""" 
from abc import ABC, abstractmethod
from typing import Dict

# Abstract base class
class BaseValidator(ABC):
    # Abstract base class for validation strategies.
    
    @abstractmethod
    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        # Validate the user input and return a structured response.
        pass

# Concrete subclass 1: Simple Email Validator
class EmailValidator(BaseValidator):
    # Validates email addresses with basic rules.
    
    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        if "@" in user_answer and "." in user_answer:
            return {
                "status": "valid",
                "feedback": "Email looks good!",
                "formatted_answer": user_answer.lower()
            }
        return {
            "status": "clarify",
            "feedback": "Please enter a valid email (e.g., user@example.com).",
            "formatted_answer": user_answer
        }

# Concrete subclass 2: Simple Name Validator
class NameValidator(BaseValidator):
    # Validates names by checking length and formatting.
    
    def validate(self, question: str, user_answer: str) -> Dict[str, str]:
        if len(user_answer.strip()) >= 2:
            formatted_name = user_answer.strip().title()
            return {
                "status": "valid",
                "feedback": "Name is valid!",
                "formatted_answer": formatted_name
            }
        return {
            "status": "clarify",
            "feedback": "Name must be at least 2 characters long.",
            "formatted_answer": user_answer
        }

# Example usage
def process_input(validator: BaseValidator, question: str, user_answer: str):
    result = validator.validate(question, user_answer)
    print(f"Question: {question}")
    print(f"Answer: {user_answer}")
    print(f"Result: {result}\n")

# Create instances and test
email_validator = EmailValidator()
name_validator = NameValidator()

process_input(email_validator, "What is your email?", "john@example.com")
process_input(email_validator, "What is your email?", "invalid_email")
process_input(name_validator, "What is your name?", "Alice Smith")
process_input(name_validator, "What is your name?", "A")
"""