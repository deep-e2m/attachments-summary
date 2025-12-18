"""
Factory for creating model providers.
"""
from enum import Enum
from typing import Optional
from .base import BaseModelProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider, OPENROUTER_MODELS


class ModelType(str, Enum):
    """Supported model types."""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    OPENROUTER = "openrouter"


def get_model_provider(
    model_type: ModelType,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> BaseModelProvider:
    """
    Factory function to create model providers.

    Args:
        model_type: Type of model provider (ollama, gemini, openai, openrouter)
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
    elif model_type == ModelType.OPENROUTER:
        # If user provides short name, convert to full OpenRouter model name
        resolved_model = model_name
        if model_name and model_name in OPENROUTER_MODELS:
            resolved_model = OPENROUTER_MODELS[model_name]
        elif not model_name:
            resolved_model = "openai/gpt-4o-mini"  # Default

        return OpenRouterProvider(
            model_name=resolved_model,
            api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def get_available_openrouter_models() -> dict:
    """Return list of available OpenRouter model shortcuts."""
    return OPENROUTER_MODELS
