"""
Summary service that combines document/video processing with LLM summarization.
"""
from typing import Optional
from models import get_model_provider, ModelType, BaseModelProvider
from prompts import (
    TEXT_SUMMARY_PROMPT,
    DOCUMENT_SUMMARY_PROMPT,
    VIDEO_SUMMARY_PROMPT,
    SYSTEM_PROMPT
)
from .document_processor import DocumentProcessor
from .video_processor import VideoProcessor


class SummaryService:
    """Service for generating summaries using LLMs."""

    def __init__(
        self,
        model_type: ModelType = ModelType.OLLAMA,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        whisper_model: str = "base"
    ):
        """
        Initialize summary service.

        Args:
            model_type: Type of LLM provider
            model_name: Specific model name
            api_key: API key for cloud providers
            whisper_model: Whisper model size for video transcription
        """
        self.model_provider = get_model_provider(model_type, model_name, api_key)
        self.document_processor = DocumentProcessor()
        self.video_processor = VideoProcessor(whisper_model)

    def get_model_info(self) -> dict:
        """Get information about current model provider."""
        return self.model_provider.get_model_info()

    async def summarize_text(
        self,
        task_description: str,
        task_comments: str = ""
    ) -> dict:
        """
        Generate summary for task description and comments.

        Args:
            task_description: The task description text
            task_comments: Optional task comments

        Returns:
            Summary result with model info
        """
        prompt = TEXT_SUMMARY_PROMPT.format(
            task_description=task_description,
            task_comments=task_comments or "No comments provided."
        )

        summary = await self.model_provider.generate(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "model_info": self.get_model_info(),
            "input": {
                "task_description": task_description,
                "task_comments": task_comments
            }
        }

    def summarize_text_sync(
        self,
        task_description: str,
        task_comments: str = ""
    ) -> dict:
        """Synchronous version of summarize_text."""
        prompt = TEXT_SUMMARY_PROMPT.format(
            task_description=task_description,
            task_comments=task_comments or "No comments provided."
        )

        summary = self.model_provider.generate_sync(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "model_info": self.get_model_info(),
            "input": {
                "task_description": task_description,
                "task_comments": task_comments
            }
        }

    async def summarize_document(
        self,
        filename: str,
        file_content: bytes
    ) -> dict:
        """
        Generate summary for a document.

        Args:
            filename: Document filename
            file_content: Document content as bytes

        Returns:
            Summary result with model info
        """
        # Extract text from document
        document_text = self.document_processor.extract_text(filename, file_content)

        prompt = DOCUMENT_SUMMARY_PROMPT.format(document_content=document_text)

        summary = await self.model_provider.generate(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "model_info": self.get_model_info(),
            "document_info": {
                "filename": filename,
                "extracted_text_length": len(document_text)
            }
        }

    def summarize_document_sync(
        self,
        filename: str,
        file_content: bytes
    ) -> dict:
        """Synchronous version of summarize_document."""
        # Extract text from document
        document_text = self.document_processor.extract_text(filename, file_content)

        prompt = DOCUMENT_SUMMARY_PROMPT.format(document_content=document_text)

        summary = self.model_provider.generate_sync(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "model_info": self.get_model_info(),
            "document_info": {
                "filename": filename,
                "extracted_text_length": len(document_text)
            }
        }

    async def summarize_video(
        self,
        filename: str,
        file_content: bytes
    ) -> dict:
        """
        Transcribe video and generate summary.

        Args:
            filename: Video filename
            file_content: Video content as bytes

        Returns:
            Summary result with transcript and model info
        """
        # Process video and get transcript
        video_result = self.video_processor.process_video(filename, file_content)
        transcript = video_result["transcript"]

        prompt = VIDEO_SUMMARY_PROMPT.format(transcript=transcript)

        summary = await self.model_provider.generate(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "transcript": transcript,
            "model_info": self.get_model_info(),
            "video_info": {
                "filename": filename,
                "language": video_result["language"],
                "segments_count": len(video_result["segments"])
            }
        }

    def summarize_video_sync(
        self,
        filename: str,
        file_content: bytes
    ) -> dict:
        """Synchronous version of summarize_video."""
        # Process video and get transcript
        video_result = self.video_processor.process_video(filename, file_content)
        transcript = video_result["transcript"]

        prompt = VIDEO_SUMMARY_PROMPT.format(transcript=transcript)

        summary = self.model_provider.generate_sync(prompt, SYSTEM_PROMPT)

        return {
            "summary": summary,
            "transcript": transcript,
            "model_info": self.get_model_info(),
            "video_info": {
                "filename": filename,
                "language": video_result["language"],
                "segments_count": len(video_result["segments"])
            }
        }
