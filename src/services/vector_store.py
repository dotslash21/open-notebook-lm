"""Vector storage service for managing embeddings."""

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from src.config.settings import get_settings
from src.models.source import (
    ChunkMatch,
    PaginatedResults,
    SearchQuery,
    SearchResult,
    Source,
    TextChunk,
)


class VectorStorageService:
    """Service for managing vector storage operations."""

    COLLECTION_NAME = "chunks"
    VECTOR_SIZE = 384  # Size of BAAI/bge-small-en-v1.5 embeddings

    def __init__(self):
        """Initialize vector storage service."""
        settings = get_settings()
        self.client = QdrantClient(host=settings.qdrant.host, port=settings.qdrant.port)
        self.embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self._ensure_collection()
        self._sources: dict[str, Source] = {}  # In-memory source storage

    def _ensure_collection(self) -> None:
        """Ensure the chunks collection exists with proper configuration."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE, distance=Distance.COSINE
                ),
            )

    def generate_embeddings(self, text: str) -> list[float]:
        """Generate embeddings for vector storage."""
        embeddings = list(self.embedding_model.embed(text))
        return embeddings[0].tolist()

    def store_source(self, source: Source) -> str:
        """Store source and its chunks."""
        # Store source in memory (could be replaced with proper database)
        self._sources[str(source.id)] = source

        # Store chunks in vector database
        points = []
        for chunk in source.chunks:
            embedding = self.generate_embeddings(chunk.content)

            # Store minimal chunk data with source reference
            points.append(
                models.PointStruct(
                    id=str(chunk.id),
                    vector=embedding,
                    payload={
                        "chunk_id": str(chunk.id),
                        "source_id": str(source.id),
                        "content": chunk.content,
                        "start_index": chunk.start_index,
                        "end_index": chunk.end_index,
                        "section_title": chunk.section_title,
                        "page_number": chunk.page_number,
                        "previous_chunk_id": str(chunk.previous_chunk_id)
                        if chunk.previous_chunk_id
                        else None,
                        "next_chunk_id": str(chunk.next_chunk_id)
                        if chunk.next_chunk_id
                        else None,
                    },
                )
            )

        if points:
            self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)

        return str(source.id)

    def search(self, query: SearchQuery) -> list[SearchResult]:
        """Search for relevant chunks and group by source."""
        # Generate query embedding
        query_vector = self.generate_embeddings(query.query)

        # Search for relevant chunks
        db_results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=query.rerank_count,
            score_threshold=query.min_chunk_score,
        )

        # Group chunks by source
        source_chunks: dict[str, list[tuple[TextChunk, float]]] = {}
        for res in db_results:
            source_id = res.payload["source_id"]
            if source_id not in source_chunks:
                source_chunks[source_id] = []

            chunk = TextChunk(
                id=res.payload["chunk_id"],
                source_id=source_id,
                content=res.payload["content"],
                start_index=res.payload["start_index"],
                end_index=res.payload["end_index"],
                section_title=res.payload["section_title"],
                page_number=res.payload["page_number"],
            )

            # Restore chunk relationships
            if res.payload.get("previous_chunk_id"):
                chunk.previous_chunk_id = res.payload["previous_chunk_id"]
            if res.payload.get("next_chunk_id"):
                chunk.next_chunk_id = res.payload["next_chunk_id"]

            source_chunks[source_id].append((chunk, res.score))

        # Convert to search results
        results = []
        for source_id, chunks in source_chunks.items():
            # Get source from memory
            source = self._sources.get(source_id)
            if not source:
                continue  # Skip if source not found

            # Create chunk matches
            matched_chunks = [
                ChunkMatch(chunk=chunk, score=score) for chunk, score in chunks
            ]

            # Calculate result scores
            max_chunk_score = max(match.score for match in matched_chunks)
            coverage_score = len(matched_chunks) / query.rerank_count
            combined_score = 0.7 * max_chunk_score + 0.3 * coverage_score

            results.append(
                SearchResult(
                    source=source,
                    matched_chunks=matched_chunks,
                    combined_score=combined_score,
                    max_chunk_score=max_chunk_score,
                    chunk_coverage=coverage_score,
                )
            )

        # Sort by combined score and limit
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[: query.limit]

    def search_source_chunks(self, source_id: str, query: SearchQuery) -> SearchResult:
        """Search for chunks within a specific source."""
        # Check if source exists
        source = self._sources.get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        # Generate query embedding
        query_vector = self.generate_embeddings(query.query)

        # Search with source filter
        db_results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id", match=models.MatchValue(value=source_id)
                    )
                ]
            ),
            limit=query.limit,
            score_threshold=query.min_chunk_score,
        )

        # Create chunk matches
        matched_chunks = []
        for res in db_results:
            chunk = TextChunk(
                id=res.payload["chunk_id"],
                source_id=source_id,
                content=res.payload["content"],
                start_index=res.payload["start_index"],
                end_index=res.payload["end_index"],
                section_title=res.payload["section_title"],
                page_number=res.payload["page_number"],
            )
            matched_chunks.append(ChunkMatch(chunk=chunk, score=res.score))

        # Calculate scores
        max_score = max((m.score for m in matched_chunks), default=0)
        coverage = len(matched_chunks) / query.limit

        return SearchResult(
            source=source,
            matched_chunks=matched_chunks,
            combined_score=0.7 * max_score + 0.3 * coverage,
            max_chunk_score=max_score,
            chunk_coverage=coverage,
        )

    def delete_source(self, source_id: str) -> None:
        """Delete source and its chunks."""
        # Delete chunks from vector database
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id", match=models.MatchValue(value=source_id)
                    )
                ]
            ),
        )

        # Remove source from memory
        self._sources.pop(source_id, None)

    def list_sources(
        self, limit: int = 10, offset: int = 0
    ) -> PaginatedResults[Source]:
        """List available sources from memory store."""
        sources = list(self._sources.values())
        start_idx = offset
        end_idx = offset + limit

        return PaginatedResults(
            data=sources[start_idx:end_idx], limit=limit, offset=offset
        )
