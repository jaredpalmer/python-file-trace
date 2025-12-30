"""Payment service."""
from typing import Optional
from .base import BaseService
from core.config import settings
from models.user import User


class PaymentService(BaseService):
    """Service for payment processing via Stripe."""

    def __init__(self, session=None):
        if session:
            super().__init__(session)
        self.api_key = settings.stripe_api_key

    async def create_customer(self, user: User) -> str:
        # In real app: call Stripe API
        return f"cus_{user.id}"

    async def create_payment_intent(self, price_id: str, user: User) -> dict:
        return {
            "id": "pi_test",
            "client_secret": "secret_test",
            "amount": 1000,
            "currency": "usd",
        }

    async def create_checkout_session(
        self,
        price_id: str,
        user: User,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        return {
            "id": "cs_test",
            "url": "https://checkout.stripe.com/test",
        }

    async def get_checkout_session(self, session_id: str) -> dict:
        return {
            "id": session_id,
            "url": "https://checkout.stripe.com/test",
            "status": "complete",
            "product_id": "prod_test",
            "price_id": "price_test",
        }

    async def create_subscription(self, customer_id: str, price_id: str) -> dict:
        return {
            "id": "sub_test",
            "status": "active",
        }

    async def cancel_subscription(self, subscription_id: str) -> dict:
        return {
            "id": subscription_id,
            "status": "canceled",
        }

    async def handle_webhook(self, payload: bytes, signature: str) -> Optional[dict]:
        # Verify and parse Stripe webhook
        return {"type": "checkout.session.completed"}
