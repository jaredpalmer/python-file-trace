"""Redis integration."""


class Redis:
    """Redis client."""

    async def close(self, wait: bool = False):
        """Close Redis connection."""
        pass


def create_redis(name: str):
    """Create Redis client."""
    return Redis()
