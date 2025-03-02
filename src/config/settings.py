"""Application configuration management."""

from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseModel):
    """OpenAI API configuration."""

    api_key: str
    base_url: str


class QdrantSettings(BaseModel):
    """Qdrant vector database configuration."""

    host: str = "localhost"
    port: int = 6333


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openai_api_key: str
    openai_base_url: str
    openai_llm_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-ada-002"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def openai(self) -> OpenAISettings:
        """Get OpenAI configuration."""
        return OpenAISettings(
            api_key=self.openai_api_key, base_url=self.openai_base_url
        )

    @property
    def qdrant(self) -> QdrantSettings:
        """Get Qdrant configuration."""
        return QdrantSettings(host=self.qdrant_host, port=self.qdrant_port)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
