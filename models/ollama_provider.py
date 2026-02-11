"""
Ollama model provider for local LLM inference.
"""
import ollama
from typing import Optional
from .base import BaseModelProvider


class OllamaProvider(BaseModelProvider):
    """Provider for Ollama local models (e.g., llama3.1)."""

    def __init__(self, model_name: str = "llama3.1"):
        super().__init__(model_name)
        self.client = ollama.Client()

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using Ollama.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages
            )
            return response["message"]["content"]
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")

    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Synchronous version of generate.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=messages
            )
            return response["message"]["content"]
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
