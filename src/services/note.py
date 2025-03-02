"""Note service for managing note operations."""


from src.models.note import Note, SearchQuery, SearchResult, Summary
from src.services.llm import LLMService
from src.services.vector_store import VectorStorageService


class NoteService:
    """Service for managing note operations."""

    def __init__(self):
        """Initialize note service with required dependencies."""
        self.llm_service = LLMService()
        self.vector_store = VectorStorageService()
        self._notes: dict[str, Note] = {}  # In-memory storage for demo
        self._summaries: dict[str, Summary] = {}

    def create_note(self, content: str, tags: list[str] | None = None) -> Note:
        """Create a new note, process it, and store it."""
        # Create note
        note = Note(content=content, tags=tags or [])

        # Generate summary using LLM
        summary = self.llm_service.generate_summary(note)

        # Store in vector database
        vector_id = self.vector_store.store_note(note)
        note.vector_id = vector_id

        # Store in memory
        self._notes[str(note.id)] = note
        self._summaries[str(note.id)] = summary

        return note

    def get_note(self, note_id: str) -> Note | None:
        """Retrieve a note by its ID."""
        return self._notes.get(note_id)

    def get_summary(self, note_id: str) -> Summary | None:
        """Retrieve a note's summary by note ID."""
        return self._summaries.get(note_id)

    def search_notes(
        self, query: str, tags: list[str] | None = None, limit: int = 10
    ) -> list[SearchResult]:
        """Search for notes using semantic similarity."""
        search_query = SearchQuery(query=query, tags=tags, limit=limit)
        results = self.vector_store.search(search_query)

        # Enhance results with summaries if available
        for result in results:
            note_id = str(result.note.id)
            if note_id in self._summaries:
                result.summary = self._summaries[note_id]

        return results

    def delete_note(self, note_id: str) -> bool:
        """Delete a note and its associated data."""
        if note_id not in self._notes:
            return False

        # Remove from vector store
        self.vector_store.delete_note(note_id)

        # Remove from memory
        del self._notes[note_id]
        if note_id in self._summaries:
            del self._summaries[note_id]

        return True
