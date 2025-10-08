"""
Comprehensive tests for WebPublisher service
Tests cover validation, preview, publishing, and error handling
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from halcytone_content_generator.services.publishers.web_publisher import WebPublisher
from halcytone_content_generator.services.publishers.base import (
    PublishStatus, ValidationSeverity, ValidationIssue, ValidationResult,
    PreviewResult, PublishResult
)
from halcytone_content_generator.schemas.content import Content, WebUpdateContent


class TestWebPublisher:
    """Test WebPublisher functionality"""

    @pytest.fixture
    def publisher_config(self):
        return {
            'platform_base_url': 'https://api.test.com',
            'platform_api_key': 'test-key',
            'posts_per_hour': 5,
            'posts_per_day': 25,
            'average_page_views': 1000,
            'average_time_on_page': 3.0
        }

    @pytest.fixture
    def web_publisher(self, publisher_config):
        with patch('halcytone_content_generator.services.publishers.web_publisher.EnhancedPlatformClient'):
            return WebPublisher(config=publisher_config)

    @pytest.fixture
    def valid_web_content(self):
        """Create valid web content for testing"""
        content = MagicMock(spec=Content)
        content.content_type = "web"
        content.dry_run = False

        # Mock to_web_update method
        web_update = MagicMock(spec=WebUpdateContent)
        web_update.title = "Test Web Article"
        web_update.content = "This is a comprehensive test article about web publishing. " * 10
        web_update.excerpt = "This is a test excerpt for the web article."
        web_update.slug = "test-web-article"
        web_update.tags = ["test", "web", "article"]
        web_update.published_at = datetime.now(timezone.utc)

        content.to_web_update.return_value = web_update
        return content

    @pytest.fixture
    def invalid_web_content(self):
        """Create invalid web content for testing"""
        content = MagicMock(spec=Content)
        content.content_type = "email"  # Wrong type
        content.dry_run = False
        return content

    def test_init(self, web_publisher, publisher_config):
        """Test WebPublisher initialization"""
        assert web_publisher.channel_name == "web"
        assert web_publisher.config == publisher_config
        assert web_publisher.content_limits['title_max_length'] == 200
        assert web_publisher.rate_limits['posts_per_hour'] == 5
        assert hasattr(web_publisher, 'platform_client')

    def test_init_default_config(self):
        """Test WebPublisher initialization with default config"""
        with patch('halcytone_content_generator.services.publishers.web_publisher.EnhancedPlatformClient'):
            publisher = WebPublisher()
            assert publisher.config == {}
            assert publisher.rate_limits['posts_per_hour'] == 10
            assert publisher.rate_limits['posts_per_day'] == 50

    @pytest.mark.asyncio
    async def test_validate_valid_content(self, web_publisher, valid_web_content):
        """Test validation of valid web content"""
        result = await web_publisher.validate(valid_web_content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.metadata['channel'] == 'web'

    @pytest.mark.asyncio
    async def test_validate_wrong_content_type(self, web_publisher, invalid_web_content):
        """Test validation of wrong content type"""
        result = await web_publisher.validate(invalid_web_content)

        assert result.is_valid is False
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.ERROR
        assert "Content type must be 'web'" in result.issues[0].message

    @pytest.mark.asyncio
    async def test_validate_missing_title(self, web_publisher):
        """Test validation with missing title"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = ""  # Empty title
        web_update.content = "Valid content"
        web_update.excerpt = "Valid excerpt"
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        assert result.is_valid is False
        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert len(error_issues) >= 1
        assert any("Title is required" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_title_length_limits(self, web_publisher):
        """Test validation of title length limits"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        # Test short title warning
        web_update = MagicMock()
        web_update.title = "Short"  # Under min length
        web_update.content = "Valid content with enough length to pass minimum requirements"
        web_update.excerpt = "Valid excerpt"
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("very short" in issue.message for issue in warning_issues)

        # Test long title error
        web_update.title = "x" * 250  # Over max length
        result = await web_publisher.validate(content)

        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("too long" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_content_requirements(self, web_publisher):
        """Test validation of content requirements"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Valid Title"
        web_update.content = ""  # Empty content
        web_update.excerpt = "Valid excerpt"
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        assert result.is_valid is False
        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("Content is required" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_excerpt_recommendations(self, web_publisher):
        """Test validation of excerpt recommendations"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Valid Title"
        web_update.content = "Valid content with sufficient length"
        web_update.excerpt = ""  # Missing excerpt
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("recommended for SEO" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_slug_format(self, web_publisher):
        """Test validation of slug format"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Valid Title"
        web_update.content = "Valid content with sufficient length"
        web_update.excerpt = "Valid excerpt"
        web_update.slug = "invalid slug with spaces!"  # Invalid format
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("alphanumeric characters" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_tags_limit(self, web_publisher):
        """Test validation of tags limit"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Valid Title"
        web_update.content = "Valid content with sufficient length"
        web_update.excerpt = "Valid excerpt"
        web_update.slug = "valid-slug"
        web_update.tags = ["tag" + str(i) for i in range(15)]  # Too many tags

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("Too many tags" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_seo_warnings(self, web_publisher):
        """Test SEO-related validation warnings"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "This is a very long title that exceeds the recommended length for search engine results"
        web_update.content = "Valid content"
        web_update.excerpt = "This is a very long excerpt that exceeds the recommended length for meta descriptions and should trigger a warning"
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        info_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.INFO]
        assert any("search engine results" in issue.message for issue in info_issues)
        assert any("meta description" in issue.message for issue in info_issues)

    @pytest.mark.asyncio
    async def test_validate_exception_handling(self, web_publisher):
        """Test validation exception handling"""
        content = MagicMock(spec=Content)
        content.content_type = "web"
        content.to_web_update.side_effect = Exception("Test exception")

        result = await web_publisher.validate(content)

        assert result.is_valid is False
        critical_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.CRITICAL]
        assert len(critical_issues) == 1
        assert "Validation failed" in critical_issues[0].message

    @pytest.mark.asyncio
    async def test_preview_valid_content(self, web_publisher, valid_web_content):
        """Test preview generation for valid content"""
        result = await web_publisher.preview(valid_web_content)

        assert isinstance(result, PreviewResult)
        assert "title" in result.preview_data
        assert "estimated_url" in result.preview_data
        assert "seo_score" in result.preview_data
        assert result.estimated_reach == 1000  # From config
        assert result.character_count > 0
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_preview_long_content_truncation(self, web_publisher):
        """Test preview content truncation for long content"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Test Title"
        web_update.content = "x" * 1500  # Long content
        web_update.excerpt = "Test excerpt"
        web_update.slug = "test-slug"
        web_update.tags = ["test"]

        content.to_web_update.return_value = web_update

        result = await web_publisher.preview(content)

        assert len(result.formatted_content) <= 1003  # 1000 + "..."
        assert result.formatted_content.endswith("...")

    @pytest.mark.asyncio
    async def test_preview_slug_generation(self, web_publisher):
        """Test preview slug generation when not provided"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "Test Article Title"
        web_update.content = "Test content"
        web_update.excerpt = "Test excerpt"
        web_update.slug = None  # No slug provided
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.preview(content)

        assert "estimated_url" in result.preview_data
        assert "test-article-title" in result.preview_data["estimated_url"]

    @pytest.mark.asyncio
    async def test_preview_exception_handling(self, web_publisher):
        """Test preview exception handling"""
        content = MagicMock(spec=Content)
        content.to_web_update.side_effect = Exception("Test exception")

        result = await web_publisher.preview(content)

        assert "error" in result.preview_data
        assert "Preview failed" in result.formatted_content
        assert result.metadata.get("error") is True

    @pytest.mark.asyncio
    async def test_publish_dry_run_mode(self, web_publisher, valid_web_content):
        """Test publish in dry run mode"""
        valid_web_content.dry_run = True

        result = await web_publisher.publish(valid_web_content)

        assert result.status == PublishStatus.SUCCESS
        assert "dry run" in result.message
        assert result.metadata["dry_run"] is True
        assert "dry-run-" in result.external_id

    @pytest.mark.asyncio
    async def test_publish_success(self, web_publisher, valid_web_content):
        """Test successful publish"""
        # Mock platform client response
        mock_response = {
            'id': 'content-123',
            'url': '/updates/test-web-article'
        }
        web_publisher.platform_client.publish_content = AsyncMock(return_value=mock_response)

        result = await web_publisher.publish(valid_web_content)

        assert result.status == PublishStatus.SUCCESS
        assert result.external_id == 'content-123'
        assert result.url == '/updates/test-web-article'
        assert result.metadata['content_id'] == 'content-123'

    @pytest.mark.asyncio
    async def test_publish_slug_generation(self, web_publisher):
        """Test publish with automatic slug generation"""
        content = MagicMock(spec=Content)
        content.content_type = "web"
        content.dry_run = False

        web_update = MagicMock()
        web_update.title = "Test Article With No Slug"
        web_update.content = "Test content"
        web_update.excerpt = "Test excerpt"
        web_update.slug = None  # No slug
        web_update.tags = []
        web_update.published_at = None

        content.to_web_update.return_value = web_update

        # Mock platform client response
        mock_response = {'id': 'content-123', 'url': '/updates/generated-slug'}
        web_publisher.platform_client.publish_content = AsyncMock(return_value=mock_response)

        result = await web_publisher.publish(content)

        # Check that slug was generated
        web_publisher.platform_client.publish_content.assert_called_once()
        call_args = web_publisher.platform_client.publish_content.call_args
        assert call_args[1]['slug'] is not None

    @pytest.mark.asyncio
    async def test_publish_platform_client_call(self, web_publisher, valid_web_content):
        """Test that platform client is called with correct parameters"""
        mock_response = {'id': 'content-123', 'url': '/test-url'}
        web_publisher.platform_client.publish_content = AsyncMock(return_value=mock_response)

        await web_publisher.publish(valid_web_content)

        web_publisher.platform_client.publish_content.assert_called_once()
        call_args = web_publisher.platform_client.publish_content.call_args

        assert call_args[1]['title'] == "Test Web Article"
        assert call_args[1]['slug'] == "test-web-article"
        assert 'content' in call_args[1]
        assert 'excerpt' in call_args[1]

    @pytest.mark.asyncio
    async def test_publish_exception_handling(self, web_publisher, valid_web_content):
        """Test publish exception handling"""
        web_publisher.platform_client.publish_content = AsyncMock(side_effect=Exception("Platform error"))

        result = await web_publisher.publish(valid_web_content)

        assert result.status == PublishStatus.FAILED
        assert "Platform error" in result.message
        assert "Platform error" in result.errors

    def test_supports_scheduling(self, web_publisher):
        """Test scheduling support"""
        assert web_publisher.supports_scheduling() is True

    def test_get_rate_limits(self, web_publisher, publisher_config):
        """Test rate limits getter"""
        limits = web_publisher.get_rate_limits()
        assert limits['posts_per_hour'] == publisher_config['posts_per_hour']
        assert limits['posts_per_day'] == publisher_config['posts_per_day']

    def test_get_content_limits(self, web_publisher):
        """Test content limits getter"""
        limits = web_publisher.get_content_limits()
        assert limits['title_max_length'] == 200
        assert limits['content_max_length'] == 100000
        assert limits['max_tags'] == 10

    @pytest.mark.asyncio
    async def test_health_check_success(self, web_publisher):
        """Test health check success"""
        web_publisher.platform_client.health_check = AsyncMock(return_value=True)

        result = await web_publisher.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, web_publisher):
        """Test health check failure"""
        web_publisher.platform_client.health_check = AsyncMock(side_effect=Exception("Health check failed"))

        result = await web_publisher.health_check()
        assert result is False

    def test_generate_slug(self, web_publisher):
        """Test slug generation utility"""
        test_cases = [
            ("Simple Title", "simple-title"),
            ("Title with Numbers 123", "title-with-numbers-123"),
            ("Special @#$ Characters!", "special-characters"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("UPPERCASE TITLE", "uppercase-title"),
            ("Title-with-existing-hyphens", "title-with-existing-hyphens")
        ]

        for title, expected in test_cases:
            slug = web_publisher._generate_slug(title)
            assert slug == expected

    def test_generate_slug_length_limit(self, web_publisher):
        """Test slug generation respects length limit"""
        long_title = "This is a very long title that should be truncated when converted to a slug " * 5
        slug = web_publisher._generate_slug(long_title)
        assert len(slug) <= web_publisher.content_limits['slug_max_length']

    def test_calculate_seo_score(self, web_publisher):
        """Test SEO score calculation"""
        # Create a web update with optimal SEO factors
        web_update = MagicMock()
        web_update.title = "Perfect Length Title for SEO Optimization"  # ~45 chars
        web_update.excerpt = "This is a perfect length excerpt for meta descriptions that should score well for SEO optimization factors."  # ~130 chars
        web_update.content = " ".join(["word"] * 350)  # 350 words
        web_update.tags = ["seo", "optimization", "web", "content"]  # 4 tags

        score = web_publisher._calculate_seo_score(web_update)
        assert 0.0 <= score <= 1.0
        assert score >= 0.8  # Should score high with optimal factors

    def test_calculate_seo_score_poor_factors(self, web_publisher):
        """Test SEO score with poor factors"""
        web_update = MagicMock()
        web_update.title = "Bad"  # Too short
        web_update.excerpt = ""  # No excerpt
        web_update.content = "Short content"  # Too short
        web_update.tags = []  # No tags

        score = web_publisher._calculate_seo_score(web_update)
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should score low with poor factors

    def test_calculate_readability_score(self, web_publisher):
        """Test readability score calculation"""
        # Easy to read content
        easy_content = "This is easy. It has short words. Each sentence is brief."
        score = web_publisher._calculate_readability_score(easy_content)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should score well

        # Hard to read content
        hard_content = "This is an extraordinarily complicated sentence with an excessive number of multisyllabic words that are difficult to comprehend and process effectively."
        score = web_publisher._calculate_readability_score(hard_content)
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should score poorly

    def test_calculate_readability_score_empty_content(self, web_publisher):
        """Test readability score with empty content"""
        score = web_publisher._calculate_readability_score("")
        assert score == 0.0

        score = web_publisher._calculate_readability_score("No sentences here")
        assert score == 0.0  # No periods, so no sentences

    def test_dry_run_property(self, web_publisher):
        """Test dry_run property inheritance from Publisher base"""
        # Initially false
        assert web_publisher.dry_run is False

        # Can be set
        web_publisher.dry_run = True
        assert web_publisher.dry_run is True

    @pytest.mark.asyncio
    async def test_integration_with_settings(self, publisher_config):
        """Test integration with Settings object creation"""
        with patch('halcytone_content_generator.services.publishers.web_publisher.Settings') as mock_settings, \
             patch('halcytone_content_generator.services.publishers.web_publisher.EnhancedPlatformClient') as mock_client:

            mock_settings_instance = MagicMock()
            mock_settings.return_value = mock_settings_instance

            publisher = WebPublisher(config=publisher_config)

            # Verify Settings object was configured correctly
            assert mock_settings_instance.PLATFORM_BASE_URL == publisher_config['platform_base_url']
            assert mock_settings_instance.PLATFORM_API_KEY == publisher_config['platform_api_key']

            # Verify EnhancedPlatformClient was initialized with Settings
            mock_client.assert_called_once_with(mock_settings_instance)

    @pytest.mark.asyncio
    async def test_validation_with_all_severity_levels(self, web_publisher):
        """Test validation produces all severity levels appropriately"""
        content = MagicMock(spec=Content)
        content.content_type = "web"

        web_update = MagicMock()
        web_update.title = "This title is too long for optimal search engine results and will trigger an info warning" + "x" * 100  # Long title (error + info)
        web_update.content = "x"  # Too short (warning)
        web_update.excerpt = ""  # Missing (warning)
        web_update.slug = "valid-slug"
        web_update.tags = []

        content.to_web_update.return_value = web_update

        result = await web_publisher.validate(content)

        # Should have different severity levels
        severities = {issue.severity for issue in result.issues}
        assert ValidationSeverity.ERROR in severities
        assert ValidationSeverity.WARNING in severities
        assert ValidationSeverity.INFO in severities

    def test_logging_integration(self, web_publisher, caplog):
        """Test logging integration"""
        import logging

        with caplog.at_level(logging.INFO):
            # Test logging in various methods
            web_publisher._generate_slug("Test Title")

        # Should not raise any exceptions with logging