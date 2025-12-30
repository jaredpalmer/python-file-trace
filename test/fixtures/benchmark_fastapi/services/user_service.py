"""User service."""
from typing import Optional, List
from .base import BaseService
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import hash_password


class UserService(BaseService):
    """Service for user operations."""

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return User(id=user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return User(id="user_id", email=email)

    async def create(self, data: UserCreate) -> User:
        password_hash = hash_password(data.password)
        user = User(
            id="new_user",
            email=data.email,
            name=data.name,
            password_hash=password_hash,
        )
        await self.commit()
        return user

    async def update(self, user_id: str, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        if data.name:
            user.name = data.name
        if data.email:
            user.email = data.email
        await self.commit()
        return user

    async def delete(self, user_id: str) -> bool:
        await self.commit()
        return True

    async def list_all(self) -> List[User]:
        return []
