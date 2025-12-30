"""Subscription model."""
from db.base import Base


class Subscription(Base):
    """Subscription model."""
    __tablename__ = "subscriptions"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.user_id = kwargs.get("user_id")
        self.product_id = kwargs.get("product_id")
        self.price_id = kwargs.get("price_id")
        self.status = kwargs.get("status", "active")
        self.stripe_subscription_id = kwargs.get("stripe_subscription_id")
        self.current_period_start = kwargs.get("current_period_start")
        self.current_period_end = kwargs.get("current_period_end")
        self.canceled_at = kwargs.get("canceled_at")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
