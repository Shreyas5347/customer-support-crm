from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.logger import logger
from app.models import Note, Ticket
from app.routes.tickets import router as ticket_router
from app.services.exceptions import (
    TicketCreationError,
    TicketNotFoundError,
    TicketUpdateError,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Support CRM API",
    description="Customer support ticket management system API",
    version="1.0.0",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(TicketNotFoundError)
async def ticket_not_found_handler(request: Request, exc: TicketNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": {
                "code": "TICKET_NOT_FOUND",
                "message": str(exc),
            },
        },
    )


@app.exception_handler(TicketCreationError)
async def ticket_creation_handler(request: Request, exc: TicketCreationError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "TICKET_CREATION_FAILED",
                "message": str(exc),
            },
        },
    )


@app.exception_handler(TicketUpdateError)
async def ticket_update_handler(request: Request, exc: TicketUpdateError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "TICKET_UPDATE_FAILED",
                "message": str(exc),
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed for request parameters or body.",
                "details": exc.errors(),
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error processing request {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        },
    )


app.include_router(ticket_router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}
