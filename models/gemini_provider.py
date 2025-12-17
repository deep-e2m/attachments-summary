"""
Google Gemini model provider.
"""
import google.generativeai as genai
from typing import Optional
from .base import BaseModelProvider


class GeminiProvider(BaseModelProvider):
    """Provider for Google Gemini models."""

    def __init__(self, model_name: str = "gemini-pro", api_key: Optional[str] = None):
        super().__init__(model_name)
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using Gemini.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")

    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Synchronous version of generate.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")
