"""
OpenRouter model provider - Access multiple LLMs with one API key.
Supports: GPT-4, Claude, Gemini, Llama, Mistral, and many more.
"""
from openai import OpenAI
from typing import Optional
from .base import BaseModelProvider


class OpenRouterProvider(BaseModelProvider):
    """
    Provider for OpenRouter API.

    OpenRouter gives access to multiple models with one API key:
    - openai/gpt-4o
    - openai/gpt-4o-mini
    - anthropic/claude-3.5-sonnet
    - google/gemini-pro-1.5
    - meta-llama/llama-3.1-70b-instruct
    - mistralai/mistral-large
    - and many more...

    Full list: https://openrouter.ai/models
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model_name: str = "openai/gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize OpenRouter provider.

        Args:
            model_name: Model identifier (e.g., "openai/gpt-4o-mini", "google/gemini-pro-1.5")
            api_key: OpenRouter API key
        """
        super().__init__(model_name)
        self.client = OpenAI(
            base_url=self.OPENROUTER_BASE_URL,
            api_key=api_key
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response using OpenRouter.

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
                temperature=0.3,  # Lower temperature for consistent detailed output
                max_tokens=8000  # Allow long responses for detailed summaries
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenRouter generation failed: {str(e)}")

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
                temperature=0.3,  # Lower temperature for consistent detailed output
                max_tokens=8000  # Allow long responses for detailed summaries
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenRouter generation failed: {str(e)}")

    async def generate_with_file(
        self,
        prompt: str,
        file_content: str,
        file_type: str = "application/pdf",
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response with a file attachment (PDF).

        Args:
            prompt: The user prompt
            file_content: Base64 encoded file content
            file_type: MIME type of the file (default: application/pdf)
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

        # Create message with file content
        # For vision-capable models (GPT-4o, Gemini), we use the image_url format
        # with base64 data URL for PDFs
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{file_type};base64,{file_content}"
                    }
                }
            ]
        })

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,  # Lower temperature for extraction
                max_tokens=16000  # Allow long responses for full extraction
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenRouter file processing failed: {str(e)}")

    def get_model_info(self) -> dict:
        """Return information about the model provider."""
        return {
            "provider": "OpenRouterProvider",
            "model": self.model_name,
            "api_base": self.OPENROUTER_BASE_URL
        }


# Popular models available on OpenRouter
OPENROUTER_MODELS = {
    # OpenAI Models (Recommended for summaries)
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4-turbo": "openai/gpt-4-turbo",

    # Anthropic Models
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3-opus": "anthropic/claude-3-opus",
    "claude-3-haiku": "anthropic/claude-3-haiku",

    # Google Models (Recommended for summaries)
    "gemini-2.5-pro": "google/gemini-2.5-pro-preview-05-06",
    "gemini-2.0-flash": "google/gemini-2.0-flash-001",
    "gemini-pro": "google/gemini-pro-1.5",
    "gemini-flash": "google/gemini-flash-1.5",

    # Meta Models - Llama 4
    "llama4-maverick": "meta-llama/llama-4-maverick",
    "llama4-scout": "meta-llama/llama-4-scout",

    # Meta Models - Llama 3.1
    "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",

    # Mistral Models
    "mistral-large": "mistralai/mistral-large",
    "mistral-medium": "mistralai/mistral-medium",

    # Others
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
    "qwen-72b": "qwen/qwen-2-72b-instruct",
}
