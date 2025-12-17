"""
Summary API - FastAPI application with three endpoints for generating summaries.

Endpoints:
1. POST /api/v1/summarize/text - Summarize task description and comments
2. POST /api/v1/summarize/attachment - Summarize PDF, TXT, or DOCX files
3. POST /api/v1/summarize/video - Transcribe and summarize video files
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from config import get_settings
from models import ModelType
from services import SummaryService, DocumentProcessor, VideoProcessor


# Initialize FastAPI app
app = FastAPI(
    title="Summary API",
    description="API for generating summaries using multiple LLM providers (Ollama, Gemini, OpenAI)",
    version="1.0.0"
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
    task_description: str = Field(..., description="The task description to summarize")
    task_comments: Optional[str] = Field(default="", description="Optional task comments")
    model_type: Optional[str] = Field(
        default=None,
        description="Model type: ollama, gemini, or openai. Uses default if not specified."
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Specific model name (e.g., llama3.1, gemini-pro, gpt-4o-mini)"
    )


class SummaryResponse(BaseModel):
    """Response model for summary endpoints."""
    success: bool
    summary: str
    model_info: dict
    additional_info: Optional[dict] = None


class VideoSummaryResponse(BaseModel):
    """Response model for video summary endpoint."""
    success: bool
    summary: str
    transcript: str
    model_info: dict
    video_info: dict


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
            detail=f"Invalid model type: {model_type_str}. Must be one of: ollama, gemini, openai"
        )


def get_api_key(model_type: ModelType) -> Optional[str]:
    """Get API key for the specified model type."""
    if model_type == ModelType.GEMINI:
        return settings.gemini_api_key
    elif model_type == ModelType.OPENAI:
        return settings.openai_api_key
    return None


def get_default_model_name(model_type: ModelType) -> str:
    """Get default model name for the specified model type."""
    if model_type == ModelType.OLLAMA:
        return settings.ollama_model
    elif model_type == ModelType.GEMINI:
        return settings.gemini_model
    elif model_type == ModelType.OPENAI:
        return settings.openai_model
    return settings.default_model_name


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# Endpoint 1: Text Summary
@app.post("/api/v1/summarize/text", response_model=SummaryResponse)
async def summarize_text(request: TextSummaryRequest):
    """
    Summarize task description and comments.

    Args:
        request: TextSummaryRequest containing task description, comments, and model settings

    Returns:
        SummaryResponse with generated summary
    """
    try:
        model_type = get_model_type_enum(request.model_type)
        api_key = get_api_key(model_type)
        model_name = request.model_name or get_default_model_name(model_type)

        service = SummaryService(
            model_type=model_type,
            model_name=model_name,
            api_key=api_key,
            whisper_model=settings.whisper_model
        )

        result = await service.summarize_text(
            task_description=request.task_description,
            task_comments=request.task_comments or ""
        )

        return SummaryResponse(
            success=True,
            summary=result["summary"],
            model_info=result["model_info"],
            additional_info={"input": result["input"]}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 2: Attachment Summary (Gemini Only)
@app.post("/api/v1/summarize/attachment", response_model=SummaryResponse)
async def summarize_attachment(
    file: UploadFile = File(..., description="Document file (PDF, TXT, or DOCX)")
):
    """
    Summarize an attachment file (PDF, TXT, or DOCX).
    Uses Gemini model only.

    Args:
        file: Uploaded document file

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

        # Always use Gemini for attachments
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=400,
                detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
            )

        service = SummaryService(
            model_type=ModelType.GEMINI,
            model_name=settings.gemini_model,
            api_key=settings.gemini_api_key,
            whisper_model=settings.whisper_model
        )

        result = await service.summarize_document(
            filename=file.filename,
            file_content=file_content
        )

        return SummaryResponse(
            success=True,
            summary=result["summary"],
            model_info=result["model_info"],
            additional_info={"document_info": result["document_info"]}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint 3: Video Summary (Gemini Only)
@app.post("/api/v1/summarize/video", response_model=VideoSummaryResponse)
async def summarize_video(
    file: UploadFile = File(..., description="Video or audio file")
):
    """
    Transcribe video/audio and generate summary.
    Uses Gemini model only for summarization.

    Args:
        file: Uploaded video or audio file

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

        # Always use Gemini for video summarization
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=400,
                detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file."
            )

        service = SummaryService(
            model_type=ModelType.GEMINI,
            model_name=settings.gemini_model,
            api_key=settings.gemini_api_key,
            whisper_model=settings.whisper_model
        )

        result = await service.summarize_video(
            filename=file.filename,
            file_content=file_content
        )

        return VideoSummaryResponse(
            success=True,
            summary=result["summary"],
            transcript=result["transcript"],
            model_info=result["model_info"],
            video_info=result["video_info"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Model info endpoint
@app.get("/api/v1/models")
async def list_available_models():
    """List available model providers and their configurations per endpoint."""
    return {
        "endpoints": {
            "text_summary": {
                "path": "/api/v1/summarize/text",
                "supported_models": ["ollama", "gemini", "openai"],
                "description": "Supports all three models - Ollama (llama3.1), Gemini, and OpenAI"
            },
            "attachment_summary": {
                "path": "/api/v1/summarize/attachment",
                "supported_models": ["gemini"],
                "description": "Uses Gemini model only for document summarization"
            },
            "video_summary": {
                "path": "/api/v1/summarize/video",
                "supported_models": ["gemini"],
                "description": "Uses Gemini model only for video/audio summarization"
            }
        },
        "available_providers": [
            {
                "type": "ollama",
                "description": "Local Ollama models (e.g., llama3.1)",
                "default_model": settings.ollama_model,
                "requires_api_key": False,
                "used_for": ["text_summary"]
            },
            {
                "type": "gemini",
                "description": "Google Gemini models",
                "default_model": settings.gemini_model,
                "requires_api_key": True,
                "api_key_configured": bool(settings.gemini_api_key),
                "used_for": ["text_summary", "attachment_summary", "video_summary"]
            },
            {
                "type": "openai",
                "description": "OpenAI models (e.g., GPT-4)",
                "default_model": settings.openai_model,
                "requires_api_key": True,
                "api_key_configured": bool(settings.openai_api_key),
                "used_for": ["text_summary"]
            }
        ],
        "default_provider": settings.default_model_type
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
