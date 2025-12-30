"""Email background tasks."""
from services.email_service import EmailService
from models.user import User


async def send_email_task(
    to: str,
    subject: str,
    body: str,
    html_body: str = None,
) -> bool:
    """Background task to send an email."""
    service = EmailService()
    return await service.send_email(to, subject, body, html_body)


async def send_welcome_email_task(user_id: str):
    """Background task to send welcome email."""
    user = User(id=user_id, email="user@example.com", name="User")
    service = EmailService()
    return await service.send_welcome_email(user)


async def send_password_reset_task(user_id: str, token: str):
    """Background task to send password reset email."""
    user = User(id=user_id, email="user@example.com", name="User")
    service = EmailService()
    return await service.send_password_reset(user, token)
