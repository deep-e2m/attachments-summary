"""
OpenAI model provider.
"""
from openai import OpenAI
from typing import Optional
from .base import BaseModelProvider


class OpenAIProvider(BaseModelProvider):
    """Provider for OpenAI models."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        super().__init__(model_name)
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using OpenAI.

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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")

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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")
