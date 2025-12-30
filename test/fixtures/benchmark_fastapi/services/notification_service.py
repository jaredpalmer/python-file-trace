"""Notification service."""
from typing import Optional, List
from .base import BaseService
from models.user import User


class Notification:
    """Notification model placeholder."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class NotificationPreferences:
    """Notification preferences model placeholder."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class NotificationService(BaseService):
    """Service for managing user notifications."""

    async def list_for_user(self, user_id: str) -> List[Notification]:
        return []

    async def get_unread_count(self, user_id: str) -> int:
        return 0

    async def mark_as_read(self, notification_id: str) -> bool:
        await self.commit()
        return True

    async def mark_all_as_read(self, user_id: str) -> bool:
        await self.commit()
        return True

    async def create(
        self,
        user_id: str,
        title: str,
        body: str,
        type: str = "info",
    ) -> Notification:
        notification = Notification(
            id="new_notification",
            user_id=user_id,
            title=title,
            body=body,
            type=type,
            read=False,
        )
        await self.commit()
        return notification

    async def get_preferences(self, user_id: str) -> NotificationPreferences:
        return NotificationPreferences(
            email_enabled=True,
            push_enabled=True,
            marketing_enabled=False,
        )

    async def update_preferences(self, user_id: str, prefs) -> bool:
        await self.commit()
        return True
