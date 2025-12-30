"""CORS middleware."""
from typing import List
from .base import BaseMiddleware


class CORSMiddleware(BaseMiddleware):
    """Middleware for handling CORS."""

    def __init__(self, app, allow_origins: List[str] = None, **kwargs):
        super().__init__(app, **kwargs)
        self.allow_origins = allow_origins or ["*"]

    async def __call__(self, request, call_next):
        response = await call_next(request)
        origin = request.headers.get("Origin", "")
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        return response
