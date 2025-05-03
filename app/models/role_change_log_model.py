from app.database import Base
from sqlalchemy import Column, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from app.models.user_model import UserRole
import uuid
from datetime import datetime

class RoleChangeLog(Base):
    __tablename__ = "role_change_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    new_role = Column(SQLEnum(UserRole), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)