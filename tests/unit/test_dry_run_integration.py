"""
Comprehensive tests for dry-run mode integration across all systems
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.schemas.content import (
    ContentGenerationRequest, Content, NewsletterContent, WebUpdateContent, SocialPost
)
from src.halcytone_content_generator.services.publishers.base import (
    ValidationResult, PreviewResult, PublishResult, PublishStatus
)
from src.halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler


class TestDryRunIntegration:
    """Test comprehensive dry-run mode integration"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_content_data(self):
        """Mock content generation data"""
        return {
            'breathscape': [{'title': 'Dry Run Update', 'content': 'Test content for dry run'}],
            'hardware': [{'title': 'Hardware Test', 'content': 'Hardware content for dry run'}],
            'tips': [{'title': 'Breathing Tip', 'content': 'Practice deep breathing for 5 minutes'}],
            'vision': [{'title': 'Vision', 'content': 'Making breathing accessible to everyone'}]
        }

    @pytest.fixture
    def mock_dry_run_publishers(self):
        """Mock publishers configured for dry-run mode"""
        mock_email = Mock()
        mock_email.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_email.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"subject": "Dry Run Email"},
            formatted_content="Dry run content",
            metadata={"channel": "email", "dry_run": True},
            estimated_reach=1000
        ))
        mock_email.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Would be sent successfully (dry run)",
            metadata={"dry_run": True, "recipients": 1000},
            external_id="dry-run-email-123"
        ))

        mock_web = Mock()
        mock_web.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_web.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"title": "Dry Run Web Update"},
            formatted_content="Dry run web content",
            metadata={"channel": "web", "dry_run": True},
            estimated_reach=2000
        ))
        mock_web.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Would be published successfully (dry run)",
            metadata={"dry_run": True, "url": "https://example.com/dry-run"},
            external_id="dry-run-web-456"
        ))

        mock_social = Mock()
        mock_social.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_social.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"platform": "twitter"},
            formatted_content="Dry run social post",
            metadata={"channel": "social", "dry_run": True},
            estimated_reach=500
        ))
        mock_social.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Would be posted successfully (dry run)",
            metadata={"dry_run": True, "platform": "twitter"},
            external_id="dry-run-social-789"
        ))

        return {
            'email': mock_email,
            'web': mock_web,
            'social': mock_social
        }

    def test_global_dry_run_configuration(self, client, mock_dry_run_publishers, mock_content_data):
        """Test global dry-run mode via configuration"""
        with patch('src.halcytone_content_generator.config.get_settings') as mock_settings, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            # Configure global dry-run mode
            settings = Mock()
            settings.DRY_RUN = True
            settings.CRM_BASE_URL = "test"
            settings.CRM_API_KEY = "test"
            settings.PLATFORM_BASE_URL = "test"
            settings.PLATFORM_API_KEY = "test"
            mock_settings.return_value = settings

            mock_get_pub.return_value = mock_dry_run_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Dry Run Newsletter',
                'html': '<h1>Dry Run</h1>',
                'text': 'Dry Run',
                'preview_text': 'Preview'
            }
            mock_content_assembler.generate_web_update.return_value = {
                'title': 'Dry Run Update',
                'content': 'Content',
                'excerpt': 'Excerpt'
            }
            mock_content_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'twitter',
                    'content': 'Dry run post',
                    'hashtags': ['#test'],
                    'media_urls': []
                }
            ]
            mock_assembler.return_value = mock_content_assembler

            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

            # Verify all channels show dry-run results
            assert "dry_run" in data["results"]["email"]["metadata"]
            assert data["results"]["email"]["metadata"]["dry_run"] is True
            assert "Would be sent successfully" in data["results"]["email"]["message"]

            assert "dry_run" in data["results"]["web"]["metadata"]
            assert data["results"]["web"]["metadata"]["dry_run"] is True

            assert "posts" in data["results"]["social"]

    def test_batch_dry_run_mode(self, client, mock_dry_run_publishers, mock_content_data):
        """Test dry-run mode in batch operations"""
        with patch('src.halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_document_fetcher') as mock_get_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_get_assembler:

            mock_get_pub.return_value = mock_dry_run_publishers

            mock_fetcher = Mock()
            mock_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_get_fetcher.return_value = mock_fetcher

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Batch Dry Run Newsletter',
                'html': '<h1>Batch Dry Run</h1>',
                'text': 'Batch Dry Run',
                'preview_text': 'Batch Preview'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Batch Dry Run Update',
                'content': 'Batch content',
                'excerpt': 'Batch excerpt'
            }
            mock_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'twitter',
                    'content': 'Batch dry run post',
                    'hashtags': ['#batch'],
                    'media_urls': []
                }
            ]
            mock_get_assembler.return_value = mock_assembler

            # Test explicit dry-run parameter
            response = client.post("/api/v1/batch/generateBatch", params={
                "period": "week",
                "channels": ["email", "web", "social"],
                "count": 3,
                "dry_run": True
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["dry_run"] is True
            assert len(data["items"]) > 0

            # Verify all batch items are marked as dry-run
            for item in data["items"]:
                assert item["content"]["dry_run"] is True

    def test_content_object_dry_run_propagation(self):
        """Test that dry-run flag propagates through Content objects"""
        # Test NewsletterContent
        newsletter = NewsletterContent(
            subject="Test",
            html="<h1>Test</h1>",
            text="Test"
        )

        content = Content.from_newsletter(newsletter, dry_run=True)
        assert content.dry_run is True
        assert content.content_type == "email"

        # Test WebUpdateContent
        web_update = WebUpdateContent(
            title="Test Update",
            content="Test content",
            excerpt="Test excerpt"
        )

        content = Content.from_web_update(web_update, dry_run=True)
        assert content.dry_run is True
        assert content.content_type == "web"

        # Test SocialPost
        social_post = SocialPost(
            platform="twitter",
            content="Test post",
            hashtags=["#test"]
        )

        content = Content.from_social_post(social_post, dry_run=True)
        assert content.dry_run is True
        assert content.content_type == "social"

    def test_publisher_dry_run_behavior(self, mock_dry_run_publishers):
        """Test that publishers respect dry-run mode"""
        from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
        from src.halcytone_content_generator.services.publishers.web_publisher import WebPublisher
        from src.halcytone_content_generator.services.publishers.social_publisher import SocialPublisher

        config = {
            'dry_run': True,
            'crm_base_url': 'test',
            'crm_api_key': 'test',
            'platform_base_url': 'test',
            'platform_api_key': 'test'
        }

        # Test email publisher in dry-run mode
        email_pub = EmailPublisher(config)
        assert email_pub.dry_run is True

        # Test web publisher in dry-run mode
        web_pub = WebPublisher(config)
        assert web_pub.dry_run is True

        # Test social publisher in dry-run mode
        social_pub = SocialPublisher(config)
        assert social_pub.dry_run is True

    def test_breathscape_template_dry_run_integration(self, mock_content_data):
        """Test Breathscape templates work with dry-run mode"""
        assembler = EnhancedContentAssembler(template_style='breathscape')

        # Generate Breathscape content
        newsletter = assembler.generate_breathscape_newsletter(mock_content_data)
        web_content = assembler.generate_breathscape_web_content(mock_content_data)
        social_posts = assembler.generate_breathscape_social_posts(mock_content_data)

        # Create Content objects in dry-run mode
        newsletter_content = NewsletterContent(**newsletter)
        newsletter_obj = Content.from_newsletter(newsletter_content, dry_run=True)
        assert newsletter_obj.dry_run is True

        web_update_content = WebUpdateContent(**web_content)
        web_obj = Content.from_web_update(web_update_content, dry_run=True)
        assert web_obj.dry_run is True

        for post_data in social_posts:
            social_post = SocialPost(**post_data)
            social_obj = Content.from_social_post(social_post, dry_run=True)
            assert social_obj.dry_run is True

    def test_batch_scheduling_dry_run(self, client):
        """Test batch scheduling in dry-run mode"""
        # Test dry-run scheduling
        response = client.post("/api/v1/batch/schedule/test-batch-dry-run", json={
            "batch_id": "test-batch-dry-run",
            "schedule_all": True,
            "dry_run": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "test-batch-dry-run"
        assert data["dry_run"] is True
        assert "dry_run" in data["schedule_summary"]
        assert data["schedule_summary"]["dry_run"] is True

        # Test non-dry-run scheduling
        response = client.post("/api/v1/batch/schedule/test-batch-live", json={
            "batch_id": "test-batch-live",
            "schedule_all": True,
            "dry_run": False
        })

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "test-batch-live"
        assert data["dry_run"] is False

    def test_dry_run_with_validation_failures(self, client, mock_content_data):
        """Test dry-run mode when validation fails"""
        from src.halcytone_content_generator.services.publishers.base import ValidationIssue, ValidationSeverity

        # Create publisher that fails validation
        mock_publisher = Mock()
        mock_publisher.validate = AsyncMock(return_value=ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Content validation failed in dry-run",
                field="content"
            )],
            metadata={"dry_run": True}
        ))

        mock_publishers = {
            'email': mock_publisher,
            'web': mock_publisher,
            'social': mock_publisher
        }

        with patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Validation Test',
                'html': '<h1>Invalid</h1>',
                'text': 'Invalid'
            }
            mock_content_assembler.generate_web_update.return_value = {}
            mock_content_assembler.generate_social_posts.return_value = []
            mock_assembler.return_value = mock_content_assembler

            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["results"]["email"]["status"] == "validation_failed"
            assert len(data["results"]["email"]["issues"]) > 0

    def test_dry_run_environment_variables(self):
        """Test dry-run configuration from environment"""
        from src.halcytone_content_generator.config import Settings

        # Test with DRY_RUN enabled
        with patch.dict('os.environ', {'DRY_RUN': 'true'}):
            settings = Settings()
            assert settings.DRY_RUN is True

        # Test with DRY_RUN disabled
        with patch.dict('os.environ', {'DRY_RUN': 'false'}):
            settings = Settings()
            assert settings.DRY_RUN is False

    def test_preview_mode_vs_dry_run_mode(self, client, mock_dry_run_publishers, mock_content_data):
        """Test the difference between preview mode and dry-run mode"""
        with patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            mock_get_pub.return_value = mock_dry_run_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Preview vs Dry Run Test',
                'html': '<h1>Test</h1>',
                'text': 'Test'
            }
            mock_content_assembler.generate_web_update.return_value = {
                'title': 'Test Update',
                'content': 'Content',
                'excerpt': 'Excerpt'
            }
            mock_content_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'twitter',
                    'content': 'Test post',
                    'hashtags': ['#test'],
                    'media_urls': []
                }
            ]
            mock_assembler.return_value = mock_content_assembler

            # Test preview mode (should not call publishers)
            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": True
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "preview"
            assert "newsletter" in data
            assert "web_update" in data
            assert "social_posts" in data
            # In preview mode, no results from publishers
            assert "results" not in data or not data.get("results")

            # Reset mocks
            for publisher in mock_dry_run_publishers.values():
                publisher.publish.reset_mock()

            # Test dry-run mode (should call publishers but in dry-run)
            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "results" in data
            # In dry-run mode, publishers are called but don't actually send
            assert "Would be sent successfully" in data["results"]["email"]["message"]

    def test_comprehensive_dry_run_workflow(self, client, mock_dry_run_publishers, mock_content_data):
        """Test complete dry-run workflow from content generation to batch processing"""
        with patch('src.halcytone_content_generator.config.get_settings') as mock_settings, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_batch_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_document_fetcher') as mock_batch_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_batch_assembler:

            # Configure global dry-run
            settings = Mock()
            settings.DRY_RUN = True
            settings.CRM_BASE_URL = "test"
            settings.CRM_API_KEY = "test"
            settings.PLATFORM_BASE_URL = "test"
            settings.PLATFORM_API_KEY = "test"
            mock_settings.return_value = settings

            # Configure mocks for both endpoints and batch
            mock_get_pub.return_value = mock_dry_run_publishers
            mock_batch_get_pub.return_value = mock_dry_run_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher
            mock_batch_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Comprehensive Dry Run Test',
                'html': '<h1>Comprehensive Test</h1>',
                'text': 'Comprehensive Test'
            }
            mock_content_assembler.generate_web_update.return_value = {
                'title': 'Comprehensive Update',
                'content': 'Content',
                'excerpt': 'Excerpt'
            }
            mock_content_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'twitter',
                    'content': 'Comprehensive post',
                    'hashtags': ['#comprehensive'],
                    'media_urls': []
                }
            ]
            mock_assembler.return_value = mock_content_assembler
            mock_batch_assembler.return_value = mock_content_assembler

            # Step 1: Test individual content generation in dry-run
            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert all("dry_run" in result["metadata"] for result in data["results"].values()
                      if isinstance(result, dict) and "metadata" in result)

            # Step 2: Test batch generation in dry-run
            response = client.post("/api/v1/batch/generateBatch", params={
                "period": "week",
                "channels": ["email", "web", "social"],
                "count": 5,
                "dry_run": True
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["dry_run"] is True
            assert all(item["content"]["dry_run"] for item in data["items"])

            # Step 3: Test batch scheduling in dry-run
            response = client.post("/api/v1/batch/schedule/comprehensive-test", json={
                "batch_id": "comprehensive-test",
                "schedule_all": True,
                "dry_run": True
            })

            assert response.status_code == 200
            data = response.json()
            assert data["dry_run"] is True