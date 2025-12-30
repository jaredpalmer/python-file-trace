"""Organization model."""
from db.base import Base


class Organization(Base):
    """Organization model."""
    __tablename__ = "organizations"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.slug = kwargs.get("slug")
        self.owner_id = kwargs.get("owner_id")
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")


class OrganizationMember(Base):
    """Organization membership model."""
    __tablename__ = "organization_members"

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.organization_id = kwargs.get("organization_id")
        self.user_id = kwargs.get("user_id")
        self.role = kwargs.get("role", "member")
        self.created_at = kwargs.get("created_at")
