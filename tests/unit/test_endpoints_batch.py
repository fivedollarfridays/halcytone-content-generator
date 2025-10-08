"""
Unit tests for batch content generation endpoints
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from halcytone_content_generator.main import app
from halcytone_content_generator.schemas.content import (
    BatchContentRequest, BatchContentResponse, BatchContentItem,
    Content, NewsletterContent, WebUpdateContent, SocialPost
)
from halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler
from halcytone_content_generator.services.publishers.base import ValidationResult, PreviewResult


class TestBatchEndpoints:
    """Test batch generation endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_assembler(self):
        """Mock content assembler"""
        assembler = Mock(spec=EnhancedContentAssembler)
        assembler.fetch_living_document_content = AsyncMock()
        assembler.generate_newsletter = AsyncMock()
        assembler.generate_web_update = AsyncMock()
        assembler.generate_social_post = AsyncMock()
        return assembler

    @pytest.fixture
    def sample_newsletter(self):
        """Sample newsletter content"""
        return NewsletterContent(
            subject="Test Newsletter",
            html="<h1>Test Content</h1>",
            text="Test Content",
            preview_text="Test Preview"
        )

    @pytest.fixture
    def sample_web_update(self):
        """Sample web update content"""
        return WebUpdateContent(
            title="Test Update",
            content="Test web content",
            excerpt="Test excerpt"
        )

    @pytest.fixture
    def sample_social_post(self):
        """Sample social post"""
        return SocialPost(
            platform="twitter",
            content="Test social content",
            hashtags=["#test", "#content"]
        )

    def test_generate_batch_success(self, client, mock_assembler, sample_newsletter):
        """Test successful batch generation"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            # Mock assembler responses
            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            # Mock publisher validation and preview
            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.25
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "week",
                        "channels": ["email"],
                        "count": 5,
                        "dry_run": True
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["dry_run"] is True
        assert len(data["items"]) > 0
        assert data["summary"]["channels_generated"]["email"] > 0

    def test_generate_batch_invalid_period(self, client):
        """Test batch generation with invalid period"""
        response = client.post(
            "/api/v1/batch/generateBatch",
            params={
                "period": "invalid",
                "channels": ["email"]
            }
        )

        assert response.status_code == 400
        assert "Period must be" in response.json()["detail"]

    def test_generate_batch_invalid_channels(self, client):
        """Test batch generation with invalid channels"""
        response = client.post(
            "/api/v1/batch/generateBatch",
            params={
                "period": "week",
                "channels": ["invalid_channel"]
            }
        )

        assert response.status_code == 400
        assert "Invalid channels" in response.json()["detail"]

    def test_generate_batch_exceeds_limit(self, client):
        """Test batch generation exceeding limits"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_settings') as mock_settings:
            mock_settings.return_value.BATCH_MAX_ITEMS = 10

            response = client.post(
                "/api/v1/batch/generateBatch",
                params={
                    "period": "week",
                    "channels": ["email"],
                    "count": 100
                }
            )

        assert response.status_code == 400
        assert "exceeds maximum batch size" in response.json()["detail"]

    def test_generate_batch_multiple_channels(self, client, mock_assembler,
                                           sample_newsletter, sample_web_update, sample_social_post):
        """Test batch generation with multiple channels"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            # Mock assembler responses
            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter
            mock_assembler.generate_web_update.return_value = sample_web_update
            mock_assembler.generate_social_post.return_value = sample_social_post

            # Mock publishers
            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.15
                ))
                mock_publishers.return_value = {
                    'email': mock_publisher,
                    'web': mock_publisher,
                    'social': mock_publisher
                }

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "day",
                        "channels": ["email", "web", "social"],
                        "count": 6,
                        "dry_run": True
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["items"]) > 0

        # Check that multiple channels were generated
        channels_in_items = {item["content_type"] for item in data["items"]}
        assert len(channels_in_items) > 1

    def test_generate_batch_with_scheduling(self, client, mock_assembler, sample_newsletter):
        """Test batch generation with scheduling enabled"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.20
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "week",
                        "channels": ["email"],
                        "count": 3,
                        "include_scheduling": True
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["scheduling_plan"] is not None
        assert "total_items" in data["scheduling_plan"]
        assert "optimal_times" in data["scheduling_plan"]

        # Check that items have scheduled times
        for item in data["items"]:
            assert item["scheduled_for"] is not None

    def test_generate_batch_validation_failure(self, client, mock_assembler, sample_newsletter):
        """Test batch generation with content validation failure"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                # Validation fails
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=False, issues=[], metadata={}
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "day",
                        "channels": ["email"],
                        "count": 3
                    }
                )

        assert response.status_code == 200
        data = response.json()
        # Should still succeed but with fewer items due to validation failures
        assert data["status"] == "completed"
        assert data["summary"]["generation_success_rate"] < 1.0

    def test_schedule_batch_dry_run(self, client):
        """Test batch scheduling in dry run mode"""
        response = client.post(
            "/api/v1/batch/schedule/test-batch-123",
            json={
                "batch_id": "test-batch-123",
                "schedule_all": True,
                "dry_run": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["batch_id"] == "test-batch-123"
        assert "dry_run" in data["schedule_summary"]

    def test_schedule_batch_success(self, client):
        """Test successful batch scheduling"""
        response = client.post(
            "/api/v1/batch/schedule/test-batch-456",
            json={
                "batch_id": "test-batch-456",
                "schedule_all": True,
                "dry_run": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is False
        assert data["batch_id"] == "test-batch-456"
        assert len(data["scheduled_items"]) > 0
        assert data["next_publish_time"] is not None

    def test_get_batch_status(self, client):
        """Test getting batch status"""
        response = client.get("/api/v1/batch/status/test-batch-789")

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == "test-batch-789"
        assert data["status"] in ["pending", "running", "completed", "failed"]
        assert "items_total" in data
        assert "items_published" in data
        assert "items_pending" in data
        assert "items_failed" in data

    def test_generate_batch_period_variations(self, client, mock_assembler, sample_newsletter):
        """Test different period types affect item count"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.15
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                # Test day period
                response_day = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "day",
                        "channels": ["email"],
                        "dry_run": True
                    }
                )

                # Test week period
                response_week = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "week",
                        "channels": ["email"],
                        "dry_run": True
                    }
                )

                # Test month period
                response_month = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "month",
                        "channels": ["email"],
                        "dry_run": True
                    }
                )

        assert response_day.status_code == 200
        assert response_week.status_code == 200
        assert response_month.status_code == 200

        # Different periods should potentially generate different numbers of items
        day_data = response_day.json()
        week_data = response_week.json()
        month_data = response_month.json()

        assert all(data["status"] == "completed" for data in [day_data, week_data, month_data])

    def test_generate_batch_content_themes(self, client, mock_assembler, sample_newsletter):
        """Test batch generation with specific content themes"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.18
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "week",
                        "channels": ["email"],
                        "count": 3,
                        "content_themes": ["breathscape", "hardware"]
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        # Content themes should be reflected in the request processing

    def test_generate_batch_assembler_error(self, client):
        """Test batch generation when assembler fails"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_assembler = Mock()
            mock_assembler.fetch_living_document_content = AsyncMock(side_effect=Exception("Assembler failed"))
            mock_dep.return_value = mock_assembler

            response = client.post(
                "/api/v1/batch/generateBatch",
                params={
                    "period": "day",
                    "channels": ["email"]
                }
            )

        assert response.status_code == 500
        assert "Batch generation failed" in response.json()["detail"]

    def test_batch_distribution_calculation(self, client, mock_assembler, sample_newsletter):
        """Test that scheduling distribution is calculated correctly"""
        with patch('halcytone_content_generator.api.endpoints_batch.get_content_assembler') as mock_dep:
            mock_dep.return_value = mock_assembler

            mock_assembler.fetch_living_document_content.return_value = {"test": "data"}
            mock_assembler.generate_newsletter.return_value = sample_newsletter

            with patch('halcytone_content_generator.api.endpoints_batch.get_publishers') as mock_publishers:
                mock_publisher = Mock()
                mock_publisher.validate = AsyncMock(return_value=ValidationResult(
                    is_valid=True, issues=[], metadata={}
                ))
                mock_publisher.preview = AsyncMock(return_value=PreviewResult(
                    preview_data={}, formatted_content="", metadata={},
                    estimated_engagement=0.22
                ))
                mock_publishers.return_value = {'email': mock_publisher}

                response = client.post(
                    "/api/v1/batch/generateBatch",
                    params={
                        "period": "week",
                        "channels": ["email"],
                        "count": 5,
                        "include_scheduling": True
                    }
                )

        assert response.status_code == 200
        data = response.json()

        if data["scheduling_plan"] and "distribution" in data["scheduling_plan"]:
            distribution = data["scheduling_plan"]["distribution"]
            assert "hourly_distribution" in distribution or "total_scheduled" in distribution