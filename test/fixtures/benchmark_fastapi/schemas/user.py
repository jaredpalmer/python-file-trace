"""User schemas."""
from typing import Optional
from .common import BaseSchema


class UserCreate(BaseSchema):
    """Schema for creating a user."""
    email: str
    name: str
    password: str


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    email: Optional[str] = None
    name: Optional[str] = None


class UserResponse(BaseSchema):
    """Schema for user response."""
    id: str
    email: str
    name: str
    is_active: bool
