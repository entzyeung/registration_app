from pydantic import (BaseModel, Field, field_validator)
import re

# This file defines a Pydantic model for validating and formatting LLM responses,
# used by Guardrails AI to enforce structure and formatting rules.

class ValidatedLLMResponse(BaseModel):
    """Validates & formats user responses using Guardrails AI & Pydantic."""

    status: str = Field(..., pattern="^(valid|clarify|error)$")  # required (...),
    # with a regex pattern ensuring it’s either "valid", "clarify", or "error".
    feedback: str
    formatted_answer: str

    @field_validator("formatted_answer", mode="before")  # executed before default Pydantic validation (mode="before").
    #@classmethod
    # Marks the method as a class method,
    # 1. a class method doesn't need an instance to be called.
    # 2. Using cls (the class), the method can call these static methods without needing an instance.
    def validate_and_format(cls, value, values):
        """Formats & validates responses based on the question type."""

        if values.get("status") == "error":
            return value  # Skip validation for errors

        question = values.get("question", "").lower()

        # Validate Email Format
        if "email" in question:
            return cls.validate_email(value)

        # Validate Name Format (Capitalize First & Last Name)
        if "name" in question:
            return cls.validate_name(value)

        # Validate Phone Number (Format: 0XX XXX XXXX or 07XXX XXXXXX for UK)
        if "phone" in question:
            return cls.validate_phone(value)

        # Validate Address (Must contain house number, street, town/city, postcode for UK)
        if "address" in question:
            return cls.validate_address(value)

        return value  # Default: Return unchanged

    @staticmethod
    def validate_email(email: str) -> str:
        """Validates email format and converts to lowercase."""
        return (
            email.lower() if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) else "clarify"
        )

    @staticmethod
    def validate_name(name: str) -> str:
        """Capitalizes first & last name."""
        return " ".join(word.capitalize() for word in name.split())

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validates & formats UK phone numbers with strict +44 handling."""
        digits = re.sub(r"\D", "", phone.strip())
        
        # Debug print to trace digits
        print(f"Validating phone, digits extracted: {digits}")

        # Reject if digits is empty or too short
        if not digits or len(digits) < 10:
            print("Rejected: Empty or too short")
            return "clarify"

        # Handle +44 prefix strictly
        if digits.startswith("44"):
            if len(digits) != 12:
                print(f"Rejected: Invalid +44 number length: {len(digits)} digits")
                return "clarify"  # Reject +4407442757070 (13 digits)
            digits = "0" + digits[2:]  # Convert +44 to 0
            print(f"Converted +44 number to national format: {digits}")

        # At this point, digits must start with 0 for UK numbers
        if not digits.startswith("0"):
            print("Rejected: Number does not start with 0 after +44 conversion")
            return "clarify"

        # Validate UK landline: 10 digits, starts with 0 but NOT 07
        if len(digits) == 10 and digits.startswith("0") and not digits.startswith("07"):
            formatted = f"{digits[:3]} {digits[3:6]} {digits[6:]}"
            print(f"Valid landline formatted: {formatted}")
            return formatted

        # Validate UK mobile: 11 digits, starts with 07
        if len(digits) == 11 and digits.startswith("07"):
            formatted = f"{digits[:5]} {digits[5:8]} {digits[8:]}"
            print(f"Valid mobile formatted: {formatted}")
            return formatted

        # Reject any other format
        print("Rejected: Phone number did not match any valid UK format")
        return "clarify"



    @staticmethod
    def validate_address(address: str) -> str:
        """Ensures address includes house number, street, town/city, and postcode & formats correctly for UK."""
        # Split and strip each component
        components = [comp.strip() for comp in address.split(",")]
        if len(components) != 4:
            return "clarify"  # Must have exactly 4 components

        house_number, street, town, postcode = components

        # House number must contain at least one digit and not be empty
        if not house_number or not re.search(r"\d", house_number):
            return "clarify"

        # Street must contain alphabetic characters and not be empty
        if not street or not re.search(r"[A-Za-z]", street):
            return "clarify"

        # Town must not be empty
        if not town:
            return "clarify"

        # Strip trailing punctuation and uppercase postcode
        postcode = postcode.strip().upper().rstrip(".,")

        # Stricter UK postcode regex (with space)
        if not re.match(r"^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$", postcode):
            return "clarify"

        # Capitalize each component
        formatted_address = ", ".join([house_number.title(), street.title(), town.title(), postcode])
        return formatted_address
