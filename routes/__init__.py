from .health import router as health_router
from .wordpress import router as wordpress_router

__all__ = ["health_router", "wordpress_router"]
