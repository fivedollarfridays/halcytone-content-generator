"""
Integration tests for Publisher pattern in endpoints and batch operations
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.schemas.content import (
    ContentGenerationRequest, NewsletterContent, WebUpdateContent, SocialPost
)
from src.halcytone_content_generator.services.publishers.base import (
    ValidationResult, PreviewResult, PublishResult, PublishStatus,
    ValidationIssue, ValidationSeverity
)


class TestPublisherIntegration:
    """Test Publisher pattern integration across endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_publishers(self):
        """Mock all publishers with successful operations"""
        mock_email = Mock()
        mock_email.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_email.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"subject": "Test Subject"},
            formatted_content="Test HTML",
            metadata={"channel": "email"},
            estimated_reach=1000,
            estimated_engagement=0.25
        ))
        mock_email.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Email sent successfully",
            external_id="email-123",
            metadata={"recipients": 1000}
        ))

        mock_web = Mock()
        mock_web.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_web.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"title": "Test Web Update"},
            formatted_content="Test web content",
            metadata={"channel": "web", "reading_time": "5 minutes"},
            estimated_reach=2000,
            estimated_engagement=0.15,
            word_count=500,
            character_count=2500
        ))
        mock_web.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Web update published",
            external_id="web-456",
            metadata={"url": "https://example.com/post/456"}
        ))

        mock_social = Mock()
        mock_social.validate = AsyncMock(return_value=ValidationResult(
            is_valid=True, issues=[], metadata={}
        ))
        mock_social.preview = AsyncMock(return_value=PreviewResult(
            preview_data={"platform": "twitter", "platform_tips": ["Keep it concise"]},
            formatted_content="Test social post #test",
            metadata={"channel": "social"},
            estimated_reach=500,
            estimated_engagement=0.12,
            character_count=30
        ))
        mock_social.publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.SUCCESS,
            message="Social post scheduled",
            external_id="social-789",
            metadata={"platform": "twitter", "manual_posting_required": True}
        ))

        return {
            'email': mock_email,
            'web': mock_web,
            'social': mock_social
        }

    @pytest.fixture
    def mock_content_data(self):
        """Mock content generation data"""
        return {
            'breathscape': [{'title': 'Breathscape Update', 'content': 'Latest breathing techniques'}],
            'hardware': [{'title': 'Hardware News', 'content': 'New sensor released'}],
            'tips': [{'title': 'Daily Tip', 'content': 'Practice deep breathing'}],
            'vision': [{'title': 'Our Vision', 'content': 'Healthier breathing for all'}]
        }

    def test_v1_endpoint_publisher_integration(self, client, mock_publishers, mock_content_data):
        """Test v1 endpoint with Publisher pattern"""
        with patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            # Setup mocks
            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test</h1>',
                'text': 'Test',
                'preview_text': 'Preview'
            }
            mock_content_assembler.generate_web_update.return_value = {
                'title': 'Test Update',
                'content': 'Test content',
                'excerpt': 'Test excerpt'
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

            # Test request
            response = client.post("/api/v1/generate-content", json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "email" in data["results"]
            assert "web" in data["results"]
            assert "social" in data["results"]
            assert data["results"]["email"]["status"] == "success"
            assert data["results"]["web"]["status"] == "success"

    def test_v1_endpoint_validation_failure(self, client, mock_publishers, mock_content_data):
        """Test v1 endpoint with validation failure"""
        # Make email validation fail
        mock_publishers['email'].validate = AsyncMock(return_value=ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Subject line too short",
                field="subject"
            )],
            metadata={}
        ))

        with patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Hi',  # Too short
                'html': '<h1>Test</h1>',
                'text': 'Test'
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

    def test_v2_endpoint_enhanced_features(self, client, mock_publishers, mock_content_data):
        """Test v2 endpoint with enhanced Publisher features"""
        with patch('src.halcytone_content_generator.api.endpoints_v2.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints_v2.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints_v2.EnhancedContentAssembler') as mock_assembler, \
             patch('src.halcytone_content_generator.api.endpoints_v2.ContentValidator') as mock_validator:

            # Setup mocks
            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Enhanced Newsletter',
                'html': '<h1>Enhanced Test</h1>',
                'text': 'Enhanced Test',
                'preview_text': 'Enhanced Preview'
            }
            mock_content_assembler.generate_web_update.return_value = {
                'title': 'Enhanced Update',
                'content': 'Enhanced content',
                'excerpt': 'Enhanced excerpt',
                'meta_description': 'SEO description',
                'tags': ['seo', 'test'],
                'reading_time': 5,
                'word_count': 500
            }
            mock_content_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'linkedin',
                    'content': 'Professional post',
                    'hashtags': ['#professional'],
                    'media_urls': []
                }
            ]
            mock_assembler.return_value = mock_content_assembler

            mock_content_validator = Mock()
            mock_content_validator.validate_content.return_value = (True, [])
            mock_content_validator.enhance_categorization.return_value = mock_content_data
            mock_content_validator.sanitize_content.return_value = mock_content_data
            mock_content_validator.generate_content_summary.return_value = {"total_items": 4}
            mock_validator.return_value = mock_content_validator

            # Test request with enhanced features
            response = client.post("/api/v2/generate-content", params={
                "template_style": "modern",
                "social_platforms": ["linkedin", "twitter"],
                "seo_optimize": True,
                "validate_content": True
            }, json={
                "send_email": True,
                "publish_web": True,
                "generate_social": True,
                "preview_only": False
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "email" in data["results"]
            assert "web" in data["results"]
            assert "social" in data["results"]

            # Check enhanced features
            web_result = data["results"]["web"]
            assert "seo" in web_result
            assert web_result["seo"]["word_count"] is not None

            social_result = data["results"]["social"]
            assert "enhanced_features" in social_result
            assert social_result["enhanced_features"]["validation_enabled"] is True

    def test_batch_endpoint_publisher_integration(self, client, mock_publishers, mock_content_data):
        """Test batch endpoint with Publisher pattern"""
        with patch('src.halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_document_fetcher') as mock_get_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_get_assembler:

            # Setup mocks
            mock_get_pub.return_value = mock_publishers

            mock_fetcher = Mock()
            mock_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_get_fetcher.return_value = mock_fetcher

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {
                'subject': 'Batch Newsletter',
                'html': '<h1>Batch Test</h1>',
                'text': 'Batch Test',
                'preview_text': 'Batch Preview'
            }
            mock_assembler.generate_web_update.return_value = {
                'title': 'Batch Update',
                'content': 'Batch content',
                'excerpt': 'Batch excerpt'
            }
            mock_assembler.generate_social_posts.return_value = [
                {
                    'platform': 'twitter',
                    'content': 'Batch post',
                    'hashtags': ['#batch'],
                    'media_urls': []
                }
            ]
            mock_get_assembler.return_value = mock_assembler

            # Test batch generation
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
            assert len(data["items"]) > 0

            # Verify Publisher validation was called
            for item in data["items"]:
                assert item["content"]["dry_run"] is True
                assert "metadata" in item

    def test_dry_run_integration(self, client, mock_publishers, mock_content_data):
        """Test dry-run integration across all endpoints"""
        # Configure publishers for dry-run mode
        for publisher in mock_publishers.values():
            publisher.publish = AsyncMock(return_value=PublishResult(
                status=PublishStatus.SUCCESS,
                message="Would be published (dry run)",
                external_id="dry-run-123",
                metadata={"dry_run": True}
            ))

        with patch('src.halcytone_content_generator.config.get_settings') as mock_settings, \
             patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            # Enable dry-run in settings
            settings = Mock()
            settings.DRY_RUN = True
            settings.CRM_BASE_URL = "test"
            settings.CRM_API_KEY = "test"
            settings.PLATFORM_BASE_URL = "test"
            settings.PLATFORM_API_KEY = "test"
            mock_settings.return_value = settings

            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Dry Run Newsletter',
                'html': '<h1>Dry Run</h1>',
                'text': 'Dry Run'
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
            assert "dry_run" in data["results"]["email"]["metadata"]

    def test_publisher_error_handling(self, client, mock_publishers, mock_content_data):
        """Test error handling in Publisher operations"""
        # Make publish operation fail
        mock_publishers['email'].publish = AsyncMock(return_value=PublishResult(
            status=PublishStatus.FAILED,
            message="CRM service unavailable",
            metadata={},
            errors=["Connection timeout"]
        ))

        with patch('src.halcytone_content_generator.api.endpoints.get_publishers') as mock_get_pub, \
             patch('src.halcytone_content_generator.api.endpoints.DocumentFetcher') as mock_fetcher, \
             patch('src.halcytone_content_generator.api.endpoints.ContentAssembler') as mock_assembler:

            mock_get_pub.return_value = mock_publishers

            mock_doc_fetcher = Mock()
            mock_doc_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
            mock_fetcher.return_value = mock_doc_fetcher

            mock_content_assembler = Mock()
            mock_content_assembler.generate_newsletter.return_value = {
                'subject': 'Test Newsletter',
                'html': '<h1>Test</h1>',
                'text': 'Test'
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
            assert data["results"]["email"]["status"] == "failed"
            assert "CRM service unavailable" in data["results"]["email"]["message"]

    def test_batch_scheduling_integration(self, client):
        """Test batch scheduling endpoints"""
        # Test scheduling
        response = client.post("/api/v1/batch/schedule/test-batch-123", json={
            "batch_id": "test-batch-123",
            "schedule_all": True,
            "dry_run": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "test-batch-123"
        assert data["dry_run"] is True

        # Test status
        response = client.get("/api/v1/batch/status/test-batch-123")
        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "test-batch-123"
        assert "status" in data

    def test_comprehensive_validation_scenarios(self, client, mock_publishers, mock_content_data):
        """Test comprehensive validation scenarios across all publishers"""
        # Test different validation scenarios
        test_cases = [
            {
                "name": "email_critical_error",
                "publisher": "email",
                "validation": ValidationResult(
                    is_valid=False,
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        message="HTML content corrupted",
                        field="html"
                    )],
                    metadata={}
                )
            },
            {
                "name": "web_warning_only",
                "publisher": "web",
                "validation": ValidationResult(
                    is_valid=True,
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Title could be more SEO-friendly",
                        field="title"
                    )],
                    metadata={}
                )
            },
            {
                "name": "social_info_message",
                "publisher": "social",
                "validation": ValidationResult(
                    is_valid=True,
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        message="Consider adding more hashtags",
                        field="hashtags"
                    )],
                    metadata={}
                )
            }
        ]

        for test_case in test_cases:
            # Reset mocks
            for pub in mock_publishers.values():
                pub.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))

            # Set specific validation for this test
            mock_publishers[test_case["publisher"]].validate = AsyncMock(
                return_value=test_case["validation"]
            )

            with patch('src.halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_get_pub, \
                 patch('src.halcytone_content_generator.api.endpoints_batch.get_document_fetcher') as mock_get_fetcher, \
                 patch('src.halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_get_assembler:

                mock_get_pub.return_value = mock_publishers

                mock_fetcher = Mock()
                mock_fetcher.fetch_content = AsyncMock(return_value=mock_content_data)
                mock_get_fetcher.return_value = mock_fetcher

                mock_assembler = Mock()
                mock_assembler.generate_newsletter.return_value = {
                    'subject': 'Test',
                    'html': '<h1>Test</h1>',
                    'text': 'Test'
                }
                mock_assembler.generate_web_update.return_value = {
                    'title': 'Test',
                    'content': 'Test',
                    'excerpt': 'Test'
                }
                mock_assembler.generate_social_posts.return_value = [
                    {
                        'platform': 'twitter',
                        'content': 'Test',
                        'hashtags': ['#test'],
                        'media_urls': []
                    }
                ]
                mock_get_assembler.return_value = mock_assembler

                response = client.post("/api/v1/batch/generateBatch", params={
                    "period": "day",
                    "channels": [test_case["publisher"]],
                    "count": 1
                })

                assert response.status_code == 200
                data = response.json()

                if test_case["validation"].is_valid:
                    assert len(data["items"]) > 0
                else:
                    # Critical errors should prevent item creation
                    if any(issue.severity == ValidationSeverity.CRITICAL
                           for issue in test_case["validation"].issues):
                        assert data["summary"]["generation_success_rate"] < 1.0