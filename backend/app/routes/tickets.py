from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CreateTicketRequest,
    CreateTicketResponse,
    CustomerTrackResponse,
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
    track_ticket,
    update_ticket,
    delete_ticket,
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
    "/track",
    response_model=CustomerTrackResponse,
    status_code=status.HTTP_200_OK,
    summary="Track a ticket by ID and Email",
    description="Allows customers to track their own ticket status securely using Ticket ID and Email. Does not reveal internal notes or other tickets.",
)
def track_customer_ticket(
    ticket_id: str = Query(..., description="Ticket ID (e.g. TKT-72EEA95B)"),
    email: str = Query(..., description="Customer Email address"),
    db: Session = Depends(get_db)
):
    return track_ticket(
        db=db,
        ticket_id=ticket_id,
        email=email
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
    status: str | None = Query(None, description="Filter by ticket status (e.g. Open, OPEN, IN_PROGRESS, Closed)"),
    priority: str | None = Query(None, description="Filter by ticket priority"),
    category: str | None = Query(None, description="Filter by ticket category"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of tickets per page"),
    db: Session = Depends(get_db)
):
    status_enum = None
    if status:
        try:
            status_enum = TicketStatus(status.upper().strip().replace(" ", "_"))
        except ValueError:
            pass

    priority_enum = None
    if priority:
        try:
            priority_enum = TicketPriority(priority.upper().strip())
        except ValueError:
            pass

    category_enum = None
    if category:
        try:
            category_enum = TicketCategory(category.upper().strip())
        except ValueError:
            pass

    return list_tickets(
        db=db,
        status=status_enum,
        search=search,
        priority=priority_enum,
        category=category_enum,
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


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a ticket",
    description="Deletes a ticket by its ID.",
)
def delete_existing_ticket(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    delete_ticket(
        db=db,
        ticket_id=ticket_id
    )
