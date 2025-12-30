"""Subscription service."""
from typing import Optional, List
from .base import BaseService
from models.subscription import Subscription
from models.user import User
from schemas.subscription import SubscriptionCreate


class SubscriptionService(BaseService):
    """Service for subscription operations."""

    async def get_by_id(self, sub_id: str) -> Optional[Subscription]:
        return Subscription(id=sub_id)

    async def list_for_user(self, user_id: str) -> List[Subscription]:
        return []

    async def create(self, data: SubscriptionCreate, user: User) -> Subscription:
        sub = Subscription(
            id="new_sub",
            user_id=user.id,
            product_id=data.product_id,
            price_id=data.price_id,
            status="active",
        )
        await self.commit()
        return sub

    async def create_from_checkout(self, checkout: dict, user: User) -> Subscription:
        sub = Subscription(
            id="checkout_sub",
            user_id=user.id,
            product_id=checkout.get("product_id"),
            price_id=checkout.get("price_id"),
            status="active",
        )
        await self.commit()
        return sub

    async def cancel(self, sub_id: str) -> Subscription:
        sub = await self.get_by_id(sub_id)
        sub.status = "canceled"
        await self.commit()
        return sub

    async def renew(self, sub_id: str) -> Subscription:
        sub = await self.get_by_id(sub_id)
        sub.status = "active"
        await self.commit()
        return sub
