from .health import router as health_router
from .wordpress import router as wordpress_router
from .summarize import router as summarize_router

__all__ = ["health_router", "wordpress_router", "summarize_router"]
