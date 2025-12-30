"""Base service class."""
from db.session import AsyncSession


class BaseService:
    """Base class for all services."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
