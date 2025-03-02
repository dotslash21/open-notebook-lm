"""Data models for the source management application."""

from datetime import datetime, timezone
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Represents a source with metadata."""

    id: UUID = Field(default_factory=uuid4)
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceSummary(BaseModel):
    """Contains the processed information from a source."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    summary: str
    key_points: list[str]
    entities: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "dates": [],
            "names": [],
            "actions": []
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    """Represents a search result with similarity score."""

    source: Source
    score: float
    summary: SourceSummary | None = None


class SearchQuery(BaseModel):
    """Represents a search query for searching sources."""

    query: str
    limit: int = 10


T = TypeVar("T")


class PaginatedResults(BaseModel, Generic[T]):
    """A paginated list of results."""

    data: list[T]
    limit: int
    offset: int
