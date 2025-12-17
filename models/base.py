"""
Base class for model providers.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseModelProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Synchronous version of generate.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context

        Returns:
            Generated text response
        """
        pass

    def get_model_info(self) -> dict:
        """Return information about the model provider."""
        return {
            "provider": self.__class__.__name__,
            "model": self.model_name
        }
