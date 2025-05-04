"""Defines the RoleChangeLog model for auditing user role changes."""

from uuid import uuid4

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base

class RoleChangeLog(Base):
    """
    Logs changes to user roles for auditing purposes.

    Attributes:
        id (UUID): Primary key for the log entry.
        changed_by (UUID): ID of the user who made the change.
        target_user_id (UUID): ID of the user whose role was changed.
        old_role (str): Previous role of the user.
        new_role (str): New role of the user.
        timestamp (datetime): Time when the role change occurred.
    """
    __tablename__ = "role_change_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    target_user_id = Column(UUID(as_uuid=True), nullable=False)
    old_role = Column(String(50))
    new_role = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
