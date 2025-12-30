"""Health check endpoints."""
from api.router import Router
from db.session import get_session
from core.config import settings


router = Router()


@router.get("/")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}


@router.get("/ready")
async def readiness_check():
    # Check database connectivity
    async for session in get_session():
        return {"status": "ready", "database": "connected"}
    return {"status": "not_ready", "database": "disconnected"}
