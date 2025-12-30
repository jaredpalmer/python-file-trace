"""OAuth endpoints."""
from api.router import Router
from api.deps import get_db_session
from services.user_service import UserService
from core.security import create_access_token, verify_password
from schemas.auth import LoginRequest, TokenResponse, AuthorizeRequest


router = Router()


@router.post("/token")
async def get_token(data: LoginRequest, session):
    service = UserService(session)
    user = await service.get_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise PermissionError("Invalid credentials")
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/authorize")
async def authorize(params: AuthorizeRequest):
    # OAuth authorization endpoint
    return {
        "client_id": params.client_id,
        "redirect_uri": params.redirect_uri,
        "scope": params.scope,
    }


@router.post("/revoke")
async def revoke_token(token: str):
    # Revoke an access token
    return {"revoked": True}
