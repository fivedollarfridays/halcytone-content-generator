"""
Unit tests for main API endpoints
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, BackgroundTasks

from src.halcytone_content_generator.api.endpoints import router
from src.halcytone_content_generator.schemas.content import ContentGenerationRequest, ContentGenerationResponse
from fastapi import FastAPI


@pytest.fixture
def app():
    """Create FastAPI app with router for testing"""
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
    settings.SERVICE_NAME = "content-generator"
    settings.ENVIRONMENT = "test"
    settings.LIVING_DOC_TYPE = "google_docs"
    settings.CRM_BASE_URL = "https://api.crm.test"
    settings.CRM_API_KEY = "test_crm_key"
    settings.PLATFORM_BASE_URL = "https://api.platform.test"
    settings.PLATFORM_API_KEY = "test_platform_key"
    settings.OPENAI_API_KEY = "test_openai_key"
    settings.SOCIAL_PLATFORMS = ["twitter", "linkedin"]
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
        'excerpt': 'Test excerpt'
    }


@pytest.fixture
def sample_social_posts():
    """Sample social posts for testing"""
    return [
        {
            'platform': 'twitter',
            'content': 'Test tweet'
        },
        {
            'platform': 'linkedin',
            'content': 'Test LinkedIn post'
        }
    ]


class TestGenerateContent:
    """Test generate content endpoint"""

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @patch('src.halcytone_content_generator.api.endpoints.CRMClient')
    @patch('src.halcytone_content_generator.api.endpoints.PlatformClient')
    @pytest.mark.asyncio
    async def test_generate_content_preview_only(
        self, mock_platform_client, mock_crm_client, mock_assembler,
        mock_fetcher, mock_get_settings, client, mock_settings,
        sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test content generation in preview mode"""
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

        # Make request
        response = client.post(
            "/generate-content",
            json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": True,
                "include_preview": True
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'preview'
        assert 'newsletter' in data
        assert 'web_update' in data
        assert 'social_posts' in data
        assert data['newsletter']['subject'] == 'Test Newsletter'
        assert data['web_update']['title'] == 'Test Update'
        assert len(data['social_posts']) == 2

        # Verify services were called correctly
        mock_fetcher_instance.fetch_content.assert_called_once()
        mock_assembler_instance.generate_newsletter.assert_called_once_with(sample_content)
        mock_assembler_instance.generate_web_update.assert_called_once_with(sample_content)
        mock_assembler_instance.generate_social_posts.assert_called_once_with(sample_content)

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @patch('src.halcytone_content_generator.api.endpoints.CRMClient')
    @patch('src.halcytone_content_generator.api.endpoints.PlatformClient')
    @pytest.mark.asyncio
    async def test_generate_content_full_flow(
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
            "/generate-content",
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

        # Verify external services were called
        mock_crm_instance.send_newsletter.assert_called_once_with(
            sample_newsletter['subject'],
            sample_newsletter['html'],
            sample_newsletter['text']
        )
        mock_platform_instance.publish_update.assert_called_once_with(
            sample_web_update['title'],
            sample_web_update['content'],
            sample_web_update['excerpt']
        )

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @pytest.mark.asyncio
    async def test_generate_content_partial_flow(
        self, mock_assembler, mock_fetcher, mock_get_settings, client,
        mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test content generation with only some channels enabled"""
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

        # Make request with only email enabled
        response = client.post(
            "/generate-content",
            json={
                "send_email": False,
                "publish_web": False,
                "generate_social": False,
                "preview_only": True
            }
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'preview'

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_generate_content_error_handling(
        self, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test error handling in content generation"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.side_effect = Exception("Fetch failed")
        mock_fetcher.return_value = mock_fetcher_instance

        response = client.post(
            "/generate-content",
            json={"preview_only": True}
        )

        assert response.status_code == 500
        assert "Fetch failed" in response.json()['detail']

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @patch('src.halcytone_content_generator.api.endpoints.CRMClient')
    @pytest.mark.asyncio
    async def test_generate_content_email_only(
        self, mock_crm_client, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test content generation with only email enabled"""
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
        mock_crm_instance.send_newsletter.return_value = {'sent': 50, 'failed': 0}
        mock_crm_client.return_value = mock_crm_instance

        # Make request with only email
        response = client.post(
            "/generate-content",
            json={
                "send_email": True,
                "publish_web": False,
                "generate_social": False,
                "preview_only": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'email' in data['results']
        assert 'web' not in data['results']

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @patch('src.halcytone_content_generator.api.endpoints.PlatformClient')
    @pytest.mark.asyncio
    async def test_generate_content_web_only(
        self, mock_platform_client, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test content generation with only web publishing enabled"""
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

        mock_platform_instance = AsyncMock()
        mock_platform_instance.publish_update.return_value = {'id': 'web123'}
        mock_platform_client.return_value = mock_platform_instance

        # Make request with only web
        response = client.post(
            "/generate-content",
            json={
                "send_email": False,
                "publish_web": True,
                "generate_social": False,
                "preview_only": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'web' in data['results']
        assert 'email' not in data['results']

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @patch('src.halcytone_content_generator.api.endpoints.CRMClient')
    @pytest.mark.asyncio
    async def test_generate_content_email_error(
        self, mock_crm_client, mock_assembler, mock_fetcher, mock_get_settings,
        client, mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test handling email sending errors"""
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
        mock_crm_instance.send_newsletter.side_effect = Exception("Email failed")
        mock_crm_client.return_value = mock_crm_instance

        response = client.post(
            "/generate-content",
            json={
                "send_email": True,
                "publish_web": False,
                "preview_only": False
            }
        )

        assert response.status_code == 500


class TestPreviewContent:
    """Test preview content endpoint"""

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_content_success(
        self, mock_assembler, mock_fetcher, mock_get_settings, client,
        mock_settings, sample_content, sample_newsletter, sample_web_update, sample_social_posts
    ):
        """Test successful content preview"""
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

        response = client.get("/preview")

        assert response.status_code == 200
        data = response.json()
        assert 'newsletter' in data
        assert 'web_update' in data
        assert 'social_posts' in data
        assert 'content_summary' in data

        # Check content summary
        summary = data['content_summary']
        assert summary['breathscape'] == 1
        assert summary['hardware'] == 1
        assert summary['tips'] == 1
        assert summary['vision'] == 1

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @pytest.mark.asyncio
    async def test_preview_content_error(
        self, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test content preview error handling"""
        mock_get_settings.return_value = mock_settings

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.side_effect = Exception("Preview failed")
        mock_fetcher.return_value = mock_fetcher_instance

        response = client.get("/preview")

        assert response.status_code == 500
        assert "Preview failed" in response.json()['detail']

    @patch('src.halcytone_content_generator.api.endpoints.get_settings')
    @patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher')
    @patch('src.halcytone_content_generator.api.endpoints.ContentAssembler')
    @pytest.mark.asyncio
    async def test_preview_content_empty(
        self, mock_assembler, mock_fetcher, mock_get_settings, client, mock_settings
    ):
        """Test content preview with empty content"""
        # Setup mocks
        mock_get_settings.return_value = mock_settings

        empty_content = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        mock_fetcher_instance = AsyncMock()
        mock_fetcher_instance.fetch_content.return_value = empty_content
        mock_fetcher.return_value = mock_fetcher_instance

        mock_assembler_instance = Mock()
        mock_assembler_instance.generate_newsletter.return_value = {'subject': '', 'html': '', 'text': ''}
        mock_assembler_instance.generate_web_update.return_value = {'title': '', 'content': '', 'excerpt': ''}
        mock_assembler_instance.generate_social_posts.return_value = []
        mock_assembler.return_value = mock_assembler_instance

        response = client.get("/preview")

        assert response.status_code == 200
        data = response.json()
        assert data['content_summary']['breathscape'] == 0
        assert data['content_summary']['hardware'] == 0
        assert data['content_summary']['tips'] == 0
        assert data['content_summary']['vision'] == 0


class TestGetStatus:
    """Test get status endpoint"""

    def test_get_status_all_configured(self, app, mock_settings):
        """Test status endpoint with all services configured"""
        from src.halcytone_content_generator.config import get_settings

        # Override dependency
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            client = TestClient(app)
            response = client.get("/status")

            assert response.status_code == 200
            data = response.json()

            assert data['service'] == "content-generator"
            assert data['environment'] == "test"
            assert data['document_source'] == "google_docs"
            assert data['crm_configured'] is True
            assert data['platform_configured'] is True
            assert data['ai_enabled'] is True
            assert data['social_platforms'] == ["twitter", "linkedin"]
        finally:
            # Clean up
            app.dependency_overrides.clear()

    def test_get_status_partially_configured(self, app):
        """Test status endpoint with some services not configured"""
        from src.halcytone_content_generator.config import get_settings

        settings = MagicMock()
        settings.SERVICE_NAME = "content-generator"
        settings.ENVIRONMENT = "test"
        settings.LIVING_DOC_TYPE = "google_docs"
        settings.CRM_BASE_URL = None
        settings.CRM_API_KEY = None
        settings.PLATFORM_BASE_URL = "https://api.platform.test"
        settings.PLATFORM_API_KEY = "test_key"
        settings.OPENAI_API_KEY = None
        settings.SOCIAL_PLATFORMS = []

        app.dependency_overrides[get_settings] = lambda: settings

        try:
            client = TestClient(app)
            response = client.get("/status")

            assert response.status_code == 200
            data = response.json()

            assert data['crm_configured'] is False
            assert data['platform_configured'] is True
            assert data['ai_enabled'] is False
            assert data['social_platforms'] == []
        finally:
            app.dependency_overrides.clear()

    def test_get_status_minimal_configuration(self, app):
        """Test status endpoint with minimal configuration"""
        from src.halcytone_content_generator.config import get_settings

        settings = MagicMock()
        settings.SERVICE_NAME = "test-service"
        settings.ENVIRONMENT = "dev"
        settings.LIVING_DOC_TYPE = "markdown"
        settings.CRM_BASE_URL = ""
        settings.CRM_API_KEY = ""
        settings.PLATFORM_BASE_URL = ""
        settings.PLATFORM_API_KEY = ""
        settings.OPENAI_API_KEY = ""
        settings.SOCIAL_PLATFORMS = ["twitter"]

        app.dependency_overrides[get_settings] = lambda: settings

        try:
            client = TestClient(app)
            response = client.get("/status")

            assert response.status_code == 200
            data = response.json()

            assert data['service'] == "test-service"
            assert data['environment'] == "dev"
            assert data['document_source'] == "markdown"
            assert data['crm_configured'] is False
            assert data['platform_configured'] is False
            assert data['ai_enabled'] is False
            assert data['social_platforms'] == ["twitter"]
        finally:
            app.dependency_overrides.clear()


class TestRequestValidation:
    """Test request validation for endpoints"""

    def test_generate_content_request_validation(self, client):
        """Test content generation request validation"""
        # Test with valid request
        response = client.post(
            "/generate-content",
            json={
                "send_email": True,
                "publish_web": False,
                "generate_social": True,
                "preview_only": True,
                "include_preview": False,
                "force_refresh": False
            }
        )

        # Should pass validation but fail on missing dependencies
        assert response.status_code in [200, 500]  # 500 due to missing mocks

        # Test with invalid field types
        response = client.post(
            "/generate-content",
            json={
                "send_email": "not_boolean",
                "publish_web": True
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_content_default_values(self, client):
        """Test that default values work correctly"""
        with patch('src.halcytone_content_generator.api.endpoints.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            with patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher:
                mock_fetcher_instance = AsyncMock()
                mock_fetcher_instance.fetch_content.return_value = {}
                mock_fetcher.return_value = mock_fetcher_instance

                with patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:
                    mock_assembler_instance = Mock()
                    mock_assembler_instance.generate_newsletter.return_value = {'subject': '', 'html': '', 'text': ''}
                    mock_assembler_instance.generate_web_update.return_value = {'title': '', 'content': '', 'excerpt': ''}
                    mock_assembler_instance.generate_social_posts.return_value = []
                    mock_assembler.return_value = mock_assembler_instance

                    with patch('src.halcytone_content_generator.api.endpoints.CRMClient') as mock_crm:
                        mock_crm_instance = AsyncMock()
                        mock_crm_instance.send_newsletter.return_value = {'sent': 10, 'failed': 0}
                        mock_crm.return_value = mock_crm_instance

                        with patch('src.halcytone_content_generator.api.endpoints.PlatformClient') as mock_platform:
                            mock_platform_instance = AsyncMock()
                            mock_platform_instance.publish_update.return_value = {'id': 'test123'}
                            mock_platform.return_value = mock_platform_instance

                            response = client.post("/generate-content", json={})

                            assert response.status_code == 200
                            data = response.json()
                            # Should use default values and successfully send
                            assert data['status'] == 'success'