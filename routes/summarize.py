"""Summarize endpoints for document and video summarization."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import httpx

from config import get_settings
from models import ModelType
from models.gemini_provider import GeminiProvider
from services import SummaryService, DocumentProcessor, VideoProcessor

router = APIRouter(prefix="/api/v1/summarize", tags=["Summarize"])
settings = get_settings()


class VideoSummaryResponse(BaseModel):
    """Response model for single video summary endpoint."""
    success: bool
    summary: str
    transcript: str


class VideoFileSummaryResponse(BaseModel):
    """Response model for video file upload summarization."""
    success: bool
    summary: str
    filename: str


class BatchVideoURLResponse(BaseModel):
    """Response model for batch video URL summarization."""
    success: bool
    results: Dict[str, dict]  # url -> {summary, transcript}
    errors: Dict[str, str]


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
                model_name="gpt-4o",
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

            # Add headers to avoid 403 errors from websites blocking bots
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                file_content = response.content

            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                return (url, None, f"File too large. Maximum size: {settings.max_file_size_mb}MB")

            service = SummaryService(
                model_type=ModelType.OPENROUTER,
                model_name="gpt-4o",
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


@router.post("/video", response_model=BatchVideoURLResponse)
async def summarize_video_urls(urls: List[str]):
    """
    ## Transcribe and summarize videos from URLs using Gemini

    Accepts a list of video URLs and generates summaries using Google Gemini.

    ### Supported URL Types:
    - **YouTube URLs**: Passed directly to Gemini (no download needed)
    - **Direct video URLs** (e.g., .mp4, .mov): Downloaded and uploaded to Gemini File API
    - **Loom URLs**: Note - Loom share URLs don't provide direct video access.
      For Loom videos, download the video and use `/video/file` endpoint instead.

    ### Request Body:
    ```json
    [
        "https://www.youtube.com/watch?v=xxxxx",
        "https://example.com/video.mp4"
    ]
    ```

    ### Response:
    ```json
    {
        "success": true,
        "results": {
            "https://www.youtube.com/watch?v=xxxxx": {
                "summary": "Summary of video...",
                "transcript": "Transcript from Gemini..."
            }
        },
        "errors": {}
    }
    ```
    """
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
        )

    results = {}
    errors = {}

    # Video summary prompt
    video_prompt = """Analyze this video thoroughly and provide a comprehensive summary.

Please include:
1. Overview - What is this video about? What is being shown or discussed?
2. Main Topics - List all key subjects and topics covered
3. Key Points - Important information, details, and specifics mentioned
4. People/Speakers - If there are people speaking, note who they are and their main points
5. Visual Content - Describe any important visuals, demonstrations, or on-screen content
6. Action Items/Takeaways - Any tasks, recommendations, or conclusions

Provide a detailed, thorough summary that captures ALL important information from the video.
Do not skip any significant details."""

    async def process_video_url(url: str) -> tuple:
        """Process a single video URL with Gemini."""
        try:
            gemini = GeminiProvider(
                model_name="gemini-2.5-flash",
                api_key=settings.gemini_api_key
            )

            # Check if it's a Loom URL
            if GeminiProvider.is_loom_url(url):
                return (url, None, "Loom share URLs don't provide direct video access. Please download the video from Loom and use the /video/file endpoint instead.")

            # Check if it's a YouTube URL - pass directly to Gemini
            if GeminiProvider.is_youtube_url(url):
                result = await gemini.summarize_youtube_url(url, video_prompt)
            else:
                # For other URLs, download and upload to File API
                result = await gemini.summarize_video_url(url, video_prompt)

            return (url, {"summary": result["summary"], "transcript": result["transcript"]}, None)

        except Exception as e:
            return (url, None, f"Error: {str(e)}")

    # Process videos sequentially
    for url in urls:
        url_result, data, error = await process_video_url(url)
        if error:
            errors[url_result] = error
        else:
            results[url_result] = data

    return BatchVideoURLResponse(
        success=len(errors) == 0,
        results=results,
        errors=errors
    )


@router.post("/video/file", response_model=VideoFileSummaryResponse)
async def summarize_video_file(
    file: UploadFile = File(..., description="Video file (MP4, MOV, AVI, etc.)")
):
    """
    ## Summarize uploaded video file using Gemini 2.5 Flash

    Upload a video file directly and get a summary using Google Gemini 2.5 Flash.

    ### Supported Video Types:
    - MP4, MOV, AVI, MKV, WEBM, FLV, WMV

    ### Request:
    - Content-Type: multipart/form-data
    - Field: `file` (video file)

    ### Response:
    ```json
    {
        "success": true,
        "summary": "Detailed summary of the video...",
        "filename": "video.mp4"
    }
    ```
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
        )

    # Check file extension
    allowed_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if f'.{ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {', '.join(allowed_extensions)}"
        )

    try:
        file_content = await file.read()

        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        # Video summary prompt
        video_prompt = """Analyze this video thoroughly and provide a comprehensive summary.

Please include:
1. Overview - What is this video about? What is being shown or discussed?
2. Main Topics - List all key subjects and topics covered
3. Key Points - Important information, details, and specifics mentioned
4. People/Speakers - If there are people speaking, note who they are and their main points
5. Visual Content - Describe any important visuals, demonstrations, or on-screen content
6. Action Items/Takeaways - Any tasks, recommendations, or conclusions

Provide a detailed, thorough summary that captures ALL important information from the video.
Do not skip any significant details."""

        gemini = GeminiProvider(
            model_name="gemini-2.5-flash",
            api_key=settings.gemini_api_key
        )

        result = await gemini.summarize_video_file(
            file_content=file_content,
            filename=file.filename,
            prompt=video_prompt
        )

        return VideoFileSummaryResponse(
            success=True,
            summary=result["summary"],
            filename=file.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
