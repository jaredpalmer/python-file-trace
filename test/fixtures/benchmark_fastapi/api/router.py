"""Main API router."""
from .deps import get_current_user, get_db_session


class Router:
    """Simple router for tracing purposes."""

    def __init__(self):
        self.routes = []

    def get(self, path):
        def decorator(func):
            self.routes.append(("GET", path, func))
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.routes.append(("POST", path, func))
            return func
        return decorator


router = Router()


@router.get("/")
async def root():
    return {"message": "API v1"}
