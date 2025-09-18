"""
Email Publisher implementation using CRM client for newsletter distribution
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from .base import Publisher, PublishResult, ValidationResult, PreviewResult, PublishStatus, ValidationIssue, ValidationSeverity
from ...schemas.content import Content, NewsletterContent
from ..crm_client_v2 import EnhancedCRMClient
from ..email_analytics import EmailAnalyticsService as EmailAnalytics

logger = logging.getLogger(__name__)


class EmailPublisher(Publisher):
    """
    Publisher for email newsletters via CRM integration
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("email", config)
        self.crm_client = EnhancedCRMClient(
            base_url=self.config.get('crm_base_url', 'http://localhost:8001'),
            api_key=self.config.get('crm_api_key', ''),
            dry_run=self.dry_run
        )
        self.analytics = EmailAnalytics()

        # Email-specific limits
        self.content_limits = {
            'subject_max_length': 100,
            'subject_min_length': 10,
            'html_max_length': 500000,  # 500KB
            'text_min_length': 50,
            'max_recipients': self.config.get('max_recipients', 10000)
        }

        # Rate limits
        self.rate_limits = {
            'emails_per_hour': self.config.get('emails_per_hour', 1000),
            'campaigns_per_day': self.config.get('campaigns_per_day', 5)
        }

    async def validate(self, content: Content) -> ValidationResult:
        """
        Validate email content for CRM requirements
        """
        issues = []

        try:
            # Ensure content is email type
            if content.content_type != "email":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content type must be 'email', got '{content.content_type}'",
                    field="content_type"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            newsletter = content.to_newsletter()

            # Validate subject line
            if not newsletter.subject:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Subject line is required",
                    field="subject"
                ))
            elif len(newsletter.subject) < self.content_limits['subject_min_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Subject line is very short ({len(newsletter.subject)} chars)",
                    field="subject"
                ))
            elif len(newsletter.subject) > self.content_limits['subject_max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Subject line too long ({len(newsletter.subject)} > {self.content_limits['subject_max_length']} chars)",
                    field="subject"
                ))

            # Validate HTML content
            if not newsletter.html:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="HTML content is required",
                    field="html"
                ))
            elif len(newsletter.html) > self.content_limits['html_max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"HTML content too large ({len(newsletter.html)} > {self.content_limits['html_max_length']} chars)",
                    field="html"
                ))

            # Validate text content
            if not newsletter.text:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Text version is recommended for better deliverability",
                    field="text"
                ))
            elif len(newsletter.text) < self.content_limits['text_min_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Text content is very short ({len(newsletter.text)} chars)",
                    field="text"
                ))

            # Check for spam indicators
            spam_words = ['free', 'urgent', 'act now', 'limited time', 'click here']
            subject_lower = newsletter.subject.lower()
            for word in spam_words:
                if word in subject_lower:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Subject contains potential spam word: '{word}'",
                        field="subject",
                        code="SPAM_RISK"
                    ))

            # Validate recipient count if provided
            if newsletter.recipient_count and newsletter.recipient_count > self.content_limits['max_recipients']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Recipient count ({newsletter.recipient_count}) exceeds limit ({self.content_limits['max_recipients']})",
                    field="recipient_count"
                ))

        except Exception as e:
            logger.error(f"Email validation error: {e}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation failed: {str(e)}",
                code="VALIDATION_ERROR"
            ))

        is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for issue in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            metadata={
                "channel": self.channel_name,
                "content_limits": self.content_limits,
                "validation_timestamp": datetime.now().isoformat()
            }
        )

    async def preview(self, content: Content) -> PreviewResult:
        """
        Generate email preview
        """
        try:
            newsletter = content.to_newsletter()

            # Generate preview HTML (truncated for preview)
            preview_html = newsletter.html[:1000] + "..." if len(newsletter.html) > 1000 else newsletter.html

            # Estimate metrics
            estimated_recipients = newsletter.recipient_count or self.config.get('default_recipients', 100)
            estimated_open_rate = self.config.get('average_open_rate', 0.25)
            estimated_click_rate = self.config.get('average_click_rate', 0.05)

            preview_data = {
                "subject": newsletter.subject,
                "preview_text": newsletter.preview_text or newsletter.subject,
                "html_preview": preview_html,
                "text_preview": newsletter.text[:500] + "..." if len(newsletter.text) > 500 else newsletter.text,
                "estimated_opens": int(estimated_recipients * estimated_open_rate),
                "estimated_clicks": int(estimated_recipients * estimated_click_rate),
                "send_time_estimate": "2-5 minutes",
                "deliverability_score": self._calculate_deliverability_score(newsletter)
            }

            return PreviewResult(
                preview_data=preview_data,
                formatted_content=preview_html,
                metadata={
                    "channel": self.channel_name,
                    "preview_mode": True,
                    "dry_run": self.dry_run
                },
                estimated_reach=estimated_recipients,
                estimated_engagement=estimated_open_rate,
                character_count=len(newsletter.html),
                word_count=len(newsletter.text.split()) if newsletter.text else 0
            )

        except Exception as e:
            logger.error(f"Email preview error: {e}")
            return PreviewResult(
                preview_data={"error": str(e)},
                formatted_content=f"Preview failed: {str(e)}",
                metadata={"channel": self.channel_name, "error": True}
            )

    async def publish(self, content: Content) -> PublishResult:
        """
        Publish email newsletter via CRM
        """
        try:
            newsletter = content.to_newsletter()

            # Check if this is a dry run
            if self.dry_run or content.dry_run:
                logger.info("Email publish: DRY RUN MODE - not actually sending")
                return PublishResult(
                    status=PublishStatus.SUCCESS,
                    message="Email would be sent successfully (dry run)",
                    metadata={
                        "channel": self.channel_name,
                        "dry_run": True,
                        "would_send_to": newsletter.recipient_count or "default_list",
                        "subject": newsletter.subject
                    },
                    external_id=f"dry-run-{datetime.now().timestamp()}"
                )

            # Send via CRM client
            logger.info(f"Sending newsletter: {newsletter.subject}")

            # Use the enhanced CRM client's bulk send method
            send_result = await self.crm_client.send_newsletter_bulk(
                subject=newsletter.subject,
                html_content=newsletter.html,
                text_content=newsletter.text or "",
                recipient_list="default",  # Could be configurable
                sender_info={
                    "name": self.config.get('sender_name', 'Halcytone'),
                    "email": self.config.get('sender_email', 'noreply@halcytone.com')
                }
            )

            # Track analytics
            if send_result and hasattr(send_result, 'job_id'):
                await self.analytics.track_send(
                    campaign_id=send_result.job_id,
                    recipient_count=send_result.total_recipients or 0,
                    subject=newsletter.subject
                )

            return PublishResult(
                status=PublishStatus.SUCCESS if send_result.status == 'completed' else PublishStatus.FAILED,
                message=f"Newsletter sent successfully to {send_result.sent_count} recipients",
                metadata={
                    "channel": self.channel_name,
                    "job_id": send_result.job_id,
                    "recipients_sent": send_result.sent_count,
                    "recipients_total": send_result.total_recipients,
                    "subject": newsletter.subject
                },
                external_id=send_result.job_id,
                published_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Email publish error: {e}")
            return PublishResult(
                status=PublishStatus.FAILED,
                message=f"Failed to send newsletter: {str(e)}",
                metadata={"channel": self.channel_name, "error": str(e)},
                errors=[str(e)]
            )

    def supports_scheduling(self) -> bool:
        """Email publisher supports scheduled sending"""
        return True

    def get_rate_limits(self) -> Dict[str, int]:
        """Get email-specific rate limits"""
        return self.rate_limits

    def get_content_limits(self) -> Dict[str, int]:
        """Get email-specific content limits"""
        return self.content_limits

    async def health_check(self) -> bool:
        """Check CRM client health"""
        try:
            return await self.crm_client.health_check()
        except Exception as e:
            logger.error(f"Email publisher health check failed: {e}")
            return False

    def _calculate_deliverability_score(self, newsletter: NewsletterContent) -> float:
        """
        Calculate estimated deliverability score based on content analysis
        """
        score = 1.0

        # Penalize for spam words
        spam_words = ['free', 'urgent', 'act now', 'limited time', 'click here', '!!!', 'winner']
        subject_lower = newsletter.subject.lower()
        html_lower = newsletter.html.lower()

        for word in spam_words:
            if word in subject_lower:
                score -= 0.1
            if word in html_lower:
                score -= 0.05

        # Reward for good practices
        if newsletter.text:  # Has text version
            score += 0.1
        if newsletter.preview_text:  # Has preview text
            score += 0.05
        if len(newsletter.subject) <= 50:  # Good subject length
            score += 0.05

        return max(0.0, min(1.0, score))