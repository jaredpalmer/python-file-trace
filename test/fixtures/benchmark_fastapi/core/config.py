"""Application configuration."""
from typing import List, Optional
from .security import generate_secret_key


class Settings:
    """Application settings loaded from environment."""

    def __init__(self):
        self.app_name: str = "benchmark-app"
        self.debug: bool = False
        self.database_url: str = "postgresql://localhost/app"
        self.read_replica_url: Optional[str] = None
        self.redis_url: str = "redis://localhost:6379"
        self.secret_key: str = generate_secret_key()
        self.allowed_origins: List[str] = ["http://localhost:3000"]
        self.stripe_api_key: Optional[str] = None
        self.sendgrid_api_key: Optional[str] = None
        self.sentry_dsn: Optional[str] = None


settings = Settings()
