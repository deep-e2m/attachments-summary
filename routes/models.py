"""Models information endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Models"])


@router.get("/models")
async def list_available_models():
    """
    ## List available models
    """
    return {
        "extraction": {
            "open_source": ["PyPDF2 (PDF)", "python-docx (DOCX)", "built-in (TXT)"],
            "ai_models": ["gpt-4o", "gemini-2.5-pro"]
        },
        "summarization": {
            "attachments": ["llama-3.1-70b", "llama-3.1-8b"],
            "video": ["gpt-4o", "gpt-4o-mini", "gemini-2.5-pro"]
        }
    }
