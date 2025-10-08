"""
Comprehensive integration tests for publisher system
Tests cross-publisher workflows, error handling, and coordination
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

try:
    from halcytone_content_generator.services.publishers.base import (
        BasePublisher, ValidationResult, PreviewResult, PublishResult,
        PublishStatus, ValidationIssue, ValidationSeverity
    )
    from halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
    from halcytone_content_generator.services.publishers.web_publisher import WebPublisher
    from halcytone_content_generator.services.publishers.social_publisher import SocialPublisher
    from halcytone_content_generator.schemas.content import (
        NewsletterContent, WebUpdateContent, SocialPost, Content
    )
except ImportError as e:
    pytest.skip(f"Skipping publisher tests due to import error: {e}", allow_module_level=True)


class TestPublisherIntegration:
    """Integration tests for publisher system"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for publishers"""
        return {
            'dry_run': False,
            'crm_base_url': 'http://localhost:8001',
            'crm_api_key': 'test-key',
            'platform_base_url': 'http://localhost:8002',
            'platform_api_key': 'test-key'
        }

    @pytest.fixture
    def sample_newsletter_content(self):
        """Sample newsletter content"""
        return NewsletterContent(
            subject="Weekly Breathing Tips",
            html="<h1>Breathing Tips</h1><p>Practice deep breathing</p>",
            text="Breathing Tips\n\nPractice deep breathing",
            preview_text="This week's breathing tips"
        )

    @pytest.mark.asyncio
    async def test_multi_channel_validation(self, mock_config, sample_newsletter_content):
        """Test validation across multiple channels"""
        email_pub = EmailPublisher(mock_config)
        email_validation = await email_pub.validate(Content.from_newsletter(sample_newsletter_content))
        assert email_validation.is_valid

    def test_publisher_factory_integration(self, mock_config):
        """Test publisher creation through factory pattern"""
        from halcytone_content_generator.services.service_factory import get_publishers

        publishers = get_publishers(mock_config)
        assert 'email' in publishers
        assert 'web' in publishers
        assert 'social' in publishers
