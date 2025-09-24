"""
Comprehensive unit tests for API endpoints
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, BackgroundTasks

from src.halcytone_content_generator.api.endpoints import (
    generate_content, preview_content, get_status, get_publishers
)
from src.halcytone_content_generator.config import Settings
from src.halcytone_content_generator.schemas.content import (
    ContentGenerationRequest, NewsletterContent, WebUpdateContent, SocialPost
)


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = Mock(spec=Settings)
    settings.SERVICE_NAME = "test-service"
    settings.ENVIRONMENT = "test"
    settings.LIVING_DOC_TYPE = "google_docs"
    settings.CRM_BASE_URL = "https://test-crm.com"
    settings.CRM_API_KEY = "test-crm-key"
    settings.PLATFORM_BASE_URL = "https://test-platform.com"
    settings.PLATFORM_API_KEY = "test-platform-key"
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.SOCIAL_PLATFORMS = ["twitter", "linkedin"]
    settings.DRY_RUN = True
    return settings

@pytest.fixture
def mock_background_tasks():
    """Create mock background tasks"""
    return Mock(spec=BackgroundTasks)

@pytest.fixture
def sample_request():
    """Create sample content generation request"""
    return ContentGenerationRequest(
        send_email=True,
        publish_web=True,
        generate_social=True,
        preview_only=False,
        include_preview=True
    )

@pytest.fixture
def sample_content():
    """Create sample content data"""
    return {
        'breathscape': [{'title': 'New Algorithm', 'content': 'AI improvements'}],
        'hardware': [{'title': 'Sensor Update', 'content': 'Better accuracy'}],
        'tips': [{'title': 'Breathing Tip', 'content': 'Try 4-7-8 technique'}],
        'vision': [{'title': 'Future Plans', 'content': 'Expanding globally'}]
    }


class TestEndpoints:
    """Test API endpoints functionality"""


class TestGetPublishers:
    """Test get_publishers function"""

    def test_get_publishers_configuration(self, mock_settings):
        """Test publishers are configured correctly"""
        publishers = get_publishers(mock_settings)

        assert 'email' in publishers
        assert 'web' in publishers
        assert 'social' in publishers

        # Check that publishers are properly instantiated
        assert publishers['email'] is not None
        assert publishers['web'] is not None
        assert publishers['social'] is not None


class TestGenerateContent:
    """Test generate_content endpoint"""

    @pytest.mark.asyncio
    async def test_generate_content_preview_only(self, sample_request, mock_settings, mock_background_tasks, sample_content):
        """Test content generation in preview mode"""
        sample_request.preview_only = True

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class:

            # Mock fetcher
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            # Mock assembler
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test Newsletter</h1><p>January 2024</p>',
                'text': 'Test Newsletter\nJanuary 2024',
                'preview_text': 'Preview of newsletter'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Web Update',
                'content': 'Web content details',
                'excerpt': 'Brief web update summary'
            }
            mock_assembler.generate_social_posts.return_value = [
                {'platform': 'twitter', 'content': 'Tweet content'}
            ]

            result = await generate_content(sample_request, mock_background_tasks, mock_settings)

            assert result.status == "preview"
            assert result.newsletter is not None
            assert result.web_update is not None
            assert result.social_posts is not None
            assert len(result.social_posts) == 1

    @pytest.mark.asyncio
    async def test_generate_content_with_publishing(self, sample_request, mock_settings, mock_background_tasks, sample_content):
        """Test content generation with actual publishing"""
        sample_request.preview_only = False

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_publishers:

            # Mock fetcher
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            # Mock assembler
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test Newsletter</h1><p>January 2024</p>',
                'text': 'Test Newsletter\nJanuary 2024',
                'preview_text': 'Preview of newsletter'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Web Update',
                'content': 'Web content details',
                'excerpt': 'Brief web update summary'
            }
            mock_assembler.generate_social_posts.return_value = [
                {'platform': 'twitter', 'content': 'Tweet content'}
            ]

            # Mock publishers
            mock_email_publisher = AsyncMock()
            mock_web_publisher = AsyncMock()
            mock_social_publisher = AsyncMock()

            # Mock successful validation and publishing
            mock_validation = Mock()
            mock_validation.is_valid = True

            mock_publish_result = Mock()
            mock_publish_result.status.value = "success"
            mock_publish_result.message = "Published successfully"
            mock_publish_result.external_id = "test-123"
            mock_publish_result.metadata = {"key": "value"}

            mock_email_publisher.validate.return_value = mock_validation
            mock_email_publisher.publish.return_value = mock_publish_result
            mock_web_publisher.validate.return_value = mock_validation
            mock_web_publisher.publish.return_value = mock_publish_result
            mock_social_publisher.validate.return_value = mock_validation
            mock_social_publisher.publish.return_value = mock_publish_result

            mock_get_publishers.return_value = {
                'email': mock_email_publisher,
                'web': mock_web_publisher,
                'social': mock_social_publisher
            }

            result = await generate_content(sample_request, mock_background_tasks, mock_settings)

            assert result.status == "success"
            assert 'email' in result.results
            assert 'web' in result.results
            assert 'social' in result.results
            assert result.results['email']['status'] == 'success'
            assert result.results['web']['status'] == 'success'

    @pytest.mark.asyncio
    async def test_generate_content_validation_failure(self, sample_request, mock_settings, mock_background_tasks, sample_content):
        """Test content generation with validation failures"""
        sample_request.preview_only = False

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_publishers:

            # Mock fetcher
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            # Mock assembler
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test Newsletter</h1><p>January 2024</p>',
                'text': 'Test Newsletter\nJanuary 2024',
                'preview_text': 'Preview of newsletter'
            }
            mock_assembler.generate_web_update.return_value = None
            mock_assembler.generate_social_posts.return_value = []

            # Mock publishers with validation failure
            mock_email_publisher = AsyncMock()
            mock_validation = Mock()
            mock_validation.is_valid = False
            mock_validation.issues = ["Missing required field"]
            mock_email_publisher.validate.return_value = mock_validation

            mock_get_publishers.return_value = {
                'email': mock_email_publisher,
                'web': AsyncMock(),
                'social': AsyncMock()
            }

            result = await generate_content(sample_request, mock_background_tasks, mock_settings)

            assert result.status == "success"
            assert 'email' in result.results
            assert result.results['email']['status'] == 'validation_failed'
            assert 'issues' in result.results['email']

    @pytest.mark.asyncio
    async def test_generate_content_exception_handling(self, sample_request, mock_settings, mock_background_tasks):
        """Test exception handling in generate_content"""
        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class:
            mock_fetcher_class.side_effect = Exception("Test error")

            with pytest.raises(HTTPException) as exc_info:
                await generate_content(sample_request, mock_background_tasks, mock_settings)

            assert exc_info.value.status_code == 500
            assert "Test error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_generate_content_selective_publishing(self, mock_settings, mock_background_tasks, sample_content):
        """Test selective publishing options"""
        # Test email only
        request = ContentGenerationRequest(
            send_email=True,
            publish_web=False,
            generate_social=False,
            preview_only=False
        )

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_publishers:

            # Mock setup
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test Newsletter</h1><p>January 2024</p>',
                'text': 'Test Newsletter\nJanuary 2024',
                'preview_text': 'Preview'
            }
            mock_assembler.generate_web_update.return_value = None
            mock_assembler.generate_social_posts.return_value = []

            # Mock publishers
            mock_email_publisher = AsyncMock()
            mock_validation = Mock()
            mock_validation.is_valid = True
            mock_publish_result = Mock()
            mock_publish_result.status.value = "success"
            mock_publish_result.message = "Email sent"
            mock_publish_result.external_id = "email-123"
            mock_publish_result.metadata = {}

            mock_email_publisher.validate.return_value = mock_validation
            mock_email_publisher.publish.return_value = mock_publish_result

            mock_get_publishers.return_value = {
                'email': mock_email_publisher,
                'web': AsyncMock(),
                'social': AsyncMock()
            }

            result = await generate_content(request, mock_background_tasks, mock_settings)

            assert result.status == "success"
            assert 'email' in result.results
            assert 'web' not in result.results
            assert 'social' not in result.results


class TestPreviewContent:
    """Test preview_content endpoint"""

    @pytest.mark.asyncio
    async def test_preview_content_success(self, mock_settings, sample_content):
        """Test successful content preview"""
        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class:

            # Mock fetcher
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            # Mock assembler
            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Preview Newsletter',
                'html': '<h1>Preview Newsletter</h1><p>January 2024</p>',
                'text': 'Preview Newsletter\nJanuary 2024',
                'preview_text': 'Preview text'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Preview Web Update',
                'content': 'Preview content',
                'excerpt': 'Preview excerpt'
            }
            mock_assembler.generate_social_posts.return_value = [
                {'platform': 'twitter', 'content': 'Preview tweet'}
            ]

            result = await preview_content(mock_settings)

            assert result.newsletter is not None
            assert result.web_update is not None
            assert result.social_posts is not None
            assert result.content_summary['breathscape'] == 1
            assert result.content_summary['hardware'] == 1
            assert result.content_summary['tips'] == 1
            assert result.content_summary['vision'] == 1

    @pytest.mark.asyncio
    async def test_preview_content_exception_handling(self, mock_settings):
        """Test exception handling in preview_content"""
        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class:
            mock_fetcher_class.side_effect = Exception("Preview error")

            with pytest.raises(HTTPException) as exc_info:
                await preview_content(mock_settings)

            assert exc_info.value.status_code == 500
            assert "Preview error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_preview_content_empty_data(self, mock_settings):
        """Test preview with empty content data"""
        empty_content = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class:

            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = empty_content

            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Empty Newsletter',
                'html': '<html><body><p>No content available</p></body></html>',
                'text': 'No content available',
                'preview_text': 'Empty'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Empty Update',
                'content': 'No content available',
                'excerpt': 'No content'
            }
            mock_assembler.generate_social_posts.return_value = []

            result = await preview_content(mock_settings)

            assert result.newsletter is not None
            assert result.newsletter.subject == 'Empty Newsletter'
            assert result.web_update is not None
            assert result.web_update.title == 'Empty Update'
            assert result.social_posts == []
            assert all(count == 0 for count in result.content_summary.values())


class TestGetStatus:
    """Test get_status endpoint"""

    @pytest.mark.asyncio
    async def test_get_status_all_configured(self, mock_settings):
        """Test status when all services are configured"""
        result = await get_status(mock_settings)

        assert result['service'] == 'test-service'
        assert result['environment'] == 'test'
        assert result['document_source'] == 'google_docs'
        assert result['crm_configured'] is True
        assert result['platform_configured'] is True
        assert result['ai_enabled'] is True
        assert result['social_platforms'] == ['twitter', 'linkedin']

    @pytest.mark.asyncio
    async def test_get_status_partially_configured(self, mock_settings):
        """Test status when some services are not configured"""
        mock_settings.CRM_API_KEY = None
        mock_settings.OPENAI_API_KEY = ""

        result = await get_status(mock_settings)

        assert result['crm_configured'] is False
        assert result['platform_configured'] is True  # Still has base URL and API key
        assert result['ai_enabled'] is False

    @pytest.mark.asyncio
    async def test_get_status_minimal_config(self, mock_settings):
        """Test status with minimal configuration"""
        mock_settings.CRM_BASE_URL = None
        mock_settings.CRM_API_KEY = None
        mock_settings.PLATFORM_BASE_URL = ""
        mock_settings.PLATFORM_API_KEY = ""
        mock_settings.OPENAI_API_KEY = None

        result = await get_status(mock_settings)

        assert result['crm_configured'] is False
        assert result['platform_configured'] is False
        assert result['ai_enabled'] is False


class TestEndpointsIntegration:
    """Integration tests for endpoints"""

    @pytest.mark.asyncio
    async def test_full_workflow_preview_to_publish(self, mock_settings):
        """Test full workflow from preview to publish"""
        sample_content = {
            'breathscape': [{'title': 'AI Update', 'content': 'New ML model'}],
            'hardware': [{'title': 'Sensor v2', 'content': 'Improved sensors'}],
            'tips': [],
            'vision': []
        }

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class:

            # Setup mocks
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Monthly Update',
                'html': '<h1>Monthly Update</h1><p>January 2024</p><div><h2>AI Update</h2><p>New ML model</p></div>',
                'text': 'Monthly Update\nJanuary 2024\n\nAI Update\nNew ML model',
                'preview_text': 'Monthly update preview'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Website Update',
                'content': 'Latest developments',
                'excerpt': 'Website update excerpt'
            }
            mock_assembler.generate_social_posts.return_value = [
                {'platform': 'twitter', 'content': 'Exciting AI update!'}
            ]

            # Test preview first
            preview_result = await preview_content(mock_settings)
            assert preview_result.newsletter is not None
            assert preview_result.content_summary['breathscape'] == 1
            assert preview_result.content_summary['hardware'] == 1

            # Then test actual generation in preview mode
            preview_request = ContentGenerationRequest(
                send_email=True,
                publish_web=True,
                generate_social=True,
                preview_only=True
            )

            generation_result = await generate_content(
                preview_request,
                Mock(spec=BackgroundTasks),
                mock_settings
            )

            assert generation_result.status == "preview"
            assert generation_result.newsletter is not None
            assert generation_result.web_update is not None
            assert len(generation_result.social_posts) == 1

    @pytest.mark.asyncio
    async def test_error_handling_across_endpoints(self, mock_settings):
        """Test error handling consistency across endpoints"""
        error_message = "Document service unavailable"

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class:
            mock_fetcher_class.side_effect = Exception(error_message)

            # Test preview endpoint error handling
            with pytest.raises(HTTPException) as exc_info:
                await preview_content(mock_settings)
            assert exc_info.value.status_code == 500
            assert error_message in str(exc_info.value.detail)

            # Test generate endpoint error handling
            request = ContentGenerationRequest(preview_only=True)
            with pytest.raises(HTTPException) as exc_info:
                await generate_content(request, Mock(spec=BackgroundTasks), mock_settings)
            assert exc_info.value.status_code == 500
            assert error_message in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_social_posts_processing(self, mock_settings, mock_background_tasks):
        """Test social posts processing with multiple platforms"""
        sample_content = {'breathscape': [], 'hardware': [], 'tips': [], 'vision': []}

        with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher_class, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler_class, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_publishers:

            # Setup mocks
            mock_fetcher = AsyncMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch_content.return_value = sample_content

            mock_assembler = Mock()
            mock_assembler_class.return_value = mock_assembler
            mock_assembler.generate_newsletter.return_value = None
            mock_assembler.generate_web_update.return_value = None
            mock_assembler.generate_social_posts.return_value = [
                {'platform': 'twitter', 'content': 'Twitter post'},
                {'platform': 'linkedin', 'content': 'LinkedIn post'},
                {'platform': 'twitter', 'content': 'Another Twitter post'}
            ]

            # Mock social publisher
            mock_social_publisher = AsyncMock()
            mock_validation = Mock()
            mock_validation.is_valid = True
            mock_publish_result = Mock()
            mock_publish_result.status.value = "success"
            mock_publish_result.message = "Posted successfully"
            mock_publish_result.external_id = "post-123"
            mock_publish_result.metadata = {}

            mock_social_publisher.validate.return_value = mock_validation
            mock_social_publisher.publish.return_value = mock_publish_result

            mock_get_publishers.return_value = {
                'email': AsyncMock(),
                'web': AsyncMock(),
                'social': mock_social_publisher
            }

            # Test request with only social generation
            request = ContentGenerationRequest(
                send_email=False,
                publish_web=False,
                generate_social=True,
                preview_only=False
            )

            result = await generate_content(request, mock_background_tasks, mock_settings)

            assert result.status == "success"
            assert 'social' in result.results
            assert result.results['social']['total_posts'] == 3
            assert set(result.results['social']['platforms']) == {'twitter', 'linkedin'}
            assert len(result.results['social']['posts']) == 3