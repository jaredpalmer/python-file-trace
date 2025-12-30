"""Authentication middleware."""
from .base import BaseMiddleware
from core.security import decode_access_token


class AuthMiddleware(BaseMiddleware):
    """Middleware for handling authentication."""

    async def __call__(self, request, call_next):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            try:
                payload = decode_access_token(token[7:])
                request.state.user_id = payload.get("sub")
            except Exception:
                request.state.user_id = None
        else:
            request.state.user_id = None
        return await call_next(request)
