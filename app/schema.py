from typing import Literal
from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    ticket: str = Field(
        min_length=10,
        max_length=5000,
        description="Customer support ticket"
    )


class TicketResponse(BaseModel):
    category: Literal[
        "Technical",
        "Billing",
        "Account",
        "Subscription",
        "Delivery",
        "Refund",
        "General",
        "Other"
    ]

    priority: Literal[
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    product: str
    summary: str
    draft_reply: str