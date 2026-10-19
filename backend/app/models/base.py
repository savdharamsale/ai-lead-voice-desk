import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class TenantScopedModel(Base, TimestampMixin):
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), index=True, nullable=False)
