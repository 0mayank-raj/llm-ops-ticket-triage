from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.schema import TicketResponse


client = TestClient(app)


def test_home_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "LLMOps Ticket Triage API is running"
    }


def test_health_check():

    response = client.get("/healthz")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }

def test_invalid_ticket():

    response = client.post(
        "/triage",
        json={"ticket": "Help"}
    )

    assert response.status_code == 422

@patch("app.main.process_ticket")
def test_successful_ticket_triage(mock_process_ticket):

    mock_process_ticket.return_value = {
        "category": "Technical",
        "priority": "High",
        "product": "Mobile App",
        "summary": "User cannot log in to the mobile application.",
        "draft_reply": "We apologize for the inconvenience. Please try resetting your password."
    }

    response = client.post(
        "/triage",
        json={
            "ticket": "I cannot log in to my mobile application."
        }
    )

    assert response.status_code == 200

    assert response.json()["category"] == "Technical"
    assert response.json()["priority"] == "High"
    assert response.json()["product"] == "Mobile App"

    mock_process_ticket.assert_called_once()

@patch("app.main.process_ticket")
def test_llm_service_failure(mock_process_ticket):

    mock_process_ticket.side_effect = RuntimeError(
        "Both Gemini and Groq providers failed."
    )

    response = client.post(
        "/triage",
        json={
            "ticket": "I cannot access my account."
        }
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "LLM service is currently unavailable. Please try again later."
    }

    mock_process_ticket.assert_called_once()

@patch("app.main.process_ticket")
def test_invalid_llm_response(mock_process_ticket):

    mock_process_ticket.side_effect = lambda ticket: (
        TicketResponse.model_validate_json(
            '{"category": "Billing", "priority": "High"}'
        )
    )

    response = client.post(
        "/triage",
        json={
            "ticket": "I have an issue with my recent payment."
        }
    )

    assert response.status_code == 502

    assert response.json() == {
        "detail": "The AI service returned an invalid response. Please try again."
    }

@patch("app.main.process_ticket")
def test_unexpected_error(mock_process_ticket):

    mock_process_ticket.side_effect = ValueError(
        "Unexpected internal error"
    )

    response = client.post(
        "/triage",
        json={
            "ticket": "My account is not working properly."
        }
    )

    assert response.status_code == 500

    assert response.json() == {
        "detail": "An unexpected error occurred while processing the ticket."
    }
def test_api_blocks_unsafe_draft_reply():
    unsafe_response = """
    {
        "category": "Billing",
        "priority": "High",
        "product": "Unknown",
        "summary": "Customer was charged twice.",
        "draft_reply": "I have processed your refund successfully."
    }
    """

    with patch(
        "app.triage.call_llm",
        return_value=unsafe_response
    ):
        response = client.post(
            "/triage",
            json={
                "ticket": "I was charged twice for my subscription."
            }
        )

    assert response.status_code == 200

    result = response.json()

    assert result["draft_reply"] == (
        "Thank you for contacting us. We understand your concern "
        "and apologize for any inconvenience. Our support team "
        "will need to review the details of your issue before "
        "confirming the next steps. Please share the relevant "
        "reference information so we can assist you further."
    )


def test_api_allows_safe_draft_reply():
    safe_reply = (
        "Thank you for contacting us. "
        "Please share your transaction reference number."
    )

    safe_response = f"""
    {{
        "category": "Billing",
        "priority": "High",
        "product": "Unknown",
        "summary": "Customer reported a duplicate charge.",
        "draft_reply": "{safe_reply}"
    }}
    """

    with patch(
        "app.triage.call_llm",
        return_value=safe_response
    ):
        response = client.post(
            "/triage",
            json={
                "ticket": "I was charged twice for my subscription."
            }
        )

    assert response.status_code == 200
    assert response.json()["draft_reply"] == safe_reply
