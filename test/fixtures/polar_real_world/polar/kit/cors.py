"""CORS configuration utilities."""
from typing import Callable, Any

Scope = dict


class CORSConfig:
    """CORS configuration."""

    def __init__(
        self,
        matcher: Callable,
        allow_origins: list,
        allow_credentials: bool = False,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        self.matcher = matcher
        self.allow_origins = allow_origins
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or []
        self.allow_headers = allow_headers or []


class CORSMatcherMiddleware:
    """CORS matcher middleware."""

    def __init__(self, app, configs: list):
        self.app = app
        self.configs = configs
