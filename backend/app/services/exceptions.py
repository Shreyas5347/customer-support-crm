class TicketNotFoundError(Exception):
    """Raised when a requested ticket does not exist."""


class TicketCreationError(Exception):
    """Raised when ticket creation fails."""


class TicketUpdateError(Exception):
    """Raised when ticket update fails."""