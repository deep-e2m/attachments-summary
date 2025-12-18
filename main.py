"""
Summary API - FastAPI application with three endpoints for generating summaries.

Endpoints:
1. POST /api/v1/summarize/text - Summarize task description and comments
2. POST /api/v1/summarize/attachment - Summarize PDF, TXT, or DOCX files
3. POST /api/v1/summarize/video - Transcribe and summarize video files

Supports OpenRouter API for access to multiple models (GPT-4, Claude, Gemini, Llama, etc.)
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from config import get_settings
from models import ModelType, get_available_openrouter_models, OPENROUTER_MODELS
from services import SummaryService, DocumentProcessor, VideoProcessor


# Initialize FastAPI app
app = FastAPI(
    title="Summary API",
    description="API for generating summaries using OpenRouter (GPT-4, Claude, Gemini, Llama, etc.)",
    version="2.0.0"
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


# Request/Response Models
class TextSummaryRequest(BaseModel):
    """Request model for text summary endpoint."""
    task_description: str = Field(..., description="The task description in HTML format to summarize")
    task_comments_html: Optional[List[str]] = Field(
        default=[],
        description="List of task comments in HTML format, in chronological order (1st comment, 2nd comment, etc.)"
    )
    model_type: Optional[str] = Field(
        default="openrouter",
        description="Model provider: openrouter (recommended), ollama, gemini, or openai"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Model name. For OpenRouter use: gpt-4o, gemini-2.5-pro, claude-3.5-sonnet, etc."
    )


class SummaryResponse(BaseModel):
    """Response model for summary endpoints."""
    success: bool
    summary_html: str


class VideoSummaryResponse(BaseModel):
    """Response model for video summary endpoint."""
    success: bool
    summary_html: str
    transcript: str


# Helper function to get model type
def get_model_type_enum(model_type_str: Optional[str]) -> ModelType:
    """Convert string to ModelType enum."""
    if model_type_str is None:
        model_type_str = settings.default_model_type

    try:
        return ModelType(model_type_str.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type: {model_type_str}. Must be one of: openrouter, ollama, gemini, openai"
        )


def get_api_key(model_type: ModelType) -> Optional[str]:
    """Get API key for the specified model type."""
    if model_type == ModelType.OPENROUTER:
        return settings.openrouter_api_key
    elif model_type == ModelType.GEMINI:
        return settings.gemini_api_key
    elif model_type == ModelType.OPENAI:
        return settings.openai_api_key
    return None


def get_default_model_name(model_type: ModelType) -> str:
    """Get default model name for the specified model type."""
    if model_type == ModelType.OLLAMA:
        return settings.ollama_model
    elif model_type == ModelType.OPENROUTER:
        return settings.openrouter_default_model
    elif model_type == ModelType.GEMINI:
        return settings.gemini_model
    elif model_type == ModelType.OPENAI:
        return settings.openai_model
    return settings.default_model_name


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


# Endpoint 1: Text Summary (Supports all models via OpenRouter)
@app.post("/api/v1/summarize/text", response_model=SummaryResponse)
async def summarize_text(request: TextSummaryRequest):
    """
    Summarize task description and comments.

    Supports multiple models via OpenRouter:
    - gpt-4o, gpt-4o-mini (OpenAI)
    - claude-3.5-sonnet, claude-3-opus (Anthropic)
    - gemini-pro, gemini-flash (Google)
    - llama-3.1-70b, llama-3.1-8b (Meta)
    - mistral-large, mixtral-8x7b (Mistral)

    Args:
        request: TextSummaryRequest containing task description, comments, and model settings

    Returns:
        SummaryResponse with generated summary
    """
    try:
        model_type = get_model_type_enum(request.model_type)
        api_key = get_api_key(model_type)

        # Check API key
        if model_type == ModelType.OPENROUTER and not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file."
            )

        model_name = request.model_name or get_default_model_name(model_type)

        service = SummaryService(
            model_type=model_type,
            model_name=model_name,
            api_key=api_key,
            whisper_model=settings.whisper_model
        )

        result = await service.summarize_text(
            task_description=request.task_description,
            task_comments=request.task_comments_html or []
        )

        # Remove newlines from HTML
        clean_html = result["summary"].replace("\n", "").replace("\r", "")

        return SummaryResponse(
            success=True,
            summary_html=clean_html
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 2: Attachment Summary (OpenRouter)
@app.post("/api/v1/summarize/attachment", response_model=SummaryResponse)
async def summarize_attachment(
    file: UploadFile = File(..., description="Document file (PDF, TXT, or DOCX)"),
    model_name: Optional[str] = Form(default=None, description="Model name (e.g., gpt-4o, claude-3.5-sonnet, gemini-pro)")
):
    """
    Summarize an attachment file (PDF, TXT, or DOCX).
    Uses OpenRouter API.

    Args:
        file: Uploaded document file
        model_name: Optional model name (defaults to gpt-4o-mini)

    Returns:
        SummaryResponse with generated summary
    """
    try:
        # Validate file type
        if not DocumentProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: PDF, TXT, DOCX"
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

        # Remove newlines from HTML
        clean_html = result["summary"].replace("\n", "").replace("\r", "")

        return SummaryResponse(
            success=True,
            summary_html=clean_html
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 3: Video Summary (OpenRouter)
@app.post("/api/v1/summarize/video", response_model=VideoSummaryResponse)
async def summarize_video(
    file: UploadFile = File(..., description="Video or audio file"),
    model_name: Optional[str] = Form(default=None, description="Model name (e.g., gpt-4o, claude-3.5-sonnet, gemini-pro)")
):
    """
    Transcribe video/audio and generate summary.
    Uses OpenRouter API for summarization.

    Args:
        file: Uploaded video or audio file
        model_name: Optional model name (defaults to gpt-4o-mini)

    Returns:
        VideoSummaryResponse with transcript and summary
    """
    try:
        # Validate file type
        if not VideoProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported video types: MP4, AVI, MOV, MKV, WEBM, FLV, WMV. Supported audio types: MP3, WAV, M4A, FLAC, OGG"
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

        # Remove newlines from HTML
        clean_html = result["summary"].replace("\n", "").replace("\r", "")

        return VideoSummaryResponse(
            success=True,
            summary_html=clean_html,
            transcript=result["transcript"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Model info endpoint
@app.get("/api/v1/models")
async def list_available_models():
    """List available models via OpenRouter."""
    return {
        "message": "Use OpenRouter for access to all models with one API key",
        "recommended_for_summaries": {
            "openai": "gpt-4o",
            "google": "gemini-2.5-pro"
        },
        "openrouter_models": {
            "openai": {
                "gpt-4o": "openai/gpt-4o",
                "gpt-4o-mini": "openai/gpt-4o-mini",
                "gpt-4-turbo": "openai/gpt-4-turbo"
            },
            "anthropic": {
                "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
                "claude-3-opus": "anthropic/claude-3-opus",
                "claude-3-haiku": "anthropic/claude-3-haiku"
            },
            "google": {
                "gemini-2.5-pro": "google/gemini-2.5-pro-preview-05-06",
                "gemini-2.0-flash": "google/gemini-2.0-flash-001",
                "gemini-pro": "google/gemini-pro-1.5",
                "gemini-flash": "google/gemini-flash-1.5"
            },
            "meta": {
                "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
                "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct"
            },
            "mistral": {
                "mistral-large": "mistralai/mistral-large",
                "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct"
            }
        },
        "usage_example": {
            "text_summary_gpt4o": {
                "model_type": "openrouter",
                "model_name": "gpt-4o"
            },
            "text_summary_gemini": {
                "model_type": "openrouter",
                "model_name": "gemini-2.5-pro"
            }
        },
        "note": "You can use either short names (gpt-4o) or full names (openai/gpt-4o)",
        "openrouter_api_configured": bool(settings.openrouter_api_key)
    }


# List all available model shortcuts
@app.get("/api/v1/models/shortcuts")
async def list_model_shortcuts():
    """List all available model name shortcuts."""
    return {
        "shortcuts": OPENROUTER_MODELS,
        "usage": "Use shortcut name in 'model_name' field, e.g., 'gpt-4o-mini' instead of 'openai/gpt-4o-mini'"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
