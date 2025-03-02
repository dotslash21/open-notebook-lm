"""Data models for the note-taking application."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Note(BaseModel):
    """Represents a user's note with metadata."""

    id: UUID = Field(default_factory=uuid4)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    vector_id: str | None = None


class Summary(BaseModel):
    """Contains the processed information from a note."""

    note_id: UUID
    summary: str
    key_points: list[str]
    entities: dict[str, list[str]] = Field(
        default_factory=lambda: {"dates": [], "names": [], "actions": []}
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Represents a search result with similarity score."""

    note: Note
    score: float
    summary: Summary | None = None


class SearchQuery(BaseModel):
    """Represents a search query with optional filters."""

    query: str
    tags: list[str] | None = None
    limit: int = 10
