"""
Schema-based content validation service
Sprint 2: Implement content validation before publishing
"""
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, timezone
from pydantic import ValidationError

from ..schemas.content_types import (
    ContentUnion, ContentType, ContentValidationResult,
    UpdateContentStrict, BlogContentStrict, AnnouncementContentStrict,
    NewsletterContentStrict, WebUpdateContentStrict, SocialPostStrict,
    ChannelType, SocialPlatform, TemplateStyle
)

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Comprehensive schema validation service
    Validates content structure before publishing using strict Pydantic models
    """

    def __init__(self):
        self.content_type_mapping = {
            "update": UpdateContentStrict,
            "blog": BlogContentStrict,
            "announcement": AnnouncementContentStrict
        }

    def detect_content_type(self, content_data: Dict[str, Any]) -> ContentType:
        """
        Detect content type from content data

        Args:
            content_data: Raw content dictionary

        Returns:
            Detected ContentType enum
        """
        # Explicit type detection
        if 'type' in content_data:
            try:
                return ContentType(content_data['type'])
            except ValueError:
                pass

        # Heuristic detection based on content and structure
        title = content_data.get('title', '').lower()
        content = content_data.get('content', '').lower()

        # Announcement indicators
        if any(indicator in title for indicator in [
            'announcement', 'launch', 'release', 'new partnership',
            '🎉', 'urgent', 'breaking', 'press release'
        ]):
            return ContentType.ANNOUNCEMENT

        # Blog indicators
        if any(indicator in title or indicator in content for indicator in [
            'science', 'technique', 'guide', 'how to', 'tips',
            'benefits', 'research', 'study', 'article'
        ]):
            return ContentType.BLOG

        # Default to update for weekly progress, features, etc.
        return ContentType.UPDATE

    def validate_content_structure(
        self,
        content_data: Dict[str, Any],
        content_type: Optional[ContentType] = None
    ) -> ContentValidationResult:
        """
        Validate content against strict schema

        Args:
            content_data: Raw content dictionary
            content_type: Optional explicit content type

        Returns:
            ContentValidationResult with validation status and details
        """
        issues = []
        warnings = []
        enhanced_metadata = {}

        # Detect content type if not provided
        if content_type is None:
            content_type = self.detect_content_type(content_data)

        # Get the appropriate model class
        model_class = self.content_type_mapping.get(content_type.value)
        if not model_class:
            issues.append(f"Unsupported content type: {content_type}")
            return ContentValidationResult(
                is_valid=False,
                content_type=content_type,
                issues=issues
            )

        # Attempt validation
        try:
            # Enrich content data with defaults
            enriched_data = self._enrich_content_data(content_data, content_type)

            # Validate using Pydantic model
            validated_content = model_class(**enriched_data)

            # Additional business logic validation
            business_warnings = self._validate_business_rules(validated_content)
            warnings.extend(business_warnings)

            # Generate enhanced metadata
            enhanced_metadata = self._generate_enhanced_metadata(validated_content)

            logger.info(f"Successfully validated {content_type} content: {validated_content.title}")

            return ContentValidationResult(
                is_valid=True,
                content_type=content_type,
                issues=issues,
                warnings=warnings,
                enhanced_metadata=enhanced_metadata
            )

        except ValidationError as e:
            # Convert Pydantic validation errors to readable format
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                issues.append(f"{field_path}: {message}")

            logger.warning(f"Validation failed for {content_type} content: {issues}")

            return ContentValidationResult(
                is_valid=False,
                content_type=content_type,
                issues=issues,
                warnings=warnings,
                enhanced_metadata=enhanced_metadata
            )

        except Exception as e:
            issues.append(f"Unexpected validation error: {str(e)}")
            logger.error(f"Unexpected validation error: {e}", exc_info=True)

            return ContentValidationResult(
                is_valid=False,
                content_type=content_type,
                issues=issues
            )

    def _enrich_content_data(
        self,
        content_data: Dict[str, Any],
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Enrich content data with intelligent defaults

        Args:
            content_data: Original content data
            content_type: Detected content type

        Returns:
            Enriched content data dictionary
        """
        enriched = content_data.copy()

        # Set content type
        enriched['type'] = content_type.value

        # Auto-generate missing fields
        if 'date' not in enriched:
            enriched['date'] = datetime.now(timezone.utc)

        # Auto-generate excerpt for content types that need it
        if content_type in [ContentType.BLOG, ContentType.UPDATE]:
            if 'excerpt' not in enriched and 'content' in enriched:
                content_text = enriched['content']
                # Generate excerpt from first 200 characters
                excerpt = content_text[:200].strip()
                if len(content_text) > 200:
                    # Find last complete word
                    last_space = excerpt.rfind(' ')
                    if last_space > 100:  # Ensure minimum length
                        excerpt = excerpt[:last_space] + '...'
                enriched['excerpt'] = excerpt

        # Auto-generate category for blog posts
        if content_type == ContentType.BLOG and 'category' not in enriched:
            enriched['category'] = self._detect_blog_category(enriched)

        # Auto-detect urgency for announcements
        if content_type == ContentType.ANNOUNCEMENT and 'urgency' not in enriched:
            enriched['urgency'] = self._detect_announcement_urgency(enriched)

        return enriched

    def _detect_blog_category(self, content_data: Dict[str, Any]) -> str:
        """Auto-detect blog category from content"""
        title = content_data.get('title', '').lower()
        content = content_data.get('content', '').lower()
        combined = f"{title} {content}"

        # Category mapping based on keywords
        if any(word in combined for word in ['breath', 'breathing', 'technique', 'exercise']):
            return 'Breathing Techniques'
        elif any(word in combined for word in ['science', 'research', 'study', 'data']):
            return 'Science & Research'
        elif any(word in combined for word in ['wellness', 'health', 'mindfulness', 'meditation']):
            return 'Wellness'
        elif any(word in combined for word in ['technology', 'app', 'device', 'hardware']):
            return 'Technology'
        elif any(word in combined for word in ['community', 'story', 'testimonial', 'user']):
            return 'Community'
        else:
            return 'General'

    def _detect_announcement_urgency(self, content_data: Dict[str, Any]) -> str:
        """Auto-detect announcement urgency"""
        title = content_data.get('title', '').lower()
        content = content_data.get('content', '').lower()
        combined = f"{title} {content}"

        if any(word in combined for word in ['urgent', 'critical', 'immediate', 'breaking']):
            return 'critical'
        elif any(word in combined for word in ['important', 'major', 'significant']):
            return 'high'
        elif any(word in combined for word in ['minor', 'small', 'routine']):
            return 'low'
        else:
            return 'medium'

    def _validate_business_rules(self, content: ContentUnion) -> List[str]:
        """
        Apply additional business logic validation

        Args:
            content: Validated content object

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for optimal posting times
        if content.scheduled_for:
            hour = content.scheduled_for.hour
            weekday = content.scheduled_for.weekday()  # 0=Monday, 6=Sunday

            # Business hours warning
            if hour < 8 or hour > 17:
                warnings.append("Content scheduled outside business hours may have lower engagement")

            # Weekend warning
            if weekday >= 5:  # Saturday/Sunday
                warnings.append("Weekend scheduling may result in reduced visibility")

        # Check content length recommendations
        content_length = len(content.content.split())
        if content.type == ContentType.BLOG and content_length < 300:
            warnings.append("Blog posts under 300 words may not perform well for SEO")
        elif content.type == ContentType.UPDATE and content_length > 500:
            warnings.append("Update content over 500 words may be too long for some channels")

        # Check for featured content limits
        if content.featured:
            warnings.append("Ensure max 3 featured items are active simultaneously")

        # Priority and channel alignment
        if (content.priority.value <= 2 and  # High/Urgent priority
            ChannelType.EMAIL not in content.channels):
            warnings.append("High priority content should include email distribution")

        return warnings

    def _generate_enhanced_metadata(self, content: ContentUnion) -> Dict[str, Any]:
        """
        Generate enhanced metadata from validated content

        Args:
            content: Validated content object

        Returns:
            Dictionary of enhanced metadata
        """
        metadata = {
            'word_count': len(content.content.split()),
            'character_count': len(content.content),
            'estimated_read_time': max(1, len(content.content.split()) // 200),
            'content_complexity': self._assess_content_complexity(content.content),
            'seo_score': self._calculate_basic_seo_score(content),
            'recommended_channels': self._recommend_channels(content),
            'optimal_publish_time': self._suggest_optimal_publish_time(content)
        }

        # Type-specific metadata
        if content.type == ContentType.BLOG:
            metadata['blog_category'] = getattr(content, 'category', 'General')
            if hasattr(content, 'target_keywords'):
                metadata['keyword_density'] = self._calculate_keyword_density(
                    content.content, content.target_keywords
                )

        elif content.type == ContentType.ANNOUNCEMENT:
            metadata['urgency_level'] = getattr(content, 'urgency', 'medium')
            metadata['press_release_ready'] = getattr(content, 'press_release', False)

        return metadata

    def _assess_content_complexity(self, content: str) -> str:
        """Assess content complexity based on various factors"""
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length > 25:
            return 'complex'
        elif avg_sentence_length > 15:
            return 'moderate'
        else:
            return 'simple'

    def _calculate_basic_seo_score(self, content: ContentUnion) -> int:
        """Calculate a basic SEO score (0-100)"""
        score = 50  # Base score

        # Title length (optimal 30-60 chars)
        title_len = len(content.title)
        if 30 <= title_len <= 60:
            score += 15
        elif title_len < 30 or title_len > 60:
            score -= 5

        # Content length (optimal 300+ words for blogs)
        word_count = len(content.content.split())
        if content.type == ContentType.BLOG:
            if word_count >= 300:
                score += 20
            elif word_count < 150:
                score -= 10

        # Has excerpt/description
        if hasattr(content, 'excerpt') and getattr(content, 'excerpt'):
            score += 10

        # Has tags
        if hasattr(content, 'tags') and getattr(content, 'tags'):
            score += 10

        # SEO-specific fields for blogs
        if content.type == ContentType.BLOG:
            if hasattr(content, 'seo_description') and getattr(content, 'seo_description'):
                score += 15

        return min(100, max(0, score))

    def _recommend_channels(self, content: ContentUnion) -> List[str]:
        """Recommend optimal channels for content"""
        recommendations = []

        # All content types can go to email and web
        recommendations.extend(['email', 'web'])

        # Social media recommendations
        if content.type == ContentType.ANNOUNCEMENT:
            recommendations.append('social')  # Announcements work well on all social
        elif content.type == ContentType.BLOG:
            if len(content.content.split()) <= 300:
                recommendations.append('social')  # Shorter blogs good for social
        elif content.type == ContentType.UPDATE:
            recommendations.append('social')  # Updates are perfect for social

        return recommendations

    def _suggest_optimal_publish_time(self, content: ContentUnion) -> Optional[str]:
        """Suggest optimal publishing time based on content type"""
        if content.type == ContentType.ANNOUNCEMENT and hasattr(content, 'urgency'):
            if content.urgency in ['critical', 'high']:
                return 'immediate'

        # General recommendations
        publish_times = {
            ContentType.BLOG: 'Tuesday-Thursday, 9-11 AM EST',
            ContentType.UPDATE: 'Tuesday-Thursday, 10 AM-2 PM EST',
            ContentType.ANNOUNCEMENT: 'Monday-Wednesday, 9 AM-12 PM EST'
        }

        return publish_times.get(content.type)

    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density for target keywords"""
        content_lower = content.lower()
        total_words = len(content.split())

        density = {}
        for keyword in keywords:
            keyword_lower = keyword.lower()
            occurrences = content_lower.count(keyword_lower)
            density[keyword] = (occurrences / total_words) * 100 if total_words > 0 else 0

        return density

    def validate_newsletter_content(
        self,
        newsletter_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Optional[NewsletterContentStrict]]:
        """
        Validate newsletter content specifically

        Returns:
            Tuple of (is_valid, issues, validated_content)
        """
        issues = []

        try:
            validated = NewsletterContentStrict(**newsletter_data)
            logger.info(f"Newsletter validation successful: {validated.subject}")
            return True, issues, validated
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                issues.append(f"Newsletter {field_path}: {error['msg']}")
            return False, issues, None

    def validate_social_content(
        self,
        social_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Optional[SocialPostStrict]]:
        """
        Validate social media content specifically

        Returns:
            Tuple of (is_valid, issues, validated_content)
        """
        issues = []

        try:
            validated = SocialPostStrict(**social_data)
            logger.info(f"Social content validation successful for {validated.platform}")
            return True, issues, validated
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                issues.append(f"Social {field_path}: {error['msg']}")
            return False, issues, None

    def validate_web_content(
        self,
        web_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Optional[WebUpdateContentStrict]]:
        """
        Validate web content specifically

        Returns:
            Tuple of (is_valid, issues, validated_content)
        """
        issues = []

        try:
            validated = WebUpdateContentStrict(**web_data)
            logger.info(f"Web content validation successful: {validated.title}")
            return True, issues, validated
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error['loc'])
                issues.append(f"Web {field_path}: {error['msg']}")
            return False, issues, None