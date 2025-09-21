"""
Content Personalization Engine for Halcytone Content Generator.

This module provides dynamic content personalization based on user segments,
preferences, and behavioral data. It integrates with the user segmentation
system and AI content enhancer to deliver tailored content experiences.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from ..config import get_settings
from .user_segmentation import UserSegmentationService, SegmentCategory
from .ai_content_enhancer import AIContentEnhancer


logger = logging.getLogger(__name__)


@dataclass
class UserSegment:
    """User segment information for personalization."""
    segment_id: str
    segment_name: str
    confidence: float
    characteristics: Dict[str, Any] = field(default_factory=dict)
    engagement_level: str = "medium"
    assigned_date: datetime = field(default_factory=datetime.utcnow)


class PersonalizationLevel(Enum):
    """Levels of content personalization."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PREMIUM = "premium"


class ContentType(Enum):
    """Types of content that can be personalized."""
    EMAIL = "email"
    WEB_PAGE = "web_page"
    SOCIAL_POST = "social_post"
    NEWSLETTER = "newsletter"
    PRODUCT_DESCRIPTION = "product_description"
    BLOG_POST = "blog_post"


@dataclass
class UserPreference:
    """User preference data structure."""
    user_id: str
    preference_type: str
    value: Any
    confidence: float = 1.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    source: str = "explicit"  # explicit, inferred, behavioral


@dataclass
class PersonalizationContext:
    """Context for content personalization."""
    user_id: str
    user_segment: UserSegment
    preferences: Dict[str, Any]
    behavioral_data: Dict[str, Any]
    content_type: ContentType
    personalization_level: PersonalizationLevel
    template_variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalizedContent:
    """Personalized content result."""
    content: str
    personalization_score: float
    applied_personalizations: List[str]
    segment_match_score: float
    preference_match_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContentPersonalizationEngine:
    """
    Advanced content personalization engine that creates tailored content
    experiences based on user segments, preferences, and behavioral data.
    """

    def __init__(self):
        self.config = get_settings()
        self.segmentation_service = UserSegmentationService()
        self.ai_enhancer = AIContentEnhancer()
        self.user_preferences: Dict[str, Dict[str, UserPreference]] = {}
        self.personalization_templates: Dict[str, Dict[str, Any]] = {}
        self.content_variations: Dict[str, List[str]] = {}
        self._initialize_personalization_templates()

    def _initialize_personalization_templates(self):
        """Initialize personalization templates for different content types."""
        self.personalization_templates = {
            ContentType.EMAIL.value: {
                "greeting_variations": {
                    "formal": "Dear {name}",
                    "friendly": "Hi {name}!",
                    "casual": "Hey {name}",
                    "professional": "Hello {name}"
                },
                "closing_variations": {
                    "formal": "Best regards",
                    "friendly": "Best wishes",
                    "casual": "Cheers",
                    "professional": "Sincerely"
                },
                "tone_adjustments": {
                    "excited": {"adjectives": ["amazing", "fantastic", "incredible"], "punctuation": "!"},
                    "calm": {"adjectives": ["peaceful", "serene", "tranquil"], "punctuation": "."},
                    "urgent": {"adjectives": ["immediate", "critical", "essential"], "punctuation": "!"},
                    "supportive": {"adjectives": ["encouraging", "helpful", "caring"], "punctuation": "."}
                }
            },
            ContentType.WEB_PAGE.value: {
                "cta_variations": {
                    "action_oriented": ["Get Started Now", "Take Action", "Start Today"],
                    "benefit_focused": ["Discover Benefits", "See Results", "Experience More"],
                    "urgency": ["Limited Time", "Act Fast", "Don't Miss Out"],
                    "social_proof": ["Join Thousands", "Trusted by Many", "Community Choice"]
                },
                "headline_styles": {
                    "question": "Are you ready to {action}?",
                    "benefit": "Unlock {benefit} with {product}",
                    "problem_solution": "Struggling with {problem}? We have the solution.",
                    "testimonial": "See how {customer} achieved {result}"
                }
            },
            ContentType.SOCIAL_POST.value: {
                "hashtag_groups": {
                    "professional": ["#business", "#productivity", "#success", "#growth"],
                    "lifestyle": ["#wellness", "#balance", "#mindfulness", "#inspiration"],
                    "technical": ["#innovation", "#technology", "#digital", "#future"],
                    "community": ["#together", "#support", "#family", "#friends"]
                },
                "engagement_hooks": {
                    "question": "What's your experience with {topic}?",
                    "tip": "Pro tip: {advice}",
                    "story": "Here's what happened when {scenario}...",
                    "poll": "Which do you prefer: {option1} or {option2}?"
                }
            }
        }

    async def track_user_preference(
        self,
        user_id: str,
        preference_type: str,
        value: Any,
        confidence: float = 1.0,
        source: str = "explicit"
    ) -> bool:
        """
        Track a user preference for personalization.

        Args:
            user_id: User identifier
            preference_type: Type of preference (e.g., 'tone', 'content_length', 'topics')
            value: Preference value
            confidence: Confidence score (0.0-1.0)
            source: Source of preference (explicit, inferred, behavioral)

        Returns:
            Success status
        """
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}

            preference = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                value=value,
                confidence=confidence,
                source=source
            )

            self.user_preferences[user_id][preference_type] = preference

            logger.info(f"Tracked preference for user {user_id}: {preference_type}={value}")
            return True

        except Exception as e:
            logger.error(f"Error tracking user preference: {e}")
            return False

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all preferences for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of user preferences
        """
        if user_id not in self.user_preferences:
            return {}

        preferences = {}
        for pref_type, pref in self.user_preferences[user_id].items():
            preferences[pref_type] = {
                "value": pref.value,
                "confidence": pref.confidence,
                "source": pref.source,
                "last_updated": pref.last_updated.isoformat()
            }

        return preferences

    async def infer_preferences_from_behavior(
        self,
        user_id: str,
        behavioral_data: Dict[str, Any]
    ) -> Dict[str, UserPreference]:
        """
        Infer user preferences from behavioral data.

        Args:
            user_id: User identifier
            behavioral_data: User behavioral data

        Returns:
            Dictionary of inferred preferences
        """
        inferred_preferences = {}

        try:
            # Infer content length preference
            if "avg_read_time" in behavioral_data:
                avg_read_time = behavioral_data["avg_read_time"]
                if avg_read_time < 30:
                    length_pref = "short"
                elif avg_read_time < 120:
                    length_pref = "medium"
                else:
                    length_pref = "long"

                inferred_preferences["content_length"] = UserPreference(
                    user_id=user_id,
                    preference_type="content_length",
                    value=length_pref,
                    confidence=0.7,
                    source="behavioral"
                )

            # Infer engagement time preference
            if "engagement_times" in behavioral_data:
                times = behavioral_data["engagement_times"]
                if len(times) > 0:
                    avg_hour = sum(int(t.split(":")[0]) for t in times) / len(times)
                    if avg_hour < 10:
                        time_pref = "morning"
                    elif avg_hour < 14:
                        time_pref = "midday"
                    elif avg_hour < 18:
                        time_pref = "afternoon"
                    else:
                        time_pref = "evening"

                    inferred_preferences["preferred_time"] = UserPreference(
                        user_id=user_id,
                        preference_type="preferred_time",
                        value=time_pref,
                        confidence=0.8,
                        source="behavioral"
                    )

            # Infer tone preference from interaction patterns
            if "interaction_types" in behavioral_data:
                interactions = behavioral_data["interaction_types"]
                formal_interactions = interactions.get("formal", 0)
                casual_interactions = interactions.get("casual", 0)

                total_interactions = formal_interactions + casual_interactions
                if total_interactions > 0:
                    formality_ratio = formal_interactions / total_interactions
                    if formality_ratio > 0.7:
                        tone_pref = "formal"
                    elif formality_ratio < 0.3:
                        tone_pref = "casual"
                    else:
                        tone_pref = "professional"

                    inferred_preferences["tone"] = UserPreference(
                        user_id=user_id,
                        preference_type="tone",
                        value=tone_pref,
                        confidence=0.6,
                        source="behavioral"
                    )

            # Store inferred preferences
            for pref_type, preference in inferred_preferences.items():
                await self.track_user_preference(
                    user_id=user_id,
                    preference_type=pref_type,
                    value=preference.value,
                    confidence=preference.confidence,
                    source=preference.source
                )

            logger.info(f"Inferred {len(inferred_preferences)} preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Error inferring preferences from behavior: {e}")

        return inferred_preferences

    async def create_personalization_context(
        self,
        user_id: str,
        content_type: ContentType,
        personalization_level: PersonalizationLevel = PersonalizationLevel.INTERMEDIATE,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PersonalizationContext:
        """
        Create personalization context for a user.

        Args:
            user_id: User identifier
            content_type: Type of content to personalize
            personalization_level: Level of personalization
            additional_context: Additional context data

        Returns:
            Personalization context
        """
        # Get user segment
        user_profile_data = additional_context.get("user_profile", {}) if additional_context else {}

        # Create or update user profile if data provided
        if user_profile_data:
            self.segmentation_service.create_user_profile(user_id, user_profile_data)

        # Get user segments
        user_segments = self.segmentation_service.get_user_segments(user_id)

        # Create a UserSegment object for the primary segment
        if user_segments:
            # Use the first segment as primary, or industry segment if available
            primary_segment_id = user_segments.get(SegmentCategory.INDUSTRY)
            if not primary_segment_id:
                primary_segment_id = next(iter(user_segments.values()))

            user_segment = UserSegment(
                segment_id=primary_segment_id,
                segment_name=primary_segment_id.replace("_", " ").title(),
                confidence=0.8,  # Default confidence
                characteristics=user_profile_data,
                engagement_level="medium"
            )
        else:
            # Create default segment for new users
            user_segment = UserSegment(
                segment_id="general_user",
                segment_name="General User",
                confidence=0.5,
                characteristics={},
                engagement_level="medium"
            )

        # Get user preferences
        preferences = await self.get_user_preferences(user_id)

        # Get behavioral data
        behavioral_data = additional_context.get("behavioral_data", {}) if additional_context else {}

        # Infer preferences if behavioral data is available
        if behavioral_data:
            await self.infer_preferences_from_behavior(user_id, behavioral_data)
            preferences = await self.get_user_preferences(user_id)

        # Create template variables
        template_variables = {
            "user_id": user_id,
            "segment": user_segment.segment_id,
            "preferences": preferences
        }

        # Add additional template variables if provided
        if additional_context and "template_variables" in additional_context:
            template_variables.update(additional_context["template_variables"])

        return PersonalizationContext(
            user_id=user_id,
            user_segment=user_segment,
            preferences=preferences,
            behavioral_data=behavioral_data,
            content_type=content_type,
            personalization_level=personalization_level,
            template_variables=template_variables
        )

    async def apply_dynamic_content_insertion(
        self,
        content: str,
        context: PersonalizationContext
    ) -> Tuple[str, List[str]]:
        """
        Apply dynamic content insertion based on personalization context.

        Args:
            content: Original content
            context: Personalization context

        Returns:
            Tuple of (personalized_content, applied_personalizations)
        """
        personalized_content = content
        applied_personalizations = []

        try:
            # Get content type templates
            content_templates = self.personalization_templates.get(context.content_type.value, {})

            # Apply greeting personalization for emails
            if context.content_type == ContentType.EMAIL:
                tone = context.preferences.get("tone", {}).get("value", "professional")
                greetings = content_templates.get("greeting_variations", {})

                if "{greeting}" in personalized_content and tone in greetings:
                    greeting = greetings[tone].format(
                        name=context.template_variables.get("name", "there")
                    )
                    personalized_content = personalized_content.replace("{greeting}", greeting)
                    applied_personalizations.append(f"greeting_{tone}")

                # Apply closing personalization
                closings = content_templates.get("closing_variations", {})
                if "{closing}" in personalized_content and tone in closings:
                    closing = closings[tone]
                    personalized_content = personalized_content.replace("{closing}", closing)
                    applied_personalizations.append(f"closing_{tone}")

            # Apply CTA personalization for web pages
            elif context.content_type == ContentType.WEB_PAGE:
                cta_style = context.user_segment.characteristics.get("preferred_cta_style", "action_oriented")
                cta_variations = content_templates.get("cta_variations", {})

                if "{cta}" in personalized_content and cta_style in cta_variations:
                    cta_options = cta_variations[cta_style]
                    # Select CTA based on segment preferences
                    cta = cta_options[0] if cta_options else "Learn More"
                    personalized_content = personalized_content.replace("{cta}", cta)
                    applied_personalizations.append(f"cta_{cta_style}")

            # Apply hashtag personalization for social posts
            elif context.content_type == ContentType.SOCIAL_POST:
                segment_category = context.user_segment.segment_id.split("_")[0]
                hashtag_groups = content_templates.get("hashtag_groups", {})

                if "{hashtags}" in personalized_content:
                    hashtags = hashtag_groups.get(segment_category, hashtag_groups.get("professional", []))
                    hashtag_string = " ".join(hashtags[:3])  # Use top 3 hashtags
                    personalized_content = personalized_content.replace("{hashtags}", hashtag_string)
                    applied_personalizations.append(f"hashtags_{segment_category}")

            # Apply segment-specific content insertions
            segment_content = self._get_segment_specific_content(context.user_segment)
            for placeholder, replacement in segment_content.items():
                if placeholder in personalized_content:
                    personalized_content = personalized_content.replace(placeholder, replacement)
                    applied_personalizations.append(f"segment_{placeholder}")

            # Apply preference-based replacements
            preference_content = self._get_preference_based_content(context.preferences)
            for placeholder, replacement in preference_content.items():
                if placeholder in personalized_content:
                    personalized_content = personalized_content.replace(placeholder, replacement)
                    applied_personalizations.append(f"preference_{placeholder}")

            logger.info(f"Applied {len(applied_personalizations)} personalizations for user {context.user_id}")

        except Exception as e:
            logger.error(f"Error applying dynamic content insertion: {e}")

        return personalized_content, applied_personalizations

    def _get_segment_specific_content(self, user_segment: UserSegment) -> Dict[str, str]:
        """Get segment-specific content replacements."""
        segment_content = {}

        # Industry-specific content
        if "healthcare" in user_segment.segment_id:
            segment_content["{industry_example}"] = "patient care and medical outcomes"
            segment_content["{industry_benefit}"] = "improved patient satisfaction"
        elif "technology" in user_segment.segment_id:
            segment_content["{industry_example}"] = "digital innovation and efficiency"
            segment_content["{industry_benefit}"] = "enhanced productivity"
        elif "education" in user_segment.segment_id:
            segment_content["{industry_example}"] = "student engagement and learning"
            segment_content["{industry_benefit}"] = "better educational outcomes"

        # Engagement level content
        if user_segment.engagement_level == "high":
            segment_content["{engagement_tone}"] = "exclusive insights and advanced strategies"
        elif user_segment.engagement_level == "medium":
            segment_content["{engagement_tone}"] = "practical tips and proven methods"
        else:
            segment_content["{engagement_tone}"] = "simple steps and easy solutions"

        return segment_content

    def _get_preference_based_content(self, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Get preference-based content replacements."""
        preference_content = {}

        # Content length preference
        length_pref = preferences.get("content_length", {}).get("value")
        if length_pref == "short":
            preference_content["{detail_level}"] = "key highlights"
        elif length_pref == "long":
            preference_content["{detail_level}"] = "comprehensive analysis"
        else:
            preference_content["{detail_level}"] = "essential details"

        # Time preference
        time_pref = preferences.get("preferred_time", {}).get("value")
        if time_pref == "morning":
            preference_content["{time_context}"] = "start your day with"
        elif time_pref == "evening":
            preference_content["{time_context}"] = "wind down with"
        else:
            preference_content["{time_context}"] = "discover"

        return preference_content

    async def generate_personalized_content(
        self,
        base_content: str,
        context: PersonalizationContext,
        use_ai_enhancement: bool = True
    ) -> PersonalizedContent:
        """
        Generate fully personalized content.

        Args:
            base_content: Base content to personalize
            context: Personalization context
            use_ai_enhancement: Whether to use AI enhancement

        Returns:
            Personalized content result
        """
        try:
            # Apply dynamic content insertion
            personalized_content, applied_personalizations = await self.apply_dynamic_content_insertion(
                base_content, context
            )

            # Calculate segment match score
            segment_match_score = self._calculate_segment_match_score(context)

            # Calculate preference match score
            preference_match_score = self._calculate_preference_match_score(context)

            # Apply AI enhancement if requested
            if use_ai_enhancement and context.personalization_level in [
                PersonalizationLevel.ADVANCED, PersonalizationLevel.PREMIUM
            ]:
                enhancement_prompt = self._create_enhancement_prompt(context)
                enhanced_content = await self.ai_enhancer.enhance_content(
                    personalized_content,
                    enhancement_type="personalization",
                    context_data={
                        "user_segment": context.user_segment.segment_id,
                        "preferences": context.preferences,
                        "enhancement_prompt": enhancement_prompt
                    }
                )
                if enhanced_content and enhanced_content.enhanced_content:
                    personalized_content = enhanced_content.enhanced_content
                    applied_personalizations.append("ai_enhancement")

            # Calculate overall personalization score
            personalization_score = self._calculate_personalization_score(
                segment_match_score,
                preference_match_score,
                len(applied_personalizations),
                context.personalization_level
            )

            result = PersonalizedContent(
                content=personalized_content,
                personalization_score=personalization_score,
                applied_personalizations=applied_personalizations,
                segment_match_score=segment_match_score,
                preference_match_score=preference_match_score,
                metadata={
                    "user_id": context.user_id,
                    "content_type": context.content_type.value,
                    "personalization_level": context.personalization_level.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Generated personalized content for user {context.user_id} "
                       f"with score {personalization_score:.2f}")

            return result

        except Exception as e:
            logger.error(f"Error generating personalized content: {e}")
            # Return basic result on error
            return PersonalizedContent(
                content=base_content,
                personalization_score=0.0,
                applied_personalizations=[],
                segment_match_score=0.0,
                preference_match_score=0.0,
                metadata={"error": str(e)}
            )

    def _calculate_segment_match_score(self, context: PersonalizationContext) -> float:
        """Calculate how well content matches user segment."""
        score = 0.0

        # Base score from segment confidence
        score += context.user_segment.confidence * 0.4

        # Bonus for segment-specific personalizations
        segment_personalizations = [p for p in context.template_variables.get("applied_personalizations", [])
                                  if "segment_" in p]
        score += len(segment_personalizations) * 0.1

        # Bonus for engagement level match
        if context.user_segment.engagement_level == "high":
            score += 0.2
        elif context.user_segment.engagement_level == "medium":
            score += 0.1

        return min(score, 1.0)

    def _calculate_preference_match_score(self, context: PersonalizationContext) -> float:
        """Calculate how well content matches user preferences."""
        if not context.preferences:
            return 0.0

        total_confidence = 0.0
        preference_count = 0

        for pref_data in context.preferences.values():
            if isinstance(pref_data, dict) and "confidence" in pref_data:
                total_confidence += pref_data["confidence"]
                preference_count += 1

        if preference_count == 0:
            return 0.0

        return total_confidence / preference_count

    def _calculate_personalization_score(
        self,
        segment_score: float,
        preference_score: float,
        personalization_count: int,
        level: PersonalizationLevel
    ) -> float:
        """Calculate overall personalization score."""
        base_score = (segment_score * 0.4 + preference_score * 0.4 +
                     min(personalization_count / 5, 1.0) * 0.2)

        # Apply level multiplier
        level_multipliers = {
            PersonalizationLevel.BASIC: 0.7,
            PersonalizationLevel.INTERMEDIATE: 0.85,
            PersonalizationLevel.ADVANCED: 1.0,
            PersonalizationLevel.PREMIUM: 1.2
        }

        return min(base_score * level_multipliers[level], 1.0)

    def _create_enhancement_prompt(self, context: PersonalizationContext) -> str:
        """Create AI enhancement prompt based on context."""
        prompt_parts = [
            f"Enhance this {context.content_type.value} content for a user in the {context.user_segment.segment_id} segment."
        ]

        if context.preferences:
            tone = context.preferences.get("tone", {}).get("value", "professional")
            length = context.preferences.get("content_length", {}).get("value", "medium")
            prompt_parts.append(f"Use a {tone} tone and {length} content length.")

        prompt_parts.append("Maintain the core message while making it more relevant and engaging for this specific user.")

        return " ".join(prompt_parts)

    async def get_personalization_analytics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get personalization analytics and insights.

        Args:
            user_id: Optional user ID for user-specific analytics
            time_range: Optional time range for analytics

        Returns:
            Analytics data
        """
        analytics = {
            "total_users_tracked": len(self.user_preferences),
            "avg_preferences_per_user": 0,
            "preference_distribution": {},
            "segment_distribution": {},
            "personalization_effectiveness": {}
        }

        try:
            if self.user_preferences:
                total_preferences = sum(len(prefs) for prefs in self.user_preferences.values())
                analytics["avg_preferences_per_user"] = total_preferences / len(self.user_preferences)

                # Preference distribution
                all_preference_types = {}
                for user_prefs in self.user_preferences.values():
                    for pref_type in user_prefs.keys():
                        all_preference_types[pref_type] = all_preference_types.get(pref_type, 0) + 1

                analytics["preference_distribution"] = all_preference_types

            # User-specific analytics
            if user_id and user_id in self.user_preferences:
                user_analytics = {
                    "preference_count": len(self.user_preferences[user_id]),
                    "preferences": await self.get_user_preferences(user_id),
                    "last_preference_update": max(
                        pref.last_updated for pref in self.user_preferences[user_id].values()
                    ).isoformat() if self.user_preferences[user_id] else None
                }
                analytics["user_specific"] = user_analytics

            logger.info(f"Generated personalization analytics for {analytics['total_users_tracked']} users")

        except Exception as e:
            logger.error(f"Error generating personalization analytics: {e}")
            analytics["error"] = str(e)

        return analytics


# Singleton instance
_personalization_engine = None


def get_personalization_engine() -> ContentPersonalizationEngine:
    """Get the singleton personalization engine instance."""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = ContentPersonalizationEngine()
    return _personalization_engine