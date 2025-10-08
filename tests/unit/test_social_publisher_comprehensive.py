"""
Comprehensive tests for Social Publisher - covering validation, preview, formatting, and edge cases.

This test file supplements test_social_publisher_automated.py to achieve 100% coverage
by focusing on validation, preview, formatting, and helper methods.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from aioresponses import aioresponses

from halcytone_content_generator.services.publishers.social_publisher import (
    SocialPublisher,
    PostStatus,
    PlatformAPIStatus,
    PlatformCredentials,
    ScheduledPost,
    PostingStats,
    APIResponse
)
from halcytone_content_generator.services.publishers.base import (
    PublishStatus,
    ValidationSeverity
)
from halcytone_content_generator.schemas.content import Content


class TestSocialPublisherValidation:
    """Test comprehensive content validation for all platforms."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                TWITTER_API_KEY="test_key",
                TWITTER_ACCESS_TOKEN="test_token",
                LINKEDIN_CLIENT_ID="linkedin_id",
                LINKEDIN_ACCESS_TOKEN="linkedin_token"
            )
            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    @pytest.fixture
    def twitter_content(self):
        """Create Twitter content for testing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test tweet content"
        social_post.hashtags = ["#test"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post
        return content

    @pytest.fixture
    def linkedin_content(self):
        """Create LinkedIn content for testing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "linkedin"
        social_post.content = "Professional LinkedIn post content"
        social_post.hashtags = ["#professional"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post
        return content

    @pytest.fixture
    def facebook_content(self):
        """Create Facebook content for testing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "facebook"
        social_post.content = "What do you think about this product?"
        social_post.hashtags = ["#facebook"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post
        return content

    @pytest.fixture
    def instagram_content(self):
        """Create Instagram content for testing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "instagram"
        social_post.content = "Beautiful visual content"
        social_post.hashtags = ["#instagram", "#visual"]
        social_post.media_urls = ["https://example.com/image.jpg"]

        content.to_social_post.return_value = social_post
        return content

    @pytest.mark.asyncio
    async def test_validate_wrong_content_type(self, social_publisher):
        """Test validation fails for non-social content."""
        content = Mock(spec=Content)
        content.content_type = "email"

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert len(result.issues) > 0
        assert any("must be 'social'" in issue.message for issue in result.issues)
        assert result.issues[0].severity == ValidationSeverity.ERROR

    @pytest.mark.asyncio
    async def test_validate_missing_platform(self, social_publisher):
        """Test validation fails when platform is missing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = None
        social_post.content = "Test content"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Platform is required" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_unsupported_platform(self, social_publisher):
        """Test validation fails for unsupported platform."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "tiktok"
        social_post.content = "Test content"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Unsupported platform" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_missing_content(self, social_publisher):
        """Test validation fails when content is missing."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = ""
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Content is required" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_content_too_long_twitter(self, social_publisher):
        """Test validation fails when Twitter content exceeds 280 chars."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "A" * 300  # Exceeds 280 char limit
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Content too long" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_too_many_hashtags(self, social_publisher):
        """Test validation warning for too many hashtags."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = [f"#tag{i}" for i in range(15)]  # Exceeds 10 hashtag limit
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert any("Too many hashtags" in issue.message for issue in result.issues)
        warning_issues = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert len(warning_issues) > 0

    @pytest.mark.asyncio
    async def test_validate_hashtag_format_no_hash(self, social_publisher):
        """Test validation warning for hashtags without # prefix."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = ["nohashtag", "#proper"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert any("should start with #" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_hashtag_with_spaces(self, social_publisher):
        """Test validation warning for hashtags with spaces."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = ["#no spaces", "#valid"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert any("should not contain spaces" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_too_many_media(self, social_publisher):
        """Test validation warning for too many media files."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = []
        social_post.media_urls = [f"http://example.com/img{i}.jpg" for i in range(10)]  # Exceeds 4 limit

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        assert any("Too many media files" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_validate_twitter_specific_platform_language(self, social_publisher):
        """Test Twitter-specific validation for platform-specific language."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Check out my latest tweet on Twitter!"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        # Should have INFO severity warning about platform-neutral language
        info_issues = [i for i in result.issues if i.severity == ValidationSeverity.INFO]
        assert any("platform-neutral language" in issue.message for issue in info_issues)

    @pytest.mark.asyncio
    async def test_validate_linkedin_casual_language(self, social_publisher):
        """Test LinkedIn-specific validation for casual language."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "linkedin"
        social_post.content = "This is lol so cool omg!"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        # Should have warnings about professional language
        warning_issues = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert any("professional language" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_facebook_engagement_tip(self, social_publisher):
        """Test Facebook-specific validation for engagement tips."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "facebook"
        social_post.content = "This is a statement without questions."
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        # Should have INFO about adding questions for engagement
        info_issues = [i for i in result.issues if i.severity == ValidationSeverity.INFO]
        assert any("question to increase engagement" in issue.message for issue in info_issues)

    @pytest.mark.asyncio
    async def test_validate_instagram_missing_media(self, social_publisher):
        """Test Instagram-specific validation for missing media."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "instagram"
        social_post.content = "Instagram post without images"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.validate(content)

        # Should have warning about visual content
        warning_issues = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        assert any("perform better with images" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_valid_content_all_platforms(self, social_publisher):
        """Test validation succeeds for valid content across all platforms."""
        platforms = ["twitter", "linkedin", "facebook", "instagram"]

        for platform in platforms:
            content = Mock(spec=Content)
            content.content_type = "social"

            social_post = Mock()
            social_post.platform = platform
            social_post.content = "Valid content for platform"
            social_post.hashtags = ["#valid"]
            social_post.media_urls = ["http://example.com/img.jpg"] if platform == "instagram" else []

            content.to_social_post.return_value = social_post

            result = await social_publisher.validate(content)

            # May have warnings/info but should be valid
            error_issues = [i for i in result.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
            assert len(error_issues) == 0, f"Platform {platform} failed validation unexpectedly"

    @pytest.mark.asyncio
    async def test_validate_exception_handling(self, social_publisher):
        """Test validation handles exceptions gracefully."""
        content = Mock(spec=Content)
        content.content_type = "social"
        content.to_social_post.side_effect = Exception("Conversion error")

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Validation failed" in issue.message for issue in result.issues)
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        assert len(critical_issues) > 0


class TestSocialPublisherPreview:
    """Test preview functionality for all platforms."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock()
            publisher = SocialPublisher(config={"twitter_followers": 5000, "linkedin_followers": 2000})
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    @pytest.mark.asyncio
    async def test_preview_twitter_content(self, social_publisher):
        """Test preview generation for Twitter content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test tweet content"
        social_post.hashtags = ["#test", "#preview"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.preview_data is not None
        assert result.preview_data["platform"] == "twitter"
        assert "#test" in result.preview_data["hashtags"]
        assert "#preview" in result.preview_data["hashtags"]
        assert result.preview_data["character_count"] > 0
        assert "estimated_reach" in result.preview_data
        assert "estimated_likes" in result.preview_data
        assert "estimated_shares" in result.preview_data
        assert "optimal_posting_time" in result.preview_data
        assert "platform_tips" in result.preview_data

    @pytest.mark.asyncio
    async def test_preview_linkedin_content(self, social_publisher):
        """Test preview generation for LinkedIn content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "linkedin"
        social_post.content = "Professional LinkedIn post"
        social_post.hashtags = ["#professional", "#business"]
        social_post.media_urls = ["http://example.com/image.jpg"]

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.preview_data["platform"] == "linkedin"
        assert result.preview_data["media_count"] == 1
        assert "8 AM - 10 AM EST" in result.preview_data["optimal_posting_time"]
        assert len(result.preview_data["platform_tips"]) > 0

    @pytest.mark.asyncio
    async def test_preview_facebook_content(self, social_publisher):
        """Test preview generation for Facebook content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "facebook"
        social_post.content = "Facebook post with engagement"
        social_post.hashtags = ["#facebook"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.preview_data["platform"] == "facebook"
        assert result.estimated_reach > 0
        assert result.estimated_engagement > 0

    @pytest.mark.asyncio
    async def test_preview_instagram_content(self, social_publisher):
        """Test preview generation for Instagram content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "instagram"
        social_post.content = "Beautiful visual content"
        social_post.hashtags = ["#insta", "#photo"]
        social_post.media_urls = ["http://example.com/image.jpg", "http://example.com/image2.jpg"]

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.preview_data["platform"] == "instagram"
        assert result.preview_data["media_count"] == 2
        # Instagram has highest engagement rate
        assert result.estimated_engagement == 0.12

    @pytest.mark.asyncio
    async def test_preview_formatted_content(self, social_publisher):
        """Test that preview includes formatted content."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = ["#test"]
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.formatted_content is not None
        assert "Test content" in result.formatted_content
        assert "#test" in result.formatted_content

    @pytest.mark.asyncio
    async def test_preview_word_count(self, social_publisher):
        """Test preview includes word count."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "This is a test with five words"
        social_post.hashtags = []
        social_post.media_urls = []

        content.to_social_post.return_value = social_post

        result = await social_publisher.preview(content)

        assert result.word_count == 7  # "This is a test with five words"

    @pytest.mark.asyncio
    async def test_preview_exception_handling(self, social_publisher):
        """Test preview handles exceptions gracefully."""
        content = Mock(spec=Content)
        content.content_type = "social"
        content.to_social_post.side_effect = Exception("Preview error")

        result = await social_publisher.preview(content)

        assert "error" in result.preview_data
        assert "Preview failed" in result.formatted_content
        assert result.metadata["error"] is True


class TestSocialPublisherFormatting:
    """Test content formatting for different platforms."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock()
            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    def test_format_twitter_with_hashtags(self, social_publisher):
        """Test Twitter formatting appends hashtags."""
        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test tweet"
        social_post.hashtags = ["#test", "#twitter"]

        formatted = social_publisher._format_for_platform(social_post)

        assert "Test tweet" in formatted
        assert "#test" in formatted
        assert "#twitter" in formatted

    def test_format_twitter_truncates_long_content(self, social_publisher):
        """Test Twitter formatting truncates content exceeding 280 chars."""
        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "A" * 300
        social_post.hashtags = ["#test"]

        formatted = social_publisher._format_for_platform(social_post)

        assert len(formatted) <= 280
        assert "..." in formatted

    def test_format_twitter_without_hashtags(self, social_publisher):
        """Test Twitter formatting without hashtags."""
        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test tweet"
        social_post.hashtags = []

        formatted = social_publisher._format_for_platform(social_post)

        assert formatted == "Test tweet"

    def test_format_linkedin_with_hashtags(self, social_publisher):
        """Test LinkedIn formatting integrates hashtags."""
        social_post = Mock()
        social_post.platform = "linkedin"
        social_post.content = "Professional post"
        social_post.hashtags = ["#professional", "#business"]

        formatted = social_publisher._format_for_platform(social_post)

        assert "Professional post" in formatted
        assert "#professional" in formatted
        assert "#business" in formatted
        assert "\n\n" in formatted  # Hashtags on new lines

    def test_format_facebook_with_hashtags(self, social_publisher):
        """Test Facebook formatting with hashtags."""
        social_post = Mock()
        social_post.platform = "facebook"
        social_post.content = "Facebook post"
        social_post.hashtags = ["#facebook"]

        formatted = social_publisher._format_for_platform(social_post)

        assert "Facebook post" in formatted
        assert "#facebook" in formatted
        assert "\n\n" in formatted

    def test_format_instagram_with_hashtags(self, social_publisher):
        """Test Instagram formatting with hashtags."""
        social_post = Mock()
        social_post.platform = "instagram"
        social_post.content = "Beautiful photo"
        social_post.hashtags = ["#insta", "#photo", "#beautiful"]

        formatted = social_publisher._format_for_platform(social_post)

        assert "Beautiful photo" in formatted
        assert all(tag in formatted for tag in ["#insta", "#photo", "#beautiful"])
        assert "\n\n" in formatted

    def test_format_unsupported_platform(self, social_publisher):
        """Test formatting for unsupported platform returns content as-is."""
        social_post = Mock()
        social_post.platform = "unsupported"
        social_post.content = "Test content"
        social_post.hashtags = []

        formatted = social_publisher._format_for_platform(social_post)

        assert formatted == "Test content"


class TestSocialPublisherHelpers:
    """Test helper methods and utility functions."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock()
            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    def test_get_optimal_posting_time_twitter(self, social_publisher):
        """Test getting optimal posting time for Twitter."""
        time = social_publisher._get_optimal_posting_time("twitter")
        assert "9 AM - 3 PM EST" in time

    def test_get_optimal_posting_time_linkedin(self, social_publisher):
        """Test getting optimal posting time for LinkedIn."""
        time = social_publisher._get_optimal_posting_time("linkedin")
        assert "8 AM - 10 AM EST" in time
        assert "weekdays" in time

    def test_get_optimal_posting_time_facebook(self, social_publisher):
        """Test getting optimal posting time for Facebook."""
        time = social_publisher._get_optimal_posting_time("facebook")
        assert "1 PM - 3 PM EST" in time

    def test_get_optimal_posting_time_instagram(self, social_publisher):
        """Test getting optimal posting time for Instagram."""
        time = social_publisher._get_optimal_posting_time("instagram")
        assert "11 AM - 1 PM EST" in time

    def test_get_optimal_posting_time_unknown(self, social_publisher):
        """Test getting optimal posting time for unknown platform."""
        time = social_publisher._get_optimal_posting_time("unknown")
        assert "Peak engagement hours vary" in time

    def test_get_platform_tips_twitter(self, social_publisher):
        """Test getting platform tips for Twitter."""
        tips = social_publisher._get_platform_tips("twitter")
        assert len(tips) == 4
        assert any("hashtags" in tip for tip in tips)
        assert any("concise" in tip for tip in tips)

    def test_get_platform_tips_linkedin(self, social_publisher):
        """Test getting platform tips for LinkedIn."""
        tips = social_publisher._get_platform_tips("linkedin")
        assert len(tips) == 4
        assert any("professional" in tip for tip in tips)
        assert any("insights" in tip for tip in tips)

    def test_get_platform_tips_facebook(self, social_publisher):
        """Test getting platform tips for Facebook."""
        tips = social_publisher._get_platform_tips("facebook")
        assert len(tips) == 4
        assert any("questions" in tip for tip in tips)

    def test_get_platform_tips_instagram(self, social_publisher):
        """Test getting platform tips for Instagram."""
        tips = social_publisher._get_platform_tips("instagram")
        assert len(tips) == 4
        assert any("Visual" in tip for tip in tips)
        assert any("hashtags" in tip for tip in tips)

    def test_get_platform_tips_unknown(self, social_publisher):
        """Test getting platform tips for unknown platform."""
        tips = social_publisher._get_platform_tips("unknown")
        assert len(tips) == 1
        assert "Tailor content to platform audience" in tips[0]

    def test_supports_scheduling(self, social_publisher):
        """Test that social publisher supports scheduling."""
        assert social_publisher.supports_scheduling() is True

    def test_get_rate_limits(self, social_publisher):
        """Test getting rate limits."""
        limits = social_publisher.get_rate_limits()

        assert "twitter" in limits
        assert "linkedin" in limits
        assert limits["twitter"]["posts_per_hour"] == 15
        assert limits["twitter"]["posts_per_day"] == 300
        assert limits["linkedin"]["posts_per_hour"] == 5
        assert limits["linkedin"]["posts_per_day"] == 25

    def test_get_content_limits(self, social_publisher):
        """Test getting content limits."""
        limits = social_publisher.get_content_limits()

        assert "twitter" in limits
        assert "linkedin" in limits
        assert "facebook" in limits
        assert "instagram" in limits
        assert limits["twitter"]["max_length"] == 280
        assert limits["linkedin"]["max_length"] == 3000
        assert limits["twitter"]["max_hashtags"] == 10
        assert limits["instagram"]["max_media"] == 10

    @pytest.mark.asyncio
    async def test_get_post_status(self, social_publisher):
        """Test getting post status."""
        # Schedule a post first
        post_id = await social_publisher.schedule_post(
            content="Test post",
            platform="twitter",
            scheduled_for=datetime.utcnow() + timedelta(hours=1)
        )

        # Get the status
        post = await social_publisher.get_post_status(post_id)

        assert post is not None
        assert post.post_id == post_id
        assert post.content == "Test post"

    @pytest.mark.asyncio
    async def test_get_post_status_nonexistent(self, social_publisher):
        """Test getting status of non-existent post."""
        post = await social_publisher.get_post_status("nonexistent_id")

        assert post is None


class TestSocialPublisherEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def social_publisher(self):
        """Create a social publisher instance for testing."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                LINKEDIN_CLIENT_ID="linkedin_id",
                LINKEDIN_ACCESS_TOKEN="linkedin_token",
                LINKEDIN_USER_ID="user123"
            )
            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()
            return publisher

    @pytest.mark.asyncio
    async def test_post_to_linkedin_failure(self, social_publisher):
        """Test LinkedIn posting failure."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="linkedin",
            scheduled_for=datetime.utcnow()
        )

        mock_error_response = {"message": "Invalid request"}

        with aioresponses() as m:
            m.post(
                social_publisher.api_endpoints['linkedin']['post'],
                status=400,
                payload=mock_error_response
            )

            result = await social_publisher._post_to_linkedin(post)

            assert result.success is False
            assert result.status_code == 400
            assert "Invalid request" in result.error

    @pytest.mark.asyncio
    async def test_post_to_linkedin_no_credentials(self, social_publisher):
        """Test LinkedIn posting without credentials."""
        social_publisher.credentials["linkedin"].access_token = None

        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="linkedin",
            scheduled_for=datetime.utcnow()
        )

        result = await social_publisher._post_to_linkedin(post)

        assert result.success is False
        assert result.status_code == 401
        assert "credentials not configured" in result.error

    @pytest.mark.asyncio
    async def test_post_to_linkedin_exception(self, social_publisher):
        """Test LinkedIn posting with exception."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="linkedin",
            scheduled_for=datetime.utcnow()
        )

        with aioresponses() as m:
            m.post(
                social_publisher.api_endpoints['linkedin']['post'],
                exception=Exception("Network error")
            )

            result = await social_publisher._post_to_linkedin(post)

            assert result.success is False
            assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_upload_twitter_media(self, social_publisher):
        """Test Twitter media upload placeholder."""
        media_urls = ["http://example.com/image.jpg"]
        creds = PlatformCredentials(platform="twitter", access_token="token")

        # Current implementation returns empty list
        media_ids = await social_publisher._upload_twitter_media(media_urls, creds)

        assert media_ids == []

    @pytest.mark.asyncio
    async def test_upload_linkedin_media(self, social_publisher):
        """Test LinkedIn media upload placeholder."""
        media_urls = ["http://example.com/image.jpg"]
        creds = PlatformCredentials(platform="linkedin", access_token="token")

        # Current implementation returns empty list
        media_assets = await social_publisher._upload_linkedin_media(media_urls, creds)

        assert media_assets == []

    @pytest.mark.asyncio
    async def test_verify_linkedin_connection(self, social_publisher):
        """Test LinkedIn connection verification."""
        creds = PlatformCredentials(
            platform="linkedin",
            access_token="valid_token"
        )

        with aioresponses() as m:
            m.get(
                social_publisher.api_endpoints['linkedin']['verify'],
                status=200
            )

            result = await social_publisher._verify_linkedin_connection(creds)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_linkedin_connection_failure(self, social_publisher):
        """Test LinkedIn connection verification failure."""
        creds = PlatformCredentials(
            platform="linkedin",
            access_token="invalid_token"
        )

        with aioresponses() as m:
            m.get(
                social_publisher.api_endpoints['linkedin']['verify'],
                status=401
            )

            result = await social_publisher._verify_linkedin_connection(creds)
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_linkedin_connection_exception(self, social_publisher):
        """Test LinkedIn connection verification with exception."""
        creds = PlatformCredentials(
            platform="linkedin",
            access_token="token"
        )

        with aioresponses() as m:
            m.get(
                social_publisher.api_endpoints['linkedin']['verify'],
                exception=Exception("Network error")
            )

            result = await social_publisher._verify_linkedin_connection(creds)
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_twitter_connection_failure(self, social_publisher):
        """Test Twitter connection verification failure."""
        creds = PlatformCredentials(
            platform="twitter",
            access_token="invalid_token"
        )

        with aioresponses() as m:
            m.get(
                social_publisher.api_endpoints['twitter']['verify'],
                status=401
            )

            result = await social_publisher._verify_twitter_connection(creds)
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_twitter_connection_exception(self, social_publisher):
        """Test Twitter connection verification with exception."""
        creds = PlatformCredentials(
            platform="twitter",
            access_token="token"
        )

        with aioresponses() as m:
            m.get(
                social_publisher.api_endpoints['twitter']['verify'],
                exception=Exception("Network error")
            )

            result = await social_publisher._verify_twitter_connection(creds)
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_platform_connection_invalid_platform(self, social_publisher):
        """Test platform verification for unsupported platform."""
        # Add credentials for unsupported platform to test ERROR path
        social_publisher.credentials["unsupported"] = PlatformCredentials(
            platform="unsupported",
            access_token="valid_token"
        )

        result = await social_publisher.verify_platform_connection("unsupported")

        assert result == PlatformAPIStatus.ERROR

    @pytest.mark.asyncio
    async def test_scheduler_loop_error_handling(self, social_publisher):
        """Test scheduler loop handles errors gracefully."""
        # Mock the process method to raise an exception
        with patch.object(social_publisher, '_process_scheduled_posts', side_effect=Exception("Scheduler error")):
            # Start the scheduler loop task
            loop_task = asyncio.create_task(social_publisher._scheduler_loop())

            # Let it run briefly
            await asyncio.sleep(0.1)

            # Cancel the task
            loop_task.cancel()

            try:
                await loop_task
            except asyncio.CancelledError:
                pass  # Expected

    @pytest.mark.asyncio
    async def test_execute_scheduled_post_exception(self, social_publisher):
        """Test scheduled post execution with exception."""
        post = ScheduledPost(
            post_id="test_post",
            content="Test content",
            platform="twitter",
            scheduled_for=datetime.utcnow(),
            status=PostStatus.SCHEDULED
        )

        with patch.object(social_publisher, '_check_rate_limits', side_effect=Exception("Rate limit check error")):
            await social_publisher._execute_scheduled_post(post)

            assert post.status == PostStatus.FAILED
            assert post.error_message is not None

    @pytest.mark.asyncio
    async def test_publish_api_posting_failure(self, social_publisher):
        """Test publish with API posting failure."""
        content = Mock(spec=Content)
        content.content_type = "social"

        social_post = Mock()
        social_post.platform = "twitter"
        social_post.content = "Test content"
        social_post.hashtags = []
        social_post.media_urls = []
        social_post.scheduled_for = None

        content.to_social_post.return_value = social_post

        # Mock credentials
        social_publisher.credentials["twitter"] = PlatformCredentials(
            platform="twitter",
            access_token="valid_token"
        )

        # Mock failed API response
        mock_api_response = APIResponse(
            success=False,
            status_code=400,
            error="API error"
        )

        with patch.object(social_publisher, '_check_rate_limits', return_value=True), \
             patch.object(social_publisher, '_post_to_platform', return_value=mock_api_response):

            result = await social_publisher.publish(content)

            assert result.status == PublishStatus.FAILED
            assert "Failed to post" in result.message
            assert "API error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_publish_exception_handling(self, social_publisher):
        """Test publish handles exceptions gracefully."""
        content = Mock(spec=Content)
        content.content_type = "social"
        content.to_social_post.side_effect = Exception("Publish error")

        result = await social_publisher.publish(content)

        assert result.status == PublishStatus.FAILED
        assert "Failed to publish" in result.message
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_health_check_exception(self, social_publisher):
        """Test health check handles exceptions gracefully."""
        with patch.object(social_publisher, 'verify_platform_connection', side_effect=Exception("Health check error")):
            health = await social_publisher.health_check()

            assert health is False

    def test_credentials_initialization_with_missing_settings(self):
        """Test credentials initialization with missing settings."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            # Create mock settings without the required attributes
            settings_mock = Mock(spec=[])  # No attributes
            mock_settings.return_value = settings_mock

            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()

            # Should handle missing credentials gracefully
            assert len(publisher.credentials) == 0

    def test_credentials_initialization_exception(self):
        """Test credentials initialization handles exceptions gracefully."""
        with patch('halcytone_content_generator.services.publishers.social_publisher.get_settings') as mock_settings:
            # Create a settings object with mock attributes
            settings_mock = Mock()
            settings_mock.TWITTER_API_KEY = "test_key"
            settings_mock.TWITTER_ACCESS_TOKEN = "test_token"
            mock_settings.return_value = settings_mock

            # Should handle exception during initialization and continue
            # Even if some settings fail, the publisher should initialize
            publisher = SocialPublisher()
            if publisher._scheduler_task:
                publisher._scheduler_task.cancel()

            # Publisher should be created successfully despite any internal exceptions
            assert publisher is not None
            assert hasattr(publisher, 'credentials')
            assert isinstance(publisher.credentials, dict)
