"""Checkout schemas."""
from typing import Optional
from .common import BaseSchema


class CheckoutSessionCreate(BaseSchema):
    """Schema for creating a checkout session."""
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseSchema):
    """Schema for checkout session response."""
    id: str
    url: str
    status: Optional[str] = None
