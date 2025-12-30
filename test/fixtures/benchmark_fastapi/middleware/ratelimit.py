"""Rate limiting middleware."""
from .base import BaseMiddleware
from core.config import settings


class RateLimitMiddleware(BaseMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, requests_per_minute: int = 60, **kwargs):
        super().__init__(app, **kwargs)
        self.requests_per_minute = requests_per_minute
        self.redis_url = settings.redis_url

    async def __call__(self, request, call_next):
        # In real app: check Redis for rate limit
        client_ip = request.client.host if request.client else "unknown"
        # Allow request through
        return await call_next(request)
