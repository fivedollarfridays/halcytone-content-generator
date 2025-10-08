"""
Unit tests for enhanced API endpoints v2
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from halcytone_content_generator.api.endpoints_v2 import router
from halcytone_content_generator.schemas.content import ContentGenerationRequest
from fastapi import FastAPI


@pytest.fixture
def app():
    """Create FastAPI app with v2 router for testing"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = MagicMock()
    settings.LIVING_DOC_TYPE = "google_docs"
    settings.GOOGLE_DOC_ID = "test_doc_id"
    settings.CRM_BASE_URL = "https://api.crm.test"
    settings.CRM_API_KEY = "test_crm_key"
    settings.PLATFORM_BASE_URL = "https://api.platform.test"
    settings.PLATFORM_API_KEY = "test_platform_key"
    return settings


@pytest.fixture
def sample_content():
    """Sample content for testing"""
    return {
        'breathscape': [
            {'title': 'Breathing Update', 'content': 'New algorithm released'}
        ],
        'hardware': [
            {'title': 'Sensor Update', 'content': 'Improved accuracy'}
        ],
        'tips': [
            {'title': 'Breathing Tip', 'content': 'Try deep breathing'}
        ],
        'vision': [
            {'title': 'Our Vision', 'content': 'Accessible breathing wellness'}
        ]
    }


@pytest.fixture
def sample_newsletter():
    """Sample newsletter for testing"""
    return {
        'subject': 'Test Newsletter',
        'html': '<html><body>Test content</body></html>',
        'text': 'Test content'
    }


@pytest.fixture
def sample_web_update():
    """Sample web update for testing"""
    return {
        'title': 'Test Update',
        'content': '# Test Update\n\nContent here',
        'excerpt': 'Test excerpt',
        'meta_description': 'Test meta description',
        'tags': ['test', 'update'],
        'schema_markup': '{}',
        'reading_time': '2 min',
        'word_count': 150
    }


@pytest.fixture
def sample_social_posts():
    """Sample social posts for testing"""
    return [
        {
            'platform': 'twitter',
            'content': 'Test tweet',
            'type': 'announcement',
            'media_suggestions': []
        },
        {
            'platform': 'linkedin',
            'content': 'Test LinkedIn post',
            'type': 'thought_leadership',
            'media_suggestions': ['image1.jpg']
        }
    ]


class TestGenerateEnhancedContent:
    """Test generate enhanced content endpoint"""

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.ContentValidator')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @patch('halcytone_content_generator.services.publishers.email_publisher.EnhancedCRMClient')
    @patch('halcytone_content_generator.services.publishers.web_publisher.EnhancedPlatformClient')
    @pytest.mark.asyncio
    async def test_generate_enhanced_content_preview_only(
        self, mock_platform_client, mock_crm_client, mock_assembler,
        mock_validator, mock_fetcher, mock_get_settings, client,
        mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test content generation in preview mode"""
        # Setup mocks
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate_content.return_value = (True, [])
        mock_validator_instance.enhance_categorization.return_value = sample_content
        mock_validator_instance.sanitize_content.return_value = sample_content
        mock_validator_instance.generate_content_summary.return_value = "Test summary"
        mock_validator.return_value = mock_validator_instance

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_newsletter.return_value = sample_newsletter
        mock_assembler_instance.generate_web_update.return_value = sample_web_update
        mock_assembler_instance.generate_social_posts.return_value = sample_social_posts
        mock_assembler.return_value = mock_assembler_instance

        # Make request
        response = client.post(
            "/v2/generate-content",
            json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": True
            },
            params={
                "template_style": "modern",
                "seo_optimize": True,
                "validate_content": True
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'preview'
        assert 'newsletter' in data
        assert 'web_update' in data
        assert 'social_posts' in data
        assert 'results' in data
        assert data['results']['template_style'] == 'modern'
        assert data['results']['seo_enabled'] is True

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @patch('halcytone_content_generator.services.publishers.email_publisher.EnhancedCRMClient')
    @patch('halcytone_content_generator.services.publishers.web_publisher.EnhancedPlatformClient')
    @pytest.mark.asyncio
    async def test_generate_enhanced_content_full_flow(
        self, mock_platform_client, mock_crm_client, mock_assembler,
        mock_fetcher, mock_get_settings, client, mock_settings,
        sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test full content generation and distribution flow"""
        # Setup mocks
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_newsletter.return_value = sample_newsletter
        mock_assembler_instance.generate_web_update.return_value = sample_web_update
        mock_assembler_instance.generate_social_posts.return_value = sample_social_posts
        mock_assembler.return_value = mock_assembler_instance

        mock_crm_instance = AsyncMock()
        mock_crm_instance.send_newsletter.return_value = {'sent': 100, 'failed': 0}
        mock_crm_client.return_value = mock_crm_instance

        mock_platform_instance = AsyncMock()
        mock_platform_instance.publish_update.return_value = {'id': 'test123', 'url': 'https://test.com/post'}
        mock_platform_client.return_value = mock_platform_instance

        # Make request
        response = client.post(
            "/v2/generate-content",
            json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False,
                "include_preview": False
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'results' in data
        assert 'email' in data['results']
        assert 'web' in data['results']
        assert 'social' in data['results']

        # Verify newsletter was None (include_preview = False)
        assert data['newsletter'] is None
        assert data['web_update'] is None
        assert data['social_posts'] is None

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_generate_enhanced_content_validation_disabled(
        self, mock_fetcher, mock_get_settings, client, mock_settings, sample_content
    ):
        """Test content generation with validation disabled"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        with patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler') as mock_assembler:
            mock_assembler_instance = Mock()
            mock_assembler_instance.generate_newsletter.return_value = {'subject': 'test', 'html': 'test', 'text': 'test'}
            mock_assembler_instance.generate_web_update.return_value = {'title': 'test', 'content': 'test', 'excerpt': 'test'}
            mock_assembler_instance.generate_social_posts.return_value = []
            mock_assembler.return_value = mock_assembler_instance

            response = client.post(
                "/v2/generate-content",
                json={
                    "send_email": False,
                    "publish_web": False,
                    "generate_social": False,
                    "preview_only": True
                },
                params={"validate_content": False}
            )

            assert response.status_code == 200

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_generate_enhanced_content_error_handling(
        self, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test error handling in content generation"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.side_effect = Exception("Fetch failed")
        mock_fetcher.return_value = mock_fetcher_instance

        response = client.post(
            "/v2/generate-content",
            json={"preview_only": True}
        )

        assert response.status_code == 500
        assert "Fetch failed" in response.json()['detail']

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.ContentValidator')
    @pytest.mark.asyncio
    async def test_content_validation_with_issues(
        self, mock_validator, mock_fetcher, mock_get_settings, client,
        mock_settings, sample_content
    ):
        """Test content generation when validation finds issues"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate_content.return_value = (False, ["Content is stale", "Missing sections"])
        mock_validator_instance.enhance_categorization.return_value = sample_content
        mock_validator_instance.sanitize_content.return_value = sample_content
        mock_validator_instance.generate_content_summary.return_value = "Content has issues"
        mock_validator.return_value = mock_validator_instance

        with patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler') as mock_assembler:
            mock_assembler_instance = Mock()
            mock_assembler_instance.generate_newsletter.return_value = {'subject': 'test', 'html': 'test', 'text': 'test'}
            mock_assembler_instance.generate_web_update.return_value = {'title': 'test', 'content': 'test', 'excerpt': 'test'}
            mock_assembler_instance.generate_social_posts.return_value = []
            mock_assembler.return_value = mock_assembler_instance

            response = client.post(
                "/v2/generate-content",
                json={
                    "send_email": True,
                    "preview_only": True
                },
                params={"validate_content": True}
            )

            assert response.status_code == 200


class TestListAvailableTemplates:
    """Test list available templates endpoint"""

    def test_list_available_templates(self, client):
        """Test listing available templates"""
        response = client.get("/v2/templates")

        assert response.status_code == 200
        data = response.json()

        # Check email templates
        assert 'email_templates' in data
        assert len(data['email_templates']) == 3

        template_ids = [t['id'] for t in data['email_templates']]
        assert 'modern' in template_ids
        assert 'minimal' in template_ids
        assert 'plain' in template_ids

        # Check social platforms
        assert 'social_platforms' in data
        assert len(data['social_platforms']) == 4

        platform_ids = [p['id'] for p in data['social_platforms']]
        assert 'twitter' in platform_ids
        assert 'linkedin' in platform_ids
        assert 'instagram' in platform_ids
        assert 'facebook' in platform_ids

    def test_template_structure(self, client):
        """Test template response structure"""
        response = client.get("/v2/templates")
        data = response.json()

        # Check email template structure
        for template in data['email_templates']:
            assert 'id' in template
            assert 'name' in template
            assert 'description' in template
            assert 'features' in template
            assert 'best_for' in template

        # Check social platform structure
        for platform in data['social_platforms']:
            assert 'id' in platform
            assert 'name' in platform
            assert 'character_limit' in platform
            assert 'features' in platform
            assert 'content_types' in platform


class TestValidateContent:
    """Test validate content endpoint"""

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.ContentValidator')
    @pytest.mark.asyncio
    async def test_validate_content_success(
        self, mock_validator, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test successful content validation"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_validator_instance = Mock()
        mock_validator_instance.validate_content.return_value = (True, [])
        mock_validator_instance.generate_content_summary.return_value = "All content looks good"
        mock_validator.return_value = mock_validator_instance

        response = client.post("/v2/validate-content")

        assert response.status_code == 200
        data = response.json()
        assert data['is_valid'] is True
        assert data['issues'] == []
        assert data['summary'] == "All content looks good"
        assert 'recommendations' in data

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.ContentValidator')
    @pytest.mark.asyncio
    async def test_validate_content_with_issues(
        self, mock_validator, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test content validation with issues found"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        issues = ["Content is stale", "duplicate content found", "Missing required sections"]
        mock_validator_instance = Mock()
        mock_validator_instance.validate_content.return_value = (False, issues)
        mock_validator_instance.generate_content_summary.return_value = "Content needs improvement"
        mock_validator.return_value = mock_validator_instance

        response = client.post("/v2/validate-content")

        assert response.status_code == 200
        data = response.json()
        assert data['is_valid'] is False
        assert len(data['issues']) == 3
        assert "stale" in str(data['issues'])
        assert data['recommendations']['add_more_content'] is True
        assert data['recommendations']['refresh_stale'] is True
        assert data['recommendations']['fix_duplicates'] is True

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_validate_content_error(
        self, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test content validation error handling"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.side_effect = Exception("Validation failed")
        mock_fetcher.return_value = mock_fetcher_instance

        response = client.post("/v2/validate-content")

        assert response.status_code == 500
        assert "Validation failed" in response.json()['detail']


class TestPreviewSocialPost:
    """Test preview social post endpoint"""

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_social_post_success(
        self, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test successful social post preview"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_post = {
            'platform': 'twitter',
            'content': 'Test tweet content',
            'type': 'announcement',
            'media_suggestions': []
        }

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_social_posts.return_value = [mock_post]
        mock_assembler.return_value = mock_assembler_instance

        response = client.get(
            "/v2/social-preview/twitter",
            params={
                "category": "breathscape",
                "post_type": "announcement"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['platform'] == 'twitter'
        assert data['content'] == 'Test tweet content'
        assert 'preview' in data
        assert 'character_count' in data['preview']
        assert 'platform_limit' in data['preview']
        assert 'fits_limit' in data['preview']
        assert 'requires_media' in data['preview']

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_social_post_no_content(
        self, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test social post preview when no content available"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_social_posts.return_value = []
        mock_assembler.return_value = mock_assembler_instance

        response = client.get("/v2/social-preview/twitter")

        assert response.status_code == 200
        data = response.json()
        assert 'error' in data
        assert 'twitter' in data['error']

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_preview_social_post_error(
        self, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test social post preview error handling"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.side_effect = Exception("Preview failed")
        mock_fetcher.return_value = mock_fetcher_instance

        response = client.get("/v2/social-preview/twitter")

        assert response.status_code == 500
        assert "Preview failed" in response.json()['detail']

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_social_post_character_limits(
        self, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test social post preview with different platform character limits"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        # Test with different platforms
        platforms = ['twitter', 'linkedin', 'instagram', 'facebook']
        expected_limits = [280, 3000, 2200, 63206]

        for platform, limit in zip(platforms, expected_limits):
            mock_post = {
                'platform': platform,
                'content': 'Test content',
                'media_suggestions': []
            }

            mock_assembler_instance = Mock()
            mock_assembler_instance.generate_social_posts.return_value = [mock_post]
            mock_assembler.return_value = mock_assembler_instance

            response = client.get(f"/v2/social-preview/{platform}")

            assert response.status_code == 200
            data = response.json()
            assert data['preview']['platform_limit'] == limit

    @patch('halcytone_content_generator.api.endpoints_v2.get_settings')
    @patch('halcytone_content_generator.api.endpoints_v2.DocumentFetcher')
    @patch('halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_social_post_with_media(
        self, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content
    ):
        """Test social post preview with media suggestions"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = sample_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_post = {
            'platform': 'instagram',
            'content': 'Test content',
            'media_suggestions': ['image1.jpg', 'image2.jpg']
        }

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_social_posts.return_value = [mock_post]
        mock_assembler.return_value = mock_assembler_instance

        response = client.get("/v2/social-preview/instagram")

        assert response.status_code == 200
        data = response.json()
        assert data['preview']['requires_media'] is True