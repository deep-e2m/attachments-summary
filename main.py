"""
Summary API - FastAPI application for summarizing attachments and videos.

Endpoints:
1. POST /api/v1/summarize/attachment - Summarize PDF, TXT, or DOCX files
2. POST /api/v1/summarize/attachments - Summarize multiple files (batch)
3. POST /api/v1/summarize/urls - Summarize documents from URLs (batch)
4. POST /api/v1/summarize/video - Transcribe and summarize video/audio files
5. POST /api/v1/extract/attachment - Extract content using open source libraries
6. POST /api/v1/extract/model - Extract content using AI model directly

Supports OpenRouter API for access to multiple models (GPT-4, Claude, Gemini, Llama, etc.)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health_router, extract_router, summarize_router, models_router


# Initialize FastAPI app
app = FastAPI(
    title="Attachment & Video Summary API",
    description="""
## API for summarizing attachments and videos using OpenRouter

### Available Endpoints:

**Extract:**
- **POST /api/v1/extract/attachment** - Extract using PyPDF2/python-docx (open source)
- **POST /api/v1/extract/model** - Extract using AI model directly (GPT-4o/Gemini)

**Summarize:**
- **POST /api/v1/summarize/attachment** - Summarize single file (PDF, TXT, DOCX)
- **POST /api/v1/summarize/attachments** - Summarize multiple files (batch)
- **POST /api/v1/summarize/urls** - Summarize documents from URLs (batch)
- **POST /api/v1/summarize/video** - Transcribe and summarize video/audio files

**Other:**
- **GET /api/v1/models** - List available models
- **GET /health** - Health check
    """,
    version="2.3.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(extract_router)
app.include_router(summarize_router)
app.include_router(models_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
