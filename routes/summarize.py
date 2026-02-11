"""Summarize endpoints for document and video summarization using Gemini."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import httpx

from config import get_settings
from models.gemini_provider import GeminiProvider
from services.document_processor import DocumentProcessor
from prompts import DOCUMENT_SUMMARY_PROMPT

router = APIRouter(prefix="/api/v1/summarize", tags=["Summarize"])
settings = get_settings()


class TokenUsage(BaseModel):
    """Token usage for a single Gemini call."""
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0


class BatchAttachmentResponse(BaseModel):
    """Response model for batch attachment URL summarization."""
    success: bool
    results: Dict[str, str]
    errors: Dict[str, str]
    usage: Dict[str, TokenUsage] = {}
    total_usage: TokenUsage = TokenUsage()


class BatchVideoURLResponse(BaseModel):
    """Response model for batch video URL summarization."""
    success: bool
    results: Dict[str, dict]
    errors: Dict[str, str]
    usage: Dict[str, TokenUsage] = {}
    total_usage: TokenUsage = TokenUsage()


@router.post("/attachments", response_model=BatchAttachmentResponse)
async def summarize_attachments(urls: List[str]):
    """
    ## Summarize documents from URLs using Gemini 2.5 Flash

    Downloads PDF, DOCX, or TXT files from URLs and generates summaries.
    Gemini sees both text AND images inside documents for comprehensive summaries.

    ### Supported File Types:
    - **PDF** - Sent directly to Gemini (text + images)
    - **DOCX** - Converted to PDF, then sent to Gemini (text + images)
    - **TXT** - Text content sent to Gemini

    ### Request Body:
    ```json
    [
        "https://example.com/doc1.pdf",
        "https://example.com/doc2.docx",
        "https://example.com/doc3.txt"
    ]
    ```

    ### Response:
    ```json
    {
        "success": true,
        "results": {
            "https://example.com/doc1.pdf": "Summary of doc1...",
            "https://example.com/doc2.docx": "Summary of doc2..."
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

    gemini = GeminiProvider(
        model_name=settings.gemini_model,
        api_key=settings.gemini_api_key
    )

    results = {}
    errors = {}

    async def process_url(url: str) -> tuple:
        """Download and summarize a single document URL."""
        try:
            filename = DocumentProcessor.get_filename_from_url(url)

            # Default to PDF if no recognizable extension
            if not DocumentProcessor.is_supported(filename):
                if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.txt', '.docx']):
                    filename = filename + ".pdf"

            # Download file
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

            ext = DocumentProcessor.get_file_extension(filename)

            if ext == ".txt":
                # For TXT files, extract text and send as prompt
                text_content = DocumentProcessor.extract_text_from_txt(file_content)
                prompt = DOCUMENT_SUMMARY_PROMPT.format(document_content=text_content)
                result = await gemini.generate(prompt)
                return (url, result["text"], None, result["usage"])

            if ext == ".docx":
                # Gemini doesn't support DOCX inline — convert to PDF first
                file_content = await asyncio.to_thread(
                    DocumentProcessor.convert_docx_to_pdf, file_content
                )
                filename = filename.rsplit(".", 1)[0] + ".pdf"

            # Send PDF directly to Gemini via inline data (sees text + images)
            result = await gemini.summarize_document(
                file_content=file_content,
                filename=filename,
                prompt=DOCUMENT_SUMMARY_PROMPT.format(document_content="[See attached document]")
            )

            return (url, result["summary"], None, result["usage"])

        except httpx.HTTPStatusError as e:
            return (url, None, f"HTTP error {e.response.status_code}: Failed to download", None)
        except httpx.RequestError as e:
            return (url, None, f"Request failed: {str(e)}", None)
        except Exception as e:
            return (url, None, f"Error: {str(e)}", None)

    # Process URLs in parallel
    tasks = [process_url(url) for url in urls]
    responses = await asyncio.gather(*tasks)

    usage_map = {}
    total_input = 0
    total_output = 0
    total_thinking = 0

    for url_result, summary, error, url_usage in responses:
        if error:
            errors[url_result] = error
        else:
            results[url_result] = summary
            if url_usage:
                usage_map[url_result] = TokenUsage(**url_usage)
                total_input += url_usage["input_tokens"]
                total_output += url_usage["output_tokens"]
                total_thinking += url_usage["thinking_tokens"]

    return BatchAttachmentResponse(
        success=len(errors) == 0,
        results=results,
        errors=errors,
        usage=usage_map,
        total_usage=TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            thinking_tokens=total_thinking,
            total_tokens=total_input + total_output + total_thinking,
        ),
    )


@router.post("/video", response_model=BatchVideoURLResponse)
async def summarize_video_urls(urls: List[str]):
    """
    ## Summarize videos from URLs using Gemini 2.5 Flash

    Accepts a list of video URLs and generates summaries using Google Gemini.

    ### Supported URL Types:
    - **YouTube URLs** - Passed directly to Gemini (no download needed)
    - **Loom URLs** - Extracts download URL via Loom API, downloads and uploads to Gemini
    - **Direct video URLs** (e.g., .mp4, .mov) - Downloaded and uploaded to Gemini File API

    ### Request Body:
    ```json
    [
        "https://www.youtube.com/watch?v=xxxxx",
        "https://www.loom.com/share/abc123def456",
        "https://example.com/video.mp4"
    ]
    ```
    """
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
        )

    gemini = GeminiProvider(
        model_name=settings.gemini_model,
        api_key=settings.gemini_api_key
    )

    results = {}
    errors = {}

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
            if GeminiProvider.is_loom_url(url):
                result = await gemini.summarize_loom_url(url, video_prompt)
            elif GeminiProvider.is_youtube_url(url):
                result = await gemini.summarize_youtube_url(url, video_prompt)
            else:
                result = await gemini.summarize_video_url(url, video_prompt)

            return (url, {"summary": result["summary"], "transcript": result["transcript"]}, None, result["usage"])

        except Exception as e:
            return (url, None, f"Error: {str(e)}", None)

    # Process videos in parallel
    tasks = [process_video_url(url) for url in urls]
    responses = await asyncio.gather(*tasks)

    usage_map = {}
    total_input = 0
    total_output = 0
    total_thinking = 0

    for url_result, data, error, url_usage in responses:
        if error:
            errors[url_result] = error
        else:
            results[url_result] = data
            if url_usage:
                usage_map[url_result] = TokenUsage(**url_usage)
                total_input += url_usage["input_tokens"]
                total_output += url_usage["output_tokens"]
                total_thinking += url_usage["thinking_tokens"]

    return BatchVideoURLResponse(
        success=len(errors) == 0,
        results=results,
        errors=errors,
        usage=usage_map,
        total_usage=TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            thinking_tokens=total_thinking,
            total_tokens=total_input + total_output + total_thinking,
        ),
    )
