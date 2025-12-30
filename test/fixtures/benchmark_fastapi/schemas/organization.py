"""Organization schemas."""
from typing import Optional
from .common import BaseSchema


class OrganizationCreate(BaseSchema):
    """Schema for creating an organization."""
    name: str
    slug: str


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""
    name: Optional[str] = None


class OrganizationResponse(BaseSchema):
    """Schema for organization response."""
    id: str
    name: str
    slug: str
    owner_id: str
    is_active: bool
