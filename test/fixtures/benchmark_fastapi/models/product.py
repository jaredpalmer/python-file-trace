"""Product model."""
from db.base import Base


class Product(Base):
    """Product model."""
    __tablename__ = "products"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
        self.price = kwargs.get("price")
        self.owner_id = kwargs.get("owner_id")
        self.organization_id = kwargs.get("organization_id")
        self.stripe_product_id = kwargs.get("stripe_product_id")
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")


class Price(Base):
    """Price model."""
    __tablename__ = "prices"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.product_id = kwargs.get("product_id")
        self.amount = kwargs.get("amount")
        self.currency = kwargs.get("currency", "usd")
        self.interval = kwargs.get("interval")  # month, year, one_time
        self.stripe_price_id = kwargs.get("stripe_price_id")
        self.is_active = kwargs.get("is_active", True)
