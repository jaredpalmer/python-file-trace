"""Subscription schemas."""
from typing import Optional
from .common import BaseSchema


class SubscriptionCreate(BaseSchema):
    """Schema for creating a subscription."""
    product_id: str
    price_id: str


class SubscriptionResponse(BaseSchema):
    """Schema for subscription response."""
    id: str
    user_id: str
    product_id: str
    price_id: str
    status: str
