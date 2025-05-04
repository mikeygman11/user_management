"""FastAPI dependencies for settings, DB sessions, authentication, and authorization."""
from typing import Dict

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..settings.config import Settings
from .database import Database
from .utils.template_manager import TemplateManager
from .services.email_service import EmailService
from .services.jwt_service import decode_token


def get_settings() -> Settings:
    """Retrieve application settings."""
    return Settings()


def get_email_service() -> EmailService:
    """Instantiate and return the EmailService."""
    template_manager = TemplateManager()
    return EmailService(template_manager=template_manager)


async def get_db() -> AsyncSession:
    """
    Provide a database session for each request.
    Rolls back on error and raises HTTP 500 on failure.
    """
    session_factory = Database.get_session_factory()  # type: ignore
    # pylint: disable=not-callable
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
    # pylint: enable=not-callable


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Dict[str, str]:
    """
    Validate and decode the OAuth2 token.
    Returns a dict with 'user_id' and 'role', or raises 401.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    user_role = payload.get("role")
    if not user_id or not user_role:
        raise credentials_exception

    return {"user_id": user_id, "role": user_role}


def require_role(required_role: str):
    """
    Dependency factory enforcing that the current user has the given role.
    Usage: Depends(require_role("ADMIN"))
    """
    def role_checker(current_user: Dict[str, str] = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=403,
                detail="Operation not permitted",
            )
        return current_user

    return role_checker
