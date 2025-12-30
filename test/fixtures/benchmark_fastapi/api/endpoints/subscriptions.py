"""Subscription endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.subscription_service import SubscriptionService
from services.payment_service import PaymentService
from schemas.subscription import SubscriptionCreate, SubscriptionResponse
from models.subscription import Subscription
from models.user import User


router = Router()


@router.get("/")
async def list_subscriptions(user: User, session):
    service = SubscriptionService(session)
    subs = await service.list_for_user(user.id)
    return [SubscriptionResponse.from_model(sub) for sub in subs]


@router.get("/{sub_id}")
async def get_subscription(sub_id: str, session):
    service = SubscriptionService(session)
    sub = await service.get_by_id(sub_id)
    return SubscriptionResponse.from_model(sub)


@router.post("/")
async def create_subscription(data: SubscriptionCreate, user: User, session):
    sub_service = SubscriptionService(session)
    payment_service = PaymentService(session)

    # Create payment intent
    await payment_service.create_payment_intent(data.price_id, user)

    # Create subscription
    sub = await sub_service.create(data, user=user)
    return SubscriptionResponse.from_model(sub)


@router.post("/{sub_id}/cancel")
async def cancel_subscription(sub_id: str, session):
    service = SubscriptionService(session)
    sub = await service.cancel(sub_id)
    return SubscriptionResponse.from_model(sub)
