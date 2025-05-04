"""Service layer for managing user-related business logic and database interactions."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_settings
from app.models.role_change_log_model import RoleChangeLog
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.services.email_service import EmailService
from app.utils.nickname_gen import generate_nickname
from app.utils.security import (
    generate_verification_token,
    hash_password,
    verify_password,
)

settings = get_settings()
logger = logging.getLogger(__name__)


class UserService:
    """Provides business logic for user creation, authentication, updates, and role management."""

    @classmethod
    async def _execute_query(
        cls, session: AsyncSession, query
    ) -> Optional[any]:
        """
        Execute a SQLAlchemy query, commit if successful, rollback on error.
        Returns the Result or None on failure.
        """
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error("Database error: %s", e)
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(
        cls, session: AsyncSession, **filters
    ) -> Optional[User]:
        """Return the first User matching the given filter criteria."""
        result = await cls._execute_query(
            session, select(User).filter_by(**filters)
        )
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(
        cls, session: AsyncSession, user_id: uuid.UUID
    ) -> Optional[User]:
        """Fetch a user by their primary key."""
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(
        cls, session: AsyncSession, nickname: str
    ) -> Optional[User]:
        """Fetch a user by nickname."""
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(
        cls, session: AsyncSession, email: str
    ) -> Optional[User]:
        """Fetch a user by email address."""
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_data: Dict[str, str],
        email_service: EmailService,
    ) -> Optional[User]:
        """
        Validate and create a new User record.
        - First user ever becomes ADMIN and is auto-verified.
        - Others start as ANONYMOUS with a verification token emailed.
        """
        try:
            data = UserCreate(**user_data).model_dump()
        except ValidationError as e:
            logger.error("Validation error during user creation: %s", e)
            return None

        if await cls.get_by_email(session, data["email"]):
            logger.error("User with given email already exists.")
            return None

        # Hash password and prepare User
        data["hashed_password"] = hash_password(data.pop("password"))
        new_user = User(**data)

        # Ensure unique nickname
        nickname = generate_nickname()
        while await cls.get_by_nickname(session, nickname):
            nickname = generate_nickname()
        new_user.nickname = nickname

        # First user is ADMIN
        if await cls.count(session) == 0:
            new_user.role = UserRole.ADMIN
            new_user.email_verified = True
        else:
            new_user.role = UserRole.ANONYMOUS
            new_user.verification_token = generate_verification_token()

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        if new_user.role != UserRole.ADMIN:
            await email_service.send_verification_email(new_user)

        return new_user

    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        user_id: uuid.UUID,
        update_data: Dict[str, str],
    ) -> Optional[User]:
        """
        Update an existing user.
        - Automatically re-hashes password if included.
        """
        try:
            data = UserUpdate(**update_data).model_dump(exclude_unset=True)
        except ValidationError as e:
            logger.error("Validation error during user update: %s", e)
            return None

        if "password" in data:
            data["hashed_password"] = hash_password(data.pop("password"))

        await cls._execute_query(
            session,
            update(User).where(User.id == user_id).values(**data)
            .execution_options(synchronize_session="fetch"),
        )

        updated = await cls.get_by_id(session, user_id)
        if updated:
            await session.refresh(updated)
            logger.info("User %s updated successfully.", user_id)
            return updated

        logger.error("User %s not found after update attempt.", user_id)
        return None

    @classmethod
    async def delete(
        cls, session: AsyncSession, user_id: uuid.UUID
    ) -> bool:
        """Delete a user by ID. Returns True if deleted, False if not found."""
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info("User with ID %s not found.", user_id)
            return False

        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(
        cls, session: AsyncSession, skip: int = 0, limit: int = 10
    ) -> List[User]:
        """Return a paginated list of users."""
        result = await cls._execute_query(
            session, select(User).offset(skip).limit(limit)
        )
        return result.scalars().all() if result else []

    @classmethod
    async def login_user(
        cls, session: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user.
        - Locks account after max failed attempts (from settings).
        - Resets failed_login_attempts on success.
        """
        user = await cls.get_by_email(session, email)
        if not user or not user.email_verified or user.is_locked:
            return None

        if verify_password(password, user.hashed_password):
            user.failed_login_attempts = 0
            user.last_login_at = datetime.now(timezone.utc)
        else:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.is_locked = True

        session.add(user)
        await session.commit()
        return user if verify_password(password, user.hashed_password) else None

    @classmethod
    async def is_account_locked(
        cls, session: AsyncSession, email: str
    ) -> bool:
        """Check if a given email’s account is locked."""
        user = await cls.get_by_email(session, email)
        return bool(user and user.is_locked)

    @classmethod
    async def reset_password(
        cls, session: AsyncSession, user_id: uuid.UUID, new_password: str
    ) -> bool:
        """Force-reset a user’s password, clearing lock and failed attempts."""
        user = await cls.get_by_id(session, user_id)
        if not user:
            return False

        user.hashed_password = hash_password(new_password)
        user.failed_login_attempts = 0
        user.is_locked = False
        session.add(user)
        await session.commit()
        return True

    @classmethod
    async def verify_email_with_token(
        cls,
        session: AsyncSession,
        user_id: uuid.UUID,
        token: str,
    ) -> bool:
        """Mark email_verified=True if the provided token matches."""
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.verification_token = None
            if user.role == UserRole.ANONYMOUS:
                user.role = UserRole.AUTHENTICATED

            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """Return the total number of users in the system."""
        result = await session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar_one()

    @classmethod
    async def unlock_user_account(
        cls, session: AsyncSession, user_id: uuid.UUID
    ) -> bool:
        """Unlock a locked account and reset its failed login counter."""
        user = await cls.get_by_id(session, user_id)
        if not user or not user.is_locked:
            return False

        user.is_locked = False
        user.failed_login_attempts = 0
        session.add(user)
        await session.commit()
        return True

    @classmethod
    async def update_role(
        cls,
        session: AsyncSession,
        user_id: uuid.UUID,
        new_role: UserRole,
        changed_by: uuid.UUID,
    ) -> Optional[User]:
        """
        Change a user’s role and log the change.
        Returns the updated User or None if user not found.
        """
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.warning("User %s not found.", user_id)
            return None

        if user.role == new_role:
            logger.info("Role is already %s; no change made.", new_role)
            return user

        old = user.role
        user.role = new_role
        session.add(user)

        log_entry = RoleChangeLog(
            target_user_id=user_id,
            changed_by=changed_by,
            old_role=old.value,
            new_role=new_role.value,
        )
        session.add(log_entry)

        await session.commit()
        await session.refresh(user)
        logger.info("Role updated successfully for user_id=%s", user_id)
        return user
