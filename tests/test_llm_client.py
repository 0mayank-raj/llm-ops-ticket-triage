import os
from unittest.mock import patch, MagicMock

from app.llm_client import call_provider
from app.metrics import LLM_FAILURES

@patch("app.llm_client.completion")
def test_call_provider_success(mock_completion):

    mock_completion.return_value.choices[0].message.content = (
        "Ticket classified successfully."
    )

    mock_completion.return_value.usage.prompt_tokens = 100
    mock_completion.return_value.usage.completion_tokens = 50
    mock_completion.return_value.usage.total_tokens = 150

    result = call_provider(
        "gemini/test-model",
        "You are a support assistant.",
        "I cannot log in."
    )

    assert result == "Ticket classified successfully."

    mock_completion.assert_called_once()

@patch("app.llm_client.time.sleep")
@patch("app.llm_client.completion")
def test_call_provider_retry_success(mock_completion, mock_sleep):

    mock_completion.side_effect = [
        Exception("Temporary Gemini failure"),
        Exception("Temporary Gemini failure"),
        type("Response", (), {
    "choices": [
                type("Choice", (), {
                    "message": type("Message", (), {
                        "content": "Success after retries."
                    })()
                })()
            ],
            "usage": type("Usage", (), {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            })()
        })()
    ]

    result = call_provider(
        "gemini/test-model",
        "You are a support assistant.",
        "I cannot log in."
    )

    assert result == "Success after retries."

    assert mock_completion.call_count == 3

    assert mock_sleep.call_count == 2

@patch.dict(os.environ, {
    "GEMINI_MODEL": "test-gemini",
    "GROQ_MODEL": "test-groq"
})
@patch("app.llm_client.call_provider")
def test_gemini_failure_groq_fallback(mock_call_provider):

    mock_call_provider.side_effect = [
        Exception("Gemini failed"),
        "Groq successfully processed the ticket."
    ]

    from app.llm_client import call_llm

    result = call_llm(
        "You are a support assistant.",
        "I cannot log in."
    )

    assert result == "Groq successfully processed the ticket."

    assert mock_call_provider.call_count == 2

    assert mock_call_provider.call_args_list[0].args[0] == "gemini/test-gemini"

    assert mock_call_provider.call_args_list[1].args[0] == "groq/test-groq"

@patch.dict(os.environ, {
    "GEMINI_MODEL": "test-gemini",
    "GROQ_MODEL": "test-groq"
})
@patch("app.llm_client.call_provider")
def test_both_providers_fail(mock_call_provider):

    mock_call_provider.side_effect = [
        Exception("Gemini failed"),
        Exception("Groq failed")
    ]

    from app.llm_client import call_llm

    import pytest

    with pytest.raises(
        RuntimeError,
        match="Both Gemini and Groq providers failed."
    ):

        call_llm(
            "You are a support assistant.",
            "I cannot log in."
        )

    assert mock_call_provider.call_count == 2

def test_failure_metrics_tracking():

    from app.llm_client import call_provider

    before = LLM_FAILURES.labels(
        provider="gemini"
    )._value.get()

    mock_response = MagicMock()

    mock_response.choices[0].message.content = '{"result": "success"}'

    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    with patch(
        "app.llm_client.completion",
        side_effect=[
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            mock_response
        ]
    ), patch("app.llm_client.time.sleep"):

        result = call_provider(
            "gemini/test-model",
            "system prompt",
            "user prompt"
        )

    after = LLM_FAILURES.labels(
        provider="gemini"
    )._value.get()

    assert result == '{"result": "success"}'
    assert after - before == 2

@patch("app.llm_client.time.sleep")
@patch("app.llm_client.completion")
def test_daily_quota_error_skips_retries(mock_completion, mock_sleep):

    mock_completion.side_effect = Exception(
        "Generate content requests per day limit exceeded"
    )

    import pytest

    with pytest.raises(Exception, match="requests per day"):

        call_provider(
            "gemini/test-model",
            "System prompt",
            "User prompt"
        )

    # Daily quota errors should not be retried.
    mock_completion.assert_called_once()
    mock_sleep.assert_not_called()


@patch("app.llm_client.time.sleep")
@patch("app.llm_client.completion")
def test_rate_limit_respects_retry_time(mock_completion, mock_sleep):

    mock_response = MagicMock()

    mock_response.choices[0].message.content = "Successful response."
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_completion.side_effect = [
        Exception("Rate limit exceeded. Please try again in 5 seconds."),
        mock_response
    ]

    result = call_provider(
        "groq/test-model",
        "System prompt",
        "User prompt"
    )

    assert result == "Successful response."

    # Should wait 5 seconds + 1 second safety buffer.
    mock_sleep.assert_called_once_with(6.0)

    assert mock_completion.call_count == 2

def test_gemini_daily_quota_cooldown(monkeypatch):
    import app.llm_client as client
    from unittest.mock import patch

    monkeypatch.setattr(client, "GEMINI_DAILY_QUOTA_EXHAUSTED", False)

    with patch("app.llm_client.call_provider") as mock_call_provider:
        mock_call_provider.side_effect = [
            Exception("Generate content requests per day limit exceeded"),
            "Groq response 1",
            "Groq response 2"
        ]

        # First request: Gemini fails, Groq handles the request.
        result1 = client.call_llm("System prompt", "User prompt")

        assert result1 == "Groq response 1"
        assert client.GEMINI_DAILY_QUOTA_EXHAUSTED is True

        # Second request: Gemini should be skipped.
        result2 = client.call_llm("System prompt", "User prompt")

        assert result2 == "Groq response 2"

        # Only one Gemini call and two Groq calls.
        assert mock_call_provider.call_count == 3

        calls = mock_call_provider.call_args_list

        assert calls[0].args[0].startswith("gemini/")
        assert calls[1].args[0].startswith("groq/")
        assert calls[2].args[0].startswith("groq/")
