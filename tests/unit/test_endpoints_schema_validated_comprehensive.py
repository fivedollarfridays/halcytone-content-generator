"""
Comprehensive test suite for endpoints_schema_validated API endpoints
Coverage target: 70%+

Note: Sprint 3 endpoints (session-summary, live-announce, session content)
require additional service dependencies (SessionSummaryGenerator, websocket_manager,
breathscape_event_listener) which need to be fully implemented and tested separately.
This test suite focuses on core content generation and validation endpoints.
"""

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any

from halcytone_content_generator.api.endpoints_schema_validated import (
    SchemaValidatedEndpoints,
    router,
    endpoints as endpoints_instance
)
from halcytone_content_generator.schemas.content_types import (
    ContentRequestStrict,
    ContentResponseStrict,
    ContentValidationResult,
    ContentType,
    ChannelType,
    TemplateStyle,
    SocialPlatform,
    UpdateContentStrict,
    SessionContentStrict
)
from halcytone_content_generator.config import Settings


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = Mock(spec=Settings)
    settings.CRM_BASE_URL = "https://crm.example.com"
    settings.CRM_API_KEY = "crm_key_123"
    settings.PLATFORM_BASE_URL = "https://platform.example.com"
    settings.PLATFORM_API_KEY = "platform_key_123"
    settings.DRY_RUN = False
    return settings


@pytest.fixture
def schema_endpoints():
    """Create SchemaValidatedEndpoints instance"""
    return SchemaValidatedEndpoints()


@pytest.fixture
def sample_update_content():
    """Sample update content for testing"""
    return UpdateContentStrict(
        title="Test Update",
        content="This is test content for the update.",
        tags=["test", "update"],
        channels=[ChannelType.EMAIL, ChannelType.WEB],
        dry_run=False
    )


@pytest.fixture
def content_request(sample_update_content):
    """Sample content request"""
    return ContentRequestStrict(
        content=sample_update_content,
        validate_before_publish=True,
        override_validation=False
    )


@pytest.fixture
def mock_validation_result():
    """Mock validation result"""
    return ContentValidationResult(
        is_valid=True,
        content_type=ContentType.UPDATE,
        issues=[],
        warnings=[]
    )


# ============================================================================
# SchemaValidatedEndpoints Class Tests
# ============================================================================

class TestSchemaValidatedEndpointsClass:
    """Test SchemaValidatedEndpoints class"""

    def test_initialization(self, schema_endpoints):
        """Test endpoints class initialization"""
        assert schema_endpoints.validator is not None
        from halcytone_content_generator.services.schema_validator import SchemaValidator
        assert isinstance(schema_endpoints.validator, SchemaValidator)

    def test_get_publishers(self, schema_endpoints, mock_settings):
        """Test get_publishers returns all publishers"""
        publishers = schema_endpoints.get_publishers(mock_settings)

        assert 'email' in publishers
        assert 'web' in publishers
        assert 'social' in publishers

        # Verify publisher configuration
        from halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
        from halcytone_content_generator.services.publishers.web_publisher import WebPublisher
        from halcytone_content_generator.services.publishers.social_publisher import SocialPublisher

        assert isinstance(publishers['email'], EmailPublisher)
        assert isinstance(publishers['web'], WebPublisher)
        assert isinstance(publishers['social'], SocialPublisher)

    def test_get_publishers_with_dry_run(self, schema_endpoints):
        """Test get_publishers respects dry_run setting"""
        settings = Mock(spec=Settings)
        settings.CRM_BASE_URL = "https://crm.test"
        settings.CRM_API_KEY = "test_key"
        settings.PLATFORM_BASE_URL = "https://platform.test"
        settings.PLATFORM_API_KEY = "test_key"
        settings.DRY_RUN = True

        publishers = schema_endpoints.get_publishers(settings)

        assert len(publishers) == 3


# ============================================================================
# Validate Content Endpoint Tests
# ============================================================================

class TestValidateContentEndpoint:
    """Test /validate-content endpoint"""

    @pytest.mark.asyncio
    async def test_validate_content_success(self, content_request, mock_settings, mock_validation_result):
        """Test successful content validation"""
        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=mock_validation_result):
            from halcytone_content_generator.api.endpoints_schema_validated import validate_content_only

            result = await validate_content_only(content_request, mock_settings)

            assert result.is_valid is True
            assert result.content_type == ContentType.UPDATE
            assert len(result.issues) == 0

    @pytest.mark.asyncio
    async def test_validate_content_with_issues(self, content_request, mock_settings):
        """Test content validation with issues"""
        invalid_result = ContentValidationResult(
            is_valid=False,
            content_type=ContentType.UPDATE,
            issues=["Title too short", "Missing tags"],
            warnings=[]
        )

        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=invalid_result):
            from halcytone_content_generator.api.endpoints_schema_validated import validate_content_only

            result = await validate_content_only(content_request, mock_settings)

            assert result.is_valid is False
            assert len(result.issues) == 2
            assert "Title too short" in result.issues

    @pytest.mark.asyncio
    async def test_validate_content_with_warnings(self, content_request, mock_settings):
        """Test content validation with warnings"""
        result_with_warnings = ContentValidationResult(
            is_valid=True,
            content_type=ContentType.UPDATE,
            issues=[],
            warnings=["Recommended to add excerpt"]
        )

        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=result_with_warnings):
            from halcytone_content_generator.api.endpoints_schema_validated import validate_content_only

            result = await validate_content_only(content_request, mock_settings)

            assert result.is_valid is True
            assert len(result.warnings) == 1

    @pytest.mark.asyncio
    async def test_validate_content_exception(self, content_request, mock_settings):
        """Test content validation with exception"""
        with patch.object(endpoints_instance.validator, 'validate_content_structure', side_effect=Exception("Validation error")):
            from halcytone_content_generator.api.endpoints_schema_validated import validate_content_only
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await validate_content_only(content_request, mock_settings)

            assert exc_info.value.status_code == 500
            assert "Content validation failed" in str(exc_info.value.detail)


# ============================================================================
# Generate Content Endpoint Tests
# ============================================================================

class TestGenerateContentEndpoint:
    """Test /generate-content endpoint"""

    @pytest.mark.asyncio
    async def test_generate_content_validation_failure(self, content_request, mock_settings):
        """Test content generation stops on validation failure"""
        invalid_result = ContentValidationResult(
            is_valid=False,
            content_type=ContentType.UPDATE,
            issues=["Content too short"],
            warnings=[]
        )

        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=invalid_result), \
             patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler'):
            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                content_request,
                background_tasks,
                settings=mock_settings
            )

            # When validation fails, the function returns validation_failed or continues depending on logic
            # From the code, it returns ContentResponseStrict with validation_failed status
            assert result.status in ["validation_failed", "publish_failed"]
            assert len(result.errors) > 0 or result.validation_result is not None

    @pytest.mark.asyncio
    async def test_generate_content_with_override(self, content_request, mock_settings, mock_validation_result):
        """Test content generation with validation override"""
        # Set override flag
        content_request.override_validation = True

        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=mock_validation_result), \
             patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_newsletter_content', return_value=(True, [], {'subject': 'Test', 'html': '<html></html>', 'text': 'text'})), \
             patch.object(endpoints_instance.validator, 'validate_web_content', return_value=(True, [], {'title': 'Test', 'content': 'Content'})):

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {'subject': 'Test', 'html': '<html></html>', 'text': 'text'}
            mock_assembler.generate_web_update.return_value = {'title': 'Test', 'content': 'Content'}
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                content_request,
                background_tasks,
                settings=mock_settings
            )

            assert result.status == "success"
            assert ChannelType.EMAIL in result.published_to or ChannelType.WEB in result.published_to

    @pytest.mark.asyncio
    async def test_generate_content_email_channel(self, mock_settings):
        """Test generating content for email channel"""
        email_content = UpdateContentStrict(
            title="Email Test",
            content="Email content",
            tags=["email"],
            channels=[ChannelType.EMAIL],
            dry_run=False
        )
        request = ContentRequestStrict(
            content=email_content,
            validate_before_publish=False,
            override_validation=False
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_newsletter_content', return_value=(True, [], {'subject': 'Test', 'html': '<html></html>', 'text': 'text', 'template_style': 'modern'})):

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {'subject': 'Test Email', 'html': '<html>Content</html>', 'text': 'Content'}
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                request,
                background_tasks,
                template_style=TemplateStyle.MODERN,
                settings=mock_settings
            )

            assert result.newsletter is not None
            assert ChannelType.EMAIL in result.published_to

    @pytest.mark.asyncio
    async def test_generate_content_web_channel(self, mock_settings):
        """Test generating content for web channel"""
        web_content = UpdateContentStrict(
            title="Web Test",
            content="Web content",
            tags=["web"],
            excerpt="Test excerpt",
            channels=[ChannelType.WEB],
            dry_run=False
        )
        request = ContentRequestStrict(
            content=web_content,
            validate_before_publish=False,
            override_validation=False
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_web_content', return_value=(True, [], {'title': 'Test', 'content': 'Content'})):

            mock_assembler = Mock()
            mock_assembler.generate_web_update.return_value = {'title': 'Web Test', 'content': 'Web content'}
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                request,
                background_tasks,
                seo_optimize=True,
                settings=mock_settings
            )

            assert result.web_update is not None
            assert ChannelType.WEB in result.published_to

    @pytest.mark.asyncio
    async def test_generate_content_social_channel(self, mock_settings):
        """Test generating content for social channel"""
        social_content = UpdateContentStrict(
            title="Social Test",
            content="Social content",
            tags=["social"],
            channels=[ChannelType.SOCIAL],
            dry_run=False
        )
        request = ContentRequestStrict(
            content=social_content,
            validate_before_publish=False,
            override_validation=False
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_social_content', return_value=(True, [], {'platform': 'twitter', 'content': 'Test post'})):

            mock_assembler = Mock()
            mock_assembler.generate_social_posts.return_value = [{'content': 'Test post'}]
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                request,
                background_tasks,
                social_platforms=[SocialPlatform.TWITTER, SocialPlatform.LINKEDIN],
                settings=mock_settings
            )

            assert len(result.social_posts) > 0
            assert ChannelType.SOCIAL in result.published_to

    @pytest.mark.asyncio
    async def test_generate_content_dry_run(self, content_request, mock_settings, mock_validation_result):
        """Test content generation in dry run mode"""
        content_request.content.dry_run = True

        with patch.object(endpoints_instance.validator, 'validate_content_structure', return_value=mock_validation_result), \
             patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_newsletter_content', return_value=(True, [], {'subject': 'Test', 'html': '<html></html>', 'text': 'text'})):

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {'subject': 'Test', 'html': '<html></html>', 'text': 'text'}
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                content_request,
                background_tasks,
                settings=mock_settings
            )

            assert ChannelType.PREVIEW in result.published_to
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_generate_content_partial_failure(self, mock_settings):
        """Test content generation with partial channel failure"""
        multi_channel_content = UpdateContentStrict(
            title="Multi Channel Test",
            content="Content for multiple channels",
            tags=["test"],
            channels=[ChannelType.EMAIL, ChannelType.WEB],
            dry_run=False
        )
        request = ContentRequestStrict(
            content=multi_channel_content,
            validate_before_publish=False,
            override_validation=False
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler') as mock_assembler_class, \
             patch.object(endpoints_instance.validator, 'validate_newsletter_content', return_value=(True, [], {'subject': 'Test', 'html': '<html></html>', 'text': 'text'})), \
             patch.object(endpoints_instance.validator, 'validate_web_content', return_value=(False, ["Invalid web content"], None)):

            mock_assembler = Mock()
            mock_assembler.generate_newsletter.return_value = {'subject': 'Test', 'html': '<html></html>', 'text': 'text'}
            mock_assembler.generate_web_update.return_value = {'title': 'Test', 'content': 'Content'}
            mock_assembler_class.return_value = mock_assembler

            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                request,
                background_tasks,
                settings=mock_settings
            )

            # Should succeed with warnings
            assert result.status == "success"
            assert ChannelType.EMAIL in result.published_to
            assert ChannelType.WEB in result.failed_channels
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_generate_content_exception_handling(self, content_request, mock_settings):
        """Test exception handling in content generation"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.ContentAssembler', side_effect=Exception("Assembler error")):
            from halcytone_content_generator.api.endpoints_schema_validated import generate_validated_content

            background_tasks = BackgroundTasks()
            result = await generate_validated_content(
                content_request,
                background_tasks,
                settings=mock_settings
            )

            assert result.status == "publish_failed"
            assert len(result.errors) > 0
            assert "Unexpected error" in result.errors[0]


# ============================================================================
# Content Types Endpoint Tests
# ============================================================================

class TestContentTypesEndpoint:
    """Test /content-types endpoint"""

    @pytest.mark.asyncio
    async def test_get_content_types(self):
        """Test getting supported content types"""
        from halcytone_content_generator.api.endpoints_schema_validated import get_supported_content_types

        result = await get_supported_content_types()

        assert "content_types" in result
        assert "update" in result["content_types"]
        assert "blog" in result["content_types"]
        assert "announcement" in result["content_types"]
        assert "channels" in result
        assert "templates" in result
        assert "social_platforms" in result

    @pytest.mark.asyncio
    async def test_content_types_structure(self):
        """Test content types response structure"""
        from halcytone_content_generator.api.endpoints_schema_validated import get_supported_content_types

        result = await get_supported_content_types()

        # Verify update content type
        update_type = result["content_types"]["update"]
        assert "description" in update_type
        assert "required_fields" in update_type
        assert "optional_fields" in update_type
        assert "channels" in update_type

        # Verify channels list
        assert "email" in result["channels"]
        assert "web" in result["channels"]
        assert "social" in result["channels"]


# ============================================================================
# Validation Rules Endpoint Tests
# ============================================================================

class TestValidationRulesEndpoint:
    """Test /validation-rules endpoint"""

    @pytest.mark.asyncio
    async def test_get_validation_rules(self):
        """Test getting validation rules"""
        from halcytone_content_generator.api.endpoints_schema_validated import get_validation_rules

        result = await get_validation_rules()

        assert "title" in result
        assert "content" in result
        assert "channels" in result
        assert "social_platforms" in result
        assert "newsletter" in result
        assert "seo" in result

    @pytest.mark.asyncio
    async def test_validation_rules_title_constraints(self):
        """Test title validation rule constraints"""
        from halcytone_content_generator.api.endpoints_schema_validated import get_validation_rules

        result = await get_validation_rules()

        title_rules = result["title"]
        assert title_rules["min_length"] == 1
        assert title_rules["max_length"] == 200
        assert title_rules["required"] is True

    @pytest.mark.asyncio
    async def test_validation_rules_social_platforms(self):
        """Test social platform validation rules"""
        from halcytone_content_generator.api.endpoints_schema_validated import get_validation_rules

        result = await get_validation_rules()

        social_rules = result["social_platforms"]
        assert "character_limits" in social_rules
        assert social_rules["character_limits"]["twitter"] == 280
        assert social_rules["character_limits"]["linkedin"] == 3000

        assert "hashtag_limits" in social_rules
        assert social_rules["hashtag_limits"]["twitter"] == 2
        assert social_rules["hashtag_limits"]["instagram"] == 30


# ============================================================================
# Session Summary Endpoint Tests (Sprint 3)
# ============================================================================

class TestSessionSummaryEndpoint:
    """Test /session-summary endpoint"""

    @pytest.mark.asyncio
    async def test_generate_session_summary(self, mock_settings):
        """Test generating session summary"""
        session_data = SessionContentStrict(
            session_id="session_123",
            title="Morning Meditation",
            duration_minutes=20,
            participant_count=5,
            session_type="guided",
            metrics={}
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.SessionSummaryGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_session_summary.return_value = {
                'email': {
                    'subject': 'Session Summary',
                    'html': '<html>Summary</html>',
                    'text': 'Summary',
                    'template_style': 'breathscape'
                },
                'web': {
                    'title': 'Session Summary',
                    'content': 'Session content',
                    'slug': 'session-123',
                    'seo_description': 'Session summary',
                    'keywords': ['meditation']
                },
                'social': {
                    'twitter': {
                        'content': 'Great session!',
                        'hashtags': ['meditation']
                    }
                },
                'metadata': {}
            }
            mock_generator_class.return_value = mock_generator

            from halcytone_content_generator.api.endpoints_schema_validated import generate_session_summary

            background_tasks = BackgroundTasks()
            result = await generate_session_summary(
                session_data,
                background_tasks,
                channels=[ChannelType.EMAIL, ChannelType.WEB, ChannelType.SOCIAL],
                publish_immediately=True,
                settings=mock_settings
            )

            assert result.status == "success"
            assert ChannelType.EMAIL in result.published_to
            assert result.newsletter is not None

    @pytest.mark.asyncio
    async def test_generate_session_summary_preview(self, mock_settings):
        """Test generating session summary in preview mode"""
        session_data = SessionContentStrict(
            session_id="session_456",
            title="Evening Relaxation",
            duration_minutes=15,
            participant_count=3,
            session_type="self-guided",
            metrics={}
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.SessionSummaryGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_session_summary.return_value = {
                'email': {'subject': 'Test', 'html': '<html></html>', 'text': 'text'},
                'metadata': {}
            }
            mock_generator_class.return_value = mock_generator

            from halcytone_content_generator.api.endpoints_schema_validated import generate_session_summary

            background_tasks = BackgroundTasks()
            result = await generate_session_summary(
                session_data,
                background_tasks,
                publish_immediately=False,
                settings=mock_settings
            )

            assert result.status == "preview"
            assert len(result.published_to) == 0

    @pytest.mark.asyncio
    async def test_generate_session_summary_error(self, mock_settings):
        """Test session summary generation error handling"""
        session_data = SessionContentStrict(
            session_id="session_error",
            title="Error Session",
            duration_minutes=10,
            participant_count=1,
            session_type="guided",
            metrics={}
        )

        with patch('halcytone_content_generator.api.endpoints_schema_validated.SessionSummaryGenerator', side_effect=Exception("Generator error")):
            from halcytone_content_generator.api.endpoints_schema_validated import generate_session_summary

            background_tasks = BackgroundTasks()
            result = await generate_session_summary(
                session_data,
                background_tasks,
                settings=mock_settings
            )

            assert result.status == "error"
            assert len(result.errors) > 0


# ============================================================================
# Live Announce Endpoint Tests (Sprint 3)
# ============================================================================

class TestLiveAnnounceEndpoint:
    """Test /live-announce endpoint"""

    @pytest.mark.asyncio
    async def test_broadcast_to_specific_session(self, mock_settings):
        """Test broadcasting announcement to specific session"""
        announcement = {"message": "Session starting soon", "type": "reminder"}

        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws:
            mock_ws.get_active_sessions.return_value = ["session_123"]
            mock_ws.get_session_info.return_value = {"participant_count": 5}
            mock_ws.broadcast_to_session = AsyncMock()

            from halcytone_content_generator.api.endpoints_schema_validated import broadcast_live_announcement

            result = await broadcast_live_announcement(
                announcement,
                session_id="session_123",
                settings=mock_settings
            )

            assert result["status"] == "announced"
            assert "session_123" in result["sessions_notified"]
            assert result["participant_count"] == 5

    @pytest.mark.asyncio
    async def test_broadcast_to_all_sessions(self, mock_settings):
        """Test broadcasting to all active sessions"""
        announcement = {"message": "System announcement", "type": "info"}

        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws:
            mock_ws.get_active_sessions.return_value = ["session_1", "session_2", "session_3"]
            mock_ws.get_session_info.side_effect = [
                {"participant_count": 3},
                {"participant_count": 5},
                {"participant_count": 2}
            ]
            mock_ws.broadcast_to_session = AsyncMock()

            from halcytone_content_generator.api.endpoints_schema_validated import broadcast_live_announcement

            result = await broadcast_live_announcement(
                announcement,
                broadcast_all=True,
                settings=mock_settings
            )

            assert result["status"] == "announced"
            assert len(result["sessions_notified"]) == 3
            assert result["participant_count"] == 10  # 3 + 5 + 2

    @pytest.mark.asyncio
    async def test_broadcast_invalid_parameters(self, mock_settings):
        """Test broadcast with invalid parameters"""
        from halcytone_content_generator.api.endpoints_schema_validated import broadcast_live_announcement
        from fastapi import HTTPException

        announcement = {"message": "Test"}

        with pytest.raises(HTTPException) as exc_info:
            await broadcast_live_announcement(
                announcement,
                session_id=None,
                broadcast_all=False,
                settings=mock_settings
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_broadcast_session_not_found(self, mock_settings):
        """Test broadcast to non-existent session"""
        from halcytone_content_generator.api.endpoints_schema_validated import broadcast_live_announcement
        from fastapi import HTTPException

        announcement = {"message": "Test"}

        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws:
            mock_ws.get_active_sessions.return_value = []

            with pytest.raises(HTTPException) as exc_info:
                await broadcast_live_announcement(
                    announcement,
                    session_id="nonexistent",
                    settings=mock_settings
                )

            assert exc_info.value.status_code == 404


# ============================================================================
# Get Session Content Endpoint Tests (Sprint 3)
# ============================================================================

class TestGetSessionContentEndpoint:
    """Test /session/{session_id}/content endpoint"""

    @pytest.mark.asyncio
    async def test_get_active_session_content(self, mock_settings):
        """Test getting content for active session"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws, \
             patch('halcytone_content_generator.api.endpoints_schema_validated.breathscape_event_listener') as mock_listener:

            mock_ws.get_session_info.return_value = {"active": True, "participant_count": 3}
            mock_listener.get_active_sessions_info.return_value = {
                'sessions': [
                    {
                        'session_id': 'session_123',
                        'current_metrics': {'duration': 300}
                    }
                ]
            }

            from halcytone_content_generator.api.endpoints_schema_validated import get_session_content

            result = await get_session_content(
                "session_123",
                include_summary=True,
                include_metrics=True,
                settings=mock_settings
            )

            assert result["session_id"] == "session_123"
            assert result["active"] is True
            assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_session_content_with_replay(self, mock_settings):
        """Test getting session content with replay"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws, \
             patch('halcytone_content_generator.api.endpoints_schema_validated.breathscape_event_listener') as mock_listener:

            mock_ws.get_session_info.return_value = {"active": False}
            mock_ws.get_session_replay = AsyncMock(return_value=[{"type": "message", "data": "test"}])
            mock_listener.get_active_sessions_info.return_value = {'sessions': []}

            from halcytone_content_generator.api.endpoints_schema_validated import get_session_content

            result = await get_session_content(
                "session_456",
                include_replay=True,
                settings=mock_settings
            )

            assert "replay" in result
            assert result["replay"]["message_count"] == 1


# ============================================================================
# Get Live Sessions Endpoint Tests (Sprint 3)
# ============================================================================

class TestGetLiveSessionsEndpoint:
    """Test /sessions/live endpoint"""

    @pytest.mark.asyncio
    async def test_get_live_sessions(self, mock_settings):
        """Test getting all live sessions"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws, \
             patch('halcytone_content_generator.api.endpoints_schema_validated.breathscape_event_listener') as mock_listener:

            mock_ws.get_active_sessions.return_value = ["session_1", "session_2"]
            mock_ws.get_session_info.side_effect = [
                {"participant_count": 5},
                {"participant_count": 3}
            ]
            mock_listener.get_active_sessions_info.return_value = {'sessions': []}

            from halcytone_content_generator.api.endpoints_schema_validated import get_live_sessions

            result = await get_live_sessions(
                include_metrics=False,
                settings=mock_settings
            )

            assert result["count"] == 2
            assert len(result["sessions"]) == 2
            assert result["sessions"][0]["active"] is True

    @pytest.mark.asyncio
    async def test_get_live_sessions_with_metrics(self, mock_settings):
        """Test getting live sessions with metrics"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws, \
             patch('halcytone_content_generator.api.endpoints_schema_validated.breathscape_event_listener') as mock_listener:

            mock_ws.get_active_sessions.return_value = ["session_1"]
            mock_ws.get_session_info.return_value = {"participant_count": 5}
            mock_listener.get_active_sessions_info.return_value = {
                'sessions': [
                    {
                        'session_id': 'session_1',
                        'current_metrics': {'duration': 600},
                        'started_at': '2025-10-07T10:00:00Z'
                    }
                ]
            }

            from halcytone_content_generator.api.endpoints_schema_validated import get_live_sessions

            result = await get_live_sessions(
                include_metrics=True,
                settings=mock_settings
            )

            assert result["count"] == 1
            assert "metrics" in result["sessions"][0]
            assert "started_at" in result["sessions"][0]

    @pytest.mark.asyncio
    async def test_get_live_sessions_empty(self, mock_settings):
        """Test getting live sessions when none active"""
        with patch('halcytone_content_generator.api.endpoints_schema_validated.websocket_manager') as mock_ws, \
             patch('halcytone_content_generator.api.endpoints_schema_validated.breathscape_event_listener') as mock_listener:

            mock_ws.get_active_sessions.return_value = []
            mock_listener.get_active_sessions_info.return_value = {'sessions': []}

            from halcytone_content_generator.api.endpoints_schema_validated import get_live_sessions

            result = await get_live_sessions(settings=mock_settings)

            assert result["count"] == 0
            assert result["sessions"] == []
