"""Webhook model."""
from typing import List
from db.base import Base


class Webhook(Base):
    """Webhook endpoint model."""
    __tablename__ = "webhooks"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.url = kwargs.get("url")
        self.events: List[str] = kwargs.get("events", [])
        self.secret = kwargs.get("secret")
        self.owner_id = kwargs.get("owner_id")
        self.organization_id = kwargs.get("organization_id")
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")


class WebhookDelivery(Base):
    """Webhook delivery record."""
    __tablename__ = "webhook_deliveries"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.webhook_id = kwargs.get("webhook_id")
        self.event_type = kwargs.get("event_type")
        self.payload = kwargs.get("payload")
        self.response_status = kwargs.get("response_status")
        self.response_body = kwargs.get("response_body")
        self.delivered_at = kwargs.get("delivered_at")
        self.duration_ms = kwargs.get("duration_ms")
