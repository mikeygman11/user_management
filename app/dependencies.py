"""Dependency injection functions for FastAPI application components."""

from builtins import Exception, dict, str

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Database
from app.services.email_service import EmailService
from app.services.jwt_service import decode_token
from app.utils.template_manager import TemplateManager
from settings.config import Settings


def get_settings() -> Settings:
    """Return application settings instance."""
    return Settings()


def get_email_service() -> EmailService:
    """Set up and return the email service with a template manager."""
    template_manager = TemplateManager()
    return EmailService(template_manager=template_manager)


async def get_db() -> AsyncSession:
    """Dependency that provides an asynchronous database session.

    Yields:
        AsyncSession: SQLAlchemy async session.

    Raises:
        HTTPException: If the session fails to yield properly.
    """
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Extract and validate the current user from the JWT token.

    Args:
        token (str): OAuth2 bearer token.

    Returns:
        dict: A dictionary containing the user_id and role.

    Raises:
        HTTPException: If credentials are invalid or missing.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    user_role: str = payload.get("role")
    if user_id is None or user_role is None:
        raise credentials_exception
    return {"user_id": user_id, "role": user_role}


def require_role(role: str):
    """Factory to enforce role-based access control.

    Args:
        role (str): Required role to access the resource.

    Returns:
        Callable: Dependency function for FastAPI routes.
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        """Check if the current user has the required role.

        Args:
            current_user (dict): The user extracted from the token.

        Returns:
            dict: The validated user.

        Raises:
            HTTPException: If the user does not have permission.
        """
        if current_user["role"] not in role:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user

    return role_checker
