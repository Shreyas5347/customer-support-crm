from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.logger import logger
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


def generate_ticket_id() -> str:
    unique_part = uuid4().hex[:8].upper()
    return f"TKT-{unique_part}"


def create_ticket(
    db: Session,
    ticket_data: CreateTicketRequest,
) -> Ticket:
    try:
        ticket = Ticket(
            ticket_id=generate_ticket_id(),
            customer_name=ticket_data.customer_name.strip(),
            customer_email=str(ticket_data.customer_email),
            subject=ticket_data.subject.strip(),
            description=ticket_data.description.strip(),
            status=TicketStatus.OPEN.value,
            priority=TicketPriority.MEDIUM.value,
            category=TicketCategory.OTHER.value,
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        logger.info(f"Ticket created: {ticket.ticket_id}")
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

    return list(db.scalars(query).all())


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
        db.refresh(ticket)

        logger.info(f"Ticket updated: {ticket.ticket_id}")
        return ticket

    except TicketNotFoundError:
        raise

    except Exception as exc:
        db.rollback()
        logger.error(f"Database error while updating ticket {ticket_id}: {exc}")
        raise TicketUpdateError(
            "Unable to update ticket."
        ) from exc


