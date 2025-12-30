"""Database session management."""
from typing import AsyncIterator
from .engine import AsyncEngine
from .base import Base


class AsyncSession:
    """Async database session."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def execute(self, query):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


class AsyncSessionMaker:
    """Factory for creating async sessions."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    def __call__(self) -> AsyncSession:
        return AsyncSession(self.engine)


def create_session_maker(engine: AsyncEngine) -> AsyncSessionMaker:
    """Create a session maker bound to an engine."""
    return AsyncSessionMaker(engine)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency for getting a database session."""
    session = AsyncSession(None)
    try:
        yield session
    finally:
        await session.close()
