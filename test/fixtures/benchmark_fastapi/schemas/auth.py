"""Authentication schemas."""
from typing import Optional
from .common import BaseSchema


class LoginRequest(BaseSchema):
    """Schema for login request."""
    email: str
    password: str


class TokenResponse(BaseSchema):
    """Schema for token response."""
    access_token: str
    token_type: str


class AuthorizeRequest(BaseSchema):
    """Schema for OAuth authorize request."""
    client_id: str
    redirect_uri: str
    scope: str
    response_type: str = "code"
    state: Optional[str] = None
