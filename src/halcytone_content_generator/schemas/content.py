"""
Pydantic models for content generation
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class ContentItem(BaseModel):
    """Individual content item from living document"""
    title: str
    content: str
    date: Optional[datetime] = None
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NewsletterContent(BaseModel):
    """Newsletter content structure"""
    subject: str
    html: str
    text: str
    preview_text: Optional[str] = None
    recipient_count: Optional[int] = None


class WebUpdateContent(BaseModel):
    """Website update content structure"""
    title: str
    content: str
    excerpt: str
    slug: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None


class SocialPost(BaseModel):
    """Social media post structure"""
    platform: str
    content: str
    hashtags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    scheduled_for: Optional[datetime] = None


class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    send_email: bool = Field(default=True, description="Send newsletter via CRM")
    publish_web: bool = Field(default=True, description="Publish to website")
    generate_social: bool = Field(default=True, description="Generate social media posts")
    preview_only: bool = Field(default=False, description="Only preview without sending")
    include_preview: bool = Field(default=True, description="Include preview in response")
    force_refresh: bool = Field(default=False, description="Force refresh from living document")


class ContentGenerationResponse(BaseModel):
    """Response model for content generation"""
    status: str
    results: Optional[Dict[str, Any]] = None
    newsletter: Optional[NewsletterContent] = None
    web_update: Optional[WebUpdateContent] = None
    social_posts: Optional[List[SocialPost]] = None
    errors: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentPreview(BaseModel):
    """Preview model for content"""
    newsletter: NewsletterContent
    web_update: WebUpdateContent
    social_posts: List[SocialPost]
    content_summary: Dict[str, int]
    preview_generated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentContent(BaseModel):
    """Parsed content from living document"""
    breathscape: List[ContentItem] = Field(default_factory=list)
    hardware: List[ContentItem] = Field(default_factory=list)
    tips: List[ContentItem] = Field(default_factory=list)
    vision: List[ContentItem] = Field(default_factory=list)
    raw_content: Optional[str] = None


class EmailDeliveryResult(BaseModel):
    """Result of email delivery"""
    sent: int
    failed: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
    delivery_id: Optional[str] = None


class WebPublishResult(BaseModel):
    """Result of web publication"""
    id: str
    url: str
    published: bool
    published_at: datetime


class Content(BaseModel):
    """
    Universal content model that can represent any type of content
    for the Publisher interface
    """
    content_type: str = Field(..., description="Type of content (email, web, social)")
    data: Dict[str, Any] = Field(..., description="Content data specific to the type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    scheduled_for: Optional[datetime] = Field(None, description="When to publish this content")
    dry_run: bool = Field(False, description="Whether this is a dry run")

    @classmethod
    def from_newsletter(cls, newsletter: NewsletterContent, **kwargs) -> "Content":
        """Create Content from NewsletterContent"""
        return cls(
            content_type="email",
            data=newsletter.model_dump(),
            **kwargs
        )

    @classmethod
    def from_web_update(cls, web_update: WebUpdateContent, **kwargs) -> "Content":
        """Create Content from WebUpdateContent"""
        return cls(
            content_type="web",
            data=web_update.model_dump(),
            **kwargs
        )

    @classmethod
    def from_social_post(cls, social_post: SocialPost, **kwargs) -> "Content":
        """Create Content from SocialPost"""
        return cls(
            content_type="social",
            data=social_post.model_dump(),
            **kwargs
        )

    def to_newsletter(self) -> NewsletterContent:
        """Convert to NewsletterContent"""
        if self.content_type != "email":
            raise ValueError(f"Cannot convert {self.content_type} content to newsletter")
        return NewsletterContent(**self.data)

    def to_web_update(self) -> WebUpdateContent:
        """Convert to WebUpdateContent"""
        if self.content_type != "web":
            raise ValueError(f"Cannot convert {self.content_type} content to web update")
        return WebUpdateContent(**self.data)

    def to_social_post(self) -> SocialPost:
        """Convert to SocialPost"""
        if self.content_type != "social":
            raise ValueError(f"Cannot convert {self.content_type} content to social post")
        return SocialPost(**self.data)


class BatchContentRequest(BaseModel):
    """Request model for batch content generation"""
    period: str = Field(..., description="Time period: 'day', 'week', 'month'")
    channels: List[str] = Field(..., description="Channels to generate content for")
    count: Optional[int] = Field(None, description="Number of content items to generate")
    start_date: Optional[datetime] = Field(None, description="Start date for content generation")
    dry_run: bool = Field(False, description="Preview mode without actual generation")
    template_variety: bool = Field(True, description="Use different templates across items")
    include_scheduling: bool = Field(True, description="Include optimal scheduling recommendations")
    content_themes: Optional[List[str]] = Field(None, description="Specific content themes to focus on")


class BatchContentItem(BaseModel):
    """Single item in a batch content generation"""
    item_id: str = Field(..., description="Unique identifier for this content item")
    content_type: str = Field(..., description="Type of content (email, web, social)")
    content: Content = Field(..., description="The actual content")
    scheduled_for: Optional[datetime] = Field(None, description="Recommended publish time")
    priority: int = Field(1, description="Priority level (1=highest, 5=lowest)")
    dependencies: List[str] = Field(default_factory=list, description="Content items this depends on")
    estimated_engagement: Optional[float] = Field(None, description="Estimated engagement score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BatchContentResponse(BaseModel):
    """Response model for batch content generation"""
    batch_id: str = Field(..., description="Unique identifier for this batch")
    status: str = Field(..., description="Generation status")
    items: List[BatchContentItem] = Field(..., description="Generated content items")
    summary: Dict[str, Any] = Field(..., description="Batch generation summary")
    scheduling_plan: Optional[Dict[str, Any]] = Field(None, description="Recommended scheduling plan")
    dry_run: bool = Field(False, description="Whether this was a dry run")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_items: int = Field(..., description="Total number of items generated")
    estimated_reach: Optional[int] = Field(None, description="Estimated total reach")


class BatchScheduleRequest(BaseModel):
    """Request model for scheduling a batch"""
    batch_id: str = Field(..., description="Batch ID to schedule")
    schedule_all: bool = Field(True, description="Schedule all items in batch")
    custom_schedule: Optional[Dict[str, datetime]] = Field(None, description="Custom schedule for specific items")
    dry_run: bool = Field(False, description="Preview scheduling without execution")


class BatchScheduleResponse(BaseModel):
    """Response model for batch scheduling"""
    batch_id: str = Field(..., description="Batch ID that was scheduled")
    scheduled_items: List[str] = Field(..., description="Item IDs that were scheduled")
    schedule_summary: Dict[str, Any] = Field(..., description="Scheduling summary")
    next_publish_time: Optional[datetime] = Field(None, description="Next scheduled publish time")
    dry_run: bool = Field(False, description="Whether this was a dry run")


class BatchStatusResponse(BaseModel):
    """Response model for batch status"""
    batch_id: str = Field(..., description="Batch identifier")
    status: str = Field(..., description="Current batch status")
    items_total: int = Field(..., description="Total items in batch")
    items_published: int = Field(..., description="Items successfully published")
    items_pending: int = Field(..., description="Items pending publication")
    items_failed: int = Field(..., description="Items that failed to publish")
    last_updated: datetime = Field(..., description="Last status update time")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")