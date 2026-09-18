from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CreateTicketRequest,
    CreateTicketResponse,
    TicketCategory,
    TicketDetailResponse,
    TicketListResponse,
    TicketPriority,
    TicketStatus,
    UpdateTicketRequest,
)
from app.services import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
)

router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"]
)


@router.post(
    "",
    response_model=CreateTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
    description="Creates a new customer support ticket, generating a unique TKT-XXXXXXXX ID.",
)
def create_new_ticket(
    ticket_data: CreateTicketRequest,
    db: Session = Depends(get_db)
):
    return create_ticket(
        db=db,
        ticket_data=ticket_data
    )


@router.get(
    "",
    response_model=list[TicketListResponse],
    status_code=status.HTTP_200_OK,
    summary="List support tickets",
    description="Retrieves a list of tickets with optional search across name/email/ID/subject/description, filtering by status/priority/category, and pagination.",
)
def list_all_tickets(
    search: str | None = Query(None, description="Search string across ticket ID, customer name, email, subject, or description"),
    status: TicketStatus | None = Query(None, description="Filter by ticket status"),
    priority: TicketPriority | None = Query(None, description="Filter by ticket priority"),
    category: TicketCategory | None = Query(None, description="Filter by ticket category"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of tickets per page"),
    db: Session = Depends(get_db)
):
    return list_tickets(
        db=db,
        status=status,
        search=search,
        priority=priority,
        category=category,
        page=page,
        limit=limit,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ticket details",
    description="Retrieves full ticket information by ticket_id including all internal notes.",
)
def get_ticket_by_id(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    return get_ticket(
        db=db,
        ticket_id=ticket_id
    )


@router.put(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update ticket status",
    description="Updates ticket status and creates an internal note within a single transaction.",
)
def update_existing_ticket(
    ticket_id: str,
    update_data: UpdateTicketRequest,
    db: Session = Depends(get_db)
):
    return update_ticket(
        db=db,
        ticket_id=ticket_id,
        update_data=update_data
    )