from types import SimpleNamespace

import app.llm_client as llm_client


# Simulate Gemini failure and Groq success
def mock_completion(model, messages):

    if model.startswith("gemini/"):
        raise Exception("Simulated Gemini failure")

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Ticket classified successfully by Groq."
                )
            )
        ]
    )


# Replace the actual API call with our mock
llm_client.completion = mock_completion


result = llm_client.call_llm(
    system_prompt="Classify the ticket.",
    user_prompt="My payment was deducted twice."
)

print("\nFinal result:", result)