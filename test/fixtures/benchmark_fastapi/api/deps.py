"""API dependencies."""
from typing import Optional
from db.session import AsyncSession, get_session
from models.user import User
from core.security import decode_access_token


async def get_db_session():
    """Get a database session dependency."""
    async for session in get_session():
        yield session


async def get_current_user(session: AsyncSession, token: str) -> Optional[User]:
    """Get the current authenticated user."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return User(id=user_id)
    except Exception:
        pass
    return None


async def get_current_user_required(session: AsyncSession, token: str) -> User:
    """Get the current user, raising if not authenticated."""
    user = await get_current_user(session, token)
    if not user:
        raise PermissionError("Not authenticated")
    return user
