# Developer Guide - Summary API

This document explains how the Summary API application works from a developer's perspective.

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [Application Flow](#application-flow)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Library Imports Explained](#library-imports-explained)
5. [How Port 8000 is Defined](#how-port-8000-is-defined)
6. [Request Flow Diagram](#request-flow-diagram)

---

## Project Structure

```
scrap-videos-and-image python/
│
├── main.py                 # Entry point - FastAPI application
├── config.py               # Configuration settings
├── prompts.py              # LLM prompt templates
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
│
├── models/                 # LLM Provider modules
│   ├── __init__.py         # Exports all model classes
│   ├── base.py             # Abstract base class
│   ├── factory.py          # Factory pattern for model selection
│   ├── ollama_provider.py  # Ollama (local) provider
│   ├── gemini_provider.py  # Google Gemini provider
│   └── openai_provider.py  # OpenAI provider
│
├── services/               # Business logic
│   ├── __init__.py         # Exports all services
│   ├── summary_service.py  # Main summary orchestration
│   ├── document_processor.py # PDF, DOCX, TXT extraction
│   └── video_processor.py  # Video transcription
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
User Request → FastAPI (main.py) → Service Layer → Model Provider → LLM → Response
```

### Detailed Flow

When you hit `http://localhost:8000/api/v1/summarize/text`:

```
1. USER sends HTTP POST request
        ↓
2. FASTAPI (main.py) receives request
        ↓
3. ENDPOINT FUNCTION validates input
        ↓
4. SUMMARY SERVICE is created with selected model
        ↓
5. MODEL PROVIDER (Ollama/Gemini/OpenAI) is initialized
        ↓
6. PROMPT is formatted with user input
        ↓
7. LLM generates summary
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
from fastapi import FastAPI, HTTPException, UploadFile, File, Form

# STEP 2: Create the application instance
app = FastAPI(
    title="Summary API",
    description="API for generating summaries",
    version="1.0.0"
)

# STEP 3: Define endpoints (routes)
@app.post("/api/v1/summarize/text")
async def summarize_text(request: TextSummaryRequest):
    # This function runs when user hits this URL
    pass

# STEP 4: Run the server
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

class Settings(BaseSettings):
    # These values come from .env file or environment
    default_model_type: str = "ollama"
    gemini_api_key: str = None
    openai_api_key: str = None

    class Config:
        env_file = ".env"  # ← Reads from this file

# Singleton pattern - creates settings once and reuses
@lru_cache()
def get_settings():
    return Settings()
```

**How it works:**
1. When `get_settings()` is called, it reads `.env` file
2. Values like `GEMINI_API_KEY=xxx` become `settings.gemini_api_key`
3. `@lru_cache()` ensures settings are loaded only once (cached)

---

### 3. `prompts.py` - Prompt Templates

Contains the instructions sent to the LLM.

```python
# prompts.py

TEXT_SUMMARY_PROMPT = """You are an expert summarizer...

Task Description:
{task_description}      ← Placeholder replaced with actual input

Task Comments:
{task_comments}         ← Placeholder replaced with actual input

Output the summary in HTML format..."""
```

**How placeholders work:**
```python
# In summary_service.py
prompt = TEXT_SUMMARY_PROMPT.format(
    task_description="User's task description",
    task_comments="User's comments"
)
# Result: Placeholders {task_description} and {task_comments} are replaced
```

---

### 4. `models/` - LLM Providers

#### `models/base.py` - Abstract Base Class

Defines the "contract" that all providers must follow.

```python
# models/base.py

from abc import ABC, abstractmethod

class BaseModelProvider(ABC):
    """All providers MUST implement these methods"""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Every provider must have this method"""
        pass
```

**Why use abstract class?**
- Ensures all providers (Ollama, Gemini, OpenAI) have the same interface
- You can swap providers without changing other code

---

#### `models/ollama_provider.py` - Ollama Implementation

```python
# models/ollama_provider.py

import ollama

class OllamaProvider(BaseModelProvider):
    def __init__(self, model_name="llama3.1"):
        self.client = ollama.Client()
        self.model_name = model_name

    async def generate(self, prompt: str, system_prompt=None) -> str:
        # Send request to local Ollama server
        response = self.client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
```

**How Ollama works:**
1. Ollama runs locally on your machine (port 11434)
2. This provider sends HTTP requests to local Ollama
3. Ollama processes with llama3.1 model and returns text

---

#### `models/factory.py` - Factory Pattern

Creates the right provider based on user's choice.

```python
# models/factory.py

def get_model_provider(model_type, model_name=None, api_key=None):
    if model_type == "ollama":
        return OllamaProvider(model_name or "llama3.1")
    elif model_type == "gemini":
        return GeminiProvider(model_name or "gemini-pro", api_key)
    elif model_type == "openai":
        return OpenAIProvider(model_name or "gpt-4o-mini", api_key)
```

**Why Factory Pattern?**
- User says "I want ollama" → Factory creates OllamaProvider
- User says "I want gemini" → Factory creates GeminiProvider
- Main code doesn't need to know implementation details

---

### 5. `services/` - Business Logic

#### `services/summary_service.py` - Orchestrator

Coordinates everything - connects prompts with providers.

```python
# services/summary_service.py

class SummaryService:
    def __init__(self, model_type, model_name, api_key):
        # Create the appropriate model provider
        self.model_provider = get_model_provider(model_type, model_name, api_key)

    async def summarize_text(self, task_description, task_comments):
        # 1. Format the prompt with user input
        prompt = TEXT_SUMMARY_PROMPT.format(
            task_description=task_description,
            task_comments=task_comments
        )

        # 2. Send to LLM and get response
        summary = await self.model_provider.generate(prompt, SYSTEM_PROMPT)

        # 3. Return result
        return {"summary": summary, "model_info": self.get_model_info()}
```

---

#### `services/document_processor.py` - File Extraction

Extracts text from different file types.

```python
# services/document_processor.py

class DocumentProcessor:
    @staticmethod
    def extract_text(filename, file_content):
        ext = get_file_extension(filename)  # ".pdf", ".docx", ".txt"

        if ext == ".pdf":
            return extract_text_from_pdf(file_content)
        elif ext == ".docx":
            return extract_text_from_docx(file_content)
        elif ext == ".txt":
            return file_content.decode("utf-8")
```

---

#### `services/video_processor.py` - Video Transcription

Extracts audio from video and transcribes using Whisper.

```python
# services/video_processor.py

class VideoProcessor:
    def process_video(self, filename, file_content):
        # 1. Save video to temp file
        # 2. Extract audio using moviepy
        # 3. Transcribe audio using Whisper
        # 4. Return transcript text
```

---

## Library Imports Explained

### `main.py` imports

| Import | Why We Need It |
|--------|----------------|
| `FastAPI` | Web framework - handles HTTP requests |
| `HTTPException` | Return error responses (400, 500, etc.) |
| `UploadFile, File` | Handle file uploads |
| `Form` | Handle form data in requests |
| `CORSMiddleware` | Allow requests from different domains |
| `BaseModel` | Define request/response data structures |

### `config.py` imports

| Import | Why We Need It |
|--------|----------------|
| `BaseSettings` | Load config from environment variables |
| `lru_cache` | Cache settings (load once, reuse) |

### `models/` imports

| Import | Why We Need It |
|--------|----------------|
| `ollama` | Client library to talk to Ollama server |
| `google.generativeai` | Google's Gemini API client |
| `openai` | OpenAI API client |
| `ABC, abstractmethod` | Create abstract base class |

### `services/` imports

| Import | Why We Need It |
|--------|----------------|
| `PyPDF2` | Extract text from PDF files |
| `python-docx` | Extract text from Word documents |
| `faster_whisper` | Transcribe audio to text |
| `moviepy` | Extract audio from video files |
| `tempfile` | Create temporary files for processing |

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

### Text Summary Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                            │
│  POST http://localhost:8000/api/v1/summarize/text              │
│  Body: {"task_description": "...", "model_type": "ollama"}     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     main.py - FastAPI                           │
│  1. Receives HTTP request                                       │
│  2. Validates JSON body (TextSummaryRequest)                   │
│  3. Calls summarize_text() function                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 main.py - summarize_text()                      │
│  1. Get model type from request ("ollama")                     │
│  2. Get API key from config (if needed)                        │
│  3. Create SummaryService with model settings                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              services/summary_service.py                        │
│  1. __init__: Call factory to create OllamaProvider            │
│  2. summarize_text(): Format prompt with user input            │
│  3. Call model_provider.generate(prompt)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  models/factory.py                              │
│  get_model_provider("ollama") → returns OllamaProvider()       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              models/ollama_provider.py                          │
│  1. generate() receives formatted prompt                        │
│  2. Sends to Ollama server (localhost:11434)                   │
│  3. Ollama runs llama3.1 model                                 │
│  4. Returns generated text                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OLLAMA SERVER                              │
│  Running locally on port 11434                                  │
│  Processes prompt with llama3.1 model                          │
│  Returns: "<h3>Summary</h3><p>...</p>"                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Response travels back                         │
│  Ollama → OllamaProvider → SummaryService → main.py → User     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      USER RESPONSE                              │
│  {                                                              │
│    "success": true,                                             │
│    "summary": "<h3>Summary</h3><p>...</p>",                    │
│    "model_info": {"provider": "OllamaProvider", "model": "..."}│
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: What Each File Does

| File | Purpose | When It's Used |
|------|---------|----------------|
| `main.py` | Entry point, defines API endpoints | Every request |
| `config.py` | Load settings from .env | App startup |
| `prompts.py` | LLM instruction templates | When generating summaries |
| `models/factory.py` | Create correct provider | When service is initialized |
| `models/ollama_provider.py` | Talk to Ollama | When model_type="ollama" |
| `models/gemini_provider.py` | Talk to Gemini API | When model_type="gemini" |
| `models/openai_provider.py` | Talk to OpenAI API | When model_type="openai" |
| `services/summary_service.py` | Orchestrate summary generation | Every summary request |
| `services/document_processor.py` | Extract text from files | Attachment endpoint |
| `services/video_processor.py` | Transcribe videos | Video endpoint |

---

## Summary

1. **User hits API** → `main.py` receives request
2. **Validation** → Pydantic models check input
3. **Service Creation** → `SummaryService` is created with correct provider
4. **Provider Selection** → Factory creates Ollama/Gemini/OpenAI provider
5. **Prompt Formatting** → User input inserted into prompt template
6. **LLM Call** → Provider sends prompt to LLM
7. **Response** → HTML summary returned to user

The port 8000 is defined in `main.py` at the bottom in `uvicorn.run()` call!
