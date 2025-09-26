"""
Enhanced Platform API client with advanced features for content publishing and monitoring
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import json
import uuid
from enum import Enum

from ..config import Settings
from ..core.resilience import CircuitBreaker, RetryPolicy, TimeoutHandler
from ..schemas.content import WebPublishResult

logger = logging.getLogger(__name__)


class ContentStatus(Enum):
    """Content publication status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ContentType(Enum):
    """Types of content"""
    BLOG_POST = "blog_post"
    UPDATE = "update"
    ANNOUNCEMENT = "announcement"
    DOCUMENTATION = "documentation"
    LANDING_PAGE = "landing_page"


@dataclass
class ContentVersion:
    """Content version information"""
    version_id: str
    content_id: str
    version_number: int
    created_at: datetime
    created_by: str
    changes: Dict[str, Any]
    is_current: bool = False


@dataclass
class PublishedContent:
    """Published content metadata"""
    content_id: str
    title: str
    slug: str
    status: ContentStatus
    type: ContentType
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    author: str = "Content Generator"
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    seo_metadata: Dict[str, Any] = field(default_factory=dict)
    analytics: Dict[str, Any] = field(default_factory=dict)
    versions: List[ContentVersion] = field(default_factory=list)


@dataclass
class MonitoringEvent:
    """Monitoring event data"""
    event_id: str
    correlation_id: str
    timestamp: datetime
    service: str
    operation: str
    status: str
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class CorrelationContext:
    """Manages correlation IDs for distributed tracing"""

    def __init__(self):
        self._correlation_id = None

    def get_or_create(self, correlation_id: Optional[str] = None) -> str:
        """Get existing or create new correlation ID"""
        if correlation_id:
            self._correlation_id = correlation_id
        elif not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
        return self._correlation_id

    def get(self) -> Optional[str]:
        """Get current correlation ID"""
        return self._correlation_id

    def clear(self):
        """Clear correlation ID"""
        self._correlation_id = None


class EnhancedPlatformClient:
    """
    Enhanced Platform API client with versioning, monitoring, and content management
    """

    def __init__(self, settings: Settings):
        """
        Initialize enhanced Platform client

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.dry_run_mode = settings.DRY_RUN_MODE or settings.DRY_RUN
        self.use_mock_services = settings.USE_MOCK_SERVICES

        # Environment-based service selection
        self.environment = getattr(settings, 'ENVIRONMENT', 'development').lower()

        if self.use_mock_services or (self.dry_run_mode and self.environment != 'production'):
            self.base_url = "http://localhost:8002"  # Mock Platform service
            self.api_key = "mock-platform-api-key"
            logger.info(f"Platform Client: Using mock service (environment: {self.environment}, dry_run: {self.dry_run_mode})")
        else:
            self.base_url = settings.PLATFORM_BASE_URL
            self.api_key = settings.PLATFORM_API_KEY

            # Validate production configuration
            if self.environment == 'production':
                self._validate_production_config()

        logger.info(f"Platform Client initialized for {self.environment} environment: {self.base_url}")

        self.service_name = settings.SERVICE_NAME

        # Initialize circuit breaker
        self.breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            expected_exception=httpx.RequestError
        )

        # Initialize retry policy
        self.retry_policy = RetryPolicy(
            max_retries=settings.MAX_RETRIES,
            base_delay=1.0,
            max_delay=settings.RETRY_MAX_WAIT
        )

        # Correlation context
        self.correlation = CorrelationContext()

        # Cache for published content
        self.content_cache: Dict[str, PublishedContent] = {}

        # Monitoring hooks
        self.monitoring_enabled = settings.ENABLE_METRICS
        self.monitoring_events: List[MonitoringEvent] = []

    def _validate_production_config(self):
        """Validate configuration for production environment"""
        validation_errors = []

        # Validate base URL
        if not self.base_url:
            validation_errors.append("PLATFORM_BASE_URL is required in production")
        elif not self.base_url.startswith('https://'):
            validation_errors.append("PLATFORM_BASE_URL must use HTTPS in production")

        # Validate API key
        if not self.api_key:
            validation_errors.append("PLATFORM_API_KEY is required in production")
        elif len(self.api_key) < 16:
            validation_errors.append("PLATFORM_API_KEY should be at least 16 characters in production")
        elif any(pattern in self.api_key.lower() for pattern in ['dev', 'test', 'mock', 'example']):
            validation_errors.append("PLATFORM_API_KEY appears to be a development placeholder")

        # Validate endpoints are not localhost
        if 'localhost' in self.base_url or '127.0.0.1' in self.base_url:
            validation_errors.append("PLATFORM_BASE_URL cannot be localhost in production")

        # Log warnings/errors
        if validation_errors:
            for error in validation_errors:
                logger.error(f"Production Platform config validation: {error}")

            if any('required' in error or 'must use HTTPS' in error for error in validation_errors):
                raise ValueError(f"Critical Platform configuration errors: {validation_errors}")
            else:
                logger.warning("Platform configuration has non-critical issues in production")

        logger.info("Platform production configuration validation passed")

    async def publish_content(
        self,
        title: str,
        content: str,
        excerpt: str,
        content_type: ContentType = ContentType.UPDATE,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        seo_metadata: Optional[Dict] = None,
        scheduled_at: Optional[datetime] = None,
        correlation_id: Optional[str] = None
    ) -> PublishedContent:
        """
        Publish content with versioning and monitoring

        Args:
            title: Content title
            content: Content body (markdown/html)
            excerpt: Brief excerpt
            content_type: Type of content
            tags: Content tags
            categories: Content categories
            seo_metadata: SEO metadata
            scheduled_at: Optional scheduling time
            correlation_id: Correlation ID for tracing

        Returns:
            PublishedContent object
        """
        # Set correlation ID
        correlation_id = self.correlation.get_or_create(correlation_id)

        # Start monitoring
        start_time = datetime.now()
        event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            timestamp=start_time,
            service=self.service_name,
            operation="publish_content",
            status="started"
        )

        try:
            # Generate slug from title
            slug = self._generate_slug(title)

            if self.dry_run_mode and self.use_mock_services:
                # Use mock Platform service
                result = await self._publish_via_mock_service(
                    title, content, excerpt, content_type, tags, scheduled_at, correlation_id
                )
            else:
                # Use real Platform API
                # Prepare request payload
                payload = {
                    "title": title,
                    "content": content,
                    "excerpt": excerpt,
                    "slug": slug,
                    "type": content_type.value,
                    "status": ContentStatus.SCHEDULED.value if scheduled_at else ContentStatus.PUBLISHED.value,
                    "tags": tags or [],
                    "categories": categories or [],
                    "seo_metadata": seo_metadata or {},
                    "author": self.service_name,
                    "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
                    "published_at": datetime.now().isoformat() if not scheduled_at else None
                }

                # Make API call with circuit breaker
                result = await self._call_with_circuit_breaker(
                    "POST",
                    "/api/v1/content",
                    json=payload,
                    headers={
                        "X-Correlation-ID": correlation_id,
                        "X-Service-Name": self.service_name
                    }
                )

            # Create published content object
            published_content = PublishedContent(
                content_id=result.get("id"),
                title=title,
                slug=slug,
                status=ContentStatus.SCHEDULED if scheduled_at else ContentStatus.PUBLISHED,
                type=content_type,
                published_at=datetime.now() if not scheduled_at else None,
                scheduled_at=scheduled_at,
                tags=tags or [],
                categories=categories or [],
                seo_metadata=seo_metadata or {},
                analytics=result.get("analytics", {})
            )

            # Cache the content
            self.content_cache[published_content.content_id] = published_content

            # Complete monitoring
            event.status = "success"
            event.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            event.metadata = {"content_id": published_content.content_id}

            logger.info(f"Content published successfully: {published_content.content_id}")
            return published_content

        except Exception as e:
            # Record failure in monitoring
            event.status = "failed"
            event.error = str(e)
            event.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Failed to publish content: {e}")
            raise

        finally:
            # Record monitoring event
            if self.monitoring_enabled:
                await self._record_monitoring_event(event)

    async def update_content(
        self,
        content_id: str,
        updates: Dict[str, Any],
        create_version: bool = True,
        correlation_id: Optional[str] = None
    ) -> PublishedContent:
        """
        Update existing content with optional versioning

        Args:
            content_id: Content ID to update
            updates: Dictionary of updates
            create_version: Whether to create a new version
            correlation_id: Correlation ID for tracing

        Returns:
            Updated PublishedContent object
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        # Create version if requested
        if create_version:
            version = await self._create_content_version(content_id, updates, correlation_id)

        # Update content
        payload = {
            **updates,
            "updated_at": datetime.now().isoformat(),
            "updated_by": self.service_name
        }

        result = await self._call_with_circuit_breaker(
            "PATCH",
            f"/api/v1/content/{content_id}",
            json=payload,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        # Update cache
        if content_id in self.content_cache:
            for key, value in updates.items():
                setattr(self.content_cache[content_id], key, value)

        return await self.get_content(content_id, correlation_id)

    async def get_content(
        self,
        content_id: str,
        correlation_id: Optional[str] = None
    ) -> Optional[PublishedContent]:
        """
        Get published content by ID

        Args:
            content_id: Content ID
            correlation_id: Correlation ID for tracing

        Returns:
            PublishedContent or None
        """
        # Check cache first
        if content_id in self.content_cache:
            return self.content_cache[content_id]

        correlation_id = self.correlation.get_or_create(correlation_id)

        try:
            result = await self._call_with_circuit_breaker(
                "GET",
                f"/api/v1/content/{content_id}",
                headers={
                    "X-Correlation-ID": correlation_id,
                    "X-Service-Name": self.service_name
                }
            )

            if result:
                published_content = self._parse_content_response(result)
                self.content_cache[content_id] = published_content
                return published_content

        except Exception as e:
            logger.error(f"Failed to get content {content_id}: {e}")

        return None

    async def list_content(
        self,
        status: Optional[ContentStatus] = None,
        content_type: Optional[ContentType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        correlation_id: Optional[str] = None
    ) -> List[PublishedContent]:
        """
        List published content with filtering

        Args:
            status: Filter by status
            content_type: Filter by type
            tags: Filter by tags
            limit: Number of results
            offset: Pagination offset
            correlation_id: Correlation ID

        Returns:
            List of PublishedContent
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        params = {
            "limit": limit,
            "offset": offset
        }

        if status:
            params["status"] = status.value
        if content_type:
            params["type"] = content_type.value
        if tags:
            params["tags"] = ",".join(tags)

        result = await self._call_with_circuit_breaker(
            "GET",
            "/api/v1/content",
            params=params,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        content_list = []
        for item in result.get("items", []):
            content = self._parse_content_response(item)
            content_list.append(content)
            self.content_cache[content.content_id] = content

        return content_list

    async def schedule_content(
        self,
        content_id: str,
        scheduled_at: datetime,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Schedule content for future publication

        Args:
            content_id: Content ID
            scheduled_at: Scheduled publication time
            correlation_id: Correlation ID

        Returns:
            Success status
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        payload = {
            "scheduled_at": scheduled_at.isoformat(),
            "status": ContentStatus.SCHEDULED.value
        }

        await self._call_with_circuit_breaker(
            "POST",
            f"/api/v1/content/{content_id}/schedule",
            json=payload,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        # Update cache
        if content_id in self.content_cache:
            self.content_cache[content_id].scheduled_at = scheduled_at
            self.content_cache[content_id].status = ContentStatus.SCHEDULED

        return True

    async def archive_content(
        self,
        content_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Archive published content

        Args:
            content_id: Content ID
            correlation_id: Correlation ID

        Returns:
            Success status
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        await self._call_with_circuit_breaker(
            "POST",
            f"/api/v1/content/{content_id}/archive",
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        # Update cache
        if content_id in self.content_cache:
            self.content_cache[content_id].status = ContentStatus.ARCHIVED

        return True

    async def get_content_analytics(
        self,
        content_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for published content

        Args:
            content_id: Content ID
            start_date: Analytics start date
            end_date: Analytics end date
            correlation_id: Correlation ID

        Returns:
            Analytics data
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        result = await self._call_with_circuit_breaker(
            "GET",
            f"/api/v1/content/{content_id}/analytics",
            params=params,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        return result

    async def sync_content_batch(
        self,
        content_items: List[Dict[str, Any]],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronize batch of content items

        Args:
            content_items: List of content items to sync
            correlation_id: Correlation ID

        Returns:
            Sync results
        """
        correlation_id = self.correlation.get_or_create(correlation_id)

        payload = {
            "items": content_items,
            "source": self.service_name,
            "timestamp": datetime.now().isoformat()
        }

        result = await self._call_with_circuit_breaker(
            "POST",
            "/api/v1/content/sync",
            json=payload,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        return result

    async def _create_content_version(
        self,
        content_id: str,
        changes: Dict[str, Any],
        correlation_id: str
    ) -> ContentVersion:
        """
        Create a new content version

        Args:
            content_id: Content ID
            changes: Changes in this version
            correlation_id: Correlation ID

        Returns:
            ContentVersion object
        """
        # Get current version number
        current = await self.get_content(content_id, correlation_id)
        version_number = len(current.versions) + 1 if current and current.versions else 1

        payload = {
            "content_id": content_id,
            "version_number": version_number,
            "changes": changes,
            "created_by": self.service_name,
            "created_at": datetime.now().isoformat()
        }

        result = await self._call_with_circuit_breaker(
            "POST",
            f"/api/v1/content/{content_id}/versions",
            json=payload,
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Service-Name": self.service_name
            }
        )

        version = ContentVersion(
            version_id=result.get("version_id"),
            content_id=content_id,
            version_number=version_number,
            created_at=datetime.now(),
            created_by=self.service_name,
            changes=changes,
            is_current=True
        )

        # Update cache
        if content_id in self.content_cache:
            self.content_cache[content_id].versions.append(version)

        return version

    @CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    @RetryPolicy(max_retries=3, base_delay=2.0)
    async def _call_with_circuit_breaker(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make API call with circuit breaker protection

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        # Add default headers
        headers = kwargs.get("headers", {})
        headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": f"HalcytoneContentGenerator/{self.service_name}"
        })
        kwargs["headers"] = headers

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                timeout=30.0,
                **kwargs
            )

            response.raise_for_status()
            return response.json()

    async def _record_monitoring_event(self, event: MonitoringEvent):
        """
        Record monitoring event

        Args:
            event: Monitoring event to record
        """
        self.monitoring_events.append(event)

        # Send to monitoring service if configured
        if self.monitoring_enabled:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.base_url}/api/v1/monitoring/events",
                        json={
                            "event_id": event.event_id,
                            "correlation_id": event.correlation_id,
                            "timestamp": event.timestamp.isoformat(),
                            "service": event.service,
                            "operation": event.operation,
                            "status": event.status,
                            "duration_ms": event.duration_ms,
                            "metadata": event.metadata,
                            "error": event.error
                        },
                        headers={"X-API-Key": self.api_key},
                        timeout=5.0
                    )
            except Exception as e:
                logger.warning(f"Failed to send monitoring event: {e}")

    def _parse_content_response(self, data: Dict) -> PublishedContent:
        """
        Parse API response into PublishedContent object

        Args:
            data: API response data

        Returns:
            PublishedContent object
        """
        return PublishedContent(
            content_id=data.get("id"),
            title=data.get("title"),
            slug=data.get("slug"),
            status=ContentStatus(data.get("status", "draft")),
            type=ContentType(data.get("type", "update")),
            published_at=datetime.fromisoformat(data["published_at"])
            if data.get("published_at") else None,
            scheduled_at=datetime.fromisoformat(data["scheduled_at"])
            if data.get("scheduled_at") else None,
            author=data.get("author", self.service_name),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            seo_metadata=data.get("seo_metadata", {}),
            analytics=data.get("analytics", {})
        )

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    async def get_monitoring_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get monitoring summary for the service

        Args:
            start_time: Start time for summary
            end_time: End time for summary

        Returns:
            Monitoring summary
        """
        if not self.monitoring_events:
            return {"message": "No monitoring events recorded"}

        # Filter events by time if specified
        events = self.monitoring_events
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Calculate summary statistics
        total_events = len(events)
        successful = len([e for e in events if e.status == "success"])
        failed = len([e for e in events if e.status == "failed"])

        durations = [e.duration_ms for e in events if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_events": total_events,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_events * 100) if total_events else 0,
            "average_duration_ms": avg_duration,
            "correlation_ids": list(set(e.correlation_id for e in events))
        }

    async def _publish_via_mock_service(
        self, title: str, content: str, excerpt: str,
        content_type, tags: Optional[List[str]],
        scheduled_at: Optional[datetime], correlation_id: str
    ) -> Dict:
        """Publish content via mock Platform service for dry run testing"""

        try:
            # Prepare payload for mock API
            payload = {
                "title": title,
                "content": content,
                "content_type": content_type.value if content_type else "web_update",
                "metadata": {
                    "excerpt": excerpt,
                    "correlation_id": correlation_id
                },
                "tags": tags or [],
                "publish_immediately": not bool(scheduled_at),
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else None
            }

            logger.info(f"Publishing content via mock Platform service: {title}")

            # Send to mock service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/content/publish",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Correlation-ID": correlation_id
                    },
                    timeout=30.0
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"Mock Platform response: {result}")

                # Return normalized result
                return {
                    "id": result.get('content_id'),
                    "url": result.get('url'),
                    "status": result.get('status', 'published'),
                    "published_at": result.get('published_at'),
                    "analytics": {}
                }

        except Exception as e:
            logger.error(f"Mock Platform service error: {e}")
            # Return mock success for dry run resilience
            return {
                "id": f"mock-{correlation_id}",
                "url": f"https://halcytone.com/content/mock-{correlation_id}",
                "status": "published",
                "published_at": datetime.utcnow().isoformat(),
                "analytics": {}
            }

    def clear_cache(self):
        """Clear content cache"""
        self.content_cache.clear()
        logger.info("Content cache cleared")