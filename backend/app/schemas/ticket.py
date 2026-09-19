from datetime import datetime
from enum import Enum
from app.schemas.note import NoteResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TicketCategory(str, Enum):
    PAYMENT = "PAYMENT"
    DELIVERY = "DELIVERY"
    ORDER = "ORDER"
    ACCOUNT = "ACCOUNT"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class CreateTicketRequest(BaseModel):
    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    customer_email: EmailStr

    subject: str = Field(
        ...,
        min_length=3,
        max_length=200
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=5000
    )


class UpdateTicketRequest(BaseModel):
    status: TicketStatus
    notes: str | None = Field(
        default=None,
        max_length=2000
    )


class TicketListResponse(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    created_at: datetime
    sla_due_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TicketDetailResponse(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: EmailStr
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime
    sla_due_at: datetime | None = None
    notes: list[NoteResponse]

    model_config = ConfigDict(from_attributes=True)


class CustomerTrackResponse(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: EmailStr
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateTicketResponse(BaseModel):
    ticket_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)