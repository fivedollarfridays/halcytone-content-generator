"""
Cache-related Database Models
Tracks cache entries and invalidation events
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, JSON, Integer, Boolean,
    Index, DateTime, UniqueConstraint
)

from .models import Base


class CacheEntry(Base):
    """
    Cache entries stored in database for persistent caching
    """
    __tablename__ = 'cache_entries'

    # Cache key and namespace
    cache_key = Column(String(500), nullable=False)
    namespace = Column(String(100), nullable=False, default='default')

    # Cache value
    value = Column(Text, nullable=True)
    value_type = Column(String(50), nullable=False, default='string')  # string, json, binary
    compressed = Column(Boolean, default=False, nullable=False)

    # Metadata
    size_bytes = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA256 hash

    # TTL and expiration
    ttl_seconds = Column(Integer, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Access tracking
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Tags for batch invalidation
    tags = Column(JSON, default=list)

    # Source information
    source_type = Column(String(50), nullable=True)  # api, computation, external
    source_id = Column(String(200), nullable=True)

    # Indexes
    __table_args__ = (
        UniqueConstraint('cache_key', 'namespace', name='uq_cache_key_namespace'),
        Index('idx_cache_expires', 'expires_at'),
        Index('idx_cache_namespace', 'namespace'),
        Index('idx_cache_accessed', 'last_accessed_at'),
    )

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def increment_access(self):
        """Increment access counter and update last access time"""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()


class CacheInvalidation(Base):
    """
    Log of cache invalidation events
    """
    __tablename__ = 'cache_invalidations'

    # Invalidation details
    invalidation_type = Column(String(50), nullable=False)  # key, pattern, tag, all
    target = Column(String(500), nullable=True)  # Specific key, pattern, or tag
    namespace = Column(String(100), nullable=True)

    # Scope
    scope = Column(String(50), nullable=False, default='local')  # local, cdn, distributed
    targets_affected = Column(Integer, nullable=True)

    # Reason and initiator
    reason = Column(String(500), nullable=True)
    initiated_by = Column(String(200), nullable=True)  # User or system
    initiated_from = Column(String(50), nullable=True)  # api, webhook, scheduled

    # Status
    status = Column(String(50), nullable=False, default='pending')  # pending, completed, failed
    error_message = Column(Text, nullable=True)

    # Timing
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Webhook notification
    webhook_url = Column(String(1000), nullable=True)
    webhook_status = Column(String(50), nullable=True)
    webhook_response = Column(JSON, nullable=True)

    # Metadata
    metadata = Column(JSON, default=dict)

    # Indexes
    __table_args__ = (
        Index('idx_invalidation_type_status', 'invalidation_type', 'status'),
        Index('idx_invalidation_time', 'created_at'),
        Index('idx_invalidation_namespace', 'namespace'),
    )