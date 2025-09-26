"""
Content-related Database Models
Stores generated content, versions, and publishing history
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, JSON, Boolean, Integer,
    ForeignKey, Index, UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship, backref

from .models import Base


class ContentRecord(Base):
    """
    Main content record storing generated content
    """
    __tablename__ = 'content_records'

    # Content identification
    content_type = Column(String(50), nullable=False, index=True)  # blog, update, announcement
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, index=True)

    # Content body
    content_html = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=True)
    content_plain = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)

    # Metadata
    author = Column(String(200), default="Content Generator")
    status = Column(String(50), default="draft", index=True)  # draft, published, archived
    source_doc_id = Column(String(500), nullable=True)
    source_doc_type = Column(String(50), nullable=True)  # google_docs, notion, internal

    # SEO and social
    seo_metadata = Column(JSON, default=dict)
    social_metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    categories = Column(JSON, default=list)

    # Publishing information
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    # Tracking
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    engagement_score = Column(Integer, default=0)

    # Relationships
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan")
    publish_logs = relationship("ContentPublishLog", back_populates="content", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        UniqueConstraint('slug', 'content_type', name='uq_slug_type'),
        Index('idx_status_published', 'status', 'published_at'),
        Index('idx_content_search', 'title', 'status'),
    )

    def create_version(self, comment: Optional[str] = None) -> 'ContentVersion':
        """Create a new version of this content"""
        version = ContentVersion(
            content_id=self.id,
            version_number=len(self.versions) + 1,
            title=self.title,
            content_html=self.content_html,
            content_markdown=self.content_markdown,
            content_plain=self.content_plain,
            excerpt=self.excerpt,
            seo_metadata=self.seo_metadata,
            social_metadata=self.social_metadata,
            tags=self.tags,
            categories=self.categories,
            comment=comment
        )
        self.versions.append(version)
        return version


class ContentVersion(Base):
    """
    Content version history for tracking changes
    """
    __tablename__ = 'content_versions'

    # Link to main content
    content_id = Column(String(36), ForeignKey('content_records.id'), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Versioned content
    title = Column(String(500), nullable=False)
    content_html = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=True)
    content_plain = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)

    # Versioned metadata
    seo_metadata = Column(JSON, default=dict)
    social_metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    categories = Column(JSON, default=list)

    # Version metadata
    comment = Column(Text, nullable=True)  # Version comment/reason
    created_by = Column(String(200), nullable=True)

    # Relationships
    content = relationship("ContentRecord", back_populates="versions")

    # Indexes
    __table_args__ = (
        UniqueConstraint('content_id', 'version_number', name='uq_content_version'),
        Index('idx_content_versions', 'content_id', 'version_number'),
    )


class ContentPublishLog(Base):
    """
    Log of content publishing events
    """
    __tablename__ = 'content_publish_logs'

    # Link to content
    content_id = Column(String(36), ForeignKey('content_records.id'), nullable=False)

    # Publishing details
    channel = Column(String(50), nullable=False, index=True)  # email, web, social
    platform = Column(String(50), nullable=True)  # twitter, linkedin, facebook
    status = Column(String(50), nullable=False)  # pending, success, failed

    # Target information
    target_url = Column(String(1000), nullable=True)
    target_id = Column(String(200), nullable=True)  # External platform ID

    # Request/response data
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timing
    initiated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Metrics
    recipients_count = Column(Integer, nullable=True)  # For email
    impressions_count = Column(Integer, nullable=True)  # For social
    clicks_count = Column(Integer, nullable=True)

    # Dry run flag
    is_dry_run = Column(Boolean, default=False, nullable=False)

    # Relationships
    content = relationship("ContentRecord", back_populates="publish_logs")

    # Indexes
    __table_args__ = (
        Index('idx_publish_channel_status', 'channel', 'status'),
        Index('idx_publish_content_channel', 'content_id', 'channel'),
    )