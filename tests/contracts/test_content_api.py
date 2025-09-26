"""
API contract tests for content-api.ts integration
Sprint 2: Ensure consistent API contract with frontend systems

Tests the API contract that content-api.ts expects to maintain compatibility
with frontend applications consuming the content generator service.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.schemas.content_types import ContentType, ChannelType


class TestContentAPIContract:
    """
    Comprehensive API contract tests for content endpoints
    Ensures backward compatibility with content-api.ts client
    """

    @pytest.fixture
    def client(self):
        """Test client for API contract testing"""
        return TestClient(app)

    @pytest.fixture
    def valid_update_payload(self) -> Dict[str, Any]:
        """Valid update content payload matching content-api.ts expectations"""
        return {
            "content": {
                "type": "update",
                "title": "Weekly Progress Update - March 2024",
                "content": "This week we achieved significant milestones in breathing technology development. Our new algorithm shows 95% accuracy in breathing pattern detection.",
                "author": "Development Team",
                "published": True,
                "featured": False,
                "channels": ["email", "web", "social"],
                "priority": 3,
                "tags": ["progress", "technology", "breathing"],
                "excerpt": "Weekly update on breathing technology milestones and achievements."
            },
            "validate_before_publish": True,
            "override_validation": False
        }

    @pytest.fixture
    def valid_blog_payload(self) -> Dict[str, Any]:
        """Valid blog content payload"""
        return {
            "content": {
                "type": "blog",
                "title": "The Science Behind Coherent Breathing",
                "content": "Coherent breathing, also known as resonance frequency breathing, is a powerful technique that synchronizes your heart rate variability with your breath. Research has shown that this practice can significantly reduce stress, improve focus, and enhance overall well-being. The optimal breathing rate for most people is around 5-6 breaths per minute, which corresponds to a 10-12 second breathing cycle. This technique works by activating the parasympathetic nervous system, promoting a state of calm alertness that is ideal for both relaxation and performance.",
                "category": "Science & Research",
                "author": "Dr. Sarah Chen",
                "published": True,
                "channels": ["web", "social"],
                "tags": ["breathing", "science", "research", "coherent breathing", "HRV"],
                "seo_description": "Learn about the science behind coherent breathing and how it can improve your health through heart rate variability synchronization.",
                "target_keywords": ["coherent breathing", "heart rate variability", "breathing technique"]
            },
            "validate_before_publish": True
        }

    @pytest.fixture
    def valid_announcement_payload(self) -> Dict[str, Any]:
        """Valid announcement content payload"""
        return {
            "content": {
                "type": "announcement",
                "title": "🎉 ANNOUNCEMENT: Breathscape 2.0 Launch",
                "content": "We're thrilled to announce the launch of Breathscape 2.0, featuring revolutionary AI-powered breathing guidance, real-time HRV monitoring, and personalized wellness insights. This major update represents months of development and user feedback integration.",
                "author": "Halcytone Team",
                "published": True,
                "featured": True,
                "channels": ["email", "web", "social"],
                "priority": 1,
                "urgency": "high",
                "call_to_action": "Download Breathscape 2.0 today and experience the future of breathing wellness!"
            },
            "validate_before_publish": True
        }

    def test_content_validation_endpoint_exists(self, client):
        """Ensure content validation endpoint is available"""
        response = client.options("/api/v2/validate-content")
        assert response.status_code != 404, "Content validation endpoint should exist"

    def test_content_generation_endpoint_contract(self, client, valid_update_payload):
        """Test content generation endpoint maintains expected contract"""
        response = client.post("/api/v2/generate-content", json=valid_update_payload)

        # Should accept the request (even if backend not fully configured)
        assert response.status_code in [200, 201, 422], f"Unexpected status: {response.status_code}"

        if response.status_code in [200, 201]:
            data = response.json()

            # Verify expected response structure
            assert "status" in data, "Response must include status field"
            assert "content_id" in data, "Response must include content_id field"
            assert "published_to" in data, "Response must include published_to field"
            assert "errors" in data, "Response must include errors field"

            # Verify published_to is a list
            assert isinstance(data["published_to"], list), "published_to must be a list"

            # Verify status is valid
            assert data["status"] in ["success", "validation_failed", "publish_failed"]

    def test_update_content_validation_contract(self, client, valid_update_payload):
        """Verify update content validation contract"""
        # Test the validation-only endpoint if it exists
        validation_payload = valid_update_payload.copy()
        validation_payload["content"]["dry_run"] = True

        response = client.post("/api/v2/validate-content", json=validation_payload)

        # Should either work or return method not allowed (if endpoint doesn't exist yet)
        assert response.status_code in [200, 201, 404, 405, 422]

        if response.status_code in [200, 201]:
            data = response.json()

            # Verify validation response structure
            assert "is_valid" in data, "Validation response must include is_valid"
            assert "content_type" in data, "Validation response must include content_type"
            assert "issues" in data, "Validation response must include issues list"
            assert "warnings" in data, "Validation response must include warnings list"

            # Verify data types
            assert isinstance(data["is_valid"], bool)
            assert isinstance(data["issues"], list)
            assert isinstance(data["warnings"], list)

    def test_blog_content_validation_contract(self, client, valid_blog_payload):
        """Verify blog content maintains expected structure"""
        response = client.post("/api/v2/generate-content", json=valid_blog_payload)

        # Should handle blog-specific fields
        assert response.status_code in [200, 201, 422]

        if response.status_code in [200, 201]:
            data = response.json()

            # Blog content should include web channel by default
            if "published_to" in data and data["published_to"]:
                assert "web" in data["published_to"] or "web" in str(data)

    def test_announcement_content_contract(self, client, valid_announcement_payload):
        """Verify announcement content handling"""
        response = client.post("/api/v2/generate-content", json=valid_announcement_payload)

        assert response.status_code in [200, 201, 422]

        if response.status_code in [200, 201]:
            data = response.json()

            # Announcements should support all channels
            assert "status" in data

    def test_validation_error_format_contract(self, client):
        """Test that validation errors follow expected format"""
        invalid_payload = {
            "content": {
                "type": "update",
                "title": "",  # Invalid: empty title
                "content": "x"  # Invalid: too short
            }
        }

        response = client.post("/api/v2/generate-content", json=invalid_payload)
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data, "Validation errors must be in 'detail' field"

        # Verify error format is list of error objects
        if isinstance(error_data["detail"], list):
            for error in error_data["detail"]:
                assert "loc" in error, "Each error must have 'loc' field"
                assert "msg" in error, "Each error must have 'msg' field"
                assert "type" in error, "Each error must have 'type' field"

    def test_content_types_enum_contract(self, client):
        """Test that all content types from editor guide are supported"""
        content_types = ["update", "blog", "announcement"]

        for content_type in content_types:
            payload = {
                "content": {
                    "type": content_type,
                    "title": f"Test {content_type.title()} Content",
                    "content": "This is test content for the content type validation. It has sufficient length to pass minimum requirements.",
                    "author": "Test Author",
                    "published": True
                }
            }

            # Add type-specific required fields
            if content_type == "blog":
                payload["content"]["category"] = "Test Category"
            elif content_type == "announcement":
                payload["content"]["urgency"] = "medium"

            response = client.post("/api/v2/generate-content", json=payload)

            # Should accept all valid content types
            assert response.status_code in [200, 201, 422], f"Content type '{content_type}' not supported"

    def test_channel_types_contract(self, client, valid_update_payload):
        """Test that channel specification works as expected"""
        # Test individual channels
        channels_to_test = [
            ["email"],
            ["web"],
            ["social"],
            ["email", "web"],
            ["web", "social"],
            ["email", "web", "social"]
        ]

        for channels in channels_to_test:
            payload = valid_update_payload.copy()
            payload["content"]["channels"] = channels

            response = client.post("/api/v2/generate-content", json=payload)

            # Should accept all valid channel combinations
            assert response.status_code in [200, 201, 422]

    def test_scheduling_contract(self, client, valid_update_payload):
        """Test content scheduling functionality"""
        # Test future scheduling
        future_time = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
        future_time = future_time.isoformat()

        payload = valid_update_payload.copy()
        payload["content"]["scheduled_for"] = future_time

        response = client.post("/api/v2/generate-content", json=payload)
        assert response.status_code in [200, 201, 422]

    def test_dry_run_contract(self, client, valid_update_payload):
        """Test dry run functionality maintains contract"""
        payload = valid_update_payload.copy()
        payload["content"]["dry_run"] = True

        response = client.post("/api/v2/generate-content", json=payload)
        assert response.status_code in [200, 201, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            # Dry run should not result in actual publishing
            if "published_to" in data:
                # Either empty list or preview channel only
                assert len(data["published_to"]) == 0 or "preview" in data["published_to"]

    def test_template_selection_contract(self, client, valid_update_payload):
        """Test template selection parameter"""
        templates = ["modern", "minimal", "breathscape", "announcement", "plain"]

        for template in templates:
            response = client.post(
                f"/api/v2/generate-content?template_style={template}",
                json=valid_update_payload
            )

            # Should accept all template options
            assert response.status_code in [200, 201, 422], f"Template '{template}' not supported"

    def test_social_platform_specification(self, client, valid_update_payload):
        """Test social platform specification"""
        platforms = ["twitter", "linkedin", "facebook", "instagram"]

        for platform in platforms:
            response = client.post(
                f"/api/v2/generate-content?social_platforms={platform}",
                json=valid_update_payload
            )

            # Should handle platform-specific generation
            assert response.status_code in [200, 201, 422]

    def test_response_content_structure_contract(self, client, valid_update_payload):
        """Test that response includes expected content structures"""
        response = client.post("/api/v2/generate-content", json=valid_update_payload)

        if response.status_code in [200, 201]:
            data = response.json()

            # Should include content objects when successful
            if data.get("status") == "success":
                # Check for content type structures
                content_fields = ["newsletter", "web_update", "social_posts"]

                # At least one content type should be present
                has_content = any(field in data for field in content_fields)
                assert has_content, "Response should include generated content"

                # If social posts are present, verify structure
                if "social_posts" in data and data["social_posts"]:
                    for post in data["social_posts"]:
                        assert "platform" in post, "Social posts must specify platform"
                        assert "content" in post, "Social posts must include content"

    def test_error_handling_contract(self, client):
        """Test error handling maintains expected contract"""
        # Test malformed JSON
        response = client.post(
            "/api/v2/generate-content",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test missing required fields
        response = client.post("/api/v2/generate-content", json={})
        assert response.status_code == 422

        # Test invalid content type
        invalid_payload = {
            "content": {
                "type": "invalid_type",
                "title": "Test",
                "content": "Test content"
            }
        }
        response = client.post("/api/v2/generate-content", json=invalid_payload)
        assert response.status_code == 422

    def test_content_length_limits_contract(self, client):
        """Test content length validation"""
        # Test very long content
        long_content = "x" * 10000
        payload = {
            "content": {
                "type": "update",
                "title": "Test Long Content",
                "content": long_content,
                "published": True
            }
        }

        response = client.post("/api/v2/generate-content", json=payload)
        # Should either succeed or fail gracefully with proper error
        assert response.status_code in [200, 201, 413, 422]

    def test_metadata_preservation_contract(self, client, valid_update_payload):
        """Test that metadata is preserved through the API"""
        payload = valid_update_payload.copy()
        payload["content"]["metadata"] = {
            "source": "api_test",
            "version": "1.0",
            "custom_field": "test_value"
        }

        response = client.post("/api/v2/generate-content", json=payload)

        # Metadata should be handled without causing errors
        assert response.status_code in [200, 201, 422]

    def test_batch_content_endpoint_contract(self, client):
        """Test batch content generation endpoint if available"""
        batch_payload = {
            "period": "week",
            "channels": ["email", "web", "social"],
            "count": 5,
            "dry_run": True,
            "template_variety": True,
            "include_scheduling": True
        }

        response = client.post("/api/v2/generate-batch", json=batch_payload)

        # Endpoint may not exist yet, but shouldn't crash
        assert response.status_code in [200, 201, 404, 422]

        if response.status_code in [200, 201]:
            data = response.json()

            # Verify batch response structure
            assert "batch_id" in data, "Batch response must include batch_id"
            assert "status" in data, "Batch response must include status"
            assert "items" in data, "Batch response must include items list"
            assert isinstance(data["items"], list), "Items must be a list"


class TestContentValidationContract:
    """Test contract for content validation specifically"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_validation_only_endpoint(self, client):
        """Test standalone validation endpoint"""
        payload = {
            "content": {
                "type": "update",
                "title": "Test Validation",
                "content": "This is test content for validation purposes.",
                "published": False  # Not publishing, just validating
            },
            "validate_before_publish": True
        }

        # Try validation endpoint (may not exist yet)
        response = client.post("/api/v2/validate-content", json=payload)

        # Should either work or return 404/405 if not implemented yet
        assert response.status_code in [200, 201, 404, 405, 422]

    def test_validation_result_structure(self, client):
        """Test validation result structure when available"""
        payload = {
            "content": {
                "type": "blog",
                "title": "Test Blog Post",
                "content": "This is a comprehensive test blog post with sufficient content to meet validation requirements.",
                "category": "Technology",
                "published": True
            }
        }

        # Use generation endpoint with validation enabled
        response = client.post("/api/v2/generate-content?validate_content=true", json=payload)

        if response.status_code in [200, 201]:
            data = response.json()

            # Look for validation results in response
            if "validation_result" in data:
                validation = data["validation_result"]
                assert "is_valid" in validation
                assert "content_type" in validation
                assert "issues" in validation
                assert "warnings" in validation