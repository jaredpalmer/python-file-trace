"""Error handling middleware."""
from .base import BaseMiddleware
from core.logging import get_logger
from schemas.common import ErrorResponse


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware for handling uncaught exceptions."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.logger = get_logger("errors")

    async def __call__(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            self.logger.error("unhandled_exception", error=str(exc))
            return ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred"
            )
