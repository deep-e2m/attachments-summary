"""
Configuration settings for the Summary API.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    app_name: str = "Summary API"
    debug: bool = False

    # Default Model Configuration
    default_model_type: str = Field(default="openrouter", description="Default model: ollama, gemini, openai, openrouter")
    default_model_name: str = Field(default="openai/gpt-4o-mini", description="Default model name")

    # OpenRouter Settings (PRIMARY - One API for all models)
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    openrouter_default_model: str = Field(default="openai/gpt-4o-mini", description="Default OpenRouter model")

    # Ollama Settings (Local - for development)
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server host")
    ollama_model: str = Field(default="llama3.1", description="Ollama model name")

    # Gemini Settings (Legacy - use OpenRouter instead)
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-pro", description="Gemini model name")

    # OpenAI Settings (Legacy - use OpenRouter instead)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")

    # File Processing Settings
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    temp_dir: str = Field(default="/tmp/summary_api", description="Temporary directory for file processing")

    # Whisper Settings (for video transcription)
    whisper_model: str = Field(default="base", description="Whisper model size: tiny, base, small, medium, large")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
