"""User service declaration"""
# pylint: disable=unused-argument
# pylint: disable=logging-fstring-interpolation
# pylint: disable=unused-import

import logging
import secrets
from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import func, null, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_settings
from app.models.role_change_log_model import RoleChangeLog
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.services.email_service import EmailService
from app.utils.nickname_gen import generate_nickname
from app.utils.security import (generate_verification_token, hash_password,
                                verify_password)

settings = get_settings()
logger = logging.getLogger(__name__)


class UserService:
    """User service class"""
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        """Execute query"""
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        """Get user"""
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        """Use ID to get"""
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(
        cls, session: AsyncSession, nickname: str
    ) -> Optional[User]:
        """Get by nickname"""
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_data: Dict[str, str],
        email_service: EmailService,
    ) -> Optional[User]:
        """Create user"""
        try:
            validated_data = UserCreate(**user_data).model_dump()
            existing_user = await cls.get_by_email(session, validated_data["email"])
            if existing_user:
                logger.error("User with given email already exists.")
                return None

            validated_data["hashed_password"] = hash_password(
                validated_data.pop("password")
            )
            new_user = User(**validated_data)

            # Assign generated nickname
            new_nickname = generate_nickname()
            while await cls.get_by_nickname(session, new_nickname):
                new_nickname = generate_nickname()
            new_user.nickname = new_nickname

            # Determine role
            user_count = await cls.count(session)
            new_user.role = UserRole.ADMIN if user_count == 0 else UserRole.ANONYMOUS

            # Mark email as verified for first ADMIN
            if new_user.role == UserRole.ADMIN:
                new_user.email_verified = True
            else:
                new_user.verification_token = generate_verification_token()

            # Save user to DB before sending email
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)  # Ensure user.id is populated

            # Send email only after user.id is ready
            if new_user.role != UserRole.ADMIN:
                await email_service.send_verification_email(new_user)

            return new_user

        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None

    @classmethod
    async def update(
        cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]
    ) -> Optional[User]:
        """Update user"""
        try:
            # validated_data = UserUpdate(**update_data).dict(exclude_unset=True)
            validated_data = UserUpdate(**update_data).model_dump(exclude_unset=True)

            if "password" in validated_data:
                validated_data["hashed_password"] = hash_password(
                    validated_data.pop("password")
                )
            query = (
                update(User)
                .where(User.id == user_id)
                .values(**validated_data)
                .execution_options(synchronize_session="fetch")
            )
            await cls._execute_query(session, query)
            updated_user = await cls.get_by_id(session, user_id)
            if updated_user:
                session.refresh(
                    updated_user
                )  # Explicitly refresh the updated user object
                logger.info(f"User {user_id} updated successfully.")
                return updated_user
            else:
                logger.error(f"User {user_id} not found after update attempt.")
            return None
        except Exception as e:  # Broad exception handling for debugging
            logger.error(f"Error during user update: {e}")
            return None

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        """Delete user"""
        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.info(f"User with ID {user_id} not found.")
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def list_users(
        cls, session: AsyncSession, skip: int = 0, limit: int = 10
    ) -> List[User]:
        """List all users"""
        query = select(User).offset(skip).limit(limit)
        result = await cls._execute_query(session, query)
        return result.scalars().all() if result else []

    @classmethod
    async def register_user(
        cls, session: AsyncSession, user_data: Dict[str, str], get_email_service
    ) -> Optional[User]:
        """Register user in db"""
        return await cls.create(session, user_data, get_email_service)

    @classmethod
    async def login_user(
        cls, session: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """Login as user"""
        user = await cls.get_by_email(session, email)
        if user:
            if user.email_verified is False:
                return None
            if user.is_locked:
                return None
            if verify_password(password, user.hashed_password):
                user.failed_login_attempts = 0
                user.last_login_at = datetime.now(timezone.utc)
                session.add(user)
                await session.commit()
                return user
            else:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.max_login_attempts:
                    user.is_locked = True
                session.add(user)
                await session.commit()
        return None

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        """Check if locked"""
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False

    @classmethod
    async def reset_password(
        cls, session: AsyncSession, user_id: UUID, new_password: str
    ) -> bool:
        """Reset pw"""
        hashed_password = hash_password(new_password)
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            user.failed_login_attempts = 0  # Resetting failed login attempts
            user.is_locked = False  # Unlocking the user account, if locked
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(
        cls, session: AsyncSession, user_id: UUID, token: str
    ) -> bool:
        """Verify email"""
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.verification_token = None

            # Only upgrade role if the user is ANONYMOUS
            if user.role == UserRole.ANONYMOUS:
                user.role = UserRole.AUTHENTICATED

            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """
        Count the number of users in the database.

        :param session: The AsyncSession instance for database access.
        :return: The count of users.
        """
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        count = result.scalar()
        return count

    @classmethod
    async def unlock_user_account(cls, session: AsyncSession, user_id: UUID) -> bool:
        """Unlock user acc"""
        user = await cls.get_by_id(session, user_id)
        if user and user.is_locked:
            user.is_locked = False
            user.failed_login_attempts = 0  # Optionally reset failed login attempts
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def update_role(
        cls, session: AsyncSession, user_id: UUID, new_role: UserRole, changed_by: UUID
    ) -> Optional[User]:
        """Update role"""
        try:
            logger.info(
                f"Updating role for user_id={user_id} to {new_role}, changed_by={changed_by}"
            )
            user = await cls.get_by_id(session, user_id)
            if not user:
                logger.warning(f"User {user_id} not found.")
                return None

            old_role = user.role
            if old_role == new_role:
                logger.info(f"Role is already {new_role}, no change.")
                return user  # No change needed

            user.role = new_role
            session.add(user)

            # Log role change
            log = RoleChangeLog(
                target_user_id=user_id,
                changed_by=changed_by,
                old_role=old_role.value,
                new_role=new_role.value,
            )
            session.add(log)

            await session.commit()
            await session.refresh(user)
            logger.info(f"Role updated successfully for user_id={user_id}")
            return user
        except Exception as e:
            logger.exception(f"Failed to update role: {e}")
            await session.rollback()
            raise
