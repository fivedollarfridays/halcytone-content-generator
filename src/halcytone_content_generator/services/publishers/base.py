"""
Base Publisher interface for content distribution across channels
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from ...schemas.content import Content


class PublishStatus(Enum):
    """Status of a publish operation"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


class ValidationSeverity(Enum):
    """Severity level for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    code: Optional[str] = None


@dataclass
class PublishResult:
    """Result of a publish operation"""
    status: PublishStatus
    message: str
    metadata: Dict[str, Any]
    published_at: Optional[datetime] = None
    external_id: Optional[str] = None
    url: Optional[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.published_at is None and self.status == PublishStatus.SUCCESS:
            self.published_at = datetime.now()


@dataclass
class ValidationResult:
    """Result of content validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors or critical issues"""
        return any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
            for issue in self.issues
        )

    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings"""
        return any(
            issue.severity == ValidationSeverity.WARNING
            for issue in self.issues
        )


@dataclass
class PreviewResult:
    """Result of content preview generation"""
    preview_data: Dict[str, Any]
    formatted_content: str
    metadata: Dict[str, Any]
    estimated_reach: Optional[int] = None
    estimated_engagement: Optional[float] = None
    character_count: Optional[int] = None
    word_count: Optional[int] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.character_count is None and self.formatted_content:
            self.character_count = len(self.formatted_content)
        if self.word_count is None and self.formatted_content:
            self.word_count = len(self.formatted_content.split())


class Publisher(ABC):
    """
    Abstract base class for content publishers across different channels.

    All publishers must implement the three core methods:
    - validate: Check if content is valid for the channel
    - preview: Generate a preview of how content will appear
    - publish: Actually distribute the content
    """

    def __init__(self, channel_name: str, config: Dict[str, Any] = None):
        """
        Initialize the publisher

        Args:
            channel_name: Name of the channel (e.g., 'email', 'twitter', 'web')
            config: Channel-specific configuration
        """
        self.channel_name = channel_name
        self.config = config or {}
        self.dry_run = self.config.get('dry_run', False)

    @abstractmethod
    async def validate(self, content: Content) -> ValidationResult:
        """
        Validate content for this channel

        Args:
            content: Content to validate

        Returns:
            ValidationResult with any issues found
        """
        pass

    @abstractmethod
    async def preview(self, content: Content) -> PreviewResult:
        """
        Generate a preview of how content will appear on this channel

        Args:
            content: Content to preview

        Returns:
            PreviewResult with formatted preview
        """
        pass

    @abstractmethod
    async def publish(self, content: Content) -> PublishResult:
        """
        Publish content to this channel

        Args:
            content: Content to publish

        Returns:
            PublishResult indicating success/failure
        """
        pass

    def supports_scheduling(self) -> bool:
        """
        Check if this publisher supports scheduled publishing

        Returns:
            True if scheduling is supported
        """
        return False

    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get rate limits for this publisher

        Returns:
            Dictionary with rate limit information
        """
        return self.config.get('rate_limits', {})

    def get_content_limits(self) -> Dict[str, int]:
        """
        Get content size/length limits for this publisher

        Returns:
            Dictionary with content limit information
        """
        return self.config.get('content_limits', {})

    async def health_check(self) -> bool:
        """
        Check if the publisher service is healthy

        Returns:
            True if service is healthy
        """
        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(channel={self.channel_name})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel='{self.channel_name}', config={self.config})"


class MockPublisher(Publisher):
    """
    Mock publisher for testing and dry-run mode
    """

    def __init__(self, channel_name: str, config: Dict[str, Any] = None):
        super().__init__(channel_name, config)
        self.published_content = []
        self.validation_results = []
        self.preview_results = []

    async def validate(self, content: Content) -> ValidationResult:
        """Mock validation - always passes"""
        result = ValidationResult(
            is_valid=True,
            issues=[],
            metadata={"mock": True, "channel": self.channel_name}
        )
        self.validation_results.append(result)
        return result

    async def preview(self, content: Content) -> PreviewResult:
        """Mock preview generation"""
        result = PreviewResult(
            preview_data={"content": content.dict()},
            formatted_content=f"MOCK PREVIEW for {self.channel_name}: {content}",
            metadata={"mock": True, "channel": self.channel_name}
        )
        self.preview_results.append(result)
        return result

    async def publish(self, content: Content) -> PublishResult:
        """Mock publishing - always succeeds"""
        result = PublishResult(
            status=PublishStatus.SUCCESS,
            message=f"Mock published to {self.channel_name}",
            metadata={"mock": True, "channel": self.channel_name},
            external_id=f"mock-{self.channel_name}-{len(self.published_content)}"
        )
        self.published_content.append(content)
        return result

    def reset(self):
        """Reset mock state"""
        self.published_content.clear()
        self.validation_results.clear()
        self.preview_results.clear()