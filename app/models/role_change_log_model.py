from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base

class RoleChangeLog(Base):
    __tablename__ = "role_change_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    target_user_id = Column(UUID(as_uuid=True), nullable=False)
    old_role = Column(String(50))
    new_role = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
