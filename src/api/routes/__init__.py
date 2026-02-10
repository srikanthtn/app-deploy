"""API routes initialization"""
from .hygiene import router as hygiene_router
from .auth import router as auth_router
from .health import router as health_router

__all__ = ["hygiene_router", "auth_router", "health_router"]
