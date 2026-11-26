from prometheus_client import Counter, Histogram

LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total number of LLM requests"
)

LLM_LATENCY = Histogram(
    "llm_request_latency_seconds",
    "Time spent processing LLM requests"
)

PROMPT_TOKENS = Counter(
    "llm_prompt_tokens_total",
    "Total number of prompt tokens used"
)

COMPLETION_TOKENS = Counter(
    "llm_completion_tokens_total",
    "Total number of completion tokens generated"
)

TOTAL_TOKENS = Counter(
    "llm_total_tokens",
    "Total number of tokens consumed"
)

PROVIDER_REQUESTS = Counter(
    "llm_provider_requests_total",
    "Total number of requests handled by each LLM provider",
    ["provider"]
)

LLM_FAILURES = Counter(
    "llm_failures_total",
    "Total number of failed LLM provider attempts",
    ["provider"]
)