"""Vector storage service for managing embeddings."""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from fastembed import TextEmbedding

from src.config.settings import get_settings
from src.models.note import Note, SearchQuery, SearchResult


class VectorStorageService:
    """Service for managing vector storage operations.

    Handles embedding generation, storage, and similarity search for notes.
    """

    COLLECTION_NAME = "notes"
    VECTOR_SIZE = 384  # Size of BAAI/bge-small-en-v1.5 embeddings

    def __init__(self):
        """Initialize vector storage service."""
        settings = get_settings()
        self.client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port
        )
        self.embedding_model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the notes collection exists with proper configuration."""
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

    def store_note(self, note: Note) -> str:
        """Store a note's embedding in the vector database."""
        # Generate embedding for the note
        embedding = self.generate_embeddings(note.content)

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=str(note.id),
                    vector=embedding,
                    payload={
                        "content": note.content,
                        "tags": note.tags,
                        "created_at": note.created_at.isoformat(),
                    }
                )
            ]
        )
        return str(note.id)

    def search(self, query: SearchQuery) -> list[SearchResult]:
        """Search for similar notes using vector similarity."""
        # Generate query embedding
        query_vector = self.generate_embeddings(query.query)

        # Prepare search filters if tags are specified
        search_params = {}
        if query.tags:
            search_params["query_filter"] = models.Filter(
                must=[
                    models.FieldCondition(
                        key="tags", match=models.MatchAny(any=query.tags)
                    )
                ]
            )

        # Search in Qdrant
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=query.limit,
            **search_params,
        )

        # Convert results to SearchResult objects
        search_results = []
        for res in results:
            note = Note(
                id=res.id,
                content=res.payload["content"],
                tags=res.payload["tags"],
                created_at=res.payload["created_at"],
            )
            search_results.append(SearchResult(note=note, score=res.score))

        return search_results

    def delete_note(self, note_id: str):
        """Delete a note's embedding from the vector database."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.PointIdsList(points=[note_id]),
        )
