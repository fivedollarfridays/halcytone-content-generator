"""
Audit and Logging Database Models
Tracks API requests, user activity, and system events
"""

from sqlalchemy import (
    Column, String, Text, JSON, Integer, Float,
    Index, DateTime
)

from .models import Base


class AuditLog(Base):
    """
    General audit log for tracking system events
    """
    __tablename__ = 'audit_logs'

    # Event information
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # security, data, system
    event_action = Column(String(100), nullable=False)

    # Actor information
    user_id = Column(String(200), nullable=True, index=True)
    user_email = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Target information
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(200), nullable=True)
    resource_name = Column(String(500), nullable=True)

    # Event details
    details = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)

    # Result
    status = Column(String(50), nullable=False)  # success, failure, error
    error_message = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_event_time', 'event_type', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )


class ApiRequestLog(Base):
    """
    Detailed API request logging for monitoring and debugging
    """
    __tablename__ = 'api_request_logs'

    # Request identification
    correlation_id = Column(String(100), nullable=True, index=True)
    request_id = Column(String(100), nullable=True, index=True)

    # Request details
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSON, nullable=True)
    headers = Column(JSON, nullable=True)
    body = Column(Text, nullable=True)  # Truncated for large payloads

    # Client information
    client_ip = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    api_key_id = Column(String(100), nullable=True, index=True)

    # Response details
    status_code = Column(Integer, nullable=True, index=True)
    response_body = Column(Text, nullable=True)  # Truncated for large payloads
    response_headers = Column(JSON, nullable=True)

    # Performance metrics
    duration_ms = Column(Float, nullable=True)
    database_queries = Column(Integer, nullable=True)
    cache_hits = Column(Integer, nullable=True)
    cache_misses = Column(Integer, nullable=True)

    # Error information
    error_type = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Service information
    service_version = Column(String(50), nullable=True)
    environment = Column(String(50), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_api_path_method', 'path', 'method'),
        Index('idx_api_status_time', 'status_code', 'created_at'),
        Index('idx_api_correlation', 'correlation_id'),
    )


class UserActivity(Base):
    """
    Track user activity and usage patterns
    """
    __tablename__ = 'user_activities'

    # User identification
    user_id = Column(String(200), nullable=False, index=True)
    user_email = Column(String(200), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Activity details
    activity_type = Column(String(100), nullable=False, index=True)
    activity_category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Context
    session_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    location = Column(JSON, nullable=True)  # {country, region, city}
    device_info = Column(JSON, nullable=True)  # {browser, os, device_type}

    # Related resources
    content_id = Column(String(200), nullable=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(200), nullable=True)

    # Metrics
    duration_seconds = Column(Integer, nullable=True)
    data_volume = Column(Integer, nullable=True)  # Bytes

    # Additional data
    metadata = Column(JSON, default=dict)

    # Indexes
    __table_args__ = (
        Index('idx_activity_user_time', 'user_id', 'created_at'),
        Index('idx_activity_type_time', 'activity_type', 'created_at'),
        Index('idx_activity_session', 'session_id'),
    )