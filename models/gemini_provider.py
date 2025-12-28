"""
Google Gemini model provider using the new google.genai library.
"""
from google import genai
from google.genai import types
import httpx
import tempfile
import os
import time
import asyncio
from typing import Optional
from .base import BaseModelProvider


class GeminiProvider(BaseModelProvider):
    """Provider for Google Gemini models using the new google.genai library."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")

    def _wait_for_file_processing(self, uploaded_file) -> None:
        """Wait for file to finish processing."""
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini file processing failed")

        return uploaded_file

    async def summarize_video_file(self, file_content: bytes, filename: str, prompt: str) -> dict:
        """
        Upload video file to Gemini File API and generate summary.

        Args:
            file_content: Video file content as bytes
            filename: Original filename
            prompt: The prompt for summarization

        Returns:
            Dict with summary
        """
        tmp_file_path = None
        uploaded_file = None

        try:
            # Determine file extension
            ext = os.path.splitext(filename)[1].lower() or ".mp4"

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name

            # Upload to Gemini File API
            uploaded_file = self.client.files.upload(file=tmp_file_path)

            # Wait for file to be processed
            uploaded_file = self._wait_for_file_processing(uploaded_file)

            # Generate content with the video
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[uploaded_file, prompt]
            )

            return {
                "summary": response.text
            }

        except Exception as e:
            raise Exception(f"Gemini video processing failed: {str(e)}")
        finally:
            # Cleanup temp file
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            # Cleanup uploaded file from Gemini
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except:
                    pass

    async def summarize_video_url(self, video_url: str, prompt: str) -> dict:
        """
        Download video from URL, upload to Gemini File API, and generate summary.

        Args:
            video_url: URL of the video to process
            prompt: The prompt for summarization

        Returns:
            Dict with summary and transcript
        """
        tmp_file_path = None
        uploaded_file = None

        try:
            # Download video from URL
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
            }

            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                response = await client.get(video_url, headers=headers)
                response.raise_for_status()
                video_content = response.content

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
                tmp_file.write(video_content)
                tmp_file_path = tmp_file.name

            # Upload to Gemini File API
            uploaded_file = self.client.files.upload(file=tmp_file_path)

            # Wait for file to be processed
            uploaded_file = self._wait_for_file_processing(uploaded_file)

            # Generate content with the video
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[uploaded_file, prompt]
            )

            summary = response.text

            return {
                "summary": summary,
                "transcript": "Transcript extracted by Gemini (embedded in summary)"
            }

        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to download video: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Gemini video processing failed: {str(e)}")
        finally:
            # Cleanup temp file
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            # Cleanup uploaded file from Gemini
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except:
                    pass

    async def summarize_video_inline(self, file_content: bytes, prompt: str, mime_type: str = "video/mp4") -> dict:
        """
        Summarize video by passing it inline (for videos under 20MB).

        Args:
            file_content: Video file content as bytes
            prompt: The prompt for summarization
            mime_type: MIME type of the video (default: video/mp4)

        Returns:
            Dict with summary
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(data=file_content, mime_type=mime_type)
                        ),
                        types.Part(text=prompt)
                    ]
                )
            )

            return {
                "summary": response.text
            }

        except Exception as e:
            raise Exception(f"Gemini inline video processing failed: {str(e)}")

    async def summarize_youtube_url(self, youtube_url: str, prompt: str) -> dict:
        """
        Summarize a YouTube video directly using its URL.
        Gemini supports YouTube URLs natively without downloading.

        Args:
            youtube_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=xxxxx)
            prompt: The prompt for summarization

        Returns:
            Dict with summary and transcript
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                file_data=types.FileData(
                                    file_uri=youtube_url,
                                    mime_type="video/*"
                                )
                            ),
                            types.Part(text=prompt)
                        ]
                    )
                ]
            )

            return {
                "summary": response.text,
                "transcript": "Transcript extracted by Gemini (embedded in summary)"
            }

        except Exception as e:
            raise Exception(f"Gemini YouTube processing failed: {str(e)}")

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is a YouTube video URL."""
        youtube_patterns = [
            "youtube.com/watch",
            "youtu.be/",
            "youtube.com/embed/",
            "youtube.com/v/",
            "youtube.com/shorts/"
        ]
        return any(pattern in url.lower() for pattern in youtube_patterns)

    @staticmethod
    def is_loom_url(url: str) -> bool:
        """Check if URL is a Loom video URL."""
        return "loom.com/share" in url.lower()
