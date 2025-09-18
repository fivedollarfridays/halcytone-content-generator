"""
Social Media Publisher implementation for various social platforms
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from .base import Publisher, PublishResult, ValidationResult, PreviewResult, PublishStatus, ValidationIssue, ValidationSeverity
from ...schemas.content import Content, SocialPost

logger = logging.getLogger(__name__)


class SocialPublisher(Publisher):
    """
    Publisher for social media content across multiple platforms
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("social", config)

        # Platform-specific limits
        self.platform_limits = {
            'twitter': {
                'max_length': 280,
                'max_hashtags': 10,
                'max_media': 4
            },
            'linkedin': {
                'max_length': 3000,
                'max_hashtags': 30,
                'max_media': 1
            },
            'facebook': {
                'max_length': 63206,
                'max_hashtags': 30,
                'max_media': 10
            },
            'instagram': {
                'max_length': 2200,
                'max_hashtags': 30,
                'max_media': 10
            }
        }

        # Rate limits per platform
        self.rate_limits = {
            'twitter': {
                'posts_per_hour': 15,
                'posts_per_day': 300
            },
            'linkedin': {
                'posts_per_hour': 5,
                'posts_per_day': 25
            },
            'facebook': {
                'posts_per_hour': 10,
                'posts_per_day': 100
            },
            'instagram': {
                'posts_per_hour': 5,
                'posts_per_day': 25
            }
        }

    async def validate(self, content: Content) -> ValidationResult:
        """
        Validate social media content for platform requirements
        """
        issues = []

        try:
            # Ensure content is social type
            if content.content_type != "social":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content type must be 'social', got '{content.content_type}'",
                    field="content_type"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            social_post = content.to_social_post()

            # Validate platform
            if not social_post.platform:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Platform is required",
                    field="platform"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            platform = social_post.platform.lower()
            if platform not in self.platform_limits:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Unsupported platform: {platform}",
                    field="platform"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            platform_config = self.platform_limits[platform]

            # Validate content length
            if not social_post.content:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Content is required",
                    field="content"
                ))
            elif len(social_post.content) > platform_config['max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too long for {platform} ({len(social_post.content)} > {platform_config['max_length']} chars)",
                    field="content"
                ))

            # Validate hashtags
            if len(social_post.hashtags) > platform_config['max_hashtags']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many hashtags for {platform} ({len(social_post.hashtags)} > {platform_config['max_hashtags']})",
                    field="hashtags"
                ))

            # Validate hashtag format
            for hashtag in social_post.hashtags:
                if not hashtag.startswith('#'):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Hashtag should start with #: {hashtag}",
                        field="hashtags"
                    ))
                elif ' ' in hashtag:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Hashtag should not contain spaces: {hashtag}",
                        field="hashtags"
                    ))

            # Validate media URLs
            if len(social_post.media_urls) > platform_config['max_media']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many media files for {platform} ({len(social_post.media_urls)} > {platform_config['max_media']})",
                    field="media_urls"
                ))

            # Platform-specific validation
            if platform == 'twitter':
                self._validate_twitter_specific(social_post, issues)
            elif platform == 'linkedin':
                self._validate_linkedin_specific(social_post, issues)
            elif platform == 'facebook':
                self._validate_facebook_specific(social_post, issues)
            elif platform == 'instagram':
                self._validate_instagram_specific(social_post, issues)

        except Exception as e:
            logger.error(f"Social validation error: {e}")
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
                "platform": social_post.platform if 'social_post' in locals() else None,
                "platform_limits": self.platform_limits.get(platform, {}) if 'platform' in locals() else {},
                "validation_timestamp": datetime.now().isoformat()
            }
        )

    async def preview(self, content: Content) -> PreviewResult:
        """
        Generate social media preview
        """
        try:
            social_post = content.to_social_post()
            platform = social_post.platform.lower()

            # Format content for platform
            formatted_content = self._format_for_platform(social_post)

            # Estimate metrics based on platform
            engagement_rates = {
                'twitter': 0.05,
                'linkedin': 0.03,
                'facebook': 0.08,
                'instagram': 0.12
            }

            estimated_followers = self.config.get(f'{platform}_followers', 1000)
            estimated_reach = int(estimated_followers * 0.1)  # 10% reach
            estimated_engagement = engagement_rates.get(platform, 0.05)

            preview_data = {
                "platform": social_post.platform,
                "formatted_content": formatted_content,
                "hashtags": social_post.hashtags,
                "media_count": len(social_post.media_urls),
                "character_count": len(formatted_content),
                "estimated_reach": estimated_reach,
                "estimated_likes": int(estimated_reach * estimated_engagement),
                "estimated_shares": int(estimated_reach * estimated_engagement * 0.1),
                "optimal_posting_time": self._get_optimal_posting_time(platform),
                "platform_tips": self._get_platform_tips(platform)
            }

            return PreviewResult(
                preview_data=preview_data,
                formatted_content=formatted_content,
                metadata={
                    "channel": self.channel_name,
                    "platform": platform,
                    "preview_mode": True,
                    "dry_run": self.dry_run
                },
                estimated_reach=estimated_reach,
                estimated_engagement=estimated_engagement,
                character_count=len(formatted_content),
                word_count=len(social_post.content.split())
            )

        except Exception as e:
            logger.error(f"Social preview error: {e}")
            return PreviewResult(
                preview_data={"error": str(e)},
                formatted_content=f"Preview failed: {str(e)}",
                metadata={"channel": self.channel_name, "error": True}
            )

    async def publish(self, content: Content) -> PublishResult:
        """
        Publish social media content

        Note: Currently returns dry-run simulation as social API integration
        is not fully implemented
        """
        try:
            social_post = content.to_social_post()
            platform = social_post.platform.lower()

            # Format content for platform
            formatted_content = self._format_for_platform(social_post)

            # For now, always treat as dry run since social APIs are not implemented
            logger.info(f"Social publish: {platform} - {formatted_content[:50]}...")

            # In the future, this would integrate with actual social media APIs
            # For now, we simulate successful posting

            return PublishResult(
                status=PublishStatus.SUCCESS,
                message=f"Social post scheduled for {platform} (manual posting required)",
                metadata={
                    "channel": self.channel_name,
                    "platform": platform,
                    "manual_posting_required": True,
                    "formatted_content": formatted_content,
                    "hashtags": social_post.hashtags,
                    "media_urls": social_post.media_urls,
                    "note": "Social media APIs not yet integrated - manual posting required"
                },
                external_id=f"social-{platform}-{datetime.now().timestamp()}",
                published_at=datetime.now() if not social_post.scheduled_for else social_post.scheduled_for
            )

        except Exception as e:
            logger.error(f"Social publish error: {e}")
            return PublishResult(
                status=PublishStatus.FAILED,
                message=f"Failed to prepare social post: {str(e)}",
                metadata={"channel": self.channel_name, "error": str(e)},
                errors=[str(e)]
            )

    def supports_scheduling(self) -> bool:
        """Social publisher supports scheduled posting"""
        return True

    def get_rate_limits(self) -> Dict[str, int]:
        """Get social-specific rate limits"""
        return self.rate_limits

    def get_content_limits(self) -> Dict[str, int]:
        """Get social-specific content limits"""
        return self.platform_limits

    async def health_check(self) -> bool:
        """Check social media API health (simulated)"""
        # In the future, this would check actual API connections
        return True

    def _format_for_platform(self, social_post: SocialPost) -> str:
        """
        Format content for specific platform
        """
        content = social_post.content
        platform = social_post.platform.lower()

        if platform == 'twitter':
            # Twitter: hashtags at end, shorter content
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                max_content_len = 280 - len(hashtag_str) - 1
                if len(content) > max_content_len:
                    content = content[:max_content_len-3] + '...'
                content = f"{content} {hashtag_str}"
            return content

        elif platform == 'linkedin':
            # LinkedIn: more professional, hashtags integrated
            if social_post.hashtags:
                # Integrate hashtags naturally into content
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        elif platform == 'facebook':
            # Facebook: longer form, hashtags at end
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        elif platform == 'instagram':
            # Instagram: hashtags are crucial, at end
            if social_post.hashtags:
                hashtag_str = ' '.join(social_post.hashtags)
                content = f"{content}\n\n{hashtag_str}"
            return content

        return content

    def _validate_twitter_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Twitter-specific validation"""
        # Check for mentions without @
        content = social_post.content.lower()
        if 'twitter' in content or 'tweet' in content:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider using platform-neutral language",
                field="content",
                code="PLATFORM_SPECIFIC"
            ))

    def _validate_linkedin_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """LinkedIn-specific validation"""
        # LinkedIn prefers professional tone
        casual_words = ['lol', 'omg', 'wtf', 'tbh']
        content_lower = social_post.content.lower()

        for word in casual_words:
            if word in content_lower:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Consider more professional language for LinkedIn (found: {word})",
                    field="content",
                    code="TONE_WARNING"
                ))

    def _validate_facebook_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Facebook-specific validation"""
        # Facebook algorithm prefers engaging content
        if '?' not in social_post.content and 'what' not in social_post.content.lower():
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Consider adding a question to increase engagement",
                field="content",
                code="ENGAGEMENT_TIP"
            ))

    def _validate_instagram_specific(self, social_post: SocialPost, issues: List[ValidationIssue]):
        """Instagram-specific validation"""
        # Instagram is visual-first
        if not social_post.media_urls:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Instagram posts typically perform better with images",
                field="media_urls",
                code="VISUAL_RECOMMENDATION"
            ))

    def _get_optimal_posting_time(self, platform: str) -> str:
        """
        Get optimal posting time for platform
        """
        optimal_times = {
            'twitter': '9 AM - 3 PM EST',
            'linkedin': '8 AM - 10 AM EST (weekdays)',
            'facebook': '1 PM - 3 PM EST',
            'instagram': '11 AM - 1 PM EST'
        }
        return optimal_times.get(platform, 'Peak engagement hours vary')

    def _get_platform_tips(self, platform: str) -> List[str]:
        """
        Get platform-specific tips
        """
        tips = {
            'twitter': [
                'Use relevant hashtags (#Breathscape)',
                'Keep it concise and engaging',
                'Include a call-to-action',
                'Tweet during peak hours'
            ],
            'linkedin': [
                'Use professional tone',
                'Include industry hashtags',
                'Share insights and value',
                'Post during business hours'
            ],
            'facebook': [
                'Ask questions to drive engagement',
                'Use visual content when possible',
                'Keep hashtags minimal',
                'Post when your audience is active'
            ],
            'instagram': [
                'Visual content is essential',
                'Use relevant hashtags (max 30)',
                'Include location tags',
                'Post consistently'
            ]
        }
        return tips.get(platform, ['Tailor content to platform audience'])