"""Database engine configuration."""
from typing import Optional
from .base import Base


class AsyncEngine:
    """Async database engine."""

    def __init__(self, url: str, **kwargs):
        self.url = url
        self.pool_size = kwargs.get("pool_size", 5)
        self.max_overflow = kwargs.get("max_overflow", 10)

    async def dispose(self):
        """Dispose of the engine."""
        pass


def create_engine(url: str, **kwargs) -> AsyncEngine:
    """Create the primary database engine."""
    return AsyncEngine(url, **kwargs)


def create_read_replica_engine(url: Optional[str], **kwargs) -> Optional[AsyncEngine]:
    """Create a read replica engine if URL is provided."""
    if url is None:
        return None
    return AsyncEngine(url, **kwargs)
