"""User model."""
from db.base import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.email = kwargs.get("email")
        self.name = kwargs.get("name")
        self.password_hash = kwargs.get("password_hash")
        self.is_active = kwargs.get("is_active", True)
        self.is_superuser = kwargs.get("is_superuser", False)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
