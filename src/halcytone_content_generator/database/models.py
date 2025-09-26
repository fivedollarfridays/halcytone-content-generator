"""
Database Models Base
Defines base model class and common model utilities
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import MetaData, Column, DateTime, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeBase


# Naming convention for constraints (helps with migrations)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    Base model class with common fields and methods
    """
    metadata = metadata

    # Common fields for all models
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now()
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        # Convert CamelCase to snake_case
        import re
        name = cls.__name__
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result

    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()

    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        """String representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Import all models here to ensure they're registered with Base
# This ensures Alembic can detect them for migrations
from .models_content import ContentRecord, ContentVersion, ContentPublishLog
from .models_audit import AuditLog, ApiRequestLog, UserActivity
from .models_cache import CacheEntry, CacheInvalidation


__all__ = [
    'Base',
    'metadata',
    'ContentRecord',
    'ContentVersion',
    'ContentPublishLog',
    'AuditLog',
    'ApiRequestLog',
    'UserActivity',
    'CacheEntry',
    'CacheInvalidation',
]