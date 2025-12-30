"""Checkout endpoints."""
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from services.payment_service import PaymentService
from services.subscription_service import SubscriptionService
from schemas.checkout import CheckoutSessionCreate, CheckoutSessionResponse
from models.user import User


router = Router()


@router.post("/sessions")
async def create_checkout_session(data: CheckoutSessionCreate, user: User, session):
    payment_service = PaymentService(session)
    checkout = await payment_service.create_checkout_session(
        price_id=data.price_id,
        user=user,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )
    return CheckoutSessionResponse(
        id=checkout["id"],
        url=checkout["url"],
    )


@router.get("/sessions/{session_id}")
async def get_checkout_session(session_id: str, session):
    payment_service = PaymentService(session)
    checkout = await payment_service.get_checkout_session(session_id)
    return CheckoutSessionResponse(
        id=checkout["id"],
        url=checkout["url"],
        status=checkout.get("status"),
    )


@router.post("/sessions/{session_id}/complete")
async def complete_checkout(session_id: str, user: User, session):
    payment_service = PaymentService(session)
    sub_service = SubscriptionService(session)

    checkout = await payment_service.get_checkout_session(session_id)
    if checkout.get("status") == "complete":
        # Create subscription
        sub = await sub_service.create_from_checkout(checkout, user)
        return {"status": "completed", "subscription_id": sub.id}
    return {"status": checkout.get("status")}
