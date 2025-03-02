"""Vector storage service for managing embeddings."""

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from src.config.settings import get_settings
from src.models.source import PaginatedResults, SearchQuery, SearchResult, Source


class VectorStorageService:
    """Service for managing vector storage operations."""

    COLLECTION_NAME = "sources"
    VECTOR_SIZE = 384  # Size of BAAI/bge-small-en-v1.5 embeddings

    def __init__(self):
        """Initialize vector storage service."""
        settings = get_settings()
        self.client = QdrantClient(host=settings.qdrant.host, port=settings.qdrant.port)
        self.embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the sources collection exists with proper configuration."""
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
        """Store a source's embedding in the vector database."""

        # Generate embedding for the source
        embedding = self.generate_embeddings(source.content)

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=str(source.id),
                    vector=embedding,
                    payload={
                        "content": source.content,
                        "created_at": source.created_at.isoformat(),
                        "id": source.id,
                    },
                )
            ],
        )
        
        return str(source.id)

    def search(self, query: SearchQuery) -> list[SearchResult]:
        """Search for similar sources using vector similarity."""
        # Generate query embedding
        query_vector = self.generate_embeddings(query.query)

        results = []
        # Search in Qdrant
        db_results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=query.limit,
        )

        # Convert results to SearchResult objects
        for res in db_results:
            source = Source(
                id=res.id,
                content=res.payload["content"],
                created_at=res.payload["created_at"],
            )
            results.append(SearchResult(source=source, score=res.score))

        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[: query.limit]

    def delete_source(self, id: str):
        """Delete the entry for the given source id."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.PointIdsList(points=[id]),
        )

    def list_sources(self, limit: int = 10, offset: int = 0) -> PaginatedResults[Source]:
        """List all available source sources in the vector database."""
        # Fetch all sources
        db_results = self.client.scroll(
            collection_name=self.COLLECTION_NAME, limit=limit, offset=offset
        )

        return PaginatedResults(
            data=[
                Source(
                    id=res.id,
                    content=res.payload["content"],
                    created_at=res.payload["created_at"],
                )
                for res in db_results[0]
            ],
            limit=limit,
            offset=offset,
        )
