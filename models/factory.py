"""
Factory for creating model providers.
"""
from enum import Enum
from typing import Optional
from .base import BaseModelProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


class ModelType(str, Enum):
    """Supported model types."""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"


def get_model_provider(
    model_type: ModelType,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> BaseModelProvider:
    """
    Factory function to create model providers.

    Args:
        model_type: Type of model provider (ollama, gemini, openai)
        model_name: Specific model name to use
        api_key: API key for cloud providers

    Returns:
        Instance of the appropriate model provider
    """
    if model_type == ModelType.OLLAMA:
        return OllamaProvider(
            model_name=model_name or "llama3.1"
        )
    elif model_type == ModelType.GEMINI:
        return GeminiProvider(
            model_name=model_name or "gemini-pro",
            api_key=api_key
        )
    elif model_type == ModelType.OPENAI:
        return OpenAIProvider(
            model_name=model_name or "gpt-4o-mini",
            api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
