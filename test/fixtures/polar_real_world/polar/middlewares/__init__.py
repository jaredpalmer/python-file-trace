"""Application middlewares."""


class FlushEnqueuedWorkerJobsMiddleware:
    """Flush enqueued worker jobs middleware."""
    pass


class LogCorrelationIdMiddleware:
    """Log correlation ID middleware."""
    pass


class PathRewriteMiddleware:
    """Path rewrite middleware."""

    def __init__(self, app, pattern: str, replacement: str):
        self.app = app
        self.pattern = pattern
        self.replacement = replacement


class SandboxResponseHeaderMiddleware:
    """Sandbox response header middleware."""
    pass
