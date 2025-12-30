"""Base middleware class."""


class BaseMiddleware:
    """Base class for all middleware."""

    def __init__(self, app, **kwargs):
        self.app = app
        self.options = kwargs

    async def __call__(self, request, call_next):
        return await call_next(request)
