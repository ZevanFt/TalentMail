from pydantic_core import PydanticCustomError
from email_validator import validate_email, EmailNotValidError
from typing import Annotated

# --- Custom Email Type for Development ---

def dev_email_validator(v: str) -> str:
    """
    A custom validator that allows '.test' TLDs in development,
    while enforcing strict validation otherwise.
    """
    from core.config import settings # Import locally to avoid circular dependency

    try:
        # Use the robust email_validator library for all checks
        validate_email(v, check_deliverability=False)
        return v
    except EmailNotValidError as e:
        # If validation fails, check if it's a '.test' domain in development
        if settings.CURRENT_ENVIRONMENT == "development" and v.endswith(".test"):
            # For .test domains, we accept them despite the standard validation error
            return v
        # For any other error, or in any other environment, raise the original error
        raise PydanticCustomError("value_error", str(e)) from e

# Create a new type using Annotated and our custom validator.
# This ensures the validation is applied everywhere this type is used.
CustomEmailStr = Annotated[str, dev_email_validator]