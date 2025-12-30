"""Webhook service."""
from typing import Optional, List
from .base import BaseService
from models.webhook import Webhook, WebhookDelivery
from models.user import User
from schemas.webhook import WebhookCreate


class WebhookService(BaseService):
    """Service for webhook management."""

    async def get_by_id(self, webhook_id: str) -> Optional[Webhook]:
        return Webhook(id=webhook_id)

    async def list_for_user(self, user_id: str) -> List[Webhook]:
        return []

    async def list_for_organization(self, org_id: str) -> List[Webhook]:
        return []

    async def create(self, data: WebhookCreate, user: User) -> Webhook:
        webhook = Webhook(
            id="new_webhook",
            url=data.url,
            events=data.events,
            secret=self._generate_secret(),
            owner_id=user.id,
        )
        await self.commit()
        return webhook

    async def update(self, webhook_id: str, url: str = None, events: List[str] = None) -> Webhook:
        webhook = await self.get_by_id(webhook_id)
        if url:
            webhook.url = url
        if events:
            webhook.events = events
        await self.commit()
        return webhook

    async def delete(self, webhook_id: str) -> bool:
        await self.commit()
        return True

    async def list_deliveries(self, webhook_id: str) -> List[WebhookDelivery]:
        return []

    async def record_delivery(
        self,
        webhook_id: str,
        payload: dict,
        response_status: int,
        response_body: str,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            id="new_delivery",
            webhook_id=webhook_id,
            payload=payload,
            response_status=response_status,
            response_body=response_body,
        )
        await self.commit()
        return delivery

    def _generate_secret(self) -> str:
        import os
        return os.urandom(32).hex()
