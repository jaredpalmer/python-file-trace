"""Background worker configuration."""
from typing import List, Callable
from core.config import settings


class Worker:
    """Background task worker."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.tasks: List[Callable] = []
        self.running = False

    def register(self, task: Callable):
        """Register a task function."""
        self.tasks.append(task)
        return task

    async def start(self):
        """Start the worker."""
        self.running = True

    async def shutdown(self):
        """Shutdown the worker."""
        self.running = False

    async def enqueue(self, task_name: str, *args, **kwargs):
        """Enqueue a task for execution."""
        pass


def create_worker() -> Worker:
    """Create and configure the background worker."""
    worker = Worker(settings.redis_url)
    return worker
