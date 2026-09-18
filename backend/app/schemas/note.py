from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateNoteRequest(BaseModel):
    note_text: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )


class NoteResponse(BaseModel):
    id: int
    note_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)