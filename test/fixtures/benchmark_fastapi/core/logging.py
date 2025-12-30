"""Logging configuration."""
from .config import settings


def configure_logging():
    """Configure application logging."""
    level = "DEBUG" if settings.debug else "INFO"
    # In real app: configure structlog, logfire, etc.
    return {"level": level, "app": settings.app_name}


def get_logger(name: str):
    """Get a logger instance."""
    return Logger(name)


class Logger:
    """Simple logger for tracing purposes."""

    def __init__(self, name: str):
        self.name = name

    def info(self, msg: str, **kwargs):
        pass

    def error(self, msg: str, **kwargs):
        pass

    def debug(self, msg: str, **kwargs):
        pass
