"""
Strict Pydantic v2 models for all content types with comprehensive validation
Sprint 2: Schema Validation Implementation
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Dict, List, Optional, Any, Union, Literal, Annotated
from datetime import datetime, timezone, timedelta
from enum import Enum
import re


class ContentType(str, Enum):
    """Supported content types from editor guide"""
    UPDATE = "update"
    BLOG = "blog"
    ANNOUNCEMENT = "announcement"
    SESSION = "session"  # Sprint 3: Halcytone Live session summaries


class ContentPriority(int, Enum):
    """Content priority levels (1=highest, 5=lowest)"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    ARCHIVE = 5


class TemplateStyle(str, Enum):
    """Available template styles"""
    MODERN = "modern"
    MINIMAL = "minimal"
    BREATHSCAPE = "breathscape"
    ANNOUNCEMENT = "announcement"
    PLAIN = "plain"


class ChannelType(str, Enum):
    """Publishing channels"""
    EMAIL = "email"
    WEB = "web"
    SOCIAL = "social"
    PREVIEW = "preview"


class SocialPlatform(str, Enum):
    """Supported social media platforms"""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class ContentBaseStrict(BaseModel):
    """
    Base content schema with strict validation
    Implements Sprint 2 requirement for schema validation before publishing
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
        frozen=False
    )

    type: ContentType = Field(
        description="Content type (update, blog, announcement, session)"
    )

    title: Annotated[str, Field(
        min_length=1,
        max_length=200,
        description="Content title (1-200 characters)"
    )]

    content: Annotated[str, Field(
        min_length=10,
        description="Main content body (minimum 10 characters)"
    )]

    date: Annotated[datetime, Field(
        description="Content creation/publication date"
    )] = Field(default_factory=lambda: datetime.now(timezone.utc))

    author: Annotated[str, Field(
        max_length=100,
        description="Content author name"
    )] = "Halcytone Team"

    published: bool = Field(
        default=False,
        description="Whether content is ready for publication"
    )

    featured: bool = Field(
        default=False,
        description="Whether content should get priority placement"
    )

    channels: List[ChannelType] = Field(
        default=[ChannelType.EMAIL, ChannelType.WEB, ChannelType.SOCIAL],
        description="Target publishing channels"
    )

    priority: ContentPriority = Field(
        default=ContentPriority.NORMAL,
        description="Content priority level"
    )

    template: Optional[TemplateStyle] = Field(
        default=None,
        description="Override template selection"
    )

    scheduled_for: Optional[datetime] = Field(
        default=None,
        description="Scheduled publication time (UTC)"
    )

    dry_run: bool = Field(
        default=False,
        description="Generate preview only, don't publish"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping"""
        if not v.strip():
            raise ValueError('Title cannot be empty or only whitespace')
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content meets minimum quality standards"""
        if not v.strip():
            raise ValueError('Content cannot be empty or only whitespace')

        # Check for minimum word count (approximately 10 words)
        word_count = len(v.split())
        if word_count < 3:
            raise ValueError('Content must contain at least 3 words')

        return v.strip()

    @field_validator('scheduled_for')
    @classmethod
    def validate_schedule(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled time is in the future"""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            # Allow scheduling up to 1 year in advance
            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError('Scheduled time must be in the future')

            max_future = now.replace(year=now.year + 1)
            if v > max_future:
                raise ValueError('Cannot schedule more than 1 year in advance')

        return v

    @model_validator(mode='after')
    def validate_content_flags(self) -> 'ContentBaseStrict':
        """Cross-field validation for content flags"""
        # If featured, must be published or scheduled
        if self.featured and not self.published and self.scheduled_for is None:
            raise ValueError('Featured content must be published or scheduled')

        # If scheduled, should be published
        if self.scheduled_for is not None and not self.published:
            raise ValueError('Scheduled content must have published=true')

        # Dry run content shouldn't be featured
        if self.dry_run and self.featured:
            raise ValueError('Dry run content cannot be featured')

        return self


class UpdateContentStrict(ContentBaseStrict):
    """
    Update content schema - Weekly product updates, progress reports
    Maps to editor guide Update content type
    """
    type: Literal[ContentType.UPDATE] = ContentType.UPDATE

    tags: List[Annotated[str, Field(max_length=50)]] = Field(
        default_factory=list,
        max_length=10,
        description="Content tags (max 10 tags, 50 chars each)"
    )

    excerpt: Optional[Annotated[str, Field(max_length=300)]] = Field(
        default=None,
        description="Brief excerpt for listings (max 300 chars)"
    )

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags"""
        cleaned_tags = []
        for tag in v:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in cleaned_tags:
                cleaned_tags.append(clean_tag)
        return cleaned_tags[:10]  # Limit to 10 tags


class BlogContentStrict(ContentBaseStrict):
    """
    Blog content schema - Educational content, thought leadership
    Maps to editor guide Blog content type
    """
    type: Literal[ContentType.BLOG] = ContentType.BLOG

    category: Annotated[str, Field(
        min_length=1,
        max_length=100,
        description="Blog category"
    )]

    tags: List[Annotated[str, Field(max_length=50)]] = Field(
        default_factory=list,
        max_length=15,
        description="SEO tags (max 15 tags, 50 chars each)"
    )

    reading_time: Optional[Annotated[int, Field(ge=1, le=120)]] = Field(
        default=None,
        description="Estimated reading time in minutes (1-120)"
    )

    seo_description: Optional[Annotated[str, Field(
        min_length=50,
        max_length=160
    )]] = Field(
        default=None,
        description="SEO meta description (50-160 characters)"
    )

    excerpt: Optional[Annotated[str, Field(max_length=500)]] = Field(
        default=None,
        description="Article excerpt for listings (max 500 chars)"
    )

    target_keywords: List[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list,
        max_length=5,
        description="Primary SEO keywords (max 5)"
    )

    @field_validator('reading_time', mode='before')
    @classmethod
    def calculate_reading_time(cls, v: Optional[int], values) -> Optional[int]:
        """Auto-calculate reading time if not provided"""
        if v is None and hasattr(values, 'data') and 'content' in values.data:
            # Approximate 200 words per minute reading speed
            word_count = len(values.data['content'].split())
            return max(1, word_count // 200)
        return v

    @model_validator(mode='after')
    def calculate_reading_time_post(self) -> 'BlogContentStrict':
        """Post-validation reading time calculation"""
        if self.reading_time is None:
            word_count = len(self.content.split())
            object.__setattr__(self, 'reading_time', max(1, word_count // 200))
        return self

    @field_validator('seo_description')
    @classmethod
    def validate_seo_description(cls, v: Optional[str]) -> Optional[str]:
        """Ensure SEO description meets best practices"""
        if v is not None:
            v = v.strip()
            if len(v) < 50:
                raise ValueError('SEO description should be at least 50 characters')
            if len(v) > 160:
                raise ValueError('SEO description should not exceed 160 characters')
        return v


class AnnouncementContentStrict(ContentBaseStrict):
    """
    Announcement content schema - Major news, product launches, events
    Maps to editor guide Announcement content type
    """
    type: Literal[ContentType.ANNOUNCEMENT] = ContentType.ANNOUNCEMENT

    urgency: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Announcement urgency level"
    )

    expires_at: Optional[datetime] = Field(
        default=None,
        description="When announcement becomes outdated"
    )

    call_to_action: Optional[Annotated[str, Field(max_length=200)]] = Field(
        default=None,
        description="Primary call-to-action text"
    )

    media_contact: Optional[Annotated[str, Field(max_length=200)]] = Field(
        default=None,
        description="Media contact information"
    )

    press_release: bool = Field(
        default=False,
        description="Whether this is a formal press release"
    )

    @field_validator('expires_at')
    @classmethod
    def validate_expiration(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure expiration is reasonable"""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError('Expiration time must be in the future')

            # Announcements shouldn't expire more than 1 year out
            max_future = now.replace(year=now.year + 1)
            if v > max_future:
                raise ValueError('Expiration cannot be more than 1 year from now')

        return v

    @model_validator(mode='after')
    def validate_announcement_flags(self) -> 'AnnouncementContentStrict':
        """Additional validation for announcements"""
        # Critical/high urgency announcements should be featured
        if self.urgency in ["critical", "high"] and not self.featured:
            object.__setattr__(self, 'featured', True)

        # Critical announcements should have higher priority
        if self.urgency == "critical":
            object.__setattr__(self, 'priority', ContentPriority.URGENT)
        elif self.urgency == "high":
            object.__setattr__(self, 'priority', ContentPriority.HIGH)

        return self


class SessionContentStrict(ContentBaseStrict):
    """
    Session summary content schema - Breathing session reports and analytics
    Sprint 3: Halcytone Live Support for session summaries
    """
    type: Literal[ContentType.SESSION] = ContentType.SESSION

    session_id: Annotated[str, Field(
        min_length=1,
        max_length=100,
        description="Unique session identifier"
    )]

    session_duration: Annotated[int, Field(
        gt=0,
        le=7200,  # Max 2 hours
        description="Session duration in seconds"
    )]

    participant_count: Annotated[int, Field(
        ge=1,
        le=1000,
        description="Number of participants in the session"
    )]

    breathing_techniques: List[Annotated[str, Field(
        min_length=1,
        max_length=100
    )]] = Field(
        min_length=1,
        max_length=10,
        description="Breathing techniques used in session"
    )

    average_hrv_improvement: Optional[Annotated[float, Field(
        ge=-100.0,
        le=200.0
    )]] = Field(
        default=None,
        description="Average HRV improvement percentage"
    )

    key_achievements: List[Annotated[str, Field(
        min_length=1,
        max_length=500
    )]] = Field(
        default_factory=list,
        max_length=10,
        description="Notable achievements from the session"
    )

    session_type: Literal["live", "guided", "practice", "workshop"] = Field(
        default="guided",
        description="Type of breathing session"
    )

    instructor_name: Optional[Annotated[str, Field(
        min_length=1,
        max_length=100
    )]] = Field(
        default=None,
        description="Name of session instructor"
    )

    session_date: datetime = Field(
        description="When the session occurred"
    )

    metrics_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional session metrics and statistics"
    )

    participant_feedback: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Aggregated participant feedback"
    )

    @field_validator('session_date')
    @classmethod
    def validate_session_date(cls, v: datetime) -> datetime:
        """Ensure session date has timezone and is not too far in future"""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if v > now.replace(hour=23, minute=59, second=59):
            raise ValueError('Session date cannot be in the future')

        # Sessions older than 30 days should not be processed
        thirty_days_ago = now - timedelta(days=30)
        if v < thirty_days_ago:
            raise ValueError('Session is too old (>30 days) for summary generation')

        return v

    @field_validator('breathing_techniques')
    @classmethod
    def validate_techniques(cls, v: List[str]) -> List[str]:
        """Validate breathing techniques"""
        valid_techniques = {
            "Box Breathing", "4-7-8 Breathing", "Coherent Breathing",
            "Belly Breathing", "Alternate Nostril", "Breath of Fire",
            "Lions Breath", "Humming Bee", "Cooling Breath", "Custom"
        }

        # Allow known techniques or custom ones
        for technique in v:
            if technique not in valid_techniques and not technique.startswith("Custom:"):
                # Add as custom technique
                v[v.index(technique)] = f"Custom: {technique}"

        return v

    @model_validator(mode='after')
    def validate_session_data(self) -> 'SessionContentStrict':
        """Additional validation for session data"""
        # Live sessions should have an instructor
        if self.session_type == "live" and not self.instructor_name:
            raise ValueError('Live sessions must have an instructor name')

        # Workshop sessions should have higher participant counts
        if self.session_type == "workshop" and self.participant_count < 5:
            raise ValueError('Workshop sessions should have at least 5 participants')

        # Calculate session quality based on metrics
        if self.average_hrv_improvement is not None:
            quality_score = 0.0
            if self.average_hrv_improvement > 10:
                quality_score = 5.0
            elif self.average_hrv_improvement > 5:
                quality_score = 4.0
            elif self.average_hrv_improvement > 0:
                quality_score = 3.0

            if not self.metrics_summary:
                object.__setattr__(self, 'metrics_summary', {})
            self.metrics_summary['quality_score'] = quality_score

        # Set appropriate priority for session summaries
        if self.session_type in ["live", "workshop"]:
            object.__setattr__(self, 'priority', ContentPriority.HIGH)
        else:
            object.__setattr__(self, 'priority', ContentPriority.NORMAL)

        # Session summaries should be featured if they have exceptional results
        if self.average_hrv_improvement and self.average_hrv_improvement > 15:
            object.__setattr__(self, 'featured', True)

        return self


class ContentValidationResult(BaseModel):
    """Result of content validation"""
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(description="Whether content passed validation")
    content_type: ContentType = Field(description="Detected content type")
    issues: List[str] = Field(
        default_factory=list,
        description="List of validation issues"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    enhanced_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from validation"
    )


class SocialPostStrict(BaseModel):
    """Strict social media post schema"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    platform: SocialPlatform = Field(description="Target social platform")
    content: Annotated[str, Field(min_length=1)] = Field(
        description="Post content"
    )
    hashtags: List[Annotated[str, Field(pattern=r'^#[a-zA-Z0-9_]+$')]] = Field(
        default_factory=list,
        max_length=10,
        description="Hashtags (max 10, must start with #)"
    )
    media_urls: List[Annotated[str, Field(pattern=r'^https?://')]] = Field(
        default_factory=list,
        max_length=4,
        description="Media URLs (max 4, must be valid URLs)"
    )
    scheduled_for: Optional[datetime] = Field(
        default=None,
        description="Scheduled post time"
    )

    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: str, info) -> str:
        """Validate content length by platform"""
        platform = info.data.get('platform')

        if platform == SocialPlatform.TWITTER and len(v) > 280:
            raise ValueError('Twitter posts cannot exceed 280 characters')
        elif platform == SocialPlatform.INSTAGRAM and len(v) > 2200:
            raise ValueError('Instagram posts cannot exceed 2200 characters')
        elif platform in [SocialPlatform.LINKEDIN, SocialPlatform.FACEBOOK] and len(v) > 3000:
            raise ValueError(f'{platform} posts cannot exceed 3000 characters')

        return v

    @field_validator('hashtags')
    @classmethod
    def validate_hashtag_limits(cls, v: List[str], info) -> List[str]:
        """Platform-specific hashtag limits"""
        platform = info.data.get('platform')

        if platform == SocialPlatform.TWITTER and len(v) > 2:
            raise ValueError('Twitter posts should use max 2 hashtags')
        elif platform == SocialPlatform.INSTAGRAM and len(v) > 30:
            raise ValueError('Instagram posts cannot exceed 30 hashtags')
        elif platform in [SocialPlatform.LINKEDIN, SocialPlatform.FACEBOOK] and len(v) > 5:
            raise ValueError(f'{platform} posts should use max 5 hashtags')

        return v


class NewsletterContentStrict(BaseModel):
    """Strict newsletter content schema"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    subject: Annotated[str, Field(
        min_length=10,
        max_length=100,
        description="Email subject line (10-100 characters)"
    )]

    html: str = Field(description="HTML email content")
    text: str = Field(description="Plain text email content")

    preview_text: Optional[Annotated[str, Field(max_length=150)]] = Field(
        default=None,
        description="Email preview text (max 150 chars)"
    )

    template_style: TemplateStyle = Field(
        default=TemplateStyle.MODERN,
        description="Email template style"
    )

    recipient_count: Optional[Annotated[int, Field(ge=0)]] = Field(
        default=None,
        description="Expected recipient count"
    )

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Ensure subject line follows best practices"""
        # Avoid spam trigger words
        spam_words = ['free', 'urgent', '!!!', 'click now', 'limited time']
        lower_subject = v.lower()

        for spam_word in spam_words:
            if spam_word in lower_subject:
                raise ValueError(f'Subject line should avoid spam trigger word: "{spam_word}"')

        return v


class WebUpdateContentStrict(BaseModel):
    """Strict web update content schema"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    title: Annotated[str, Field(
        min_length=10,
        max_length=100,
        description="Web page title (10-100 characters for SEO)"
    )]

    content: Annotated[str, Field(min_length=50)] = Field(
        description="Main content (minimum 50 characters)"
    )

    excerpt: Annotated[str, Field(
        min_length=20,
        max_length=300
    )] = Field(description="Content excerpt (20-300 characters)")

    slug: Optional[Annotated[str, Field(
        pattern=r'^[a-z0-9-]+$',
        max_length=100
    )]] = Field(
        default=None,
        description="URL slug (lowercase, hyphens only)"
    )

    tags: List[Annotated[str, Field(max_length=50)]] = Field(
        default_factory=list,
        max_length=20,
        description="Content tags (max 20)"
    )

    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication timestamp"
    )

    seo_title: Optional[Annotated[str, Field(max_length=60)]] = Field(
        default=None,
        description="SEO optimized title (max 60 chars)"
    )

    seo_description: Optional[Annotated[str, Field(
        min_length=120,
        max_length=160
    )]] = Field(
        default=None,
        description="SEO meta description (120-160 chars)"
    )

    @model_validator(mode='after')
    def generate_slug_post(self) -> 'WebUpdateContentStrict':
        """Auto-generate slug from title if not provided"""
        if self.slug is None:
            # Convert to lowercase, replace spaces and special chars with hyphens
            slug = re.sub(r'[^a-z0-9]+', '-', self.title.lower()).strip('-')
            object.__setattr__(self, 'slug', slug[:100])  # Limit length
        return self


# Union type for all content types
ContentUnion = Union[UpdateContentStrict, BlogContentStrict, AnnouncementContentStrict, SessionContentStrict]


class ContentRequestStrict(BaseModel):
    """Strict content generation request"""
    model_config = ConfigDict(extra="forbid")

    content: ContentUnion = Field(description="Content to validate and publish")
    validate_before_publish: bool = Field(
        default=True,
        description="Validate content structure before publishing"
    )
    override_validation: bool = Field(
        default=False,
        description="Override validation failures (use with caution)"
    )


class ContentResponseStrict(BaseModel):
    """Strict content generation response"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "validation_failed", "publish_failed"] = Field(
        description="Operation status"
    )
    content_id: Optional[str] = Field(
        default=None,
        description="Generated content ID"
    )
    validation_result: Optional[ContentValidationResult] = Field(
        default=None,
        description="Content validation results"
    )
    published_to: List[ChannelType] = Field(
        default_factory=list,
        description="Successfully published channels"
    )
    failed_channels: List[ChannelType] = Field(
        default_factory=list,
        description="Failed publishing channels"
    )
    newsletter: Optional[NewsletterContentStrict] = Field(
        default=None,
        description="Generated newsletter content"
    )
    web_update: Optional[WebUpdateContentStrict] = Field(
        default=None,
        description="Generated web content"
    )
    social_posts: List[SocialPostStrict] = Field(
        default_factory=list,
        description="Generated social media posts"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warning messages"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Generation timestamp"
    )