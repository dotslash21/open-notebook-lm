"""LLM service for text processing and analysis."""

import json
import uuid
from openai import OpenAI

from src.config.settings import get_settings
from src.models.note import Note, Summary

class LLMService:
    """Service for interacting with Language Models."""

    def __init__(self):
        """Initialize LLM service with configuration."""
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai.api_key,
            base_url=self.settings.openai.base_url
        )

    def generate_summary(self, note: Note) -> Summary:
        """Generate a summary and extract key information from a note."""
        # System message to define the task
        system_msg = """
        Analyze the given text and provide:
        1. A concise summary
        2. Key points (max 5)
        3. Extract entities:
           - Dates and temporal references
           - Names (people, organizations)
           - Action items or tasks
        Format as JSON with the following structure:
        {
            "summary": "concise summary text",
            "key_points": ["point 1", "point 2", ...],
            "entities": {
                "dates": ["date 1", "date 2", ...],
                "names": ["name 1", "name 2", ...],
                "actions": ["action 1", "action 2", ...]
            }
        }
        """

        # Get completion from LLM
        response = self.client.beta.chat.completions.parse(
            model=self.settings.openai_llm_model,
            response_format=Summary,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": note.content},
            ],
        )

        if not response.choices:
            raise ValueError("No choices returned from the LLM.")
        
        result = response.choices[0].message.content
        data = json.loads(result)  # Parse JSON response safely

        # Safely extract entities with fallbacks
        entities = data.get("entities", {})
        
        return Summary(
            note_id=uuid.uuid4(),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            entities={
                "dates": entities.get("dates", []),
                "names": entities.get("names", []),
                "actions": entities.get("actions", [])
            },
        )
