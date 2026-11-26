import os
import time
import re

from app.logger import get_logger
from dotenv import load_dotenv
from litellm import completion

from app.metrics import (
    LLM_REQUESTS,
    LLM_LATENCY,
    PROMPT_TOKENS,
    COMPLETION_TOKENS,
    TOTAL_TOKENS,
    PROVIDER_REQUESTS,
    LLM_FAILURES
)

load_dotenv()

logger = get_logger(__name__)
GEMINI_DAILY_QUOTA_EXHAUSTED = False

def is_daily_quota_error(error):
    error_message = str(error).lower()

    daily_quota_keywords = [
        "requests per day",
        "per day limit",
        "daily quota",
        "daily limit",
        "free_tier_requests"
    ]

    return any(
        keyword in error_message
        for keyword in daily_quota_keywords
    )


def get_retry_delay(error, attempt):

    # First, check response headers for Retry-After.
    response = getattr(error, "response", None)

    if response is not None:
        headers = getattr(response, "headers", {})

        retry_after = headers.get("retry-after")

        if retry_after:
            try:
                return min(float(retry_after) + 1, 60)
            except (ValueError, TypeError):
                pass

    # Next, check the error message for suggested retry time.
    error_message = str(error).lower()

    patterns = [
        r"retry after\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)",
        r"try again in\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)",
        r"retry in\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)"
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message)

        if match:
            return min(float(match.group(1)) + 1, 60)

    # If no retry time is provided, use exponential backoff.
    return min(5 * (2 ** attempt), 30)


def call_provider(model: str, system_prompt: str, user_prompt: str):

    max_retries = 3

    for attempt in range(max_retries):

        try:
            start_time = time.perf_counter()

            response = completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
            )

            latency = time.perf_counter() - start_time

            LLM_LATENCY.observe(latency)

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            PROMPT_TOKENS.inc(prompt_tokens)
            COMPLETION_TOKENS.inc(completion_tokens)
            TOTAL_TOKENS.inc(total_tokens)

            logger.info(
                f"Successful response from {model} | "
                f"Latency: {latency:.2f} seconds | "
                f"Prompt Tokens: {prompt_tokens} | "
                f"Completion Tokens: {completion_tokens} | "
                f"Total Tokens: {total_tokens}"
            )

            provider = model.split("/")[0]

            PROVIDER_REQUESTS.labels(provider=provider).inc()

            return response.choices[0].message.content

        except Exception as error:

            provider = model.split("/")[0]

            LLM_FAILURES.labels(provider=provider).inc()

            # Daily quota exhaustion will not recover through retries.
            if is_daily_quota_error(error):

                logger.error(
                    f"{model} daily quota exhausted. "
                    "Skipping retries."
                )

                raise error

            if attempt == max_retries - 1:
                raise error

            wait_time = get_retry_delay(error, attempt)

            logger.warning(
                f"{model} failed: {error}. "
                f"Retrying in {wait_time:.1f} seconds "
                f"(Attempt {attempt + 1}/{max_retries})..."
            )

            time.sleep(wait_time)


def call_llm(system_prompt, user_prompt):
    global GEMINI_DAILY_QUOTA_EXHAUSTED

    LLM_REQUESTS.inc()

    gemini_model = f"gemini/{os.getenv('GEMINI_MODEL')}"
    groq_model = f"groq/{os.getenv('GROQ_MODEL')}"

    if not GEMINI_DAILY_QUOTA_EXHAUSTED:
        try:
            logger.info("Trying primary provider: Gemini")
            return call_provider(gemini_model, system_prompt, user_prompt)

        except Exception as gemini_error:
            logger.error(f"Gemini failed: {gemini_error}")

            if is_daily_quota_error(gemini_error):
                GEMINI_DAILY_QUOTA_EXHAUSTED = True
                logger.warning(
                    "Gemini daily quota exhausted. "
                    "Skipping Gemini for the remainder of this process."
                )
    else:
        logger.warning(
            "Gemini daily quota cooldown is active. Skipping Gemini."
        )

    logger.warning("Switching to backup provider: Groq")

    try:
        return call_provider(groq_model, system_prompt, user_prompt)

    except Exception as groq_error:
        logger.error(f"Groq also failed: {groq_error}")
        raise RuntimeError("Both Gemini and Groq providers failed.") from groq_error