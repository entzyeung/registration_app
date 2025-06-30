from pydantic import (BaseModel, Field, field_validator)
import re

class ValidatedLLMResponse(BaseModel):
    """Validates & formats user responses using Guardrails AI & Pydantic."""

    status: str = Field(..., pattern="^(valid|clarify|error)$")  
    feedback: str
    formatted_answer: str

    @field_validator("formatted_answer", mode="before")  
    def validate_and_format(cls, value, values):
        """Formats & validates responses based on the question type."""

        if values.get("status") == "error":
            return value 

        question = values.get("question", "").lower()

        if "email" in question:
            return cls.validate_email(value)

        if "name" in question:
            return cls.validate_name(value)

        if "phone" in question:
            return cls.validate_phone(value)

        if "address" in question:
            return cls.validate_address(value)

        return value  

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
        
        print(f"Validating phone, digits extracted: {digits}")

        if not digits or len(digits) < 10:
            print("Rejected: Empty or too short")
            return "clarify"

        if digits.startswith("44"):
            if len(digits) != 12:
                print(f"Rejected: Invalid +44 number length: {len(digits)} digits")
                return "clarify" 
            digits = "0" + digits[2:] 
            print(f"Converted +44 number to national format: {digits}")

        if not digits.startswith("0"):
            print("Rejected: Number does not start with 0 after +44 conversion")
            return "clarify"

        if len(digits) == 10 and digits.startswith("0") and not digits.startswith("07"):
            formatted = f"{digits[:3]} {digits[3:6]} {digits[6:]}"
            print(f"Valid landline formatted: {formatted}")
            return formatted

        if len(digits) == 11 and digits.startswith("07"):
            formatted = f"{digits[:5]} {digits[5:8]} {digits[8:]}"
            print(f"Valid mobile formatted: {formatted}")
            return formatted

        print("Rejected: Phone number did not match any valid UK format")
        return "clarify"



    @staticmethod
    def validate_address(address: str) -> str:
        """Ensures address includes house number, street, town/city, and postcode & formats correctly for UK."""
        components = [comp.strip() for comp in address.split(",")]
        if len(components) != 4:
            return "clarify"  

        house_number, street, town, postcode = components

        if not house_number or not re.search(r"\d", house_number):
            return "clarify"

        if not street or not re.search(r"[A-Za-z]", street):
            return "clarify"

        if not town:
            return "clarify"

        postcode = postcode.strip().upper().rstrip(".,")

        if not re.match(r"^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$", postcode):
            return "clarify"

        formatted_address = ", ".join([house_number.title(), street.title(), town.title(), postcode])
        return formatted_address
