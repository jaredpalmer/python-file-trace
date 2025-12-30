"""PostgreSQL database utilities."""
from typing import TypeVar

AsyncEngine = TypeVar("AsyncEngine")
AsyncSessionMaker = TypeVar("AsyncSessionMaker")
Engine = TypeVar("Engine")
SyncSessionMaker = TypeVar("SyncSessionMaker")


def create_async_sessionmaker(engine):
    """Create async session maker."""
    return None


def create_sync_sessionmaker(engine):
    """Create sync session maker."""
    return None
