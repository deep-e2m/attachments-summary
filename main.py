"""
Summary API - FastAPI application for summarizing attachments and videos.

Endpoints:
1. POST /api/v1/summarize/attachment - Summarize PDF, TXT, or DOCX files
2. POST /api/v1/summarize/video - Transcribe and summarize video/audio files

Supports OpenRouter API for access to multiple models (GPT-4, Claude, Gemini, Llama, etc.)
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from config import get_settings
from models import ModelType, OPENROUTER_MODELS
from services import SummaryService, DocumentProcessor, VideoProcessor


# Initialize FastAPI app
app = FastAPI(
    title="Attachment & Video Summary API",
    description="""
## API for summarizing attachments and videos using OpenRouter

### Available Endpoints:

- **POST /api/v1/summarize/attachment** - Summarize PDF, TXT, or DOCX files
- **POST /api/v1/summarize/video** - Transcribe and summarize video/audio files

### Supported Models via OpenRouter:
- GPT-4o, GPT-4o-mini (OpenAI)
- Claude-3.5-sonnet, Claude-3-opus (Anthropic)
- Gemini-pro, Gemini-flash (Google)
- Llama-3.1-70b, Llama-3.1-8b (Meta)
- Mistral-large, Mixtral-8x7b (Mistral)
    """,
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()


# Response Models
class SummaryResponse(BaseModel):
    """Response model for attachment summary endpoint."""
    success: bool
    summary: str


class VideoSummaryResponse(BaseModel):
    """Response model for video summary endpoint."""
    success: bool
    summary: str
    transcript: str


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.1.0"}


# Endpoint 1: Attachment Summary
@app.post("/api/v1/summarize/attachment", response_model=SummaryResponse, tags=["Attachment"])
async def summarize_attachment(
    file: UploadFile = File(..., description="Document file (PDF, TXT, or DOCX)"),
    model_name: Optional[str] = Form(default=None, description="Model name (e.g., gpt-4o, claude-3.5-sonnet, gemini-pro)")
):
    """
    ## Summarize an attachment file (PDF, TXT, or DOCX)

    Upload a document file and get an AI-generated summary.

    ### Supported File Types:
    - **PDF** - Portable Document Format
    - **TXT** - Plain text files
    - **DOCX** - Microsoft Word documents

    ### Parameters:
    - **file**: The document file to summarize
    - **model_name**: Optional model name (defaults to gpt-4o-mini)

    ### Example Models:
    - `gpt-4o` - Best quality
    - `gpt-4o-mini` - Fast and cost-effective
    - `gemini-2.5-pro` - Google's latest
    - `claude-3.5-sonnet` - Anthropic's best
    """
    try:
        # Validate file type
        if not DocumentProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported types: PDF, TXT, DOCX"
            )

        # Check file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        # Use OpenRouter
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

        result = await service.summarize_document(
            filename=file.filename,
            file_content=file_content
        )

        return SummaryResponse(
            success=True,
            summary=result["summary"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 2: Video Summary
@app.post("/api/v1/summarize/video", response_model=VideoSummaryResponse, tags=["Video"])
async def summarize_video(
    file: UploadFile = File(..., description="Video or audio file"),
    model_name: Optional[str] = Form(default=None, description="Model name (e.g., gpt-4o, claude-3.5-sonnet, gemini-pro)")
):
    """
    ## Transcribe and summarize video/audio files

    Upload a video or audio file to get a transcript and AI-generated summary.

    ### Supported Video Types:
    - MP4, AVI, MOV, MKV, WEBM, FLV, WMV

    ### Supported Audio Types:
    - MP3, WAV, M4A, FLAC, OGG

    ### Parameters:
    - **file**: The video or audio file to transcribe and summarize
    - **model_name**: Optional model name (defaults to gpt-4o-mini)

    ### Returns:
    - **transcript**: Full transcription of the audio
    - **summary**: AI-generated summary of the content

    ### Example Models:
    - `gpt-4o` - Best quality
    - `gpt-4o-mini` - Fast and cost-effective
    - `gemini-2.5-pro` - Google's latest
    - `claude-3.5-sonnet` - Anthropic's best
    """
    try:
        # Validate file type
        if not VideoProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported video types: MP4, AVI, MOV, MKV, WEBM, FLV, WMV. Supported audio types: MP3, WAV, M4A, FLAC, OGG"
            )

        # Check file size
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        # Use OpenRouter
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


# Model info endpoint
@app.get("/api/v1/models", tags=["Models"])
async def list_available_models():
    """
    ## List available models for attachment and video summarization

    Returns all available models that can be used with the attachment and video endpoints.
    """
    return {
        "message": "Available models for attachment and video summarization",
        "recommended_models": {
            "best_quality": "gpt-4o",
            "fast_and_cheap": "gpt-4o-mini",
            "google": "gemini-2.5-pro",
            "anthropic": "claude-3.5-sonnet"
        },
        "all_models": {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "anthropic": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
            "google": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-pro", "gemini-flash"],
            "meta": ["llama-3.1-70b", "llama-3.1-8b"],
            "mistral": ["mistral-large", "mixtral-8x7b"]
        },
        "usage": {
            "attachment_endpoint": "/api/v1/summarize/attachment",
            "video_endpoint": "/api/v1/summarize/video",
            "example": "Pass model_name='gpt-4o' in the form data"
        },
        "openrouter_api_configured": bool(settings.openrouter_api_key)
    }


# List all available model shortcuts
@app.get("/api/v1/models/shortcuts", tags=["Models"])
async def list_model_shortcuts():
    """
    ## List all available model name shortcuts

    Returns the mapping of short model names to their full OpenRouter model IDs.
    """
    return {
        "shortcuts": OPENROUTER_MODELS,
        "usage": "Use shortcut name in 'model_name' field, e.g., 'gpt-4o-mini' instead of 'openai/gpt-4o-mini'"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
