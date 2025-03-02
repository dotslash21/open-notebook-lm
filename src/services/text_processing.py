"""Service for processing text content with preprocessing, chunking, and enhancement."""

import re
import unicodedata
from uuid import UUID

import dateparser
import spacy
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.models.source import EntityType, Source, TextChunk

# Map spaCy entity labels to our EntityType enum
SPACY_ENTITY_MAP = {
    "PERSON": EntityType.PERSON,
    "ORG": EntityType.ORGANIZATION,
    "GPE": EntityType.LOCATION,  # Geo-Political Entity
    "LOC": EntityType.LOCATION,  # Other locations
    "DATE": EntityType.DATE,
    "EVENT": EntityType.EVENT,
}


class TextProcessingService:
    """Service for processing and enhancing text content."""

    def __init__(self) -> None:
        """Initialize the text processing service."""
        # OpenAI's encoding
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = 400  # Target tokens per chunk
        self.chunk_overlap = 50  # Overlap between chunks in tokens

        # Initialize spaCy model with entity recognition
        self.nlp = spacy.load("en_core_web_sm")

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            # Approximate character count for desired token length
            chunk_size=2000,
            chunk_overlap=250,  # Character overlap
            length_function=lambda text: len(self.tokenizer.encode(text)),
            separators=["\n\n", "\n", " ", ""],
        )

    def preprocess_text(
        self, text: str, filename: str | None = None
    ) -> tuple[str, dict]:
        """Clean and normalize text content."""
        # Extract potential metadata
        metadata = self._extract_metadata(text, filename)

        # Normalize unicode characters
        text = unicodedata.normalize("NFKC", text)

        # Process with spaCy for initial cleaning
        doc = self.nlp(text)

        # Join sentences with appropriate spacing
        text = " ".join(sent.text.strip() for sent in doc.sents)

        # Remove redundant whitespace while preserving paragraph structure
        text = re.sub(r"\n\s*\n\s*", "\n\n", text)
        text = re.sub(r" +", " ", text)

        return text, metadata

    def _extract_metadata(self, text: str) -> dict[str, str]:
        """Use spaCy and dateparser to extract metadata from text content."""
        metadata: dict[str, str] = {}

        # Process with spaCy
        doc = self.nlp(text[:5000])  # Process first 5000 chars for efficiency

        # Extract title from first sentence if it's reasonably short
        if doc.sents:
            first_sent = next(doc.sents)
            if len(first_sent.text) < 100:
                metadata["title"] = first_sent.text.strip()

        # Look for authors using spaCy's NER
        person_names = []
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                person_names.append(ent.text)
        if person_names:
            metadata["author"] = ", ".join(person_names[:2])  # First two names only

        # Extract dates using dateparser for robust date recognition
        dates = []
        for ent in doc.ents:
            if ent.label_ == "DATE":
                parsed_date = dateparser.parse(ent.text)
                if parsed_date:
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
        if dates:
            metadata["creation_date"] = dates[0]  # Use first found date

        return metadata

    def create_chunks(self, source_id: UUID, text: str) -> list[TextChunk]:
        """Use LangChain to split text into overlapping chunks with metadata."""
        # Create base chunks using LangChain
        raw_chunks = self.text_splitter.split_text(text)
        chunks: list[TextChunk] = []

        # Process text with spaCy to identify sections and other metadata
        doc = self.nlp(text)

        # Identify sections using header detection
        sections: list[tuple[int, str]] = []
        for sent in doc.sents:
            if (
                sent.text.strip().isupper()
                or re.match(r"^#+\s+", sent.text)  # Markdown headers
                or re.match(r"^\d+\.\s+[A-Z]", sent.text)  # Numbered sections
            ):
                sections.append((sent.start_char, sent.text.strip()))

        current_section = None
        last_end = 0

        for chunk_text in raw_chunks:
            # Find chunk boundaries in original text
            start_idx = text.find(chunk_text, last_end)
            if start_idx == -1:
                continue
            end_idx = start_idx + len(chunk_text)
            last_end = end_idx

            # Update section based on chunk position
            for sec_pos, sec_title in sections:
                if sec_pos <= start_idx:
                    current_section = sec_title
                else:
                    break

            chunk = TextChunk(
                source_id=source_id,
                content=chunk_text,
                start_index=start_idx,
                end_index=end_idx,
                section_title=current_section,
            )
            chunks.append(chunk)

        # Link chunks
        for i in range(len(chunks)):
            if i > 0:
                chunks[i].previous_chunk_id = chunks[i - 1].id
            if i < len(chunks) - 1:
                chunks[i].next_chunk_id = chunks[i + 1].id

        return chunks

    def extract_entities(self, text: str) -> dict[EntityType, list[str]]:
        """Extract entities from text using spaCy's NER."""
        entities = {t: [] for t in EntityType}

        # Process text with spaCy
        doc = self.nlp(text)

        # Extract entities using spaCy's NER
        for ent in doc.ents:
            if ent.label_ in SPACY_ENTITY_MAP:
                entity_type = SPACY_ENTITY_MAP[ent.label_]
                entities[entity_type].append(ent.text)

        # Additional processing for dates using dateparser
        for ent in doc.ents:
            if ent.label_ == "DATE":
                parsed_date = dateparser.parse(ent.text)
                if parsed_date:
                    entities[EntityType.DATE].append(parsed_date.strftime("%Y-%m-%d"))

        # Look for potential events (conferences, meetings, etc.)
        event_pattern = (
            r"(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
            r"(?:Conference|Summit|Meeting|Workshop|Symposium))"
        )
        for match in re.finditer(event_pattern, text):
            entities[EntityType.EVENT].append(match.group(1))

        # Get concepts (important noun phrases not already categorized)
        for np in doc.noun_chunks:
            if (
                np.text[0].isupper()  # Starts with capital letter
                and len(np.text.split()) <= 3  # Not too long
                and not any(np.text in ent_list for ent_list in entities.values())
            ):
                entities[EntityType.CONCEPT].append(np.text)

        # Remove duplicates and sort
        for entity_type in entities:
            entities[entity_type] = sorted(set(entities[entity_type]))

        return entities

    def process_source(self, content: str, filename: str | None = None) -> Source:
        """Process a text source: preprocess, chunk, and extract entities."""
        # Preprocess text
        cleaned_text, metadata = self.preprocess_text(content, filename)

        # Create source with metadata
        source = Source(content=cleaned_text, metadata=metadata)

        # Create chunks
        chunks = self.create_chunks(source.id, cleaned_text)

        # Extract entities for each chunk
        for chunk in chunks:
            chunk.entities = self.extract_entities(chunk.content)

        source.chunks = chunks
        return source
