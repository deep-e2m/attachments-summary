"""
Google Gemini model provider using the google.genai library.
"""
from google import genai
from google.genai import types
import httpx
import tempfile
import os
import asyncio
import yt_dlp
from typing import Optional
from .base import BaseModelProvider


class GeminiProvider(BaseModelProvider):
    """Provider for Google Gemini models."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name)
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    @staticmethod
    def _extract_usage(response) -> dict:
        """Extract token usage from Gemini response."""
        usage = getattr(response, "usage_metadata", None)
        if not usage:
            return {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "total_tokens": 0}
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": input_tokens + output_tokens + thinking_tokens,
        }

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """Generate a text response using Gemini. Returns dict with text and usage."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=full_prompt
            )
            return {"text": response.text, "usage": self._extract_usage(response)}
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")

    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Synchronous version of generate."""
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

    async def _wait_for_file_processing(self, uploaded_file):
        """Wait for file to finish processing without blocking the event loop."""
        while uploaded_file.state.name == "PROCESSING":
            await asyncio.sleep(1)
            uploaded_file = await asyncio.to_thread(
                self.client.files.get, name=uploaded_file.name
            )

        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini file processing failed")

        return uploaded_file

    # MIME type mapping for documents
    MIME_TYPES = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }

    async def summarize_document(self, file_content: bytes, filename: str, prompt: str) -> dict:
        """
        Summarize a document using Gemini inline data (no File API upload needed).
        Sends the file directly in the request — much faster than upload/wait/delete cycle.
        Supports PDF and DOCX natively.

        Args:
            file_content: File content as bytes
            filename: Original filename (used for MIME type detection)
            prompt: The prompt for summarization

        Returns:
            Dict with summary
        """
        try:
            ext = os.path.splitext(filename)[1].lower() or ".pdf"
            mime_type = self.MIME_TYPES.get(ext, "application/pdf")

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(data=file_content, mime_type=mime_type)
                        ),
                        types.Part(text=prompt),
                    ]
                ),
            )

            return {"summary": response.text, "usage": self._extract_usage(response)}

        except Exception as e:
            raise Exception(f"Gemini document processing failed: {str(e)}")

    async def summarize_video_url(self, video_url: str, prompt: str) -> dict:
        """
        Download video from URL, upload to Gemini File API, and generate summary.
        """
        tmp_file_path = None
        uploaded_file = None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
            }

            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                response = await client.get(video_url, headers=headers)
                response.raise_for_status()
                video_content = response.content

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
                tmp_file.write(video_content)
                tmp_file_path = tmp_file.name

            uploaded_file = await asyncio.to_thread(
                self.client.files.upload, file=tmp_file_path
            )
            uploaded_file = await self._wait_for_file_processing(uploaded_file)

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=[uploaded_file, prompt]
            )

            return {
                "summary": response.text,
                "transcript": "Transcript extracted by Gemini (embedded in summary)",
                "usage": self._extract_usage(response),
            }

        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to download video: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Gemini video processing failed: {str(e)}")
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if uploaded_file:
                try:
                    await asyncio.to_thread(
                        self.client.files.delete, name=uploaded_file.name
                    )
                except:
                    pass

    async def summarize_youtube_url(self, youtube_url: str, prompt: str) -> dict:
        """Summarize a YouTube video directly using its URL (Gemini supports natively)."""
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
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
                "transcript": "Transcript extracted by Gemini (embedded in summary)",
                "usage": self._extract_usage(response),
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
        return "loom.com/share" in url.lower() or "loom.com/embed" in url.lower()

    @staticmethod
    def extract_loom_video_id(url: str) -> str:
        """Extract video ID from Loom URL."""
        url = url.split('?')[0]
        return url.rstrip('/').split('/')[-1]

    async def download_loom_video(self, loom_url: str) -> str:
        """Download Loom video as MP4 using yt-dlp. Returns path to temp file."""
        tmp_dir = tempfile.mkdtemp()
        output_path = os.path.join(tmp_dir, "loom_video.webm")

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_path,
            "merge_output_format": "webm",
            "quiet": True,
            "no_warnings": True,
        }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([loom_url])
            if not os.path.exists(output_path):
                raise Exception("yt-dlp download completed but output file not found")
            return output_path

        return await asyncio.to_thread(_download)

    async def summarize_loom_url(self, loom_url: str, prompt: str) -> dict:
        """Summarize a Loom video: download via yt-dlp, upload to Gemini, generate summary."""
        tmp_file_path = None
        uploaded_file = None

        try:
            tmp_file_path = await self.download_loom_video(loom_url)

            uploaded_file = await asyncio.to_thread(
                self.client.files.upload, file=tmp_file_path
            )
            uploaded_file = await self._wait_for_file_processing(uploaded_file)

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=[uploaded_file, prompt]
            )

            return {
                "summary": response.text,
                "transcript": "Transcript extracted by Gemini (embedded in summary)",
                "usage": self._extract_usage(response),
            }

        except Exception as e:
            raise Exception(f"Loom video processing failed: {str(e)}")
        finally:
            if tmp_file_path:
                try:
                    os.unlink(tmp_file_path)
                    os.rmdir(os.path.dirname(tmp_file_path))
                except:
                    pass
            if uploaded_file:
                try:
                    await asyncio.to_thread(
                        self.client.files.delete, name=uploaded_file.name
                    )
                except:
                    pass
