from unittest.mock import patch

from app.triage import (
    process_ticket,
    validate_draft_reply,
    SAFE_FALLBACK_REPLY
)
from app.schema import TicketResponse
import pytest

@patch("app.triage.call_llm")
@patch("app.triage.load_prompt")
def test_process_ticket(mock_load_prompt, mock_call_llm):

    mock_load_prompt.return_value = {
        "system_prompt": "You are a ticket classification assistant.",
        "user_prompt": "Analyze this ticket: {ticket}"
    }

    mock_call_llm.return_value = """
    {
        "category": "Technical",
        "priority": "High",
        "product": "Mobile App",
        "summary": "User cannot log in.",
        "draft_reply": "Please try resetting your password."
    }
    """

    result = process_ticket("I cannot log in to my mobile app.")

    mock_call_llm.assert_called_once_with(
    "You are a ticket classification assistant.",
    "Analyze this ticket: I cannot log in to my mobile app."
)

    assert isinstance(result, TicketResponse)

    assert result.category == "Technical"
    assert result.priority == "High"
    assert result.product == "Mobile App"

    mock_load_prompt.assert_called_once()
    mock_call_llm.assert_called_once()

@patch("app.triage.call_llm")
@patch("app.triage.load_prompt")
def test_process_ticket_invalid_response(mock_load_prompt, mock_call_llm):

    mock_load_prompt.return_value = {
        "system_prompt": "You are a ticket classification assistant.",
        "user_prompt": "Analyze this ticket: {ticket}"
    }

    mock_call_llm.return_value = """
    {
        "category": "Billing",
        "priority": "High"
    }
    """

    from pydantic import ValidationError

    import pytest

    with pytest.raises(ValidationError):

        process_ticket("I have an issue with my payment.")

def test_unsafe_draft_reply():
    reply = "I have processed your refund successfully."

    result = validate_draft_reply(reply)

    assert result == SAFE_FALLBACK_REPLY


def test_safe_draft_reply():
    reply = (
        "Thank you for contacting us. "
        "Please share your transaction reference number."
    )

    result = validate_draft_reply(reply)

    assert result == reply

@pytest.mark.parametrize(
    "unsafe_phrase",
    [
        "I have processed your refund.",
        "Your refund has been processed.",
        "I have escalated your ticket.",
        "I have located your account.",
        "I have submitted a request.",
        "Your replacement has been dispatched.",
        "Your refund will arrive tomorrow.",
        "Your refund will be credited soon.",
        "Your refund will arrive within 3-5 business days.",
        "Your refund will arrive within 3 to 5 business days."
    ]
)
def test_all_unsafe_phrases(unsafe_phrase):
    result = validate_draft_reply(unsafe_phrase)

    assert result == SAFE_FALLBACK_REPLY
