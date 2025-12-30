"""Email service."""
from typing import List, Optional
from .base import BaseService
from core.config import settings
from models.user import User


class EmailService(BaseService):
    """Service for sending emails."""

    def __init__(self, session=None):
        if session:
            super().__init__(session)
        self.api_key = settings.sendgrid_api_key

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        # In real app: call SendGrid/SES API
        return True

    async def send_welcome_email(self, user: User) -> bool:
        return await self.send_email(
            to=user.email,
            subject="Welcome!",
            body=f"Welcome to {settings.app_name}, {user.name}!",
        )

    async def send_password_reset(self, user: User, token: str) -> bool:
        return await self.send_email(
            to=user.email,
            subject="Password Reset",
            body=f"Click here to reset your password: /reset?token={token}",
        )

    async def send_subscription_confirmation(self, user: User, product_name: str) -> bool:
        return await self.send_email(
            to=user.email,
            subject="Subscription Confirmed",
            body=f"Your subscription to {product_name} is now active!",
        )

    async def send_bulk(self, recipients: List[str], subject: str, body: str) -> int:
        sent = 0
        for recipient in recipients:
            if await self.send_email(recipient, subject, body):
                sent += 1
        return sent
