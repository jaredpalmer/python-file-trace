"""Notification schemas."""
from typing import Optional
from .common import BaseSchema


class NotificationResponse(BaseSchema):
    """Schema for notification response."""
    id: str
    title: str
    body: str
    type: str
    read: bool


class NotificationPreferences(BaseSchema):
    """Schema for notification preferences."""
    email_enabled: bool = True
    push_enabled: bool = True
    marketing_enabled: bool = False
