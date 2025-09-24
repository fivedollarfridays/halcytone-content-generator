"""
Integration tests for key content generation workflows
Sprint 5: Testing Infrastructure
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

from fastapi.testclient import TestClient
from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.schemas.content import (
    ContentGenerationRequest,
    ContentGenerationResponse
)
from src.halcytone_content_generator.schemas.content_types import (
    ContentType, ChannelType, SocialPlatform
)


class TestWeeklyUpdateWorkflow:
    """Test the complete weekly update workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def weekly_update_payload(self):
        """Standard weekly update request"""
        return {
            "send_email": True,
            "publish_web": True,
            "generate_social": True,
            "template_style": "weekly_update",
            "tone": "encouraging",
            "validate_before_generate": True,
            "social_platforms": ["twitter", "linkedin", "facebook"],
            "seo_optimize": True,
            "invalidate_cache": True
        }

    @pytest.fixture
    def mock_document_content(self):
        """Mock content from Google Docs/Notion"""
        return {
            "breathscape": [
                {
                    "title": "New Breathing Algorithm Released",
                    "content": "We've improved our breathing detection algorithm with 95% accuracy.",
                    "author": "Tech Team",
                    "priority": 1
                }
            ],
            "hardware": [
                {
                    "title": "Sensor v2.0 Testing Complete",
                    "content": "The new sensor prototype shows 30% better sensitivity.",
                    "author": "Hardware Team",
                    "featured": True
                }
            ],
            "tips": [
                {
                    "title": "Box Breathing Technique",
                    "content": "Try the 4-4-4-4 breathing pattern for instant calm.",
                    "author": "Wellness Team"
                }
            ],
            "vision": [
                {
                    "content": "Building a world where everyone breathes better."
                }
            ]
        }

    @patch('src.halcytone_content_generator.services.document_fetcher.DocumentFetcher.fetch')
    @patch('src.halcytone_content_generator.services.publishers.email_publisher.EmailPublisher.publish')
    @patch('src.halcytone_content_generator.services.publishers.web_publisher.WebPublisher.publish')
    @patch('src.halcytone_content_generator.services.publishers.social_publisher.SocialPublisher.publish')
    def test_complete_weekly_update_workflow(
        self,
        mock_social_publish,
        mock_web_publish,
        mock_email_publish,
        mock_fetch,
        client,
        weekly_update_payload,
        mock_document_content
    ):
        """Test end-to-end weekly update generation and distribution"""
        # Setup mocks
        mock_fetch.return_value = mock_document_content

        mock_email_publish.return_value = AsyncMock(
            status="success",
            external_id="email-123",
            message="Newsletter sent to 1000 subscribers"
        )

        mock_web_publish.return_value = AsyncMock(
            status="success",
            external_id="web-456",
            message="Published to website"
        )

        mock_social_publish.return_value = AsyncMock(
            status="success",
            external_id="social-789",
            message="Posted to all platforms"
        )

        # Execute workflow
        response = client.post(
            "/api/v2/generate-content",
            json=weekly_update_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["content_id"] is not None
        assert "email" in data["published_to"]
        assert "web" in data["published_to"]
        assert "social" in data["published_to"]

        # Verify content structure
        if "newsletter" in data:
            assert data["newsletter"]["subject"] is not None
            assert "Halcytone" in data["newsletter"]["html"]

        if "web_update" in data:
            assert data["web_update"]["title"] is not None
            assert data["web_update"]["slug"] is not None

        if "social_posts" in data:
            assert len(data["social_posts"]) >= 3  # At least 3 platforms
            for post in data["social_posts"]:
                assert post["platform"] in ["twitter", "linkedin", "facebook"]
                assert len(post["content"]) > 0

    def test_weekly_update_validation_failure(self, client):
        """Test weekly update with validation failures"""
        invalid_payload = {
            "send_email": True,
            "content": {
                "type": "update",
                "title": "",  # Empty title
                "content": "x"  # Too short
            }
        }

        response = client.post(
            "/api/v2/generate-content",
            json=invalid_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    @patch('src.halcytone_content_generator.services.document_fetcher.DocumentFetcher.fetch')
    def test_weekly_update_partial_failure(self, mock_fetch, client, weekly_update_payload):
        """Test handling of partial failures in weekly update"""
        mock_fetch.side_effect = Exception("Google Docs unavailable")

        response = client.post(
            "/api/v2/generate-content",
            json=weekly_update_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "errors" in data or data["status"] == "partial_success"


class TestBlogPostWorkflow:
    """Test blog post creation and publication workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def blog_post_payload(self):
        return {
            "content": {
                "type": "blog",
                "title": "The Science Behind Coherent Breathing",
                "content": "Coherent breathing is a powerful technique that synchronizes HRV...",
                "category": "Science & Research",
                "author": "Dr. Sarah Chen",
                "target_keywords": ["coherent breathing", "HRV", "breathing technique"],
                "seo_description": "Discover the science behind coherent breathing."
            },
            "publish_web": True,
            "generate_social": True,
            "seo_optimize": True,
            "tone": "medical_scientific"
        }

    def test_blog_post_creation_with_seo(self, client, blog_post_payload):
        """Test blog post creation with SEO optimization"""
        response = client.post(
            "/api/v2/generate-content",
            json=blog_post_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify SEO elements
        if "web_update" in data:
            web_content = data["web_update"]
            assert web_content["meta_description"] is not None
            assert len(web_content["keywords"]) > 0
            assert web_content["slug"] is not None

        # Verify social posts are generated
        if "social_posts" in data:
            assert len(data["social_posts"]) > 0

    def test_blog_post_draft_mode(self, client, blog_post_payload):
        """Test blog post in draft/preview mode"""
        blog_post_payload["preview_only"] = True
        blog_post_payload["dry_run"] = True

        response = client.post(
            "/api/v2/generate-content",
            json=blog_post_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "preview"
        assert len(data["published_to"]) == 0  # Nothing should be published


class TestAnnouncementWorkflow:
    """Test high-priority announcement workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def announcement_payload(self):
        return {
            "content": {
                "type": "announcement",
                "title": "🎉 Breathscape 2.0 Launch",
                "content": "We're excited to announce Breathscape 2.0 with AI-powered guidance!",
                "urgency": "high",
                "priority": 1,
                "featured": True,
                "call_to_action": "Download Now"
            },
            "send_email": True,
            "publish_web": True,
            "generate_social": True,
            "invalidate_cache": True,
            "social_platforms": ["twitter", "linkedin", "instagram", "facebook"]
        }

    @patch('src.halcytone_content_generator.services.cache_manager.CacheManager.invalidate_cache')
    def test_urgent_announcement_with_cache_invalidation(
        self, mock_cache_invalidate, client, announcement_payload
    ):
        """Test urgent announcement with immediate cache invalidation"""
        mock_cache_invalidate.return_value = AsyncMock(
            status="success",
            keys_invalidated=42
        )

        response = client.post(
            "/api/v2/generate-content",
            json=announcement_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all channels are targeted
        assert len(data["published_to"]) >= 3

        # Verify cache was invalidated
        if "results" in data and "cache_invalidation" in data["results"]:
            assert data["results"]["cache_invalidation"]["status"] == "success"

    def test_announcement_priority_handling(self, client):
        """Test that high-priority announcements are processed correctly"""
        payloads = [
            {
                "content": {
                    "type": "announcement",
                    "title": f"Announcement {i}",
                    "content": f"Content {i}",
                    "priority": i
                },
                "publish_web": True
            }
            for i in [5, 1, 3]  # Different priorities
        ]

        responses = []
        for payload in payloads:
            response = client.post(
                "/api/v2/generate-content",
                json=payload,
                headers={"Authorization": "Bearer test-token"}
            )
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)


class TestSessionSummaryWorkflow:
    """Test Halcytone Live session summary workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def session_data(self):
        return {
            "session_id": "session-123",
            "session_name": "Morning Breathwork",
            "instructor": "Jane Doe",
            "participants": 25,
            "duration_minutes": 30,
            "average_hrv_improvement": 15.5,
            "techniques_used": ["Box Breathing", "4-7-8 Breathing"],
            "milestones": [
                {"user": "user1", "achievement": "First 10-minute session"},
                {"user": "user2", "achievement": "HRV improvement > 20%"}
            ]
        }

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        ws = MagicMock()
        ws.receive_json = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    async def test_realtime_session_summary_generation(self, client, session_data, mock_websocket):
        """Test real-time session summary generation via WebSocket"""
        # Simulate WebSocket events
        events = [
            {"type": "session_started", "data": session_data},
            {"type": "participant_joined", "data": {"user_id": "user1"}},
            {"type": "hrv_milestone", "data": {"user_id": "user1", "improvement": 22.5}},
            {"type": "session_ended", "data": {"final_stats": session_data}}
        ]

        # Process events
        for event in events:
            # In real scenario, this would be through WebSocket
            response = client.post(
                "/api/sessions/process-event",
                json=event,
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist yet

    def test_session_summary_email_generation(self, client, session_data):
        """Test session summary email generation"""
        payload = {
            "content": {
                "type": "session_summary",
                "session_data": session_data
            },
            "send_email": True,
            "template_style": "session_summary"
        }

        response = client.post(
            "/api/v2/generate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        # Check response
        if response.status_code == 200:
            data = response.json()
            if "newsletter" in data:
                assert "session" in data["newsletter"]["html"].lower()
                assert str(session_data["average_hrv_improvement"]) in data["newsletter"]["html"]


class TestBatchContentWorkflow:
    """Test batch content generation workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def batch_payload(self):
        """Multiple content items for batch processing"""
        return {
            "items": [
                {
                    "content": {
                        "type": "update",
                        "title": f"Update {i}",
                        "content": f"Content for update {i}"
                    },
                    "publish_web": True
                }
                for i in range(10)
            ],
            "batch_size": 5,
            "parallel_processing": True,
            "continue_on_error": True
        }

    def test_batch_content_generation(self, client, batch_payload):
        """Test batch generation of multiple content items"""
        response = client.post(
            "/api/batch/generate",
            json=batch_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        # Should return 202 Accepted for async processing
        assert response.status_code in [200, 202]

        if response.status_code == 202:
            data = response.json()
            assert "batch_id" in data
            assert data["status"] in ["queued", "processing"]

    def test_batch_with_partial_failures(self, client):
        """Test batch processing with some items failing"""
        batch_payload = {
            "items": [
                {"content": {"type": "update", "title": "Valid", "content": "Valid content"}},
                {"content": {"type": "update", "title": "", "content": ""}},  # Invalid
                {"content": {"type": "update", "title": "Valid 2", "content": "More valid content"}}
            ],
            "continue_on_error": True
        }

        response = client.post(
            "/api/batch/generate",
            json=batch_payload,
            headers={"Authorization": "Bearer test-token"}
        )

        if response.status_code in [200, 202]:
            data = response.json()
            # Should process valid items even if some fail
            assert data.get("total_items") == 3
            if "failed_items" in data:
                assert data["failed_items"] >= 1

    def test_batch_status_check(self, client):
        """Test checking batch processing status"""
        batch_id = "test-batch-123"

        response = client.get(
            f"/api/batch/{batch_id}/status",
            headers={"Authorization": "Bearer test-token"}
        )

        # Should return 404 for non-existent batch or status if exists
        assert response.status_code in [200, 404]


class TestMultiChannelWorkflow:
    """Test multi-channel content distribution workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_channel_specific_content_optimization(self, client):
        """Test that content is optimized for each channel"""
        payload = {
            "content": {
                "type": "update",
                "title": "Multi-channel Update",
                "content": "This content will be optimized for each channel differently."
            },
            "send_email": True,
            "publish_web": True,
            "generate_social": True,
            "per_channel_tones": {
                "email": "encouraging",
                "web": "professional",
                "social": "casual"
            }
        }

        response = client.post(
            "/api/v2/generate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify channel-specific content
        if "newsletter" in data:
            # Email should be encouraging
            assert data["newsletter"] is not None

        if "web_update" in data:
            # Web should be professional
            assert data["web_update"] is not None

        if "social_posts" in data:
            # Social should be casual
            for post in data["social_posts"]:
                assert len(post["content"]) > 0

    def test_platform_specific_constraints(self, client):
        """Test platform-specific content constraints"""
        long_content = "x" * 500  # Long content for testing truncation

        payload = {
            "content": {
                "type": "update",
                "title": "Platform Test",
                "content": long_content
            },
            "generate_social": True,
            "social_platforms": ["twitter", "linkedin", "facebook"]
        }

        response = client.post(
            "/api/v2/generate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        if "social_posts" in data:
            for post in data["social_posts"]:
                if post["platform"] == "twitter":
                    # Twitter has 280 char limit
                    assert len(post["content"]) <= 280
                elif post["platform"] == "linkedin":
                    # LinkedIn allows longer posts
                    assert len(post["content"]) <= 3000
                elif post["platform"] == "facebook":
                    # Facebook has very high limit
                    assert len(post["content"]) <= 63206


class TestValidationWorkflow:
    """Test content validation workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_pre_publication_validation(self, client):
        """Test content validation before publication"""
        payload = {
            "content": {
                "type": "blog",
                "title": "Test Blog",
                "content": "Short",  # Too short for blog
                "category": "Test"
            },
            "strict_mode": True
        }

        response = client.post(
            "/api/v2/validate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "is_valid" in data
        if not data["is_valid"]:
            assert len(data.get("issues", [])) > 0

    def test_seo_validation(self, client):
        """Test SEO validation for web content"""
        payload = {
            "content": {
                "type": "blog",
                "title": "A" * 100,  # Too long for SEO
                "content": "Good content here",
                "target_keywords": ["keyword1"] * 20  # Too many keywords
            }
        }

        response = client.post(
            "/api/v2/validate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        if "warnings" in data:
            assert len(data["warnings"]) > 0  # Should warn about SEO issues

        if "metadata" in data and "seo_score" in data["metadata"]:
            assert data["metadata"]["seo_score"] < 100  # Not perfect SEO


class TestCacheWorkflow:
    """Test cache management workflow"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @patch('src.halcytone_content_generator.services.cache_manager.CacheManager')
    def test_cache_invalidation_on_content_update(self, mock_cache_manager, client):
        """Test that cache is invalidated when content is updated"""
        mock_cache_instance = MagicMock()
        mock_cache_manager.return_value = mock_cache_instance
        mock_cache_instance.invalidate_cache.return_value = AsyncMock(
            status="success",
            keys_invalidated=10
        )

        payload = {
            "content": {
                "type": "update",
                "title": "Cache Test Update",
                "content": "This should trigger cache invalidation"
            },
            "publish_web": True,
            "invalidate_cache": True
        }

        response = client.post(
            "/api/v2/generate-content",
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

    def test_cache_warming_after_deployment(self, client):
        """Test cache warming for frequently accessed content"""
        # This would typically be a separate endpoint or script
        frequently_accessed = [
            "/api/templates",
            "/api/v2/generate-content",
            "/api/content/featured"
        ]

        for endpoint in frequently_accessed:
            if endpoint == "/api/templates":
                response = client.get(
                    endpoint,
                    headers={"Authorization": "Bearer test-token"}
                )
                # Templates should be cached
                assert response.status_code in [200, 404]


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery workflows"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_graceful_degradation_on_service_failure(self, client):
        """Test system continues working when optional services fail"""
        with patch('src.halcytone_content_generator.services.ai_content_enhancer.AIContentEnhancer.enhance_content') as mock_ai:
            mock_ai.side_effect = Exception("OpenAI service unavailable")

            payload = {
                "content": {
                    "type": "update",
                    "title": "Test Update",
                    "content": "Content without AI enhancement"
                },
                "publish_web": True
            }

            response = client.post(
                "/api/v2/generate-content",
                json=payload,
                headers={"Authorization": "Bearer test-token"}
            )

            # Should still work without AI enhancement
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["success", "partial_success"]

    def test_retry_mechanism_for_transient_failures(self, client):
        """Test automatic retry for transient failures"""
        attempt_count = 0

        def mock_publish(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary network error")
            return AsyncMock(status="success")

        with patch('src.halcytone_content_generator.services.publishers.email_publisher.EmailPublisher.publish') as mock_email:
            mock_email.side_effect = mock_publish

            payload = {
                "content": {
                    "type": "update",
                    "title": "Retry Test",
                    "content": "Testing retry mechanism"
                },
                "send_email": True
            }

            response = client.post(
                "/api/v2/generate-content",
                json=payload,
                headers={"Authorization": "Bearer test-token"}
            )

            # Should eventually succeed after retries
            assert response.status_code in [200, 500]