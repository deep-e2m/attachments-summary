"""
WordPress Analyzer API - FastAPI application for analyzing WordPress sites.

Endpoints:
1. POST /api/v1/wordpress/analyze - Analyze a WordPress site and extract information
2. GET /api/v1/wordpress/analyze/{url} - Analyze a WordPress site (GET method)
3. GET /health - Health check

Detects WordPress version, theme, plugins, PHP version, and security configurations
without requiring authentication.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health_router, wordpress_router
from config import get_settings


# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="WordPress Analyzer API",
    description="""
## API for analyzing WordPress sites without authentication

This API analyzes WordPress sites similar to Wappalyzer or HackerTarget,
detecting site information by analyzing publicly accessible data.

### Available Endpoints:

**WordPress Analysis:**
- **POST /api/v1/wordpress/analyze** - Analyze a WordPress site (recommended)
- **GET /api/v1/wordpress/analyze/{url}** - Analyze a WordPress site via GET

### What It Detects:
- ✅ WordPress version
- ✅ Active theme (name, version, author)
- ✅ Active plugins (with optional deep scan)
- ✅ PHP version (if exposed)
- ✅ Server information
- ✅ Security configurations (XML-RPC, REST API, etc.)
- ✅ Site metadata

**Other:**
- **GET /health** - Health check

### Features:
- No authentication required
- Works with any WordPress site
- Fast analysis (typically < 5 seconds)
- Optional deep scan for more thorough plugin detection
- Respects robots.txt and site policies
    """,
    version="1.0.0",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
