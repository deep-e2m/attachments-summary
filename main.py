"""
Combined API - WordPress Analyzer + Attachment & Video Summary API.

Endpoints:
1. GET  /api/v1/wordpress/analyze - Analyze a WordPress site
2. POST /api/v1/summarize/attachments - Summarize documents from URLs (batch)
3. POST /api/v1/summarize/video - Summarize videos from URLs (batch)
4. GET  /health - Health check
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health_router, wordpress_router, summarize_router
from config import get_settings


# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="WordPress Analyzer & Summary API",
    description="""
## Combined API: WordPress Analysis + Attachment & Video Summarization

### WordPress Analysis:
- **GET /api/v1/wordpress/analyze** - Analyze a WordPress site

### Summarize:
- **POST /api/v1/summarize/attachments** - Summarize documents from URLs (PDF, DOCX, TXT)
- **POST /api/v1/summarize/video** - Summarize videos from URLs (YouTube, Loom, direct)

### Other:
- **GET /health** - Health check
    """,
    version="3.0.0",
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
app.include_router(wordpress_router)
app.include_router(summarize_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
