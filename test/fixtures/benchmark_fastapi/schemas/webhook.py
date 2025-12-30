"""Webhook schemas."""
from typing import List, Optional
from .common import BaseSchema


class WebhookCreate(BaseSchema):
    """Schema for creating a webhook."""
    url: str
    events: List[str]


class WebhookResponse(BaseSchema):
    """Schema for webhook response."""
    id: str
    url: str
    events: List[str]
    is_active: bool


class WebhookDeliveryResponse(BaseSchema):
    """Schema for webhook delivery response."""
    id: str
    webhook_id: str
    event_type: str
    response_status: int
    delivered_at: str
