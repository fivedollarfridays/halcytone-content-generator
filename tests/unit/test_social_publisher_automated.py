"""
Unit tests for Automated Social Publishing capabilities.

Tests cover API integrations, scheduling queue, posting confirmation tracking,
and automated posting workflows.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import aiohttp
from aioresponses import aioresponses

from src.halcytone_content_generator.services.publishers.social_publisher import (
    SocialPublisher,
    PostStatus,
    PlatformAPIStatus,
    PlatformCredentials,
    ScheduledPost,
    PostingStats,
    APIResponse
)
from src.halcytone_content_generator.services.publishers.base import PublishStatus
from src.halcytone_content_generator.schemas.content import Content


class TestAutomatedSocialPublisher:
    """Test cases for automated social publishing functionality."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('src.halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                TWITTER_API_KEY="test_key",
                TWITTER_API_SECRET="test_secret",
                TWITTER_ACCESS_TOKEN="test_token",
                TWITTER_USER_ID="test_user_id",
                LINKEDIN_CLIENT_ID="linkedin_id",
                LINKEDIN_CLIENT_SECRET="linkedin_secret",
                LINKEDIN_ACCESS_TOKEN="linkedin_token",
                LINKEDIN_USER_ID="linkedin_user"
            )

            publisher = SocialPublisher()
            # Stop the scheduler for testing
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    @pytest.fixture
    def mock_content(self):
        """Create mock social content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test social media post content"
        social_post.hashtags = ["#test", "#social"]
        social_post.media_urls = []
        social_post.scheduled_for = None

        content.to_social_post.return_value = social_post
        return content

    @pytest.fixture
    def mock_scheduled_content(self):
        """Create mock scheduled social content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Scheduled post content"
        social_post.hashtags = ["#scheduled"]
        social_post.media_urls = []
        social_post.scheduled_for = datetime.utcnow() + timedelta(hours=1)

        content.to_social_post.return_value = social_post
        return content

    def test_platform_credentials_validation(self):
        """Test platform credentials validation."""
        # Valid credentials
        valid_creds = PlatformCredentials(
            platform="twitter",
            access_token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert valid_creds.is_valid()
        assert not valid_creds.is_expired()

        # Expired credentials
        expired_creds = PlatformCredentials(
            platform="twitter",
            access_token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert not expired_creds.is_valid()
        assert expired_creds.is_expired()

        # No token
        no_token_creds = PlatformCredentials(platform="twitter")
        assert not no_token_creds.is_valid()

    def test_scheduled_post_retry_logic(self):
        """Test scheduled post retry logic."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.FAILED,
            retry_count=2,
            max_retries=3
        )

        assert post.can_retry()

        post.retry_count = 3
        assert not post.can_retry()

        post.status = PostStatus.POSTED
        assert not post.can_retry()

    def test_posting_stats_calculations(self):
        """Test posting statistics calculations."""
        stats = PostingStats(
            total_posts=100,
            successful_posts=85,
            failed_posts=15
        )

        assert stats.success_rate == 0.85
        assert stats.failure_rate == 0.15

        # Empty stats
        empty_stats = PostingStats()
        assert empty_stats.success_rate == 0.0
        assert empty_stats.failure_rate == 0.0

    def test_credentials_initialization(self, social_publisher):
        """Test platform credentials initialization."""
        assert "twitter" in social_publisher.credentials
        assert "linkedin" in social_publisher.credentials

        twitter_creds = social_publisher.credentials["twitter"]
        assert twitter_creds.platform == "twitter"
        assert twitter_creds.api_key == "test_key"
        assert twitter_creds.access_token == "test_token"

    @pytest.mark.asyncio
    async def test_schedule_post(self, social_publisher):
        """Test post scheduling functionality."""
        scheduled_time = datetime.utcnow() + timedelta(hours=2)

        post_id = await social_publisher.schedule_post(
            content="Test scheduled post",
            platform="twitter",
            scheduled_for=scheduled_time,
            hashtags=["#test", "#scheduled"],
            metadata={"source": "test"}
        )

        assert post_id.startswith("post_twitter_")
        assert post_id in social_publisher.scheduled_posts

        scheduled_post = social_publisher.scheduled_posts[post_id]
        assert scheduled_post.content == "Test scheduled post"
        assert scheduled_post.platform == "twitter"
        assert scheduled_post.status == PostStatus.SCHEDULED
        assert scheduled_post.scheduled_for == scheduled_time
        assert "#test" in scheduled_post.hashtags

        # Check stats update
        stats = social_publisher.posting_stats["twitter"]
        assert stats.pending_posts == 1

    @pytest.mark.asyncio
    async def test_cancel_scheduled_post(self, social_publisher):
        """Test cancelling scheduled posts."""
        # Schedule a post
        post_id = await social_publisher.schedule_post(
            content="Test post to cancel",
            platform="twitter",
            scheduled_for=datetime.utcnow() + timedelta(hours=1)
        )

        # Cancel it
        success = await social_publisher.cancel_scheduled_post(post_id)
        assert success is True

        # Check status
        post = social_publisher.scheduled_posts[post_id]
        assert post.status == PostStatus.CANCELLED

        # Try to cancel non-existent post
        success = await social_publisher.cancel_scheduled_post("nonexistent")
        assert success is False

        # Try to cancel already posted post
        post.status = PostStatus.POSTED
        success = await social_publisher.cancel_scheduled_post(post_id)
        assert success is False

    @pytest.mark.asyncio
    async def test_get_scheduled_posts_filtering(self, social_publisher):
        """Test retrieving scheduled posts with filtering."""
        # Schedule posts for different platforms and statuses
        await social_publisher.schedule_post(
            "Twitter post 1", "twitter", datetime.utcnow() + timedelta(hours=1)
        )
        await social_publisher.schedule_post(
            "LinkedIn post 1", "linkedin", datetime.utcnow() + timedelta(hours=2)
        )

        post_id = await social_publisher.schedule_post(
            "Twitter post 2", "twitter", datetime.utcnow() + timedelta(hours=3)
        )
        await social_publisher.cancel_scheduled_post(post_id)

        # Filter by platform
        twitter_posts = await social_publisher.get_scheduled_posts(platform="twitter")
        assert len(twitter_posts) == 2
        assert all(p.platform == "twitter" for p in twitter_posts)

        # Filter by status
        cancelled_posts = await social_publisher.get_scheduled_posts(status=PostStatus.CANCELLED)
        assert len(cancelled_posts) == 1
        assert cancelled_posts[0].status == PostStatus.CANCELLED

        # Filter with limit
        limited_posts = await social_publisher.get_scheduled_posts(limit=2)
        assert len(limited_posts) == 2

    @pytest.mark.asyncio
    async def test_rate_limit_checking(self, social_publisher):
        """Test rate limit checking functionality."""
        platform = "twitter"

        # Should allow posting initially
        can_post = await social_publisher._check_rate_limits(platform)
        assert can_post is True

        # Fill up the rate limit window
        hourly_limit = social_publisher.rate_limits[platform]["posts_per_hour"]
        social_publisher.rate_limit_windows[platform] = [
            datetime.utcnow() for _ in range(hourly_limit)
        ]

        # Should now be rate limited
        can_post = await social_publisher._check_rate_limits(platform)
        assert can_post is False

        # Should allow posting after rate limit window clears
        social_publisher.rate_limit_windows[platform] = [
            datetime.utcnow() - timedelta(hours=2) for _ in range(hourly_limit)
        ]
        can_post = await social_publisher._check_rate_limits(platform)
        assert can_post is True

    @pytest.mark.asyncio
    async def test_post_to_twitter_success(self, social_publisher):
        """Test successful Twitter posting."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test tweet content",
            platform="twitter",
            scheduled_for=datetime.utcnow()
        )

        mock_response = {
            "data": {"id": "123456789", "text": "Test tweet content"}
        }

        with aioresponses() as m:
            m.post(
                social_publisher.api_endpoints['twitter']['post'],
                status=201,
                payload=mock_response,
                headers={"x-rate-limit-remaining": "299"}
            )

            result = await social_publisher._post_to_twitter(post)

            assert result.success is True
            assert result.status_code == 201
            assert result.data["id"] == "123456789"
            assert result.rate_limit_remaining == "299"

    @pytest.mark.asyncio
    async def test_post_to_twitter_failure(self, social_publisher):
        """Test failed Twitter posting."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test tweet content",
            platform="twitter",
            scheduled_for=datetime.utcnow()
        )

        mock_response = {
            "detail": "Unauthorized"
        }

        with aioresponses() as m:
            m.post(
                social_publisher.api_endpoints['twitter']['post'],
                status=401,
                payload=mock_response
            )

            result = await social_publisher._post_to_twitter(post)

            assert result.success is False
            assert result.status_code == 401
            assert "Unauthorized" in result.error

    @pytest.mark.asyncio
    async def test_post_to_twitter_no_credentials(self, social_publisher):
        """Test Twitter posting without credentials."""
        # Remove credentials
        social_publisher.credentials["twitter"].access_token = None

        post = ScheduledPost(
            post_id="test_post",
            content="Test tweet content",
            platform="twitter",
            scheduled_for=datetime.utcnow()
        )

        result = await social_publisher._post_to_twitter(post)

        assert result.success is False
        assert result.status_code == 401
        assert "credentials not configured" in result.error

    @pytest.mark.asyncio
    async def test_post_to_linkedin_success(self, social_publisher):
        """Test successful LinkedIn posting."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test LinkedIn content",
            platform="linkedin",
            scheduled_for=datetime.utcnow()
        )

        mock_response = {"id": "ugc_post_12345"}

        with aioresponses() as m:
            m.post(
                social_publisher.api_endpoints['linkedin']['post'],
                status=201,
                payload=mock_response,
                headers={"x-ratelimit-remaining": "99"}
            )

            result = await social_publisher._post_to_linkedin(post)

            assert result.success is True
            assert result.status_code == 201
            assert result.data["id"] == "ugc_post_12345"

    @pytest.mark.asyncio
    async def test_verify_platform_connections(self, social_publisher):
        """Test platform API connection verification."""
        with aioresponses() as m:
            # Mock successful Twitter verification
            m.get(
                social_publisher.api_endpoints['twitter']['verify'],
                status=200
            )

            twitter_status = await social_publisher.verify_platform_connection("twitter")
            assert twitter_status == PlatformAPIStatus.CONNECTED

        with aioresponses() as m:
            # Mock failed verification
            m.get(
                social_publisher.api_endpoints['twitter']['verify'],
                status=401
            )
            twitter_status = await social_publisher.verify_platform_connection("twitter")
            assert twitter_status == PlatformAPIStatus.ERROR

        # Test with no credentials
        social_publisher.credentials.clear()
        status = await social_publisher.verify_platform_connection("twitter")
        assert status == PlatformAPIStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_execute_scheduled_post_success(self, social_publisher):
        """Test successful execution of scheduled post."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.SCHEDULED
        )

        social_publisher.scheduled_posts[post.post_id] = post

        # Mock successful API response
        mock_api_response = APIResponse(
            success=True,
            status_code=201,
            data={"id": "123456789"}
        )

        with patch.object(social_publisher, '_check_rate_limits', return_value=True), \
             patch.object(social_publisher, '_post_to_platform', return_value=mock_api_response):

            await social_publisher._execute_scheduled_post(post)

            assert post.status == PostStatus.POSTED
            assert post.posted_at is not None
            assert post.external_id == "123456789"

            # Check stats update
            stats = social_publisher.posting_stats["twitter"]
            assert stats.successful_posts == 1

    @pytest.mark.asyncio
    async def test_execute_scheduled_post_rate_limited(self, social_publisher):
        """Test scheduled post execution when rate limited."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.SCHEDULED
        )

        original_time = post.scheduled_for

        with patch.object(social_publisher, '_check_rate_limits', return_value=False):
            await social_publisher._execute_scheduled_post(post)

            assert post.status == PostStatus.SCHEDULED
            assert post.scheduled_for > original_time  # Should be rescheduled

    @pytest.mark.asyncio
    async def test_execute_scheduled_post_failure_with_retry(self, social_publisher):
        """Test scheduled post execution failure with retry."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.SCHEDULED,
            retry_count=0,
            max_retries=3
        )

        # Mock failed API response
        mock_api_response = APIResponse(
            success=False,
            status_code=500,
            error="Server error"
        )

        with patch.object(social_publisher, '_check_rate_limits', return_value=True), \
             patch.object(social_publisher, '_post_to_platform', return_value=mock_api_response):

            await social_publisher._execute_scheduled_post(post)

            assert post.status == PostStatus.RETRYING
            assert post.retry_count == 1
            assert post.error_message == "Server error"
            assert post.scheduled_for > datetime.utcnow()  # Should be rescheduled

    @pytest.mark.asyncio
    async def test_execute_scheduled_post_permanent_failure(self, social_publisher):
        """Test scheduled post execution with permanent failure."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.SCHEDULED,
            retry_count=3,  # At max retries
            max_retries=3
        )

        # Mock failed API response
        mock_api_response = APIResponse(
            success=False,
            status_code=400,
            error="Bad request"
        )

        with patch.object(social_publisher, '_check_rate_limits', return_value=True), \
             patch.object(social_publisher, '_post_to_platform', return_value=mock_api_response):

            await social_publisher._execute_scheduled_post(post)

            assert post.status == PostStatus.FAILED
            assert post.retry_count == 4
            assert not post.can_retry()

            # Check stats update
            stats = social_publisher.posting_stats["twitter"]
            assert stats.failed_posts == 1

    @pytest.mark.asyncio
    async def test_publish_immediate_with_credentials(self, social_publisher, mock_content):
        """Test immediate publishing with valid credentials."""
        # Mock successful API response
        mock_api_response = APIResponse(
            success=True,
            status_code=201,
            data={"id": "123456789"}
        )

        with patch.object(social_publisher, '_check_rate_limits', return_value=True), \
             patch.object(social_publisher, '_post_to_platform', return_value=mock_api_response):

            result = await social_publisher.publish(mock_content)

            assert result.status == PublishStatus.SUCCESS
            assert "Successfully posted to twitter" in result.message
            assert result.external_id == "123456789"
            assert result.metadata["automated_posting"] is True

    @pytest.mark.asyncio
    async def test_publish_scheduled_post(self, social_publisher, mock_scheduled_content):
        """Test publishing scheduled content."""
        result = await social_publisher.publish(mock_scheduled_content)

        assert result.status == PublishStatus.PENDING
        assert "Post scheduled for twitter" in result.message
        assert result.metadata["automated_posting"] is True
        assert "post_id" in result.metadata

        # Verify post was added to scheduled posts
        post_id = result.metadata["post_id"]
        assert post_id in social_publisher.scheduled_posts

    @pytest.mark.asyncio
    async def test_publish_scheduled_no_credentials(self, social_publisher, mock_scheduled_content):
        """Test scheduling post without valid credentials."""
        # Remove credentials
        social_publisher.credentials["twitter"].access_token = None

        result = await social_publisher.publish(mock_scheduled_content)

        assert result.status == PublishStatus.FAILED
        assert "no valid API credentials" in result.message
        assert result.metadata["requires_credentials"] is True

    @pytest.mark.asyncio
    async def test_publish_rate_limited(self, social_publisher, mock_content):
        """Test publishing when rate limited."""
        with patch.object(social_publisher, '_check_rate_limits', return_value=False):
            result = await social_publisher.publish(mock_content)

            assert result.status == PublishStatus.FAILED
            assert "Rate limit exceeded" in result.message
            assert result.metadata["rate_limited"] is True

    @pytest.mark.asyncio
    async def test_publish_dry_run_mode(self, social_publisher, mock_content):
        """Test publishing in dry run mode."""
        social_publisher.dry_run = True

        result = await social_publisher.publish(mock_content)

        assert result.status == PublishStatus.SUCCESS
        assert "dry run mode" in result.message
        assert result.metadata["manual_posting_required"] is True
        assert result.metadata["reason"] == "dry run mode"

    @pytest.mark.asyncio
    async def test_publish_no_credentials(self, social_publisher, mock_content):
        """Test publishing without credentials."""
        social_publisher.credentials.clear()

        result = await social_publisher.publish(mock_content)

        assert result.status == PublishStatus.SUCCESS
        assert "no API credentials configured" in result.message
        assert result.metadata["manual_posting_required"] is True

    @pytest.mark.asyncio
    async def test_health_check_with_connections(self, social_publisher):
        """Test health check with valid connections."""
        with patch.object(social_publisher, 'verify_platform_connection') as mock_verify:
            mock_verify.side_effect = [
                PlatformAPIStatus.CONNECTED,
                PlatformAPIStatus.DISCONNECTED
            ]

            health = await social_publisher.health_check()
            assert health is True  # At least one platform connected

    @pytest.mark.asyncio
    async def test_health_check_no_connections(self, social_publisher):
        """Test health check with no valid connections."""
        with patch.object(social_publisher, 'verify_platform_connection') as mock_verify:
            mock_verify.return_value = PlatformAPIStatus.DISCONNECTED

            health = await social_publisher.health_check()
            assert health is False

    @pytest.mark.asyncio
    async def test_get_posting_stats(self, social_publisher):
        """Test retrieving posting statistics."""
        # Add some test stats
        social_publisher.posting_stats["twitter"] = PostingStats(
            total_posts=50,
            successful_posts=45,
            failed_posts=5
        )
        social_publisher.posting_stats["linkedin"] = PostingStats(
            total_posts=20,
            successful_posts=18,
            failed_posts=2
        )

        # Get all stats
        all_stats = await social_publisher.get_posting_stats()
        assert len(all_stats) == 2
        assert all_stats["twitter"].success_rate == 0.9
        assert all_stats["linkedin"].success_rate == 0.9

        # Get platform-specific stats
        twitter_stats = await social_publisher.get_posting_stats("twitter")
        assert len(twitter_stats) == 1
        assert twitter_stats["twitter"].total_posts == 50

    def test_generate_post_url(self, social_publisher):
        """Test post URL generation."""
        # Set username for URL generation
        social_publisher.credentials["twitter"].username = "testuser"
        social_publisher.credentials["linkedin"].username = "linkedinuser"

        # Test Twitter URL
        twitter_url = social_publisher._generate_post_url("twitter", "123456789")
        assert twitter_url == "https://twitter.com/testuser/status/123456789"

        # Test LinkedIn URL
        linkedin_url = social_publisher._generate_post_url("linkedin", "ugc_post_123")
        assert linkedin_url == "https://www.linkedin.com/feed/update/ugc_post_123"

        # Test with no external ID
        no_id_url = social_publisher._generate_post_url("twitter", None)
        assert no_id_url is None

        # Test with no username
        social_publisher.credentials["twitter"].username = None
        no_username_url = social_publisher._generate_post_url("twitter", "123")
        assert no_username_url is None

    @pytest.mark.asyncio
    async def test_process_scheduled_posts(self, social_publisher):
        """Test processing of scheduled posts."""
        # Create posts with different statuses and times
        now = datetime.utcnow()

        # Ready to post
        ready_post = ScheduledPost(
            post_id="ready_post",
            content="Ready to post",
            platform="twitter",
            scheduled_for=now - timedelta(minutes=1),
            status=PostStatus.SCHEDULED
        )

        # Future post
        future_post = ScheduledPost(
            post_id="future_post",
            content="Future post",
            platform="twitter",
            scheduled_for=now + timedelta(hours=1),
            status=PostStatus.SCHEDULED
        )

        social_publisher.scheduled_posts["ready_post"] = ready_post
        social_publisher.scheduled_posts["future_post"] = future_post

        with patch.object(social_publisher, '_execute_scheduled_post') as mock_execute:
            await social_publisher._process_scheduled_posts()

            # Only the ready post should be executed
            mock_execute.assert_called_once_with(ready_post)

    def test_rate_limit_reset_parsing(self, social_publisher):
        """Test rate limit reset timestamp parsing."""
        # Valid timestamp
        future_timestamp = str(int((datetime.utcnow() + timedelta(hours=1)).timestamp()))
        parsed = social_publisher._parse_rate_limit_reset(future_timestamp)
        assert isinstance(parsed, datetime)

        # Invalid timestamp
        invalid_parsed = social_publisher._parse_rate_limit_reset("invalid")
        assert invalid_parsed is None

        # None input
        none_parsed = social_publisher._parse_rate_limit_reset(None)
        assert none_parsed is None

    @pytest.mark.asyncio
    async def test_unsupported_platform(self, social_publisher):
        """Test posting to unsupported platform."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="unsupported",
            scheduled_for=datetime.utcnow()
        )

        result = await social_publisher._post_to_platform(post)

        assert result.success is False
        assert result.status_code == 400
        assert "Unsupported platform" in result.error