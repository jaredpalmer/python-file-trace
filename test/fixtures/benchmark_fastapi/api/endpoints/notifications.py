"""Notification endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.notification_service import NotificationService
from schemas.notification import NotificationResponse, NotificationPreferences
from models.user import User


router = Router()


@router.get("/")
async def list_notifications(user: User, session):
    service = NotificationService(session)
    notifications = await service.list_for_user(user.id)
    return [NotificationResponse.from_model(n) for n in notifications]


@router.get("/unread")
async def get_unread_count(user: User, session):
    service = NotificationService(session)
    count = await service.get_unread_count(user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str, user: User, session):
    service = NotificationService(session)
    await service.mark_as_read(notification_id)
    return {"status": "read"}


@router.post("/read-all")
async def mark_all_as_read(user: User, session):
    service = NotificationService(session)
    await service.mark_all_as_read(user.id)
    return {"status": "all_read"}


@router.get("/preferences")
async def get_preferences(user: User, session):
    service = NotificationService(session)
    prefs = await service.get_preferences(user.id)
    return NotificationPreferences.from_model(prefs)


@router.post("/preferences")
async def update_preferences(data: NotificationPreferences, user: User, session):
    service = NotificationService(session)
    await service.update_preferences(user.id, data)
    return {"status": "updated"}
