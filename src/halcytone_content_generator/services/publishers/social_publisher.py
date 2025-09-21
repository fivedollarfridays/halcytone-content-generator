"""
Social Media Publisher implementation for various social platforms with automated posting
"""
import asyncio
import hashlib
import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import base64

from .base import Publisher, PublishResult, ValidationResult, PreviewResult, PublishStatus, ValidationIssue, ValidationSeverity
from ...schemas.content import Content, SocialPost
from ...config import get_settings

logger = logging.getLogger(__name__)


class PostStatus(Enum):
    """Status of a scheduled social media post"""
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class PlatformAPIStatus(Enum):
    """Status of platform API connection"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"


@dataclass
class PlatformCredentials:
    """Credentials for social platform APIs"""
    platform: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if credentials are expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if credentials are valid for posting"""
        return bool(self.access_token and not self.is_expired())


@dataclass
class ScheduledPost:
    """A scheduled social media post"""
    post_id: str
    content: str
    platform: str
    scheduled_for: datetime
    status: PostStatus = PostStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    posted_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)

    def can_retry(self) -> bool:
        """Check if post can be retried"""
        return self.retry_count < self.max_retries and self.status == PostStatus.FAILED


@dataclass
class PostingStats:
    """Statistics for social media posting"""
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    pending_posts: int = 0
    posts_today: int = 0
    posts_this_hour: int = 0
    last_post_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_posts == 0:
            return 0.0
        return self.successful_posts / self.total_posts

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.total_posts == 0:
            return 0.0
        return self.failed_posts / self.total_posts


@dataclass
class APIResponse:
    """Response from social media API"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None


class SocialPublisher(Publisher):
    """
    Publisher for social media content across multiple platforms with automated posting capabilities
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("social", config)
        self.settings = get_settings()

        # Initialize scheduling queue
        self.scheduled_posts: Dict[str, ScheduledPost] = {}
        self.posting_queue: asyncio.Queue = asyncio.Queue()
        self.posting_stats: Dict[str, PostingStats] = {}

        # Platform credentials
        self.credentials: Dict[str, PlatformCredentials] = {}
        self._initialize_credentials()

        # API endpoints
        self.api_endpoints = {
            'twitter': {
                'post': 'https://api.twitter.com/2/tweets',
                'upload': 'https://upload.twitter.com/1.1/media/upload.json',
                'verify': 'https://api.twitter.com/2/users/me'
            },
            'linkedin': {
                'post': 'https://api.linkedin.com/v2/ugcPosts',
                'upload': 'https://api.linkedin.com/v2/assets',
                'verify': 'https://api.linkedin.com/v2/me'
            }
        }

        # Rate limiting
        self.rate_limit_windows: Dict[str, List[datetime]] = {}

        # Background task for processing scheduled posts
        self._scheduler_task = None
        self._start_scheduler()

        # Platform-specific limits
        self.platform_limits = {
            'twitter': {
                'max_length': 280,
                'max_hashtags': 10,
                'max_media': 4
            },
            'linkedin': {
                'max_length': 3000,
                'max_hashtags': 30,
                'max_media': 1
            },
            'facebook': {
                'max_length': 63206,
                'max_hashtags': 30,
                'max_media': 10
            },
            'instagram': {
                'max_length': 2200,
                'max_hashtags': 30,
                'max_media': 10
            }
        }

        # Rate limits per platform
        self.rate_limits = {
            'twitter': {
                'posts_per_hour': 15,
                'posts_per_day': 300
            },
            'linkedin': {
                'posts_per_hour': 5,
                'posts_per_day': 25
            },
            'facebook': {
                'posts_per_hour': 10,
                'posts_per_day': 100
            },
            'instagram': {
                'posts_per_hour': 5,
                'posts_per_day': 25
            }
        }

    def _initialize_credentials(self):
        """Initialize platform credentials from settings"""
        try:
            # Twitter credentials
            if hasattr(self.settings, 'TWITTER_API_KEY') and self.settings.TWITTER_API_KEY:
                self.credentials['twitter'] = PlatformCredentials(
                    platform='twitter',
                    api_key=self.settings.TWITTER_API_KEY,
                    api_secret=getattr(self.settings, 'TWITTER_API_SECRET', None),
                    access_token=getattr(self.settings, 'TWITTER_ACCESS_TOKEN', None),
                    user_id=getattr(self.settings, 'TWITTER_USER_ID', None)
                )

            # LinkedIn credentials
            if hasattr(self.settings, 'LINKEDIN_CLIENT_ID') and self.settings.LINKEDIN_CLIENT_ID:
                self.credentials['linkedin'] = PlatformCredentials(
                    platform='linkedin',
                    api_key=self.settings.LINKEDIN_CLIENT_ID,
                    api_secret=getattr(self.settings, 'LINKEDIN_CLIENT_SECRET', None),
                    access_token=getattr(self.settings, 'LINKEDIN_ACCESS_TOKEN', None),
                    user_id=getattr(self.settings, 'LINKEDIN_USER_ID', None)
                )

        except Exception as e:
            logger.warning(f"Failed to initialize social credentials: {e}")

    def _start_scheduler(self):
        """Start the background scheduler task"""
        try:
            if self._scheduler_task is None or self._scheduler_task.done():
                self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        except RuntimeError:
            # No event loop running (e.g., in tests)
            logger.debug("Cannot start scheduler: no event loop running")
            self._scheduler_task = None

    async def _scheduler_loop(self):
        """Background loop to process scheduled posts"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._process_scheduled_posts()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    async def _process_scheduled_posts(self):
        """Process posts that are ready to be published"""
        now = datetime.utcnow()
        ready_posts = []

        for post_id, post in self.scheduled_posts.items():
            if (post.status == PostStatus.SCHEDULED and
                post.scheduled_for <= now):
                ready_posts.append(post)

        for post in ready_posts:
            await self._execute_scheduled_post(post)

    async def _execute_scheduled_post(self, post: ScheduledPost):
        """Execute a scheduled post"""
        try:
            post.status = PostStatus.POSTING
            logger.info(f"Executing scheduled post {post.post_id} on {post.platform}")

            # Check rate limits
            if not await self._check_rate_limits(post.platform):
                logger.warning(f"Rate limit exceeded for {post.platform}, postponing post {post.post_id}")
                post.scheduled_for = datetime.utcnow() + timedelta(minutes=15)
                post.status = PostStatus.SCHEDULED
                return

            # Execute the post
            result = await self._post_to_platform(post)

            if result.success:
                post.status = PostStatus.POSTED
                post.posted_at = datetime.utcnow()
                post.external_id = result.data.get('id') if result.data else None
                post.external_url = self._generate_post_url(post.platform, post.external_id)

                # Update stats
                stats = self._get_or_create_stats(post.platform)
                stats.successful_posts += 1
                stats.last_post_time = post.posted_at

                logger.info(f"Successfully posted {post.post_id} to {post.platform}")
            else:
                post.status = PostStatus.FAILED
                post.error_message = result.error
                post.retry_count += 1

                if post.can_retry():
                    post.status = PostStatus.RETRYING
                    post.scheduled_for = datetime.utcnow() + timedelta(minutes=5 * post.retry_count)
                    logger.warning(f"Post {post.post_id} failed, scheduling retry {post.retry_count}")
                else:
                    logger.error(f"Post {post.post_id} failed permanently: {result.error}")

                # Update stats
                stats = self._get_or_create_stats(post.platform)
                stats.failed_posts += 1

        except Exception as e:
            logger.error(f"Error executing scheduled post {post.post_id}: {e}")
            post.status = PostStatus.FAILED
            post.error_message = str(e)

    async def _post_to_platform(self, post: ScheduledPost) -> APIResponse:
        """Post content to specific platform"""
        platform = post.platform.lower()

        if platform == 'twitter':
            return await self._post_to_twitter(post)
        elif platform == 'linkedin':
            return await self._post_to_linkedin(post)
        else:
            return APIResponse(
                success=False,
                status_code=400,
                error=f"Unsupported platform: {platform}"
            )

    async def _post_to_twitter(self, post: ScheduledPost) -> APIResponse:
        """Post to Twitter using API v2"""
        try:
            creds = self.credentials.get('twitter')
            if not creds or not creds.is_valid():
                return APIResponse(
                    success=False,
                    status_code=401,
                    error="Twitter credentials not configured or expired"
                )

            headers = {
                'Authorization': f'Bearer {creds.access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'text': post.content
            }

            # Add media if present
            if post.media_urls:
                media_ids = await self._upload_twitter_media(post.media_urls, creds)
                if media_ids:
                    payload['media'] = {'media_ids': media_ids}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoints['twitter']['post'],
                    headers=headers,
                    json=payload
                ) as response:
                    response_data = await response.json()

                    if response.status == 201:
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=response_data.get('data', {}),
                            rate_limit_remaining=response.headers.get('x-rate-limit-remaining'),
                            rate_limit_reset=self._parse_rate_limit_reset(response.headers.get('x-rate-limit-reset'))
                        )
                    else:
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            error=response_data.get('detail', 'Unknown Twitter API error')
                        )

        except Exception as e:
            logger.error(f"Twitter posting error: {e}")
            return APIResponse(success=False, status_code=500, error=str(e))

    async def _post_to_linkedin(self, post: ScheduledPost) -> APIResponse:
        """Post to LinkedIn using API"""
        try:
            creds = self.credentials.get('linkedin')
            if not creds or not creds.is_valid():
                return APIResponse(
                    success=False,
                    status_code=401,
                    error="LinkedIn credentials not configured or expired"
                )

            headers = {
                'Authorization': f'Bearer {creds.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            payload = {
                'author': f'urn:li:person:{creds.user_id}',
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': post.content
                        },
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }

            # Add media if present
            if post.media_urls:
                media_assets = await self._upload_linkedin_media(post.media_urls, creds)
                if media_assets:
                    payload['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'] = 'IMAGE'
                    payload['specificContent']['com.linkedin.ugc.ShareContent']['media'] = media_assets

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoints['linkedin']['post'],
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        response_data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data={'id': response_data.get('id', '')},
                            rate_limit_remaining=response.headers.get('x-ratelimit-remaining'),
                            rate_limit_reset=self._parse_rate_limit_reset(response.headers.get('x-ratelimit-reset'))
                        )
                    else:
                        error_data = await response.json()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            error=error_data.get('message', 'Unknown LinkedIn API error')
                        )

        except Exception as e:
            logger.error(f"LinkedIn posting error: {e}")
            return APIResponse(success=False, status_code=500, error=str(e))

    async def _upload_twitter_media(self, media_urls: List[str], creds: PlatformCredentials) -> List[str]:
        """Upload media to Twitter and return media IDs"""
        media_ids = []
        # Implementation for media upload would go here
        # For now, return empty list as media upload is complex
        return media_ids

    async def _upload_linkedin_media(self, media_urls: List[str], creds: PlatformCredentials) -> List[Dict[str, Any]]:
        """Upload media to LinkedIn and return asset references"""
        media_assets = []
        # Implementation for media upload would go here
        # For now, return empty list as media upload is complex
        return media_assets

    async def _check_rate_limits(self, platform: str) -> bool:
        """Check if we can post to platform without exceeding rate limits"""
        now = datetime.utcnow()

        if platform not in self.rate_limit_windows:
            self.rate_limit_windows[platform] = []

        # Clean old timestamps
        hour_ago = now - timedelta(hours=1)
        self.rate_limit_windows[platform] = [
            timestamp for timestamp in self.rate_limit_windows[platform]
            if timestamp > hour_ago
        ]

        # Check hourly limit
        hourly_limit = self.rate_limits[platform]['posts_per_hour']
        if len(self.rate_limit_windows[platform]) >= hourly_limit:
            return False

        return True

    def _parse_rate_limit_reset(self, reset_header: Optional[str]) -> Optional[datetime]:
        """Parse rate limit reset timestamp"""
        if not reset_header:
            return None
        try:
            timestamp = int(reset_header)
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None

    def _generate_post_url(self, platform: str, external_id: Optional[str]) -> Optional[str]:
        """Generate URL for posted content"""
        if not external_id:
            return None

        creds = self.credentials.get(platform)
        if not creds or not creds.username:
            return None

        if platform == 'twitter':
            return f"https://twitter.com/{creds.username}/status/{external_id}"
        elif platform == 'linkedin':
            return f"https://www.linkedin.com/feed/update/{external_id}"

        return None

    def _get_or_create_stats(self, platform: str) -> PostingStats:
        """Get or create posting statistics for platform"""
        if platform not in self.posting_stats:
            self.posting_stats[platform] = PostingStats()
        return self.posting_stats[platform]

    async def schedule_post(
        self,
        content: str,
        platform: str,
        scheduled_for: datetime,
        hashtags: List[str] = None,
        media_urls: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Schedule a post for future publishing

        Args:
            content: Post content
            platform: Target platform
            scheduled_for: When to publish
            hashtags: List of hashtags
            media_urls: List of media URLs
            metadata: Additional metadata

        Returns:
            Post ID for tracking
        """
        post_id = self._generate_post_id(content, platform)

        scheduled_post = ScheduledPost(
            post_id=post_id,
            content=content,
            platform=platform.lower(),
            scheduled_for=scheduled_for,
            status=PostStatus.SCHEDULED,
            hashtags=hashtags or [],
            media_urls=media_urls or [],
            metadata=metadata or {}
        )

        self.scheduled_posts[post_id] = scheduled_post

        # Update stats
        stats = self._get_or_create_stats(platform)
        stats.pending_posts += 1

        logger.info(f"Scheduled post {post_id} for {platform} at {scheduled_for}")
        return post_id

    def _generate_post_id(self, content: str, platform: str) -> str:
        """Generate unique post ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        content_hash = hashlib.md5(f"{content}{platform}".encode()).hexdigest()[:8]
        return f"post_{platform}_{timestamp}_{content_hash}"

    async def cancel_scheduled_post(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        if post_id not in self.scheduled_posts:
            return False

        post = self.scheduled_posts[post_id]
        if post.status in [PostStatus.POSTING, PostStatus.POSTED]:
            return False

        post.status = PostStatus.CANCELLED

        # Update stats
        stats = self._get_or_create_stats(post.platform)
        stats.pending_posts = max(0, stats.pending_posts - 1)

        logger.info(f"Cancelled scheduled post {post_id}")
        return True

    async def get_post_status(self, post_id: str) -> Optional[ScheduledPost]:
        """Get status of a scheduled post"""
        return self.scheduled_posts.get(post_id)

    async def get_scheduled_posts(
        self,
        platform: Optional[str] = None,
        status: Optional[PostStatus] = None,
        limit: Optional[int] = None
    ) -> List[ScheduledPost]:
        """Get list of scheduled posts with optional filtering"""
        posts = list(self.scheduled_posts.values())

        if platform:
            posts = [p for p in posts if p.platform == platform.lower()]

        if status:
            posts = [p for p in posts if p.status == status]

        # Sort by scheduled time
        posts.sort(key=lambda p: p.scheduled_for)

        if limit:
            posts = posts[:limit]

        return posts

    async def get_posting_stats(self, platform: Optional[str] = None) -> Dict[str, PostingStats]:
        """Get posting statistics"""
        if platform:
            platform = platform.lower()
            return {platform: self.posting_stats.get(platform, PostingStats())}

        return dict(self.posting_stats)

    async def verify_platform_connection(self, platform: str) -> PlatformAPIStatus:
        """Verify connection to platform API"""
        platform = platform.lower()
        creds = self.credentials.get(platform)

        if not creds:
            return PlatformAPIStatus.DISCONNECTED

        if not creds.is_valid():
            return PlatformAPIStatus.UNAUTHORIZED

        try:
            # Test API connection
            if platform == 'twitter':
                result = await self._verify_twitter_connection(creds)
            elif platform == 'linkedin':
                result = await self._verify_linkedin_connection(creds)
            else:
                return PlatformAPIStatus.ERROR

            return PlatformAPIStatus.CONNECTED if result else PlatformAPIStatus.ERROR

        except Exception as e:
            logger.error(f"Platform verification error for {platform}: {e}")
            return PlatformAPIStatus.ERROR

    async def _verify_twitter_connection(self, creds: PlatformCredentials) -> bool:
        """Verify Twitter API connection"""
        try:
            headers = {'Authorization': f'Bearer {creds.access_token}'}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_endpoints['twitter']['verify'],
                    headers=headers
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _verify_linkedin_connection(self, creds: PlatformCredentials) -> bool:
        """Verify LinkedIn API connection"""
        try:
            headers = {
                'Authorization': f'Bearer {creds.access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_endpoints['linkedin']['verify'],
                    headers=headers
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def validate(self, content: Content) -> ValidationResult:
        """
        Validate social media content for platform requirements
        """
        issues = []

        try:
            # Ensure content is social type
            if content.content_type != "social":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content type must be 'social', got '{content.content_type}'",
                    field="content_type"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            social_post = content.to_social_post()

            # Validate platform
            if not social_post.platform:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Platform is required",
                    field="platform"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            platform = social_post.platform.lower()
            if platform not in self.platform_limits:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Unsupported platform: {platform}",
                    field="platform"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            platform_config = self.platform_limits[platform]

            # Validate content length
            if not social_post.content:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Content is required",
                    field="content"
                ))
            elif len(social_post.content) > platform_config['max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too long for {platform} ({len(social_post.content)} > {platform_config['max_length']} chars)",
                    field="content"
                ))

            # Validate hashtags
            if len(social_post.hashtags) > platform_config['max_hashtags']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many hashtags for {platform} ({len(social_post.hashtags)} > {platform_config['max_hashtags']})",
                    field="hashtags"
                ))

            # Validate hashtag format
            for hashtag in social_post.hashtags:
                if not hashtag.startswith('#'):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Hashtag should start with #: {hashtag}",
                        field="hashtags"
                    ))
                elif ' ' in hashtag:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Hashtag should not contain spaces: {hashtag}",
                        field="hashtags"
                    ))

            # Validate media URLs
            if len(social_post.media_urls) > platform_config['max_media']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many media files for {platform} ({len(social_post.media_urls)} > {platform_config['max_media']})",
                    field="media_urls"
                ))

            # Platform-specific validation
            if platform == 'twitter':
                self._validate_twitter_specific(social_post, issues)
            elif platform == 'linkedin':
                self._validate_linkedin_specific(social_post, issues)
            elif platform == 'facebook':
                self._validate_facebook_specific(social_post, issues)
            elif platform == 'instagram':
                self._validate_instagram_specific(social_post, issues)

        except Exception as e:
            logger.error(f"Social validation error: {e}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation failed: {str(e)}",
                code="VALIDATION_ERROR"
            ))

        is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for issue in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            metadata={
                "channel": self.channel_name,
                "platform": social_post.platform if 'social_post' in locals() else None,
                "platform_limits": self.platform_limits.get(platform, {}) if 'platform' in locals() else {},
                "validation_timestamp": datetime.now().isoformat()
            }
        )

    async def preview(self, content: Content) -> PreviewResult:
        """
        Generate social media preview
        """
        try:
            social_post = content.to_social_post()
            platform = social_post.platform.lower()

            # Format content for platform
            formatted_content = self._format_for_platform(social_post)

            # Estimate metrics based on platform
            engagement_rates = {
                'twitter': 0.05,
                'linkedin': 0.03,
                'facebook': 0.08,
                'instagram': 0.12
            }

            estimated_followers = self.config.get(f'{platform}_followers', 1000)
            estimated_reach = int(estimated_followers * 0.1)  # 10% reach
            estimated_engagement = engagement_rates.get(platform, 0.05)

            preview_data = {
                "platform": social_post.platform,
                "formatted_content": formatted_content,
                "hashtags": social_post.hashtags,
                "media_count": len(social_post.media_urls),
                "character_count": len(formatted_content),
                "estimated_reach": estimated_reach,
                "estimated_likes": int(estimated_reach * estimated_engagement),
                "estimated_shares": int(estimated_reach * estimated_engagement * 0.1),
                "optimal_posting_time": self._get_optimal_posting_time(platform),
                "platform_tips": self._get_platform_tips(platform)
            }

            return PreviewResult(
                preview_data=preview_data,
                formatted_content=formatted_content,
                metadata={
                    "channel": self.channel_name,
                    "platform": platform,
                    "preview_mode": True,
                    "dry_run": self.dry_run
                },
                estimated_reach=estimated_reach,
                estimated_engagement=estimated_engagement,
                character_count=len(formatted_content),
                word_count=len(social_post.content.split())
            )

        except Exception as e:
            logger.error(f"Social preview error: {e}")
            return PreviewResult(
                preview_data={"error": str(e)},
                formatted_content=f"Preview failed: {str(e)}",
                metadata={"channel": self.channel_name, "error": True}
            )

    async def publish(self, content: Content) -> PublishResult:
        """
        Publish social media content with automated posting
        """
        try:
            social_post = content.to_social_post()
            platform = social_post.platform.lower()

            # Format content for platform
            formatted_content = self._format_for_platform(social_post)

            # Check if we have valid credentials for automated posting
            creds = self.credentials.get(platform)
            has_valid_creds = creds and creds.is_valid()

            # If scheduled, use the scheduling system
            if social_post.scheduled_for and social_post.scheduled_for > datetime.utcnow():
                if not has_valid_creds:
                    return PublishResult(
                        status=PublishStatus.FAILED,
                        message=f"Cannot schedule post for {platform} - no valid API credentials configured",
                        metadata={
                            "channel": self.channel_name,
                            "platform": platform,
                            "requires_credentials": True
                        },
                        errors=[f"No valid {platform} API credentials"]
                    )

                # Schedule the post
                post_id = await self.schedule_post(
                    content=formatted_content,
                    platform=platform,
                    scheduled_for=social_post.scheduled_for,
                    hashtags=social_post.hashtags,
                    media_urls=social_post.media_urls,
                    metadata={
                        "content_id": getattr(content, 'id', None),
                        "original_content": social_post.content
                    }
                )

                return PublishResult(
                    status=PublishStatus.PENDING,
                    message=f"Post scheduled for {platform} at {social_post.scheduled_for}",
                    metadata={
                        "channel": self.channel_name,
                        "platform": platform,
                        "post_id": post_id,
                        "scheduled_for": social_post.scheduled_for.isoformat(),
                        "automated_posting": True
                    },
                    external_id=post_id,
                    published_at=social_post.scheduled_for
                )

            # For immediate posting
            if has_valid_creds and not self.dry_run:
                # Check rate limits
                if not await self._check_rate_limits(platform):
                    return PublishResult(
                        status=PublishStatus.FAILED,
                        message=f"Rate limit exceeded for {platform}",
                        metadata={
                            "channel": self.channel_name,
                            "platform": platform,
                            "rate_limited": True
                        },
                        errors=["Rate limit exceeded"]
                    )

                # Create temporary post for immediate execution
                temp_post = ScheduledPost(
                    post_id=self._generate_post_id(formatted_content, platform),
                    content=formatted_content,
                    platform=platform,
                    scheduled_for=datetime.utcnow(),
                    hashtags=social_post.hashtags,
                    media_urls=social_post.media_urls
                )

                # Execute immediately
                result = await self._post_to_platform(temp_post)

                if result.success:
                    # Update rate limit tracking
                    if platform not in self.rate_limit_windows:
                        self.rate_limit_windows[platform] = []
                    self.rate_limit_windows[platform].append(datetime.utcnow())

                    # Update stats
                    stats = self._get_or_create_stats(platform)
                    stats.successful_posts += 1
                    stats.total_posts += 1
                    stats.last_post_time = datetime.utcnow()

                    return PublishResult(
                        status=PublishStatus.SUCCESS,
                        message=f"Successfully posted to {platform}",
                        metadata={
                            "channel": self.channel_name,
                            "platform": platform,
                            "automated_posting": True,
                            "formatted_content": formatted_content,
                            "hashtags": social_post.hashtags,
                            "media_urls": social_post.media_urls
                        },
                        external_id=result.data.get('id') if result.data else None,
                        url=self._generate_post_url(platform, result.data.get('id') if result.data else None),
                        published_at=datetime.utcnow()
                    )
                else:
                    # Update stats
                    stats = self._get_or_create_stats(platform)
                    stats.failed_posts += 1
                    stats.total_posts += 1

                    return PublishResult(
                        status=PublishStatus.FAILED,
                        message=f"Failed to post to {platform}: {result.error}",
                        metadata={
                            "channel": self.channel_name,
                            "platform": platform,
                            "api_error": result.error,
                            "status_code": result.status_code
                        },
                        errors=[result.error]
                    )

            # Fallback to manual posting mode (dry run or no credentials)
            else:
                logger.info(f"Social publish (manual mode): {platform} - {formatted_content[:50]}...")

                reason = "dry run mode" if self.dry_run else "no API credentials configured"
                return PublishResult(
                    status=PublishStatus.SUCCESS,
                    message=f"Social post prepared for {platform} ({reason})",
                    metadata={
                        "channel": self.channel_name,
                        "platform": platform,
                        "manual_posting_required": True,
                        "formatted_content": formatted_content,
                        "hashtags": social_post.hashtags,
                        "media_urls": social_post.media_urls,
                        "reason": reason
                    },
                    external_id=f"manual-{platform}-{datetime.utcnow().timestamp()}",
                    published_at=datetime.utcnow()
                )

        except Exception as e:
            logger.error(f"Social publish error: {e}")
            return PublishResult(
                status=PublishStatus.FAILED,
                message=f"Failed to publish social post: {str(e)}",
                metadata={"channel": self.channel_name, "error": str(e)},
                errors=[str(e)]
            )

    def supports_scheduling(self) -> bool:
        """Social publisher supports scheduled posting"""
        return True

    def get_rate_limits(self) -> Dict[str, int]:
        """Get social-specific rate limits"""
        return self.rate_limits

    def get_content_limits(self) -> Dict[str, int]:
        """Get social-specific content limits"""
        return self.platform_limits

    async def health_check(self) -> bool:
        """Check social media API health"""
        try:
            # Check if any platform has valid credentials
            has_valid_platform = False

            for platform in ['twitter', 'linkedin']:
                status = await self.verify_platform_connection(platform)
                if status == PlatformAPIStatus.CONNECTED:
                    has_valid_platform = True
                    logger.debug(f"{platform} API connection: OK")
                elif status == PlatformAPIStatus.DISCONNECTED:
                    logger.debug(f"{platform} API: No credentials configured")
                else:
                    logger.warning(f"{platform} API connection issues: {status.value}")

            return has_valid_platform

        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False

    def _format_for_platform(self, social_post: SocialPost) -> str:
        """
        Format content for specific platform
        """
        content = social_post.content
        platform = social_post.platform.lower()

        if platform == 'twitter':
            # Twitter: hashtags at end, shorter content
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                max_content_len = 280 - len(hashtag_str) - 1
                if len(content) > max_content_len:
                    content = content[:max_content_len-3] + '...'
                content = f"{content} {hashtag_str}"
            return content

        elif platform == 'linkedin':
            # LinkedIn: more professional, hashtags integrated
            if social_post.hashtags:
                # Integrate hashtags naturally into content
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        elif platform == 'facebook':
            # Facebook: longer form, hashtags at end
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        elif platform == 'instagram':
            # Instagram: hashtags are crucial, at end
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        return content

    def _validate_twitter_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Twitter-specific validation"""
        # Check for mentions without @
        content = social_post.content.lower()
        if 'twitter' in content or 'tweet' in content:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider using platform-neutral language",
                field="content",
                code="PLATFORM_SPECIFIC"
            ))

    def _validate_linkedin_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """LinkedIn-specific validation"""
        # LinkedIn prefers professional tone
        casual_words = ['lol', 'omg', 'wtf', 'tbh']
        content_lower = social_post.content.lower()

        for word in casual_words:
            if word in content_lower:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Consider more professional language for LinkedIn (found: {word})",
                    field="content",
                    code="TONE_WARNING"
                ))

    def _validate_facebook_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Facebook-specific validation"""
        # Facebook algorithm prefers engaging content
        if '?' not in social_post.content and 'what' not in social_post.content.lower():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider adding a question to increase engagement",
                field="content",
                code="ENGAGEMENT_TIP"
            ))

    def _validate_instagram_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Instagram-specific validation"""
        # Instagram is visual-first
        if not social_post.media_urls:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Instagram posts typically perform better with images",
                field="media_urls",
                code="VISUAL_RECOMMENDATION"
            ))

    def _get_optimal_posting_time(self, platform: str) -> str:
        """
        Get optimal posting time for platform
        """
        optimal_times = {
            'twitter': '9 AM - 3 PM EST',
            'linkedin': '8 AM - 10 AM EST (weekdays)',
            'facebook': '1 PM - 3 PM EST',
            'instagram': '11 AM - 1 PM EST'
        }
        return optimal_times.get(platform, 'Peak engagement hours vary')

    def _get_platform_tips(self, platform: str) -> List[str]:
        """
        Get platform-specific tips
        """
        tips = {
            'twitter': [
                'Use relevant hashtags (#Breathscape)',
                'Keep it concise and engaging',
                'Include a call-to-action',
                'Tweet during peak hours'
            ],
            'linkedin': [
                'Use professional tone',
                'Include industry hashtags',
                'Share insights and value',
                'Post during business hours'
            ],
            'facebook': [
                'Ask questions to drive engagement',
                'Use visual content when possible',
                'Keep hashtags minimal',
                'Post when your audience is active'
            ],
            'instagram': [
                'Visual content is essential',
                'Use relevant hashtags (max 30)',
                'Include location tags',
                'Post consistently'
            ]
        }
        return tips.get(platform, ['Tailor content to platform audience'])