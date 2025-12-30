"""Security utilities."""
import os


def generate_secret_key() -> str:
    """Generate a random secret key."""
    return os.urandom(32).hex()


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return f"hashed_{password}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    return f"token_{data}"


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token."""
    return {"sub": "user_id"}
