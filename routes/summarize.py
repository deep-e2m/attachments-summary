"""Summarize endpoints for document and video summarization."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import httpx

from config import get_settings
from models import ModelType
from services import SummaryService, DocumentProcessor, VideoProcessor

router = APIRouter(prefix="/api/v1/summarize", tags=["Summarize"])
settings = get_settings()


class VideoSummaryResponse(BaseModel):
    """Response model for video summary endpoint."""
    success: bool
    summary: str
    transcript: str


class BatchURLResponse(BaseModel):
    """Response model for batch URL summarization."""
    success: bool
    results: Dict[str, str]
    errors: Dict[str, str]


class BatchAttachmentResponse(BaseModel):
    """Response model for batch attachment summarization."""
    success: bool
    url: Dict[str, str]
    errors: Dict[str, str]


@router.post("/attachments", response_model=BatchAttachmentResponse)
async def summarize_attachments(
    files: List[UploadFile] = File(..., description="Multiple document files (PDF, TXT, or DOCX)")
):
    """
    ## Summarize multiple attachment files

    Accepts multiple files (PDF, TXT, or DOCX) and returns individual summaries for each.

    ### Request:
    - Content-Type: multipart/form-data
    - Field: `files` (multiple files)

    ### Response:
    ```json
    {
        "success": true,
        "url": {
            "document1.pdf": "Summary of document1...",
            "document2.docx": "Summary of document2..."
        },
        "errors": {}
    }
    ```
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file."
        )

    results = {}
    errors = {}

    async def process_file(file: UploadFile) -> tuple:
        """Process a single file and return summary."""
        try:
            filename = file.filename or "unknown"

            if not DocumentProcessor.is_supported(filename):
                return (filename, None, "Unsupported file type. Supported types: PDF, TXT, DOCX")

            file_content = await file.read()

            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                return (filename, None, f"File too large. Maximum size: {settings.max_file_size_mb}MB")

            service = SummaryService(
                model_type=ModelType.OPENROUTER,
                model_name="llama-3.1-70b",
                api_key=settings.openrouter_api_key,
                whisper_model=settings.whisper_model
            )

            result = await service.summarize_document(
                filename=filename,
                file_content=file_content
            )

            return (filename, result["summary"], None)

        except Exception as e:
            return (file.filename or "unknown", None, f"Error: {str(e)}")

    tasks = [process_file(file) for file in files]
    responses = await asyncio.gather(*tasks)

    for filename, summary, error in responses:
        if error:
            errors[filename] = error
        else:
            results[filename] = summary

    return BatchAttachmentResponse(
        success=len(errors) == 0,
        url=results,
        errors=errors
    )


@router.post("/urls", response_model=BatchURLResponse)
async def summarize_urls(urls: List[str]):
    """
    ## Summarize multiple documents from URLs

    Accepts a simple list of URLs pointing to PDF, TXT, or DOCX files.
    Downloads each file, extracts content, and generates summaries using Llama 3.1-70b.

    ### Request Body:
    ```json
    [
        "https://example.com/doc1.pdf",
        "https://example.com/doc2.pdf",
        "https://example.com/doc3.pdf"
    ]
    ```

    ### Response:
    ```json
    {
        "success": true,
        "results": {
            "https://example.com/doc1.pdf": "Summary of doc1...",
            "https://example.com/doc2.pdf": "Summary of doc2..."
        },
        "errors": {}
    }
    ```
    """
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file."
        )

    results = {}
    errors = {}

    async def process_url(url: str) -> tuple:
        """Download and summarize a single URL."""
        try:
            filename = url.split("/")[-1].split("?")[0]
            if not filename:
                filename = "document"

            if not DocumentProcessor.is_supported(filename):
                if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.txt', '.docx']):
                    filename = filename + ".pdf"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                file_content = response.content

            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                return (url, None, f"File too large. Maximum size: {settings.max_file_size_mb}MB")

            service = SummaryService(
                model_type=ModelType.OPENROUTER,
                model_name="llama-3.1-70b",
                api_key=settings.openrouter_api_key,
                whisper_model=settings.whisper_model
            )

            result = await service.summarize_document(
                filename=filename,
                file_content=file_content
            )

            return (url, result["summary"], None)

        except httpx.HTTPStatusError as e:
            return (url, None, f"HTTP error {e.response.status_code}: Failed to download")
        except httpx.RequestError as e:
            return (url, None, f"Request failed: {str(e)}")
        except Exception as e:
            return (url, None, f"Error: {str(e)}")

    tasks = [process_url(url) for url in urls]
    responses = await asyncio.gather(*tasks)

    for url, summary, error in responses:
        if error:
            errors[url] = error
        else:
            results[url] = summary

    return BatchURLResponse(
        success=len(errors) == 0,
        results=results,
        errors=errors
    )


@router.post("/video", response_model=VideoSummaryResponse)
async def summarize_video(
    file: UploadFile = File(..., description="Video or audio file"),
    model_name: Optional[str] = Form(default=None, description="Model name (e.g., gpt-4o, gemini-2.5-pro)")
):
    """
    ## Transcribe and summarize video/audio files

    ### Supported Video Types:
    - MP4, AVI, MOV, MKV, WEBM, FLV, WMV

    ### Supported Audio Types:
    - MP3, WAV, M4A, FLAC, OGG
    """
    try:
        if not VideoProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported video types: MP4, AVI, MOV, MKV, WEBM, FLV, WMV. Supported audio types: MP3, WAV, M4A, FLAC, OGG"
            )

        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        if not settings.openrouter_api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file."
            )

        resolved_model = model_name or settings.openrouter_default_model

        service = SummaryService(
            model_type=ModelType.OPENROUTER,
            model_name=resolved_model,
            api_key=settings.openrouter_api_key,
            whisper_model=settings.whisper_model
        )

        result = await service.summarize_video(
            filename=file.filename,
            file_content=file_content
        )

        return VideoSummaryResponse(
            success=True,
            summary=result["summary"],
            transcript=result["transcript"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
