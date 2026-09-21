import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.services.triage_service import triage_ticket
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)
from app.models.ticket import Ticket
from app.models.note import Note
from app.schemas.ticket import (
    CreateTicketRequest,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UpdateTicketRequest,
)
from app.services.exceptions import (
    TicketCreationError,
    TicketNotFoundError,
    TicketUpdateError,
)

SLA_HOURS = {
    "HIGH": 4,
    "MEDIUM": 24,
    "LOW": 48,
}


def generate_ticket_id() -> str:
    unique_part = uuid4().hex[:8].upper()
    return f"TKT-{unique_part}"


def calculate_sla_due_at(created_at: datetime, priority: str) -> datetime:
    hours = SLA_HOURS.get(priority, 24)
    return created_at + timedelta(hours=hours)


def create_ticket(
    db: Session,
    ticket_data: CreateTicketRequest,
) -> Ticket:
    try:
        ticket_id = generate_ticket_id()
        # AI Triage
        triage_result = triage_ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
        )
        now = datetime.now(timezone.utc)
        hours = SLA_HOURS.get(triage_result.priority.value, 24)
        sla_due = now + timedelta(hours=hours)

        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=ticket_data.customer_name.strip(),
            customer_email=str(ticket_data.customer_email),
            subject=ticket_data.subject.strip(),
            description=ticket_data.description.strip(),
            status=TicketStatus.OPEN.value,
            priority=triage_result.priority.value,
            category=triage_result.category.value,
            ai_summary=triage_result.summary,
            sla_due_at=sla_due,
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(f"Ticket created: {ticket.ticket_id} with SLA due at {sla_due}")
        return ticket

    except Exception as exc:
        db.rollback()
        logger.error(f"Database error while creating ticket: {exc}")
        raise TicketCreationError(
            "Unable to create ticket."
        ) from exc


def list_tickets(
    db: Session,
    status: TicketStatus | None = None,
    search: str | None = None,
    priority: TicketPriority | None = None,
    category: TicketCategory | None = None,
    page: int = 1,
    limit: int = 20,
) -> list[Ticket]:
    query = select(Ticket)

    if status:
        query = query.where(
            Ticket.status == status.value
        )

    if priority:
        query = query.where(
            Ticket.priority == priority.value
        )

    if category:
        query = query.where(
            Ticket.category == category.value
        )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                Ticket.ticket_id.ilike(search_term),
                Ticket.customer_name.ilike(search_term),
                Ticket.customer_email.ilike(search_term),
                Ticket.subject.ilike(search_term),
                Ticket.description.ilike(search_term),
            )
        )

    query = query.order_by(
        Ticket.created_at.desc()
    )

    offset_val = (page - 1) * limit
    query = query.offset(offset_val).limit(limit)

    tickets = list(db.scalars(query).all())
    for t in tickets:
        if t.sla_due_at is None and t.created_at:
            t.sla_due_at = calculate_sla_due_at(t.created_at, t.priority)
    return tickets


def get_ticket(
    db: Session,
    ticket_id: str,
) -> Ticket:
    query = (
        select(Ticket)
        .where(Ticket.ticket_id == ticket_id)
        .options(selectinload(Ticket.notes))
    )

    ticket = db.scalars(query).first()

    if ticket is None:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise TicketNotFoundError(
            f"Ticket '{ticket_id}' was not found."
        )

    if ticket.sla_due_at is None and ticket.created_at:
        ticket.sla_due_at = calculate_sla_due_at(ticket.created_at, ticket.priority)

    return ticket


def track_ticket(
    db: Session,
    ticket_id: str,
    email: str,
) -> Ticket:
    clean_id = ticket_id.strip().upper()
    clean_email = email.strip().lower()

    query = (
        select(Ticket)
        .where(
            Ticket.ticket_id == clean_id,
            Ticket.customer_email.ilike(clean_email)
        )
    )

    ticket = db.scalars(query).first()

    if ticket is None:
        logger.warning(f"Ticket tracking failed for ID: {clean_id}, email: {clean_email}")
        raise TicketNotFoundError(
            f"No ticket found matching ID '{clean_id}' and Email '{clean_email}'."
        )

    return ticket



def update_ticket(
    db: Session,
    ticket_id: str,
    update_data: UpdateTicketRequest,
) -> Ticket:
    try:
        ticket = get_ticket(db, ticket_id)

        ticket.status = update_data.status.value

        if update_data.notes:
            note_text = update_data.notes.strip()

            if note_text:
                note = Note(
                    ticket_id=ticket.id,
                    note_text=note_text,
                )

                db.add(note)

        db.commit()
        logger.info(f"Ticket updated: {ticket.ticket_id}")
        return get_ticket(db, ticket_id)

    except TicketNotFoundError:
        raise

    except Exception as exc:
        db.rollback()
        logger.error(f"Database error while updating ticket {ticket_id}: {exc}")
        raise TicketUpdateError(
            "Unable to update ticket."
        ) from exc

def delete_ticket(
    db: Session,
    ticket_id: str,
) -> None:
    try:
        ticket = get_ticket(db, ticket_id)
        db.delete(ticket)
        db.commit()
        logger.info(f"Ticket deleted: {ticket_id}")
    except TicketNotFoundError:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Database error while deleting ticket {ticket_id}: {exc}")
        raise TicketUpdateError(
            "Unable to delete ticket."
        ) from exc
