from .health import router as health_router
from .extract import router as extract_router
from .summarize import router as summarize_router
from .models import router as models_router

__all__ = ["health_router", "extract_router", "summarize_router", "models_router"]
