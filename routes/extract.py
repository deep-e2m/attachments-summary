"""Extract endpoints for document content extraction."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import base64

from config import get_settings
from models import ModelType, get_model_provider
from services import DocumentProcessor

router = APIRouter(prefix="/api/v1/extract", tags=["Extract"])
settings = get_settings()


class ExtractResponse(BaseModel):
    """Response model for extraction endpoint."""
    success: bool
    filename: str
    file_type: str
    content_length: int
    extracted_content: str
    extraction_method: str


@router.post("/attachment", response_model=ExtractResponse)
async def extract_attachment_opensource(
    file: UploadFile = File(..., description="Document file (PDF, TXT, or DOCX)")
):
    """
    ## Extract content using Open Source Libraries

    Extracts text using:
    - **PDF** → PyPDF2
    - **DOCX** → python-docx
    - **TXT** → Built-in Python

    No AI model is used. Pure library extraction.
    """
    try:
        if not DocumentProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported types: PDF, TXT, DOCX"
            )

        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        extracted_content = DocumentProcessor.extract_text(file.filename, file_content)
        file_ext = DocumentProcessor.get_file_extension(file.filename)

        return ExtractResponse(
            success=True,
            filename=file.filename,
            file_type=file_ext,
            content_length=len(extracted_content),
            extracted_content=extracted_content,
            extraction_method="open_source_library"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model", response_model=ExtractResponse)
async def extract_attachment_model(
    file: UploadFile = File(..., description="Document file (PDF only for model extraction)"),
    model_name: Optional[str] = Form(default="gpt-4o", description="Model: gpt-4o or gemini-2.5-pro")
):
    """
    ## Extract content using AI Model

    Passes the PDF directly to the AI model for extraction.

    ### Supported Models:
    - `gpt-4o` - OpenAI (default, best for PDFs)
    - `gemini-2.5-pro` - Google Gemini

    ### How it works:
    1. PDF is converted to base64
    2. Sent directly to the model
    3. Model extracts and returns the text

    **Note:** Only PDF files are supported for model extraction.
    """
    try:
        file_ext = DocumentProcessor.get_file_extension(file.filename)

        if file_ext != ".pdf":
            raise HTTPException(
                status_code=400,
                detail="Model extraction only supports PDF files. Use /extract/attachment for DOCX/TXT."
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

        pdf_base64 = base64.standard_b64encode(file_content).decode("utf-8")

        resolved_model = model_name or "gpt-4o"
        model_provider = get_model_provider(
            ModelType.OPENROUTER,
            resolved_model,
            settings.openrouter_api_key
        )

        extraction_prompt = """You are a precise document text extractor. Your task is to extract ALL text content from this PDF document.

INSTRUCTIONS:
1. Extract every single word, number, and character from the document
2. Preserve the original structure: headings, paragraphs, lists, tables
3. Maintain the reading order (top to bottom, left to right)
4. Keep line breaks where they naturally occur
5. For tables, use | to separate columns and new lines for rows
6. Include headers, footers, page numbers if visible
7. Extract text from any images or diagrams if readable

IMPORTANT RULES:
- Do NOT summarize or paraphrase - extract verbatim
- Do NOT skip any sections, even if repetitive
- Do NOT add your own commentary or explanations
- Do NOT modify spellings or fix errors in the original
- If text is unclear, write [unclear] but try your best

OUTPUT FORMAT:
Return ONLY the extracted text content. Nothing else. No introductions like "Here is the extracted text" - just the raw content."""

        extracted_content = await model_provider.generate_with_file(
            prompt=extraction_prompt,
            file_content=pdf_base64,
            file_type="application/pdf"
        )

        return ExtractResponse(
            success=True,
            filename=file.filename,
            file_type=file_ext,
            content_length=len(extracted_content),
            extracted_content=extracted_content,
            extraction_method=f"ai_model_{resolved_model}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
