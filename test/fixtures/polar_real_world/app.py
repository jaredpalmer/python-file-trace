"""
Real-world test fixture based on Polar's app.py structure.
This mimics the import patterns found in production FastAPI applications.
See: https://github.com/polarsource/polar/blob/main/server/polar/app.py
"""
import contextlib
from collections.abc import AsyncIterator
from typing import TypedDict

# Third-party imports (will be unresolved - that's expected)
# import structlog
# from fastapi import FastAPI
# from fastapi.routing import APIRoute

# Internal imports - these should all be traced
from polar import worker  # noqa
from polar.api import router
from polar.auth.middlewares import AuthSubjectMiddleware
from polar.backoffice import app as backoffice_app
from polar.checkout import ip_geolocation
from polar.config import settings
from polar.exception_handlers import add_exception_handlers
from polar.health.endpoints import router as health_router
from polar.kit.cors import CORSConfig, CORSMatcherMiddleware, Scope
from polar.kit.db.postgres import (
    AsyncEngine,
    AsyncSessionMaker,
    Engine,
    SyncSessionMaker,
    create_async_sessionmaker,
    create_sync_sessionmaker,
)
from polar.logfire import (
    configure_logfire,
    instrument_fastapi,
    instrument_httpx,
    instrument_sqlalchemy,
)
from polar.logging import Logger
from polar.logging import configure as configure_logging
from polar.middlewares import (
    FlushEnqueuedWorkerJobsMiddleware,
    LogCorrelationIdMiddleware,
    PathRewriteMiddleware,
    SandboxResponseHeaderMiddleware,
)
from polar.oauth2.endpoints.well_known import router as well_known_router
from polar.oauth2.exception_handlers import OAuth2Error, oauth2_error_exception_handler
from polar.openapi import OPENAPI_PARAMETERS, APITag, set_openapi_generator
from polar.postgres import (
    AsyncSessionMiddleware,
    create_async_engine,
    create_async_read_engine,
    create_sync_engine,
)
from polar.posthog import configure_posthog
from polar.redis import Redis, create_redis
from polar.search.endpoints import router as search_router
from polar.sentry import configure_sentry
from polar.webhook.webhooks import document_webhooks

from . import rate_limit


class State(TypedDict):
    """Application state type."""
    async_engine: object
    redis: object


@contextlib.asynccontextmanager
async def lifespan(app: object) -> AsyncIterator[State]:
    """Application lifespan context manager."""
    yield {
        "async_engine": None,
        "redis": None,
    }


def create_app():
    """Create and configure the FastAPI application."""
    configure_sentry()
    configure_logfire("server")
    configure_logging(logfire=True)
    configure_posthog()
    return None
