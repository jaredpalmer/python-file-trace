"""Logging middleware."""
from .base import BaseMiddleware
from core.logging import get_logger


class LoggingMiddleware(BaseMiddleware):
    """Middleware for request/response logging."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.logger = get_logger("http")

    async def __call__(self, request, call_next):
        self.logger.info("request_started", path=request.url.path)
        response = await call_next(request)
        self.logger.info("request_completed", status=response.status_code)
        return response
