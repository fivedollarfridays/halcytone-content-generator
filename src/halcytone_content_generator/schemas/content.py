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
            data=newsletter.dict(),
            **kwargs
        )

    @classmethod
    def from_web_update(cls, web_update: WebUpdateContent, **kwargs) -> "Content":
        """Create Content from WebUpdateContent"""
        return cls(
            content_type="web",
            data=web_update.dict(),
            **kwargs
        )

    @classmethod
    def from_social_post(cls, social_post: SocialPost, **kwargs) -> "Content":
        """Create Content from SocialPost"""
        return cls(
            content_type="social",
            data=social_post.dict(),
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