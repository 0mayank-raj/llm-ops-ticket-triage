from unittest.mock import patch
from pydantic import ValidationError

from app.triage import process_ticket


invalid_response = """
{
    "category": "Billing",
    "priority": "High"
}
"""

with patch(
    "app.triage.call_llm",
    return_value=invalid_response
):

    try:
        result = process_ticket(
            "My payment was deducted twice. Please help."
        )

        print("Result:", result)

    except ValidationError as error:
        print("Validation failed!")
        print(error)