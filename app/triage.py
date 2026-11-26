from app.prompt_manager import load_prompt
from app.llm_client import call_llm
from app.schema import TicketResponse


UNSAFE_PHRASES = [
    "i have processed your refund",
    "your refund has been processed",
    "i have escalated",
    "i have located your account",
    "i have submitted a request",
    "your replacement has been dispatched",
    "your refund will arrive",
    "your refund will be credited",
    "within 3-5 business days",
    "within 3 to 5 business days",
]


SAFE_FALLBACK_REPLY = (
    "Thank you for contacting us. We understand your concern "
    "and apologize for any inconvenience. Our support team "
    "will need to review the details of your issue before "
    "confirming the next steps. Please share the relevant "
    "reference information so we can assist you further."
)


def validate_draft_reply(reply: str) -> str:
    reply_lower = reply.lower()

    for phrase in UNSAFE_PHRASES:
        if phrase in reply_lower:
            return SAFE_FALLBACK_REPLY

    return reply


def process_ticket(ticket: str):
    prompt = load_prompt()

    system_prompt = prompt["system_prompt"]
    user_prompt = prompt["user_prompt"].format(ticket=ticket)

    llm_response = call_llm(system_prompt, user_prompt)

    result = TicketResponse.model_validate_json(llm_response)

    result.draft_reply = validate_draft_reply(result.draft_reply)

    return result