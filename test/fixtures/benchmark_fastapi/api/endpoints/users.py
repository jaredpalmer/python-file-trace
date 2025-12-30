"""User endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.user_service import UserService
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User


router = Router()


@router.get("/me")
async def get_current_user_info(user: User):
    return UserResponse.from_model(user)


@router.get("/{user_id}")
async def get_user(user_id: str, session):
    service = UserService(session)
    user = await service.get_by_id(user_id)
    return UserResponse.from_model(user)


@router.post("/")
async def create_user(data: UserCreate, session):
    service = UserService(session)
    user = await service.create(data)
    return UserResponse.from_model(user)


@router.post("/{user_id}")
async def update_user(user_id: str, data: UserUpdate, session):
    service = UserService(session)
    user = await service.update(user_id, data)
    return UserResponse.from_model(user)
