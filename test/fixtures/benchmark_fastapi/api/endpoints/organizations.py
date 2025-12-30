"""Organization endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.organization_service import OrganizationService
from schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from models.organization import Organization
from models.user import User


router = Router()


@router.get("/")
async def list_organizations(user: User, session):
    service = OrganizationService(session)
    orgs = await service.list_for_user(user.id)
    return [OrganizationResponse.from_model(org) for org in orgs]


@router.get("/{org_id}")
async def get_organization(org_id: str, session):
    service = OrganizationService(session)
    org = await service.get_by_id(org_id)
    return OrganizationResponse.from_model(org)


@router.post("/")
async def create_organization(data: OrganizationCreate, user: User, session):
    service = OrganizationService(session)
    org = await service.create(data, owner=user)
    return OrganizationResponse.from_model(org)


@router.post("/{org_id}")
async def update_organization(org_id: str, data: OrganizationUpdate, session):
    service = OrganizationService(session)
    org = await service.update(org_id, data)
    return OrganizationResponse.from_model(org)
