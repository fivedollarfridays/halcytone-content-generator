"""
Unit tests for Publisher interface and implementations
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.halcytone_content_generator.services.publishers.base import (
    Publisher, MockPublisher, PublishResult, ValidationResult, PreviewResult,
    PublishStatus, ValidationSeverity, ValidationIssue
)
from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
from src.halcytone_content_generator.services.publishers.web_publisher import WebPublisher
from src.halcytone_content_generator.services.publishers.social_publisher import SocialPublisher
from src.halcytone_content_generator.schemas.content import (
    Content, NewsletterContent, WebUpdateContent, SocialPost
)


class TestPublisherBase:
    """Test Publisher base class and interface"""

    def test_publisher_abstract_class(self):
        """Test that Publisher is properly abstract"""
        with pytest.raises(TypeError):
            Publisher("test", {})

    def test_mock_publisher_initialization(self):
        """Test MockPublisher initialization"""
        publisher = MockPublisher("test", {"dry_run": True})

        assert publisher.channel_name == "test"
        assert publisher.dry_run is True
        assert publisher.published_content == []
        assert publisher.validation_results == []
        assert publisher.preview_results == []

    @pytest.mark.asyncio
    async def test_mock_publisher_validate(self):
        """Test MockPublisher validation"""
        publisher = MockPublisher("test")
        content = Content(
            content_type="email",
            data={"subject": "Test", "html": "<p>Test</p>", "text": "Test"}
        )

        result = await publisher.validate(content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.metadata["mock"] is True
        assert len(publisher.validation_results) == 1

    @pytest.mark.asyncio
    async def test_mock_publisher_preview(self):
        """Test MockPublisher preview"""
        publisher = MockPublisher("test")
        content = Content(
            content_type="email",
            data={"subject": "Test", "html": "<p>Test</p>", "text": "Test"}
        )

        result = await publisher.preview(content)

        assert isinstance(result, PreviewResult)
        assert "MOCK PREVIEW" in result.formatted_content
        assert result.metadata["mock"] is True
        assert len(publisher.preview_results) == 1

    @pytest.mark.asyncio
    async def test_mock_publisher_publish(self):
        """Test MockPublisher publishing"""
        publisher = MockPublisher("test")
        content = Content(
            content_type="email",
            data={"subject": "Test", "html": "<p>Test</p>", "text": "Test"}
        )

        result = await publisher.publish(content)

        assert isinstance(result, PublishResult)
        assert result.status == PublishStatus.SUCCESS
        assert result.metadata["mock"] is True
        assert len(publisher.published_content) == 1
        assert publisher.published_content[0] == content

    def test_mock_publisher_reset(self):
        """Test MockPublisher reset functionality"""
        publisher = MockPublisher("test")

        # Add some data
        publisher.published_content.append("test")
        publisher.validation_results.append("test")
        publisher.preview_results.append("test")

        # Reset
        publisher.reset()

        assert len(publisher.published_content) == 0
        assert len(publisher.validation_results) == 0
        assert len(publisher.preview_results) == 0


class TestEmailPublisher:
    """Test EmailPublisher implementation"""

    @pytest.fixture
    def email_publisher(self):
        """Create EmailPublisher for testing"""
        config = {
            'crm_base_url': 'http://test-crm.com',
            'crm_api_key': 'test-key',
            'dry_run': True,
            'sender_name': 'Test Sender',
            'sender_email': 'test@example.com'
        }
        return EmailPublisher(config)

    @pytest.fixture
    def valid_email_content(self):
        """Create valid email content for testing"""
        newsletter = NewsletterContent(
            subject="Test Newsletter",
            html="<p>This is a test newsletter with sufficient content.</p>",
            text="This is a test newsletter with sufficient content.",
            recipient_count=100
        )
        return Content.from_newsletter(newsletter)

    @pytest.mark.asyncio
    async def test_email_publisher_validate_valid_content(self, email_publisher, valid_email_content):
        """Test email validation with valid content"""
        result = await email_publisher.validate(valid_email_content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len([issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]) == 0

    @pytest.mark.asyncio
    async def test_email_publisher_validate_invalid_content_type(self, email_publisher):
        """Test email validation with wrong content type"""
        content = Content(content_type="web", data={"title": "Test"})

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        assert any(issue.severity == ValidationSeverity.ERROR for issue in result.issues)
        assert any("email" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_email_publisher_validate_missing_subject(self, email_publisher):
        """Test email validation with missing subject"""
        newsletter = NewsletterContent(
            subject="",
            html="<p>Content</p>",
            text="Content"
        )
        content = Content.from_newsletter(newsletter)

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        assert any(issue.field == "subject" and issue.severity == ValidationSeverity.ERROR for issue in result.issues)

    @pytest.mark.asyncio
    async def test_email_publisher_validate_subject_too_long(self, email_publisher):
        """Test email validation with subject too long"""
        newsletter = NewsletterContent(
            subject="x" * 150,  # Too long
            html="<p>Content</p>",
            text="Content"
        )
        content = Content.from_newsletter(newsletter)

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        assert any(issue.field == "subject" and "too long" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_email_publisher_validate_spam_warning(self, email_publisher):
        """Test email validation with spam words"""
        newsletter = NewsletterContent(
            subject="FREE urgent offer - click here now!",
            html="<p>Content</p>",
            text="Content"
        )
        content = Content.from_newsletter(newsletter)

        result = await email_publisher.validate(content)

        # Should still be valid but with warnings
        assert result.is_valid is True
        spam_warnings = [issue for issue in result.issues if issue.code == "SPAM_RISK"]
        assert len(spam_warnings) > 0

    @pytest.mark.asyncio
    async def test_email_publisher_preview(self, email_publisher, valid_email_content):
        """Test email preview generation"""
        result = await email_publisher.preview(valid_email_content)

        assert isinstance(result, PreviewResult)
        assert result.preview_data["subject"] == "Test Newsletter"
        assert "estimated_opens" in result.preview_data
        assert "deliverability_score" in result.preview_data
        assert result.character_count > 0

    @pytest.mark.asyncio
    async def test_email_publisher_publish_dry_run(self, email_publisher, valid_email_content):
        """Test email publishing in dry run mode"""
        result = await email_publisher.publish(valid_email_content)

        assert isinstance(result, PublishResult)
        assert result.status == PublishStatus.SUCCESS
        assert result.metadata["dry_run"] is True
        assert "would be sent" in result.message

    def test_email_publisher_supports_scheduling(self, email_publisher):
        """Test that email publisher supports scheduling"""
        assert email_publisher.supports_scheduling() is True

    def test_email_publisher_get_limits(self, email_publisher):
        """Test getting email publisher limits"""
        rate_limits = email_publisher.get_rate_limits()
        content_limits = email_publisher.get_content_limits()

        assert "emails_per_hour" in rate_limits
        assert "subject_max_length" in content_limits


class TestWebPublisher:
    """Test WebPublisher implementation"""

    @pytest.fixture
    def web_publisher(self):
        """Create WebPublisher for testing"""
        config = {
            'platform_base_url': 'http://test-platform.com',
            'platform_api_key': 'test-key',
            'dry_run': True
        }
        return WebPublisher(config)

    @pytest.fixture
    def valid_web_content(self):
        """Create valid web content for testing"""
        web_update = WebUpdateContent(
            title="Test Article",
            content="This is a test article with sufficient content for web publishing. " * 10,
            excerpt="This is a test excerpt for the article.",
            slug="test-article",
            tags=["test", "article"]
        )
        return Content.from_web_update(web_update)

    @pytest.mark.asyncio
    async def test_web_publisher_validate_valid_content(self, web_publisher, valid_web_content):
        """Test web validation with valid content"""
        result = await web_publisher.validate(valid_web_content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_web_publisher_validate_missing_title(self, web_publisher):
        """Test web validation with missing title"""
        web_update = WebUpdateContent(
            title="",
            content="Content",
            excerpt="Excerpt"
        )
        content = Content.from_web_update(web_update)

        result = await web_publisher.validate(content)

        assert result.is_valid is False
        assert any(issue.field == "title" and issue.severity == ValidationSeverity.ERROR for issue in result.issues)

    @pytest.mark.asyncio
    async def test_web_publisher_validate_content_too_short(self, web_publisher):
        """Test web validation with content too short"""
        web_update = WebUpdateContent(
            title="Test",
            content="Short",  # Too short
            excerpt="Excerpt"
        )
        content = Content.from_web_update(web_update)

        result = await web_publisher.validate(content)

        assert any(issue.field == "content" and "short" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_web_publisher_validate_seo_warnings(self, web_publisher):
        """Test web validation SEO warnings"""
        web_update = WebUpdateContent(
            title="x" * 70,  # Too long for SEO
            content="Content " * 50,
            excerpt="x" * 170  # Too long for meta description
        )
        content = Content.from_web_update(web_update)

        result = await web_publisher.validate(content)

        seo_warnings = [issue for issue in result.issues if issue.code == "SEO_WARNING"]
        assert len(seo_warnings) >= 2  # Title and excerpt warnings

    @pytest.mark.asyncio
    async def test_web_publisher_preview(self, web_publisher, valid_web_content):
        """Test web preview generation"""
        result = await web_publisher.preview(valid_web_content)

        assert isinstance(result, PreviewResult)
        assert result.preview_data["title"] == "Test Article"
        assert "seo_score" in result.preview_data
        assert "readability_score" in result.preview_data
        assert "estimated_url" in result.preview_data

    @pytest.mark.asyncio
    async def test_web_publisher_publish_dry_run(self, web_publisher, valid_web_content):
        """Test web publishing in dry run mode"""
        result = await web_publisher.publish(valid_web_content)

        assert isinstance(result, PublishResult)
        assert result.status == PublishStatus.SUCCESS
        assert result.metadata["dry_run"] is True
        assert result.url is not None

    def test_web_publisher_generate_slug(self, web_publisher):
        """Test slug generation from title"""
        slug = web_publisher._generate_slug("Test Article with Special @#$ Characters!")
        assert slug == "test-article-with-special-characters"

    def test_web_publisher_seo_score_calculation(self, web_publisher):
        """Test SEO score calculation"""
        web_update = WebUpdateContent(
            title="Perfect SEO Title Length",  # Good length
            content="Content " * 100,  # Good length
            excerpt="Perfect meta description length for SEO optimization and user engagement.",  # Good length
            tags=["seo", "content", "web", "optimization"]  # Good number of tags
        )

        score = web_publisher._calculate_seo_score(web_update)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be a good score


class TestSocialPublisher:
    """Test SocialPublisher implementation"""

    @pytest.fixture
    def social_publisher(self):
        """Create SocialPublisher for testing"""
        config = {
            'twitter_followers': 1000,
            'linkedin_followers': 500
        }
        return SocialPublisher(config)

    @pytest.fixture
    def valid_twitter_content(self):
        """Create valid Twitter content for testing"""
        social_post = SocialPost(
            platform="twitter",
            content="Check out our latest breathing exercise feature! #Breathscape #Wellness",
            hashtags=["#Breathscape", "#Wellness", "#Health"],
            media_urls=[]
        )
        return Content.from_social_post(social_post)

    @pytest.fixture
    def valid_linkedin_content(self):
        """Create valid LinkedIn content for testing"""
        social_post = SocialPost(
            platform="linkedin",
            content="We're excited to share insights about mindful breathing and its impact on productivity. Our latest research shows significant improvements in focus and stress reduction.",
            hashtags=["#Mindfulness", "#Productivity", "#Wellness"],
            media_urls=[]
        )
        return Content.from_social_post(social_post)

    @pytest.mark.asyncio
    async def test_social_publisher_validate_twitter_valid(self, social_publisher, valid_twitter_content):
        """Test social validation with valid Twitter content"""
        result = await social_publisher.validate(valid_twitter_content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_social_publisher_validate_twitter_too_long(self, social_publisher):
        """Test social validation with Twitter content too long"""
        social_post = SocialPost(
            platform="twitter",
            content="x" * 300,  # Too long for Twitter
            hashtags=[],
            media_urls=[]
        )
        content = Content.from_social_post(social_post)

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("too long" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_social_publisher_validate_unsupported_platform(self, social_publisher):
        """Test social validation with unsupported platform"""
        social_post = SocialPost(
            platform="tiktok",  # Not supported
            content="Test content",
            hashtags=[],
            media_urls=[]
        )
        content = Content.from_social_post(social_post)

        result = await social_publisher.validate(content)

        assert result.is_valid is False
        assert any("Unsupported platform" in issue.message for issue in result.issues)

    @pytest.mark.asyncio
    async def test_social_publisher_validate_hashtag_format(self, social_publisher):
        """Test social validation with incorrect hashtag format"""
        social_post = SocialPost(
            platform="twitter",
            content="Test content",
            hashtags=["NoHash", "With Space", "#Correct"],  # Mixed formats
            media_urls=[]
        )
        content = Content.from_social_post(social_post)

        result = await social_publisher.validate(content)

        # Should have warnings for incorrect hashtag formats
        hashtag_warnings = [issue for issue in result.issues if issue.field == "hashtags"]
        assert len(hashtag_warnings) >= 2

    @pytest.mark.asyncio
    async def test_social_publisher_validate_linkedin_casual_language(self, social_publisher):
        """Test LinkedIn validation with casual language warning"""
        social_post = SocialPost(
            platform="linkedin",
            content="OMG this is so cool lol! Check it out!",
            hashtags=["#Professional"],
            media_urls=[]
        )
        content = Content.from_social_post(social_post)

        result = await social_publisher.validate(content)

        # Should have warnings for casual language
        tone_warnings = [issue for issue in result.issues if issue.code == "TONE_WARNING"]
        assert len(tone_warnings) > 0

    @pytest.mark.asyncio
    async def test_social_publisher_preview_twitter(self, social_publisher, valid_twitter_content):
        """Test social preview for Twitter"""
        result = await social_publisher.preview(valid_twitter_content)

        assert isinstance(result, PreviewResult)
        assert result.preview_data["platform"] == "twitter"
        assert "optimal_posting_time" in result.preview_data
        assert "platform_tips" in result.preview_data
        assert result.character_count <= 280

    @pytest.mark.asyncio
    async def test_social_publisher_preview_linkedin(self, social_publisher, valid_linkedin_content):
        """Test social preview for LinkedIn"""
        result = await social_publisher.preview(valid_linkedin_content)

        assert isinstance(result, PreviewResult)
        assert result.preview_data["platform"] == "linkedin"
        assert "estimated_reach" in result.preview_data

    @pytest.mark.asyncio
    async def test_social_publisher_publish(self, social_publisher, valid_twitter_content):
        """Test social publishing (currently simulation)"""
        result = await social_publisher.publish(valid_twitter_content)

        assert isinstance(result, PublishResult)
        assert result.status == PublishStatus.SUCCESS
        assert "manual posting required" in result.message.lower()
        assert result.metadata["manual_posting_required"] is True

    def test_social_publisher_format_for_platform_twitter(self, social_publisher):
        """Test content formatting for Twitter"""
        social_post = SocialPost(
            platform="twitter",
            content="Test content",
            hashtags=["#Test", "#Content"],
            media_urls=[]
        )

        formatted = social_publisher._format_for_platform(social_post)
        assert "#Test #Content" in formatted
        assert len(formatted) <= 280

    def test_social_publisher_format_for_platform_linkedin(self, social_publisher):
        """Test content formatting for LinkedIn"""
        social_post = SocialPost(
            platform="linkedin",
            content="Professional content for LinkedIn",
            hashtags=["#Professional", "#LinkedIn"],
            media_urls=[]
        )

        formatted = social_publisher._format_for_platform(social_post)
        assert "Professional content for LinkedIn" in formatted
        assert "#Professional #LinkedIn" in formatted

    def test_social_publisher_optimal_posting_times(self, social_publisher):
        """Test optimal posting time retrieval"""
        twitter_time = social_publisher._get_optimal_posting_time("twitter")
        linkedin_time = social_publisher._get_optimal_posting_time("linkedin")

        assert "EST" in twitter_time
        assert "weekdays" in linkedin_time.lower()

    def test_social_publisher_platform_tips(self, social_publisher):
        """Test platform-specific tips"""
        twitter_tips = social_publisher._get_platform_tips("twitter")
        linkedin_tips = social_publisher._get_platform_tips("linkedin")

        assert len(twitter_tips) > 0
        assert len(linkedin_tips) > 0
        assert any("hashtags" in tip.lower() for tip in twitter_tips)
        assert any("professional" in tip.lower() for tip in linkedin_tips)