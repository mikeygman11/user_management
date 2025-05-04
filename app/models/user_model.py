"""Defines the User model and UserRole enum for SQLAlchemy ORM integration."""

from builtins import bool, int, str
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Enum as SQLAlchemyEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserRole(Enum):
    """Enumeration of user roles within the application."""
    ANONYMOUS = "ANONYMOUS"
    AUTHENTICATED = "AUTHENTICATED"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class User(Base):
    """
    Represents a user within the application, corresponding to the 'users' table in the database.
    """

    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nickname: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = Column(String(100), nullable=True)
    last_name: Mapped[str] = Column(String(100), nullable=True)
    bio: Mapped[str] = Column(String(500), nullable=True)
    profile_picture_url: Mapped[str] = Column(String(255), nullable=True)
    linkedin_profile_url: Mapped[str] = Column(String(255), nullable=True)
    github_profile_url: Mapped[str] = Column(String(255), nullable=True)
    role: Mapped[UserRole] = Column(
        SQLAlchemyEnum(UserRole, name='UserRole', create_constraint=True), nullable=False
    )
    is_professional: Mapped[bool] = Column(Boolean, default=False)
    professional_status_updated_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = Column(Integer, default=0)
    is_locked: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default="now()", onupdate="now()")
    verification_token = Column(String, nullable=True)
    email_verified: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)

    def __repr__(self) -> str:
        """Provides a readable string representation of the User."""
        return f"<User {self.nickname}, Role: {self.role.name}>"

    def lock_account(self):
        """Locks the user account."""
        self.is_locked = True

    def unlock_account(self):
        """Unlocks the user account."""
        self.is_locked = False

    def verify_email(self):
        """Marks the user's email as verified."""
        self.email_verified = True

    def has_role(self, role_name: UserRole) -> bool:
        """Checks if the user has a specific role."""
        return self.role == role_name

    def update_professional_status(self, status: bool):
        """
        Updates the professional status and logs the update time.
        This does not persist to the DB until explicitly committed.
        """
        self.is_professional = status
        self.professional_status_updated_at = datetime.utcnow()
