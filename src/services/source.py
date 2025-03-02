"""Source service for managing source operations."""

from src.models.source import (
    PaginatedResults,
    SearchQuery,
    SearchResult,
    Source,
)
from src.services.llm import LLMService
from src.services.text_processing import TextProcessingService
from src.services.vector_store import VectorStorageService


class SourceService:
    """Service for managing source operations."""

    def __init__(self) -> None:
        """Initialize source service with required dependencies."""
        self.llm_service = LLMService()
        self.vector_store = VectorStorageService()
        self.text_processor = TextProcessingService()

    def create_source(self, content: str) -> Source:
        """Create a new source with preprocessed chunks."""
        # Create source with preprocessed chunks
        source = self.text_processor.process_source(content)

        # Store in vector database
        self.vector_store.store_source(source)

        return source

    def get_response(self, source_id: str, query: str) -> str:
        """Get a response to a query grounded in relevant chunks."""
        # Get relevant chunks from the source
        result = self.vector_store.search_source_chunks(
            source_id, SearchQuery(query=query)
        )
        if not result.matched_chunks:
            return "No relevant content found for this query."

        # Extract relevant chunk content with metadata
        chunk_contexts = []
        for match in result.matched_chunks:
            chunk = match.chunk
            context = chunk.content
            if chunk.section_title:
                context = f"{chunk.section_title}:\n{context}"
            chunk_contexts.append(context)

        # Join chunks with markers
        combined_context = "\n---\n".join(chunk_contexts)

        # Generate grounded response
        return self.llm_service.generate_grounded_response(combined_context, query)

    def search_sources(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for sources based on relevant chunks."""
        # Search with chunk-based ranking
        search_query = SearchQuery(query=query, limit=limit)
        return self.vector_store.search(search_query)

    def delete_source(self, source_id: str) -> bool:
        """Delete a source and its associated data."""
        try:
            self.vector_store.delete_source(source_id)
            return True
        except ValueError:
            return False

    def list_sources(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedResults[Source]:
        """List all available sources."""
        return self.vector_store.list_sources(limit=limit, offset=offset)
