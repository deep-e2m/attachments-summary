# Developer Guide - WordPress Analyzer API

This document explains how the WordPress Analyzer API application works from a developer's perspective.

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [Application Flow](#application-flow)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Library Imports Explained](#library-imports-explained)
5. [How Port 8000 is Defined](#how-port-8000-is-defined)
6. [Request Flow Diagram](#request-flow-diagram)
7. [Detection Methods](#detection-methods)

---

## Project Structure

```
scrap-videos-and-image python/
│
├── main.py                 # Entry point - FastAPI application
├── config.py               # Configuration settings
├── schemas.py              # Pydantic data models
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
│
├── services/               # Business logic
│   ├── __init__.py         # Exports WordPressAnalyzer
│   └── wordpress_analyzer.py  # WordPress detection service
│
├── routes/                 # API endpoints
│   ├── __init__.py         # Exports routers
│   ├── health.py           # Health check endpoint
│   └── wordpress.py        # WordPress analysis endpoints
│
└── Docker files
    ├── Dockerfile
    ├── docker-compose.yml
    └── .dockerignore
```

---

## Application Flow

### High-Level Overview

```
User Request → FastAPI (main.py) → WordPress Analyzer Service → HTTP Requests to Target Site → Analysis → Response
```

### Detailed Flow

When you hit `http://localhost:8000/api/v1/wordpress/analyze`:

```
1. USER sends HTTP POST/GET request with WordPress URL
        ↓
2. FASTAPI (main.py) receives request
        ↓
3. ENDPOINT FUNCTION validates URL format
        ↓
4. WORDPRESS ANALYZER is created (context manager)
        ↓
5. ANALYZER fetches homepage HTML
        ↓
6. DETECTION METHODS check for WordPress signatures
        ↓
7. IF WORDPRESS: Extract version, theme, plugins, etc.
        ↓
8. RESPONSE is returned as JSON
```

---

## File-by-File Explanation

### 1. `main.py` - The Entry Point

This is where everything starts. It's the "front door" of your application.

```python
# main.py

# STEP 1: Import FastAPI framework
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# STEP 2: Import routers
from routes import health_router, wordpress_router

# STEP 3: Create the application instance
app = FastAPI(
    title="WordPress Analyzer API",
    description="API for analyzing WordPress sites without authentication",
    version="1.0.0"
)

# STEP 4: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STEP 5: Include routers
app.include_router(health_router)
app.include_router(wordpress_router)

# STEP 6: Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # ← PORT DEFINED HERE!
```

**What happens when you run `python main.py`:**
1. Python executes the file
2. `if __name__ == "__main__":` checks if this file is run directly
3. `uvicorn.run()` starts a web server on port 8000
4. Server listens for incoming HTTP requests

---

### 2. `config.py` - Configuration Management

Loads settings from environment variables (`.env` file).

```python
# config.py

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    app_name: str = "WordPress Analyzer API"
    debug: bool = False

    # HTTP Client Settings
    request_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    user_agent: str = Field(default="Mozilla/5.0 (compatible; WordPress-Analyzer/1.0)")

    # WordPress Detection Settings
    enable_plugin_detection: bool = Field(default=True)
    enable_theme_detection: bool = Field(default=True)
    enable_version_detection: bool = Field(default=True)

    class Config:
        env_file = ".env"  # ← Reads from this file

# Singleton pattern - creates settings once and reuses
@lru_cache()
def get_settings():
    return Settings()
```

**How it works:**
1. When `get_settings()` is called, it reads `.env` file
2. Values like `REQUEST_TIMEOUT=30` become `settings.request_timeout`
3. `@lru_cache()` ensures settings are loaded only once (cached)

---

### 3. `schemas.py` - Pydantic Data Models

Defines the structure of request/response data.

```python
# schemas.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class WordPressVersion(BaseModel):
    """WordPress version information."""
    version: Optional[str] = None
    detected_from: Optional[str] = None

class ThemeInfo(BaseModel):
    """WordPress theme information."""
    name: Optional[str] = None
    slug: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None

class PluginInfo(BaseModel):
    """WordPress plugin information."""
    name: Optional[str] = None
    slug: Optional[str] = None
    version: Optional[str] = None

class WordPressSiteInfo(BaseModel):
    """Complete WordPress site information."""
    url: str
    is_wordpress: bool
    wordpress_version: Optional[WordPressVersion] = None
    theme: Optional[ThemeInfo] = None
    plugins: List[PluginInfo] = []
    scan_duration_ms: Optional[int] = None
```

**Why Pydantic?**
- Automatic validation of data
- Auto-generates API documentation
- Type hints for better IDE support
- Serialization to JSON

---

### 4. `services/wordpress_analyzer.py` - The Core Logic

This is where all the WordPress detection happens.

```python
# services/wordpress_analyzer.py

import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

class WordPressAnalyzer:
    """Analyzes WordPress sites and extracts information."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            follow_redirects=True
        )

    async def analyze(self, url: str, deep_scan: bool = False):
        """Main analysis method."""
        # Fetch homepage
        response = await self.client.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')

        # Check if WordPress
        is_wp = await self._is_wordpress(url, html_content, soup)

        if is_wp:
            # Extract information
            version = await self._detect_wordpress_version(url, html_content, soup)
            theme = await self._detect_theme(url, html_content, soup)
            plugins = await self._detect_plugins(url, html_content, soup, deep_scan)

        return result
```

**Key Methods:**
- `analyze()` - Main entry point
- `_is_wordpress()` - Detect if site is WordPress
- `_detect_wordpress_version()` - Find WP version
- `_detect_theme()` - Find active theme
- `_detect_plugins()` - Find active plugins
- `_detect_server_info()` - Extract server details
- `_check_security()` - Check security configs

---

### 5. `routes/wordpress.py` - API Endpoints

Defines the HTTP endpoints users can call.

```python
# routes/wordpress.py

from fastapi import APIRouter
from schemas import AnalyzeRequest, AnalyzeResponse
from services import WordPressAnalyzer

router = APIRouter(prefix="/api/v1/wordpress", tags=["WordPress"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_wordpress_site(request: AnalyzeRequest):
    """
    Analyze a WordPress site and extract information.
    """
    try:
        async with WordPressAnalyzer() as analyzer:
            site_info = await analyzer.analyze(
                url=str(request.url),
                deep_scan=request.deep_scan
            )

            return AnalyzeResponse(
                success=True,
                data=site_info,
                message="Site analysis completed successfully"
            )
    except Exception as e:
        return AnalyzeResponse(
            success=False,
            error=str(e),
            message="An error occurred during site analysis"
        )
```

---

### 6. `routes/health.py` - Health Check

Simple endpoint to verify the API is running.

```python
# routes/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

---

## Library Imports Explained

### `main.py` imports

| Import | Why We Need It |
|--------|----------------|
| `FastAPI` | Web framework - handles HTTP requests |
| `CORSMiddleware` | Allow requests from different domains (browsers) |

### `config.py` imports

| Import | Why We Need It |
|--------|----------------|
| `BaseSettings` | Load config from environment variables |
| `lru_cache` | Cache settings (load once, reuse) |
| `Field` | Define field validation and defaults |

### `schemas.py` imports

| Import | Why We Need It |
|--------|----------------|
| `BaseModel` | Define data structures with validation |
| `HttpUrl` | Validate URL format |
| `Optional, List` | Type hints for optional and list fields |

### `services/wordpress_analyzer.py` imports

| Import | Why We Need It |
|--------|----------------|
| `httpx` | Modern async HTTP client |
| `BeautifulSoup` | Parse HTML and extract data |
| `re` | Regular expressions for pattern matching |
| `urljoin` | Safely join URL parts |

---

## How Port 8000 is Defined

### Method 1: In `main.py` (Direct)

```python
# main.py - at the bottom

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # ← PORT HERE
```

- `host="0.0.0.0"` → Listen on all network interfaces
- `port=8000` → Listen on port 8000

### Method 2: Command Line

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

- `main:app` → File `main.py`, variable `app`
- `--port 8000` → Override port

### Method 3: Docker (`docker-compose.yml`)

```yaml
ports:
  - "8001:8000"  # host_port:container_port
```

- Container runs on 8000 internally
- Exposed as 8001 on your machine

---

## Request Flow Diagram

### WordPress Analysis Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                            │
│  POST http://localhost:8000/api/v1/wordpress/analyze            │
│  Body: {"url": "https://example.com", "deep_scan": false}      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     main.py - FastAPI                           │
│  1. Receives HTTP request with URL                              │
│  2. Validates request body (Pydantic)                           │
│  3. Routes to wordpress.py endpoint                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              routes/wordpress.py                                │
│  1. Receives AnalyzeRequest                                     │
│  2. Creates WordPressAnalyzer instance                          │
│  3. Calls analyzer.analyze(url)                                 │
│  4. Returns AnalyzeResponse                                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│          services/wordpress_analyzer.py                         │
│  1. Fetch homepage HTML with httpx                              │
│  2. Parse HTML with BeautifulSoup                               │
│  3. Check if WordPress (_is_wordpress)                          │
│  4. Detect version (_detect_wordpress_version)                  │
│  5. Detect theme (_detect_theme)                                │
│  6. Detect plugins (_detect_plugins)                            │
│  7. Check security (_check_security)                            │
│  8. Return WordPressSiteInfo                                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER RESPONSE                              │
│  {                                                              │
│    "success": true,                                             │
│    "data": {                                                    │
│      "url": "https://example.com",                              │
│      "is_wordpress": true,                                      │
│      "wordpress_version": {"version": "6.4", ...},              │
│      "theme": {"name": "...", ...},                             │
│      "plugins": [...]                                           │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detection Methods

### 1. WordPress Detection

**How we check if a site is WordPress:**

```python
async def _is_wordpress(self, url, html, soup):
    # Method 1: Meta generator tag
    generator = soup.find('meta', attrs={'name': 'generator'})
    if generator and 'wordpress' in generator.get('content', '').lower():
        return True

    # Method 2: wp-content or wp-includes in HTML
    if 'wp-content' in html or 'wp-includes' in html:
        return True

    # Method 3: WordPress REST API endpoint
    wp_json_url = urljoin(url, '/wp-json/')
    response = await self.client.get(wp_json_url)
    if response.status_code == 200:
        return True

    # Method 4: Common WordPress files
    for file_path in ['/wp-login.php', '/xmlrpc.php']:
        check_url = urljoin(url, file_path)
        response = await self.client.head(check_url)
        if response.status_code in [200, 302, 403]:
            return True

    return False
```

---

### 2. Version Detection

**Multiple methods to find WordPress version:**

```python
async def _detect_wordpress_version(self, url, html, soup):
    # Method 1: Meta generator tag
    # <meta name="generator" content="WordPress 6.4" />

    # Method 2: RSS feed
    # https://example.com/feed/

    # Method 3: readme.html
    # https://example.com/readme.html

    # Method 4: CSS/JS version strings
    # /wp-includes/css/dist/block-library/style.min.css?ver=6.4
```

---

### 3. Theme Detection

**How we find the active theme:**

```python
async def _detect_theme(self, url, html, soup):
    # Look for theme paths in HTML
    # Example: /wp-content/themes/twentytwentyfour/style.css

    theme_pattern = re.compile(r'/wp-content/themes/([^/]+)/')
    matches = theme_pattern.findall(html)

    # Most common theme = active theme
    theme_slug = most_common(matches)

    # Try to get theme info from style.css
    style_url = f'/wp-content/themes/{theme_slug}/style.css'
    # Parse: Theme Name, Version, Author
```

---

### 4. Plugin Detection

**How we detect plugins:**

```python
async def _detect_plugins(self, url, html, soup, deep_scan):
    # Look for plugin paths in HTML
    # Example: /wp-content/plugins/contact-form-7/includes/css/styles.css

    plugin_pattern = re.compile(r'/wp-content/plugins/([^/]+)/')
    matches = plugin_pattern.findall(html)

    plugins = []
    for plugin_slug in unique(matches):
        plugin_info = PluginInfo(slug=plugin_slug)

        # If deep_scan, try to get version from readme.txt
        if deep_scan:
            readme_url = f'/wp-content/plugins/{plugin_slug}/readme.txt'
            # Parse: Stable tag: 1.2.3

        plugins.append(plugin_info)

    return plugins
```

---

## Quick Reference: What Each File Does

| File | Purpose | When It's Used |
|------|---------|----------------|
| `main.py` | Entry point, defines API app | App startup |
| `config.py` | Load settings from .env | App startup |
| `schemas.py` | Define data structures | Every request/response |
| `services/wordpress_analyzer.py` | WordPress detection logic | Every analysis request |
| `routes/wordpress.py` | WordPress API endpoints | WordPress analysis requests |
| `routes/health.py` | Health check endpoint | Health checks |

---

## Summary

1. **User sends request** → `main.py` receives it
2. **Validation** → Pydantic validates URL
3. **Analyzer Creation** → `WordPressAnalyzer` instance created
4. **HTTP Requests** → Fetch homepage and WordPress files
5. **HTML Parsing** → BeautifulSoup extracts data
6. **Pattern Matching** → Regex finds themes/plugins
7. **Detection** → Multiple methods detect WordPress info
8. **Response** → JSON data returned to user

The port 8000 is defined in `main.py` at the bottom in `uvicorn.run()` call!

---

## Key Differences from Traditional APIs

Unlike APIs that require authentication:
- ✅ No admin username/password needed
- ✅ Only analyzes publicly accessible data
- ✅ Similar to browser view-source
- ✅ Ethical and legal (public information)
- ✅ Fast (no complex authentication flows)

This is exactly how tools like Wappalyzer, BuiltWith, and HackerTarget work!
