"""Product schemas."""
from typing import Optional
from .common import BaseSchema


class ProductCreate(BaseSchema):
    """Schema for creating a product."""
    name: str
    description: str
    price: int


class ProductUpdate(BaseSchema):
    """Schema for updating a product."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None


class ProductResponse(BaseSchema):
    """Schema for product response."""
    id: str
    name: str
    description: str
    price: int
    is_active: bool
