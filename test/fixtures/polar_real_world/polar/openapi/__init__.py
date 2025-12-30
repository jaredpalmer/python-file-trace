"""OpenAPI configuration."""
from enum import Enum


class APITag(str, Enum):
    """API tags."""
    USERS = "users"
    PRODUCTS = "products"


OPENAPI_PARAMETERS = {
    "title": "Polar API",
    "version": "1.0.0",
}


def set_openapi_generator(app):
    """Set OpenAPI generator."""
    pass
