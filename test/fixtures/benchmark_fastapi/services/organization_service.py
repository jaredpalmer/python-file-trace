"""Organization service."""
from typing import Optional, List
from .base import BaseService
from models.organization import Organization
from models.user import User
from schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService(BaseService):
    """Service for organization operations."""

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        return Organization(id=org_id)

    async def list_for_user(self, user_id: str) -> List[Organization]:
        return []

    async def create(self, data: OrganizationCreate, owner: User) -> Organization:
        org = Organization(
            id="new_org",
            name=data.name,
            slug=data.slug,
            owner_id=owner.id,
        )
        await self.commit()
        return org

    async def update(self, org_id: str, data: OrganizationUpdate) -> Organization:
        org = await self.get_by_id(org_id)
        if data.name:
            org.name = data.name
        await self.commit()
        return org

    async def delete(self, org_id: str) -> bool:
        await self.commit()
        return True

    async def add_member(self, org_id: str, user_id: str, role: str) -> bool:
        await self.commit()
        return True

    async def remove_member(self, org_id: str, user_id: str) -> bool:
        await self.commit()
        return True
