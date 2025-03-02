"""LLM service for text processing and analysis."""

import json

from openai import OpenAI

from src.config.settings import get_settings
from src.models.source import Source, SourceSummary


class LLMService:
    """Service for interacting with Language Models."""

    def __init__(self):
        """Initialize LLM service with configuration."""
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai.api_key, base_url=self.settings.openai.base_url
        )

    def generate_grounded_response(self, source_content: str, query: str) -> str:
        """Generate a response that is grounded in the provided source content."""
        system_msg = """
        You are a helpful assistant that answers questions based ONLY on the provided source content.
        If the answer cannot be determined from the source content, say so.
        Always cite specific parts of the source to support your answers.
        Do not make assumptions or add information beyond what's in the source.
        """

        response = self.client.chat.completions.create(
            model=self.settings.openai_llm_model,
            messages=[
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": f"Source content:\n{source_content}\n\nQuestion: {query}",
                },
            ],
        )

        if not response.choices:
            raise ValueError("No response received from the LLM.")

        return response.choices[0].message.content

    def generate_summary(self, source: Source) -> SourceSummary:
        """Generate a summary and extract key information from a source."""
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
            response_format=SourceSummary,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": source.content},
            ],
        )

        if not response.choices:
            raise ValueError("No choices returned from the LLM.")

        result = response.choices[0].message.content
        data = json.loads(result)  # Parse JSON response safely

        # Safely extract entities with fallbacks
        entities = data.get("entities", {})

        return SourceSummary(
            source_id=source.id,
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            entities={
                "dates": entities.get("dates", []),
                "names": entities.get("names", []),
                "actions": entities.get("actions", []),
            },
        )
