"""Configuration module."""


class Settings:
    """Application settings."""
    CORS_ORIGINS = []
    BACKOFFICE_HOST = None

    def is_sandbox(self):
        return False

    def is_testing(self):
        return True

    def is_read_replica_configured(self):
        return False


settings = Settings()
