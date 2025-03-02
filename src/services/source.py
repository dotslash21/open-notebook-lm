"""Source service for managing source operations."""

from src.models.source import (
    PaginatedResults,
    SearchQuery,
    SearchResult,
    Source,
    SourceSummary,
)
from src.services.llm import LLMService
from src.services.vector_store import VectorStorageService


class SourceService:
    """Service for managing source operations."""

    def __init__(self) -> None:
        """Initialize source service with required dependencies."""
        self.llm_service = LLMService()
        self.vector_store = VectorStorageService()
        self._sources: dict[str, Source] = {}
        self._summaries: dict[str, SourceSummary] = {}

    def create_source(self, content: str) -> Source:
        """Create a new source, process it, and store it."""
        # Create source
        source = Source(content=content)

        # Generate summary using LLM
        summary = self.llm_service.generate_summary(source)

        # Store in vector database
        self.vector_store.store_source(source)

        # Store in memory
        self._sources[str(source.id)] = source
        self._summaries[str(source.id)] = summary

        return source

    def get_source(self, source_id: str) -> Source | None:
        """Retrieve a source by its ID."""
        return self._sources.get(source_id)

    def get_source_summary(self, source_id: str) -> SourceSummary | None:
        """Retrieve a source's summary by source ID."""
        return self._summaries.get(source_id)

    def get_response(self, source_id: str, query: str) -> str:
        """Get a response to a query that is grounded in the source's content."""
        source = self.get_source(source_id)
        if not source:
            raise ValueError("Source not found")

        return self.llm_service.generate_grounded_response(source.content, query)

    def search_sources(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for sources using semantic similarity."""
        search_query = SearchQuery(query=query, limit=limit)
        results = self.vector_store.search(search_query)

        # Enhance results with summaries if available
        for result in results:
            source_id = str(result.source.id)
            if source_id in self._summaries:
                result.summary = self._summaries[source_id]

        return results

    def delete_source(self, source_id: str) -> bool:
        """Delete a source and its associated data."""
        if source_id not in self._sources:
            return False

        # Remove from vector store
        self.vector_store.delete_source(source_id)

        # Remove from memory
        del self._sources[source_id]
        if source_id in self._summaries:
            del self._summaries[source_id]

        return True

    def list_sources(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedResults[Source]:
        """List all available sources."""
        return self.vector_store.list_sources(limit=limit, offset=offset)
