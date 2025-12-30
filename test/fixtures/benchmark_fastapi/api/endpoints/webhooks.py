"""Webhook endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.webhook_service import WebhookService
from schemas.webhook import WebhookCreate, WebhookResponse, WebhookDeliveryResponse
from models.webhook import Webhook
from models.user import User
from tasks.webhook_tasks import dispatch_webhook_task


router = Router()


@router.get("/")
async def list_webhooks(user: User, session):
    service = WebhookService(session)
    webhooks = await service.list_for_user(user.id)
    return [WebhookResponse.from_model(wh) for wh in webhooks]


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: str, session):
    service = WebhookService(session)
    webhook = await service.get_by_id(webhook_id)
    return WebhookResponse.from_model(webhook)


@router.post("/")
async def create_webhook(data: WebhookCreate, user: User, session):
    service = WebhookService(session)
    webhook = await service.create(data, user=user)
    return WebhookResponse.from_model(webhook)


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: str, session):
    service = WebhookService(session)
    webhook = await service.get_by_id(webhook_id)
    # Queue test delivery
    await dispatch_webhook_task(webhook.id, {"event": "test"})
    return {"status": "queued"}


@router.get("/{webhook_id}/deliveries")
async def list_webhook_deliveries(webhook_id: str, session):
    service = WebhookService(session)
    deliveries = await service.list_deliveries(webhook_id)
    return [WebhookDeliveryResponse.from_model(d) for d in deliveries]
