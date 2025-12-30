"""
Main FastAPI application - simulates a real-world FastAPI app like Polar.
This is the entry point for tracing benchmarks.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Core framework imports
from core.config import settings
from core.logging import configure_logging

# Database layer
from db.engine import create_engine, create_read_replica_engine
from db.session import create_session_maker, get_session

# Middleware stack
from middleware.auth import AuthMiddleware
from middleware.cors import CORSMiddleware
from middleware.ratelimit import RateLimitMiddleware
from middleware.logging import LoggingMiddleware
from middleware.errors import ErrorHandlerMiddleware

# API routers
from api.router import router as api_router
from api.endpoints.health import router as health_router
from api.endpoints.users import router as users_router
from api.endpoints.organizations import router as orgs_router
from api.endpoints.subscriptions import router as subs_router
from api.endpoints.webhooks import router as webhooks_router
from api.endpoints.oauth import router as oauth_router
from api.endpoints.checkout import router as checkout_router
from api.endpoints.products import router as products_router
from api.endpoints.files import router as files_router
from api.endpoints.notifications import router as notifications_router

# Services
from services.user_service import UserService
from services.organization_service import OrganizationService
from services.subscription_service import SubscriptionService
from services.email_service import EmailService
from services.payment_service import PaymentService
from services.webhook_service import WebhookService
from services.notification_service import NotificationService

# Background tasks
from tasks.worker import create_worker
from tasks.email_tasks import send_email_task
from tasks.webhook_tasks import dispatch_webhook_task
from tasks.subscription_tasks import process_subscription_task

# Models (for side effects / registration)
from models import user, organization, subscription, product, file, webhook

# Schemas
from schemas.common import ErrorResponse, SuccessResponse


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    configure_logging()
    engine = create_engine(settings.database_url)
    read_engine = create_read_replica_engine(settings.read_replica_url)
    session_maker = create_session_maker(engine)
    worker = create_worker()

    yield

    # Shutdown
    await engine.dispose()
    await read_engine.dispose()
    await worker.shutdown()


def create_app():
    """Create and configure the FastAPI application."""
    app = Application(lifespan=lifespan)

    # Add middleware (order matters)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins)

    # Mount routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(orgs_router, prefix="/api/v1/organizations", tags=["organizations"])
    app.include_router(subs_router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
    app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])
    app.include_router(oauth_router, prefix="/oauth", tags=["oauth"])
    app.include_router(checkout_router, prefix="/api/v1/checkout", tags=["checkout"])
    app.include_router(products_router, prefix="/api/v1/products", tags=["products"])
    app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
    app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])

    return app


class Application:
    """Minimal application class for tracing purposes."""
    def __init__(self, lifespan=None):
        self.lifespan = lifespan
        self.middleware = []
        self.routers = []

    def add_middleware(self, middleware_class, **kwargs):
        self.middleware.append((middleware_class, kwargs))

    def include_router(self, router, prefix="", tags=None):
        self.routers.append((router, prefix, tags))


app = create_app()
