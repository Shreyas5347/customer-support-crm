from enum import Enum

from pydantic import BaseModel, Field


class TriagePriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TriageCategory(str, Enum):
    PAYMENT = "PAYMENT"
    DELIVERY = "DELIVERY"
    ORDER = "ORDER"
    ACCOUNT = "ACCOUNT"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class TicketTriageResult(BaseModel):
    priority: TriagePriority
    category: TriageCategory
    summary: str = Field(
        min_length=10,
        max_length=500
    )