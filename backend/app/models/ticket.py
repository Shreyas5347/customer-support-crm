from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    ticket_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    customer_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM"
    )

    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OTHER"
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    notes = relationship(
        "Note",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
        "status IN ('OPEN', 'IN_PROGRESS', 'CLOSED')",
        name="check_ticket_status"
         ),
        CheckConstraint(
            "priority IN ('HIGH', 'MEDIUM', 'LOW')",
            name="check_ticket_priority"
        ),
        CheckConstraint(
            "category IN ('PAYMENT', 'DELIVERY', 'ORDER', 'ACCOUNT', 'TECHNICAL', 'OTHER')",
            name="check_ticket_category"
        ),
        Index("ix_tickets_created_at", "created_at"),
    )