"""
Web Publisher implementation using Platform client for website content publishing
"""
import logging
from typing import Dict, Any
from datetime import datetime

from .base import Publisher, PublishResult, ValidationResult, PreviewResult, PublishStatus, ValidationIssue, ValidationSeverity
from ...schemas.content import Content, WebUpdateContent
from ..platform_client_v2 import EnhancedPlatformClient

logger = logging.getLogger(__name__)


class WebPublisher(Publisher):
    """
    Publisher for website content via Platform API
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("web", config)
        self.platform_client = EnhancedPlatformClient(
            base_url=self.config.get('platform_base_url', 'http://localhost:8000'),
            api_key=self.config.get('platform_api_key', ''),
            dry_run=self.dry_run
        )

        # Web-specific limits
        self.content_limits = {
            'title_max_length': 200,
            'title_min_length': 10,
            'content_max_length': 100000,  # 100KB
            'content_min_length': 100,
            'excerpt_max_length': 500,
            'slug_max_length': 100,
            'max_tags': 10
        }

        # Rate limits
        self.rate_limits = {
            'posts_per_hour': self.config.get('posts_per_hour', 10),
            'posts_per_day': self.config.get('posts_per_day', 50)
        }

    async def validate(self, content: Content) -> ValidationResult:
        """
        Validate web content for Platform API requirements
        """
        issues = []

        try:
            # Ensure content is web type
            if content.content_type != "web":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content type must be 'web', got '{content.content_type}'",
                    field="content_type"
                ))
                return ValidationResult(is_valid=False, issues=issues, metadata={})

            web_update = content.to_web_update()

            # Validate title
            if not web_update.title:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Title is required",
                    field="title"
                ))
            elif len(web_update.title) < self.content_limits['title_min_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Title is very short ({len(web_update.title)} chars)",
                    field="title"
                ))
            elif len(web_update.title) > self.content_limits['title_max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Title too long ({len(web_update.title)} > {self.content_limits['title_max_length']} chars)",
                    field="title"
                ))

            # Validate content
            if not web_update.content:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Content is required",
                    field="content"
                ))
            elif len(web_update.content) < self.content_limits['content_min_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Content is very short ({len(web_update.content)} chars)",
                    field="content"
                ))
            elif len(web_update.content) > self.content_limits['content_max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Content too large ({len(web_update.content)} > {self.content_limits['content_max_length']} chars)",
                    field="content"
                ))

            # Validate excerpt
            if not web_update.excerpt:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Excerpt is recommended for SEO",
                    field="excerpt"
                ))
            elif len(web_update.excerpt) > self.content_limits['excerpt_max_length']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Excerpt too long ({len(web_update.excerpt)} > {self.content_limits['excerpt_max_length']} chars)",
                    field="excerpt"
                ))

            # Validate slug
            if web_update.slug:
                if len(web_update.slug) > self.content_limits['slug_max_length']:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Slug too long ({len(web_update.slug)} > {self.content_limits['slug_max_length']} chars)",
                        field="slug"
                    ))
                # Check slug format
                if not web_update.slug.replace('-', '').replace('_', '').replace('/', '').isalnum():
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Slug should only contain alphanumeric characters, hyphens, underscores, and slashes",
                        field="slug"
                    ))

            # Validate tags
            if len(web_update.tags) > self.content_limits['max_tags']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Too many tags ({len(web_update.tags)} > {self.content_limits['max_tags']})",
                    field="tags"
                ))

            # SEO validation
            if web_update.title and len(web_update.title) > 60:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Title may be too long for search engine results (>60 chars)",
                    field="title",
                    code="SEO_WARNING"
                ))

            if web_update.excerpt and len(web_update.excerpt) > 160:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Excerpt may be too long for meta description (>160 chars)",
                    field="excerpt",
                    code="SEO_WARNING"
                ))

        except Exception as e:
            logger.error(f"Web validation error: {e}")
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
        Generate web content preview
        """
        try:
            web_update = content.to_web_update()

            # Generate preview content (truncated for preview)
            preview_content = web_update.content[:1000] + "..." if len(web_update.content) > 1000 else web_update.content

            # Estimate metrics
            estimated_views = self.config.get('average_page_views', 500)
            estimated_engagement = self.config.get('average_time_on_page', 2.5)  # minutes

            preview_data = {
                "title": web_update.title,
                "excerpt": web_update.excerpt,
                "content_preview": preview_content,
                "slug": web_update.slug or self._generate_slug(web_update.title),
                "tags": web_update.tags,
                "estimated_url": f"/updates/{web_update.slug or self._generate_slug(web_update.title)}",
                "estimated_views": estimated_views,
                "seo_score": self._calculate_seo_score(web_update),
                "readability_score": self._calculate_readability_score(web_update.content)
            }

            return PreviewResult(
                preview_data=preview_data,
                formatted_content=preview_content,
                metadata={
                    "channel": self.channel_name,
                    "preview_mode": True,
                    "dry_run": self.dry_run
                },
                estimated_reach=estimated_views,
                estimated_engagement=estimated_engagement,
                character_count=len(web_update.content),
                word_count=len(web_update.content.split())
            )

        except Exception as e:
            logger.error(f"Web preview error: {e}")
            return PreviewResult(
                preview_data={"error": str(e)},
                formatted_content=f"Preview failed: {str(e)}",
                metadata={"channel": self.channel_name, "error": True}
            )

    async def publish(self, content: Content) -> PublishResult:
        """
        Publish web content via Platform API
        """
        try:
            web_update = content.to_web_update()

            # Check if this is a dry run
            if self.dry_run or content.dry_run:
                logger.info("Web publish: DRY RUN MODE - not actually publishing")
                return PublishResult(
                    status=PublishStatus.SUCCESS,
                    message="Web content would be published successfully (dry run)",
                    metadata={
                        "channel": self.channel_name,
                        "dry_run": True,
                        "would_publish": {
                            "title": web_update.title,
                            "slug": web_update.slug or self._generate_slug(web_update.title)
                        }
                    },
                    external_id=f"dry-run-{datetime.now().timestamp()}",
                    url=f"/updates/{web_update.slug or self._generate_slug(web_update.title)}"
                )

            # Publish via Platform client
            logger.info(f"Publishing web content: {web_update.title}")

            # Generate slug if not provided
            if not web_update.slug:
                web_update.slug = self._generate_slug(web_update.title)

            # Use the enhanced Platform client
            publish_result = await self.platform_client.publish_content(
                title=web_update.title,
                content=web_update.content,
                excerpt=web_update.excerpt,
                slug=web_update.slug,
                tags=web_update.tags,
                published_at=web_update.published_at or datetime.now()
            )

            return PublishResult(
                status=PublishStatus.SUCCESS,
                message=f"Web content published successfully",
                metadata={
                    "channel": self.channel_name,
                    "content_id": publish_result.get('id'),
                    "slug": web_update.slug,
                    "title": web_update.title,
                    "tags": web_update.tags
                },
                external_id=str(publish_result.get('id')),
                url=publish_result.get('url', f"/updates/{web_update.slug}"),
                published_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Web publish error: {e}")
            return PublishResult(
                status=PublishStatus.FAILED,
                message=f"Failed to publish web content: {str(e)}",
                metadata={"channel": self.channel_name, "error": str(e)},
                errors=[str(e)]
            )

    def supports_scheduling(self) -> bool:
        """Web publisher supports scheduled publishing"""
        return True

    def get_rate_limits(self) -> Dict[str, int]:
        """Get web-specific rate limits"""
        return self.rate_limits

    def get_content_limits(self) -> Dict[str, int]:
        """Get web-specific content limits"""
        return self.content_limits

    async def health_check(self) -> bool:
        """Check Platform client health"""
        try:
            return await self.platform_client.health_check()
        except Exception as e:
            logger.error(f"Web publisher health check failed: {e}")
            return False

    def _generate_slug(self, title: str) -> str:
        """
        Generate URL-friendly slug from title
        """
        import re
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        return slug[:self.content_limits['slug_max_length']]

    def _calculate_seo_score(self, web_update: WebUpdateContent) -> float:
        """
        Calculate SEO score based on content analysis
        """
        score = 0.0

        # Title length (optimal: 30-60 chars)
        title_len = len(web_update.title)
        if 30 <= title_len <= 60:
            score += 0.3
        elif 10 <= title_len < 30 or 60 < title_len <= 80:
            score += 0.2
        else:
            score += 0.1

        # Excerpt/meta description (optimal: 120-160 chars)
        if web_update.excerpt:
            excerpt_len = len(web_update.excerpt)
            if 120 <= excerpt_len <= 160:
                score += 0.3
            elif 80 <= excerpt_len < 120 or 160 < excerpt_len <= 200:
                score += 0.2
            else:
                score += 0.1

        # Content length (optimal: >300 words)
        word_count = len(web_update.content.split())
        if word_count >= 300:
            score += 0.2
        elif word_count >= 150:
            score += 0.1

        # Tags (good to have 3-5 tags)
        tag_count = len(web_update.tags)
        if 3 <= tag_count <= 5:
            score += 0.2
        elif 1 <= tag_count < 3 or 5 < tag_count <= 8:
            score += 0.1

        return min(1.0, score)

    def _calculate_readability_score(self, content: str) -> float:
        """
        Simple readability score based on sentence and word length
        """
        if not content:
            return 0.0

        sentences = content.split('.')
        words = content.split()

        if not sentences or not words:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Simple score: prefer shorter sentences and words
        sentence_score = max(0, 1 - (avg_sentence_length - 15) / 25)
        word_score = max(0, 1 - (avg_word_length - 5) / 5)

        return (sentence_score + word_score) / 2