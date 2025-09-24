"""
Comprehensive tests for EmailPublisher service
Tests cover validation, preview, publishing, and error handling
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
from src.halcytone_content_generator.services.publishers.base import (
    PublishStatus, ValidationSeverity, ValidationIssue, ValidationResult,
    PreviewResult, PublishResult
)
from src.halcytone_content_generator.schemas.content import Content, NewsletterContent


class TestEmailPublisher:
    """Test EmailPublisher functionality"""

    @pytest.fixture
    def publisher_config(self):
        return {
            'crm_base_url': 'https://crm.test.com',
            'crm_api_key': 'test-key',
            'max_recipients': 5000,
            'emails_per_hour': 500,
            'campaigns_per_day': 10,
            'sender_name': 'Test Sender',
            'sender_email': 'test@example.com',
            'default_recipients': 250,
            'average_open_rate': 0.3,
            'average_click_rate': 0.08
        }

    @pytest.fixture
    def email_publisher(self, publisher_config):
        with patch('src.halcytone_content_generator.services.publishers.email_publisher.EnhancedCRMClient'), \
             patch('src.halcytone_content_generator.services.publishers.email_publisher.EmailAnalytics'):
            return EmailPublisher(config=publisher_config)

    @pytest.fixture
    def valid_email_content(self):
        """Create valid email content for testing"""
        content = MagicMock(spec=Content)
        content.content_type = "email"
        content.dry_run = False

        # Mock to_newsletter method
        newsletter = MagicMock(spec=NewsletterContent)
        newsletter.subject = "Weekly Breathscape Update"
        newsletter.html = "<h1>Weekly Update</h1><p>This week we've made exciting improvements to the platform...</p>"
        newsletter.text = "Weekly Update\n\nThis week we've made exciting improvements to the platform..."
        newsletter.preview_text = "Weekly update with platform improvements"
        newsletter.recipient_count = 1000

        content.to_newsletter.return_value = newsletter
        return content

    @pytest.fixture
    def invalid_email_content(self):
        """Create invalid email content for testing"""
        content = MagicMock(spec=Content)
        content.content_type = "web"  # Wrong type
        content.dry_run = False
        return content

    def test_init(self, email_publisher, publisher_config):
        """Test EmailPublisher initialization"""
        assert email_publisher.channel_name == "email"
        assert email_publisher.config == publisher_config
        assert email_publisher.content_limits['subject_max_length'] == 100
        assert email_publisher.rate_limits['emails_per_hour'] == 500
        assert hasattr(email_publisher, 'crm_client')
        assert hasattr(email_publisher, 'analytics')

    def test_init_default_config(self):
        """Test EmailPublisher initialization with default config"""
        with patch('src.halcytone_content_generator.services.publishers.email_publisher.EnhancedCRMClient'), \
             patch('src.halcytone_content_generator.services.publishers.email_publisher.EmailAnalytics'):
            publisher = EmailPublisher()
            assert publisher.config == {}
            assert publisher.rate_limits['emails_per_hour'] == 1000
            assert publisher.content_limits['max_recipients'] == 10000

    @pytest.mark.asyncio
    async def test_validate_valid_content(self, email_publisher, valid_email_content):
        """Test validation of valid email content"""
        result = await email_publisher.validate(valid_email_content)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.issues) == 0
        assert result.metadata['channel'] == 'email'

    @pytest.mark.asyncio
    async def test_validate_wrong_content_type(self, email_publisher, invalid_email_content):
        """Test validation of wrong content type"""
        result = await email_publisher.validate(invalid_email_content)

        assert result.is_valid is False
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.ERROR
        assert "Content type must be 'email'" in result.issues[0].message

    @pytest.mark.asyncio
    async def test_validate_missing_subject(self, email_publisher):
        """Test validation with missing subject"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = ""  # Empty subject
        newsletter.html = "<p>Valid content</p>"
        newsletter.text = "Valid text"
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert len(error_issues) >= 1
        assert any("Subject line is required" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_subject_length_limits(self, email_publisher):
        """Test validation of subject line length limits"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.html = "<p>Valid content</p>"
        newsletter.text = "Valid text"
        newsletter.recipient_count = 100

        # Test short subject warning
        newsletter.subject = "Short"  # Under min length
        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("very short" in issue.message for issue in warning_issues)

        # Test long subject error
        newsletter.subject = "x" * 150  # Over max length
        result = await email_publisher.validate(content)

        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("too long" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_html_content_requirements(self, email_publisher):
        """Test validation of HTML content requirements"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Valid Subject"
        newsletter.html = ""  # Empty HTML
        newsletter.text = "Valid text"
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("HTML content is required" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_html_size_limit(self, email_publisher):
        """Test validation of HTML content size limit"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Valid Subject"
        newsletter.html = "x" * 600000  # Over size limit
        newsletter.text = "Valid text"
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("too large" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_text_content_recommendations(self, email_publisher):
        """Test validation of text content recommendations"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Valid Subject"
        newsletter.html = "<p>Valid HTML content</p>"
        newsletter.text = ""  # Missing text version
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("recommended for better deliverability" in issue.message for issue in warning_issues)

        # Test short text warning
        newsletter.text = "Short"  # Very short text
        result = await email_publisher.validate(content)

        warning_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        assert any("very short" in issue.message for issue in warning_issues)

    @pytest.mark.asyncio
    async def test_validate_spam_word_detection(self, email_publisher):
        """Test spam word detection in subject line"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "FREE urgent offer - act now!"  # Multiple spam words
        newsletter.html = "<p>Valid HTML content</p>"
        newsletter.text = "Valid text content"
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        spam_warnings = [issue for issue in result.issues
                        if issue.severity == ValidationSeverity.WARNING and issue.code == "SPAM_RISK"]
        assert len(spam_warnings) >= 2  # Should detect multiple spam words

    @pytest.mark.asyncio
    async def test_validate_recipient_count_limit(self, email_publisher):
        """Test validation of recipient count limits"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Valid Subject"
        newsletter.html = "<p>Valid content</p>"
        newsletter.text = "Valid text"
        newsletter.recipient_count = 15000  # Over limit

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        error_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        assert any("exceeds limit" in issue.message for issue in error_issues)

    @pytest.mark.asyncio
    async def test_validate_exception_handling(self, email_publisher):
        """Test validation exception handling"""
        content = MagicMock(spec=Content)
        content.content_type = "email"
        content.to_newsletter.side_effect = Exception("Test exception")

        result = await email_publisher.validate(content)

        assert result.is_valid is False
        critical_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.CRITICAL]
        assert len(critical_issues) == 1
        assert "Validation failed" in critical_issues[0].message

    @pytest.mark.asyncio
    async def test_preview_valid_content(self, email_publisher, valid_email_content):
        """Test preview generation for valid content"""
        result = await email_publisher.preview(valid_email_content)

        assert isinstance(result, PreviewResult)
        assert "subject" in result.preview_data
        assert "html_preview" in result.preview_data
        assert "estimated_opens" in result.preview_data
        assert "estimated_clicks" in result.preview_data
        assert "deliverability_score" in result.preview_data
        assert result.estimated_reach == 1000  # From newsletter.recipient_count
        assert result.character_count > 0

    @pytest.mark.asyncio
    async def test_preview_default_recipients(self, email_publisher):
        """Test preview with default recipient count"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Test Subject"
        newsletter.html = "<p>Test content</p>"
        newsletter.text = "Test content"
        newsletter.preview_text = "Preview text"
        newsletter.recipient_count = None  # No explicit count

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.preview(content)

        assert result.estimated_reach == 250  # From config default_recipients

    @pytest.mark.asyncio
    async def test_preview_long_content_truncation(self, email_publisher):
        """Test preview content truncation for long content"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Test Subject"
        newsletter.html = "<p>" + "x" * 1500 + "</p>"  # Long HTML
        newsletter.text = "x" * 1000  # Long text
        newsletter.preview_text = "Preview text"
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.preview(content)

        assert len(result.preview_data["html_preview"]) <= 1003  # 1000 + "..."
        assert result.preview_data["html_preview"].endswith("...")
        assert len(result.preview_data["text_preview"]) <= 503  # 500 + "..."

    @pytest.mark.asyncio
    async def test_preview_metrics_calculation(self, email_publisher, publisher_config):
        """Test preview metrics calculation"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Test Subject"
        newsletter.html = "<p>Test content</p>"
        newsletter.text = "Test content"
        newsletter.preview_text = "Preview text"
        newsletter.recipient_count = 1000

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.preview(content)

        expected_opens = int(1000 * publisher_config['average_open_rate'])  # 1000 * 0.3 = 300
        expected_clicks = int(1000 * publisher_config['average_click_rate'])  # 1000 * 0.08 = 80

        assert result.preview_data["estimated_opens"] == expected_opens
        assert result.preview_data["estimated_clicks"] == expected_clicks

    @pytest.mark.asyncio
    async def test_preview_exception_handling(self, email_publisher):
        """Test preview exception handling"""
        content = MagicMock(spec=Content)
        content.to_newsletter.side_effect = Exception("Test exception")

        result = await email_publisher.preview(content)

        assert "error" in result.preview_data
        assert "Preview failed" in result.formatted_content
        assert result.metadata.get("error") is True

    @pytest.mark.asyncio
    async def test_publish_dry_run_mode(self, email_publisher, valid_email_content):
        """Test publish in dry run mode"""
        valid_email_content.dry_run = True

        result = await email_publisher.publish(valid_email_content)

        assert result.status == PublishStatus.SUCCESS
        assert "dry run" in result.message
        assert result.metadata["dry_run"] is True
        assert "dry-run-" in result.external_id

    @pytest.mark.asyncio
    async def test_publish_success(self, email_publisher, valid_email_content):
        """Test successful publish"""
        # Mock CRM client response
        mock_response = MagicMock()
        mock_response.status = 'completed'
        mock_response.job_id = 'email-job-123'
        mock_response.sent_count = 950
        mock_response.total_recipients = 1000

        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_response)
        email_publisher.analytics.track_send = AsyncMock()

        result = await email_publisher.publish(valid_email_content)

        assert result.status == PublishStatus.SUCCESS
        assert result.external_id == 'email-job-123'
        assert result.metadata['recipients_sent'] == 950
        assert result.metadata['recipients_total'] == 1000

    @pytest.mark.asyncio
    async def test_publish_crm_client_call(self, email_publisher, valid_email_content, publisher_config):
        """Test that CRM client is called with correct parameters"""
        mock_response = MagicMock()
        mock_response.status = 'completed'
        mock_response.job_id = 'email-job-123'
        mock_response.sent_count = 100
        mock_response.total_recipients = 100

        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_response)
        email_publisher.analytics.track_send = AsyncMock()

        await email_publisher.publish(valid_email_content)

        email_publisher.crm_client.send_newsletter_bulk.assert_called_once()
        call_args = email_publisher.crm_client.send_newsletter_bulk.call_args

        assert call_args[1]['subject'] == "Weekly Breathscape Update"
        assert 'html_content' in call_args[1]
        assert 'text_content' in call_args[1]
        assert call_args[1]['sender_info']['name'] == publisher_config['sender_name']
        assert call_args[1]['sender_info']['email'] == publisher_config['sender_email']

    @pytest.mark.asyncio
    async def test_publish_analytics_tracking(self, email_publisher, valid_email_content):
        """Test analytics tracking during publish"""
        mock_response = MagicMock()
        mock_response.status = 'completed'
        mock_response.job_id = 'email-job-123'
        mock_response.sent_count = 100
        mock_response.total_recipients = 100

        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_response)
        email_publisher.analytics.track_send = AsyncMock()

        await email_publisher.publish(valid_email_content)

        email_publisher.analytics.track_send.assert_called_once()
        call_args = email_publisher.analytics.track_send.call_args

        assert call_args[1]['campaign_id'] == 'email-job-123'
        assert call_args[1]['recipient_count'] == 100
        assert call_args[1]['subject'] == "Weekly Breathscape Update"

    @pytest.mark.asyncio
    async def test_publish_failed_status(self, email_publisher, valid_email_content):
        """Test publish with failed CRM response"""
        mock_response = MagicMock()
        mock_response.status = 'failed'
        mock_response.job_id = 'email-job-failed'
        mock_response.sent_count = 0
        mock_response.total_recipients = 1000

        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_response)

        result = await email_publisher.publish(valid_email_content)

        assert result.status == PublishStatus.FAILED
        assert result.metadata['job_id'] == 'email-job-failed'

    @pytest.mark.asyncio
    async def test_publish_no_job_id_response(self, email_publisher, valid_email_content):
        """Test publish when response doesn't have job_id"""
        mock_response = MagicMock()
        mock_response.status = 'completed'
        mock_response.sent_count = 100
        mock_response.total_recipients = 100
        # No job_id attribute

        def mock_hasattr(obj, attr):
            return attr != 'job_id'

        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(return_value=mock_response)
        email_publisher.analytics.track_send = AsyncMock()

        with patch('builtins.hasattr', side_effect=mock_hasattr):
            result = await email_publisher.publish(valid_email_content)

        # Should still succeed, analytics just won't be tracked
        assert result.status == PublishStatus.SUCCESS
        email_publisher.analytics.track_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_exception_handling(self, email_publisher, valid_email_content):
        """Test publish exception handling"""
        email_publisher.crm_client.send_newsletter_bulk = AsyncMock(side_effect=Exception("CRM error"))

        result = await email_publisher.publish(valid_email_content)

        assert result.status == PublishStatus.FAILED
        assert "CRM error" in result.message
        assert "CRM error" in result.errors

    def test_supports_scheduling(self, email_publisher):
        """Test scheduling support"""
        assert email_publisher.supports_scheduling() is True

    def test_get_rate_limits(self, email_publisher, publisher_config):
        """Test rate limits getter"""
        limits = email_publisher.get_rate_limits()
        assert limits['emails_per_hour'] == publisher_config['emails_per_hour']
        assert limits['campaigns_per_day'] == publisher_config['campaigns_per_day']

    def test_get_content_limits(self, email_publisher):
        """Test content limits getter"""
        limits = email_publisher.get_content_limits()
        assert limits['subject_max_length'] == 100
        assert limits['html_max_length'] == 500000
        assert limits['max_recipients'] == 5000

    @pytest.mark.asyncio
    async def test_health_check_success(self, email_publisher):
        """Test health check success"""
        email_publisher.crm_client.health_check = AsyncMock(return_value=True)

        result = await email_publisher.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, email_publisher):
        """Test health check failure"""
        email_publisher.crm_client.health_check = AsyncMock(side_effect=Exception("Health check failed"))

        result = await email_publisher.health_check()
        assert result is False

    def test_calculate_deliverability_score_good_practices(self, email_publisher):
        """Test deliverability score with good practices"""
        newsletter = MagicMock()
        newsletter.subject = "Great Newsletter Update"  # No spam words, good length
        newsletter.html = "<p>Quality content without spam words</p>"
        newsletter.text = "Quality content without spam words"
        newsletter.preview_text = "Quality preview text"

        score = email_publisher._calculate_deliverability_score(newsletter)
        assert 0.0 <= score <= 1.0
        assert score >= 0.9  # Should score high with good practices

    def test_calculate_deliverability_score_spam_penalties(self, email_publisher):
        """Test deliverability score with spam penalties"""
        newsletter = MagicMock()
        newsletter.subject = "FREE urgent winner act now!"  # Multiple spam words
        newsletter.html = "<p>FREE winner click here urgent!!!</p>"  # Spam in HTML too
        newsletter.text = ""  # No text version
        newsletter.preview_text = ""  # No preview text

        score = email_publisher._calculate_deliverability_score(newsletter)
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should score low with spam indicators

    def test_calculate_deliverability_score_balanced(self, email_publisher):
        """Test deliverability score with mixed factors"""
        newsletter = MagicMock()
        newsletter.subject = "Important Update - Limited Time"  # One spam word
        newsletter.html = "<p>Important update about our platform</p>"
        newsletter.text = "Important update about our platform"  # Has text version
        newsletter.preview_text = "Platform update"  # Has preview

        score = email_publisher._calculate_deliverability_score(newsletter)
        assert 0.0 <= score <= 1.0
        assert 0.6 <= score <= 0.9  # Moderate score

    def test_calculate_deliverability_score_edge_cases(self, email_publisher):
        """Test deliverability score edge cases"""
        # Empty newsletter
        newsletter = MagicMock()
        newsletter.subject = ""
        newsletter.html = ""
        newsletter.text = ""
        newsletter.preview_text = ""

        score = email_publisher._calculate_deliverability_score(newsletter)
        assert 0.0 <= score <= 1.0

        # Newsletter with only good practices
        newsletter.subject = "Newsletter"  # Short subject
        newsletter.html = "Content"
        newsletter.text = "Content"  # Has text
        newsletter.preview_text = "Preview"  # Has preview

        score = email_publisher._calculate_deliverability_score(newsletter)
        assert score >= 1.0  # Maxed out with bonuses

    @pytest.mark.asyncio
    async def test_integration_with_settings(self, publisher_config):
        """Test integration with Settings object creation"""
        with patch('src.halcytone_content_generator.services.publishers.email_publisher.Settings') as mock_settings, \
             patch('src.halcytone_content_generator.services.publishers.email_publisher.EnhancedCRMClient') as mock_client, \
             patch('src.halcytone_content_generator.services.publishers.email_publisher.EmailAnalytics') as mock_analytics:

            mock_settings_instance = MagicMock()
            mock_settings.return_value = mock_settings_instance

            publisher = EmailPublisher(config=publisher_config)

            # Verify Settings object was configured correctly
            assert mock_settings_instance.CRM_BASE_URL == publisher_config['crm_base_url']
            assert mock_settings_instance.CRM_API_KEY == publisher_config['crm_api_key']

            # Verify clients were initialized
            mock_client.assert_called_once_with(mock_settings_instance)
            mock_analytics.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_with_all_severity_levels(self, email_publisher):
        """Test validation produces all severity levels appropriately"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "FREE urgent limited time offer - act now winner!!!"  # Long + spam words (error + warnings)
        newsletter.html = "x"  # Very short HTML (error)
        newsletter.text = ""  # Missing text (warning)
        newsletter.recipient_count = 100

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        # Should have different severity levels
        severities = {issue.severity for issue in result.issues}
        assert ValidationSeverity.ERROR in severities
        assert ValidationSeverity.WARNING in severities

    def test_logging_integration(self, email_publisher, caplog):
        """Test logging integration"""
        import logging

        newsletter = MagicMock()
        newsletter.subject = "Test"
        newsletter.html = "Content"
        newsletter.text = "Content"
        newsletter.preview_text = "Preview"

        with caplog.at_level(logging.INFO):
            # Test logging in deliverability calculation
            email_publisher._calculate_deliverability_score(newsletter)

        # Should not raise any exceptions with logging

    @pytest.mark.asyncio
    async def test_preview_fallback_values(self, email_publisher):
        """Test preview generation with fallback values"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Test Subject"
        newsletter.html = "<p>Test content</p>"
        newsletter.text = "Test content"
        newsletter.preview_text = None  # No preview text
        newsletter.recipient_count = 500

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.preview(content)

        # Should fallback to subject for preview text
        assert result.preview_data["preview_text"] == "Test Subject"

    @pytest.mark.asyncio
    async def test_validation_recipient_count_none(self, email_publisher):
        """Test validation when recipient_count is None"""
        content = MagicMock(spec=Content)
        content.content_type = "email"

        newsletter = MagicMock()
        newsletter.subject = "Valid Subject"
        newsletter.html = "<p>Valid HTML content</p>"
        newsletter.text = "Valid text"
        newsletter.recipient_count = None  # No recipient count

        content.to_newsletter.return_value = newsletter

        result = await email_publisher.validate(content)

        # Should not have recipient count validation issues
        recipient_issues = [issue for issue in result.issues
                          if "recipient" in issue.message.lower()]
        assert len(recipient_issues) == 0

    def test_dry_run_property(self, email_publisher):
        """Test dry_run property inheritance from Publisher base"""
        # Initially false
        assert email_publisher.dry_run is False

        # Can be set
        email_publisher.dry_run = True
        assert email_publisher.dry_run is True