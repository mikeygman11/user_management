"""DB model for changing user roles"""
# pylint: disable=not-callable

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base

class RoleChangeLog(Base):
    """Class that defines Role Change Log"""
    __tablename__ = (
        "role_change_logs"
    )  # had to create UUID and match them with the new endpoint

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    target_user_id = Column(UUID(as_uuid=True), nullable=False)
    old_role = Column(String(50))
    new_role = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
