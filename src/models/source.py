"""Data models for the source management application."""

from datetime import UTC, datetime
from enum import Enum
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EntityType(Enum):
    """Types of entities that can be extracted from text."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    EVENT = "event"
    CONCEPT = "concept"


class TextChunk(BaseModel):
    """Represents a chunk of text with its metadata and enhancements."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    content: str
    start_index: int  # Character index where this chunk starts in the source
    end_index: int  # Character index where this chunk ends in the source
    entities: dict[EntityType, list[str]] = Field(
        default_factory=lambda: {t: [] for t in EntityType}
    )
    section_title: str | None = None
    page_number: int | None = None
    previous_chunk_id: UUID | None = None
    next_chunk_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Source(BaseModel):
    """Represents a source with metadata."""

    id: UUID = Field(default_factory=uuid4)
    type: str | None = None
    content: str
    chunks: list[TextChunk] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChunkMatch(BaseModel):
    """Represents a matched chunk with its relevance information."""

    chunk: TextChunk
    score: float
    context_overlap: float = 0.0  # Semantic overlap with other retrieved chunks
    query_term_overlap: float = 0.0  # Lexical overlap with query terms


class SearchResult(BaseModel):
    """Represents a search result with enhanced ranking information."""

    source: Source
    matched_chunks: list[ChunkMatch]  # Chunks that matched the query
    combined_score: float  # Overall relevance score
    max_chunk_score: float  # Highest individual chunk score
    chunk_coverage: float  # Percentage of query terms covered by all chunks


class SearchQuery(BaseModel):
    """Represents a search query for searching sources."""

    query: str
    limit: int = 10
    min_chunk_score: float = 0.7  # Minimum score for chunk inclusion
    rerank_count: int = 20  # Number of initial results to consider for reranking


T = TypeVar("T")


class PaginatedResults(BaseModel, Generic[T]):
    """A paginated list of results."""

    data: list[T]
    limit: int
    offset: int
