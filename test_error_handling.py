from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.schema import TicketResponse

client = TestClient(app)


# Simulate an LLM returning incomplete JSON
def invalid_process_ticket(ticket):

    return TicketResponse.model_validate_json(
        '{"category": "Billing", "priority": "High"}'
    )


with patch(
    "app.main.process_ticket",
    side_effect=invalid_process_ticket
):

    response = client.post(
        "/triage",
        json={
            "ticket": "My payment was deducted twice. Please help."
        }
    )

    print("Status Code:", response.status_code)
    print("Response:", response.json())