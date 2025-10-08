"""
Unit tests for Content Personalization Engine.

Tests cover user preference tracking, dynamic content insertion,
personalized content generation, and analytics functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from halcytone_content_generator.services.personalization import (
    ContentPersonalizationEngine,
    PersonalizationLevel,
    ContentType,
    UserPreference,
    PersonalizationContext,
    PersonalizedContent,
    UserSegment,
    get_personalization_engine
)


class TestContentPersonalizationEngine:
    """Test cases for Content Personalization Engine."""

    @pytest.fixture
    def personalization_engine(self):
        """Create a personalization engine instance for testing."""
        return ContentPersonalizationEngine()

    @pytest.fixture
    def sample_user_segment(self):
        """Create a sample user segment for testing."""
        return UserSegment(
            segment_id="healthcare_professional",
            segment_name="Healthcare Professional",
            confidence=0.85,
            characteristics={
                "industry": "healthcare",
                "expertise_level": "professional",
                "preferred_cta_style": "benefit_focused"
            },
            engagement_level="high",
            assigned_date=datetime.utcnow()
        )

    @pytest.fixture
    def sample_preferences(self):
        """Create sample user preferences."""
        return {
            "tone": {"value": "professional", "confidence": 0.9, "source": "explicit"},
            "content_length": {"value": "medium", "confidence": 0.8, "source": "behavioral"},
            "preferred_time": {"value": "morning", "confidence": 0.7, "source": "inferred"}
        }

    @pytest.fixture
    def sample_behavioral_data(self):
        """Create sample behavioral data."""
        return {
            "avg_read_time": 45,
            "engagement_times": ["09:30", "10:15", "11:00"],
            "interaction_types": {"formal": 8, "casual": 2},
            "content_preferences": ["detailed", "professional"],
            "click_patterns": {"morning": 15, "afternoon": 8, "evening": 3}
        }

    @pytest.mark.asyncio
    async def test_track_user_preference(self, personalization_engine):
        """Test tracking user preferences."""
        user_id = "user123"

        # Track explicit preference
        success = await personalization_engine.track_user_preference(
            user_id=user_id,
            preference_type="tone",
            value="friendly",
            confidence=0.9,
            source="explicit"
        )

        assert success is True
        assert user_id in personalization_engine.user_preferences
        assert "tone" in personalization_engine.user_preferences[user_id]

        preference = personalization_engine.user_preferences[user_id]["tone"]
        assert preference.value == "friendly"
        assert preference.confidence == 0.9
        assert preference.source == "explicit"

    @pytest.mark.asyncio
    async def test_get_user_preferences(self, personalization_engine):
        """Test retrieving user preferences."""
        user_id = "user123"

        # Track multiple preferences
        await personalization_engine.track_user_preference(user_id, "tone", "professional", 0.8)
        await personalization_engine.track_user_preference(user_id, "length", "short", 0.7)

        preferences = await personalization_engine.get_user_preferences(user_id)

        assert len(preferences) == 2
        assert preferences["tone"]["value"] == "professional"
        assert preferences["length"]["value"] == "short"
        assert "last_updated" in preferences["tone"]

    @pytest.mark.asyncio
    async def test_get_user_preferences_empty(self, personalization_engine):
        """Test retrieving preferences for user with no preferences."""
        preferences = await personalization_engine.get_user_preferences("nonexistent_user")
        assert preferences == {}

    @pytest.mark.asyncio
    async def test_infer_preferences_from_behavior(self, personalization_engine, sample_behavioral_data):
        """Test inferring preferences from behavioral data."""
        user_id = "user123"

        inferred = await personalization_engine.infer_preferences_from_behavior(
            user_id, sample_behavioral_data
        )

        assert len(inferred) >= 2  # Should infer content_length and preferred_time
        assert "content_length" in inferred
        assert "preferred_time" in inferred

        # Check specific inferences
        assert inferred["content_length"].value == "medium"  # avg_read_time = 45
        assert inferred["preferred_time"].value == "midday"  # avg engagement time around 10:15

        # Verify preferences are stored
        preferences = await personalization_engine.get_user_preferences(user_id)
        assert "content_length" in preferences
        assert "preferred_time" in preferences

    @pytest.mark.asyncio
    async def test_infer_tone_from_interactions(self, personalization_engine):
        """Test inferring tone preference from interaction patterns."""
        user_id = "user123"
        behavioral_data = {
            "interaction_types": {"formal": 9, "casual": 1}  # High formality ratio
        }

        inferred = await personalization_engine.infer_preferences_from_behavior(
            user_id, behavioral_data
        )

        assert "tone" in inferred
        assert inferred["tone"].value == "formal"
        assert inferred["tone"].confidence == 0.6

    @pytest.mark.asyncio
    async def test_create_personalization_context(self, personalization_engine, sample_user_segment):
        """Test creating personalization context."""
        user_id = "user123"

        # Mock segmentation service methods
        with patch.object(personalization_engine.segmentation_service, 'create_user_profile') as mock_create, \
             patch.object(personalization_engine.segmentation_service, 'get_user_segments') as mock_get:

            # Mock return value should use SegmentCategory enum
            from halcytone_content_generator.services.user_segmentation import SegmentCategory
            mock_get.return_value = {SegmentCategory.INDUSTRY: "healthcare_professional"}

            # Track some preferences first
            await personalization_engine.track_user_preference(user_id, "tone", "professional", 0.8)

            context = await personalization_engine.create_personalization_context(
                user_id=user_id,
                content_type=ContentType.EMAIL,
                personalization_level=PersonalizationLevel.ADVANCED,
                additional_context={
                    "user_profile": {"industry": "healthcare"},
                    "template_variables": {"name": "Dr. Smith"}
                }
            )

            assert context.user_id == user_id
            assert context.content_type == ContentType.EMAIL
            assert context.personalization_level == PersonalizationLevel.ADVANCED
            assert context.user_segment.segment_id == "healthcare_professional"
            assert "tone" in context.preferences
            assert context.template_variables["name"] == "Dr. Smith"

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_email(self, personalization_engine, sample_user_segment, sample_preferences):
        """Test dynamic content insertion for email content."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences=sample_preferences,
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.INTERMEDIATE,
            template_variables={"name": "Dr. Smith"}
        )

        content = "{greeting}, this is a test email. {closing}"

        personalized_content, applied = await personalization_engine.apply_dynamic_content_insertion(
            content, context
        )

        assert "Dear Dr. Smith" in personalized_content or "Hello Dr. Smith" in personalized_content
        assert "Best regards" in personalized_content or "Sincerely" in personalized_content
        assert len(applied) >= 2  # greeting and closing
        assert any("greeting_" in p for p in applied)
        assert any("closing_" in p for p in applied)

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_web(self, personalization_engine, sample_user_segment):
        """Test dynamic content insertion for web page content."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.WEB_PAGE,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={}
        )

        content = "Welcome to our platform! {cta} to get started."

        personalized_content, applied = await personalization_engine.apply_dynamic_content_insertion(
            content, context
        )

        assert "{cta}" not in personalized_content  # Should be replaced
        assert len(applied) >= 1
        assert any("cta_" in p for p in applied)

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_social(self, personalization_engine, sample_user_segment):
        """Test dynamic content insertion for social media content."""
        # Update segment to match hashtag category
        sample_user_segment.segment_id = "professional_expert"

        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.SOCIAL_POST,
            personalization_level=PersonalizationLevel.INTERMEDIATE,
            template_variables={}
        )

        content = "Check out this amazing content! {hashtags}"

        personalized_content, applied = await personalization_engine.apply_dynamic_content_insertion(
            content, context
        )

        assert "{hashtags}" not in personalized_content
        assert "#" in personalized_content  # Should contain hashtags
        assert len(applied) >= 1
        assert any("hashtags_" in p for p in applied)

    @pytest.mark.asyncio
    async def test_generate_personalized_content_basic(self, personalization_engine, sample_user_segment, sample_preferences):
        """Test generating personalized content without AI enhancement."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences=sample_preferences,
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={"name": "Dr. Smith"}
        )

        base_content = "{greeting}, this is a test message. {closing}"

        result = await personalization_engine.generate_personalized_content(
            base_content, context, use_ai_enhancement=False
        )

        assert isinstance(result, PersonalizedContent)
        assert result.content != base_content  # Should be personalized
        assert result.personalization_score > 0
        assert len(result.applied_personalizations) > 0
        assert result.segment_match_score >= 0
        assert result.preference_match_score >= 0
        assert result.metadata["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_generate_personalized_content_with_ai(self, personalization_engine, sample_user_segment, sample_preferences):
        """Test generating personalized content with AI enhancement."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences=sample_preferences,
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.PREMIUM,
            template_variables={"name": "Dr. Smith"}
        )

        # Mock AI enhancer
        mock_enhancement = Mock()
        mock_enhancement.enhanced_content = "Enhanced personalized content"

        with patch.object(personalization_engine.ai_enhancer, 'enhance_content') as mock_enhance:
            mock_enhance.return_value = mock_enhancement

            result = await personalization_engine.generate_personalized_content(
                "Base content", context, use_ai_enhancement=True
            )

            assert "ai_enhancement" in result.applied_personalizations
            mock_enhance.assert_called_once()

    def test_calculate_segment_match_score(self, personalization_engine, sample_user_segment):
        """Test segment match score calculation."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={"applied_personalizations": ["segment_example", "other_personalization"]}
        )

        score = personalization_engine._calculate_segment_match_score(context)

        assert 0 <= score <= 1
        assert score > 0  # Should have some score due to segment confidence

    def test_calculate_preference_match_score(self, personalization_engine, sample_preferences):
        """Test preference match score calculation."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=Mock(),
            preferences=sample_preferences,
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={}
        )

        score = personalization_engine._calculate_preference_match_score(context)

        assert 0 <= score <= 1
        assert score > 0  # Should have score based on preference confidences

    def test_calculate_preference_match_score_empty(self, personalization_engine):
        """Test preference match score with no preferences."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=Mock(),
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={}
        )

        score = personalization_engine._calculate_preference_match_score(context)
        assert score == 0.0

    def test_calculate_personalization_score(self, personalization_engine):
        """Test overall personalization score calculation."""
        score = personalization_engine._calculate_personalization_score(
            segment_score=0.8,
            preference_score=0.7,
            personalization_count=3,
            level=PersonalizationLevel.ADVANCED
        )

        assert 0 <= score <= 1
        assert score > 0

    def test_calculate_personalization_score_premium(self, personalization_engine):
        """Test personalization score with premium level."""
        score = personalization_engine._calculate_personalization_score(
            segment_score=0.8,
            preference_score=0.7,
            personalization_count=5,
            level=PersonalizationLevel.PREMIUM
        )

        # Premium level should boost the score
        basic_score = personalization_engine._calculate_personalization_score(
            segment_score=0.8,
            preference_score=0.7,
            personalization_count=5,
            level=PersonalizationLevel.BASIC
        )

        assert score > basic_score

    def test_get_segment_specific_content(self, personalization_engine):
        """Test segment-specific content generation."""
        # Healthcare segment
        healthcare_segment = Mock()
        healthcare_segment.segment_id = "healthcare_professional"
        healthcare_segment.engagement_level = "high"

        content = personalization_engine._get_segment_specific_content(healthcare_segment)

        assert "{industry_example}" in content
        assert "patient care" in content["{industry_example}"]
        assert "{engagement_tone}" in content
        assert "exclusive" in content["{engagement_tone}"]

    def test_get_segment_specific_content_technology(self, personalization_engine):
        """Test segment-specific content for technology segment."""
        tech_segment = Mock()
        tech_segment.segment_id = "technology_innovator"
        tech_segment.engagement_level = "medium"

        content = personalization_engine._get_segment_specific_content(tech_segment)

        assert "digital innovation" in content["{industry_example}"]
        assert "practical tips" in content["{engagement_tone}"]

    def test_get_preference_based_content(self, personalization_engine, sample_preferences):
        """Test preference-based content generation."""
        content = personalization_engine._get_preference_based_content(sample_preferences)

        assert "{detail_level}" in content
        assert "{time_context}" in content
        assert "essential details" in content["{detail_level}"]  # medium length
        assert "start your day" in content["{time_context}"]  # morning preference

    def test_get_preference_based_content_short(self, personalization_engine):
        """Test preference-based content for short content preference."""
        preferences = {
            "content_length": {"value": "short", "confidence": 0.8},
            "preferred_time": {"value": "evening", "confidence": 0.7}
        }

        content = personalization_engine._get_preference_based_content(preferences)

        assert "key highlights" in content["{detail_level}"]
        assert "wind down" in content["{time_context}"]

    def test_create_enhancement_prompt(self, personalization_engine, sample_user_segment, sample_preferences):
        """Test AI enhancement prompt creation."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=sample_user_segment,
            preferences=sample_preferences,
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.ADVANCED,
            template_variables={}
        )

        prompt = personalization_engine._create_enhancement_prompt(context)

        assert "email" in prompt.lower()
        assert "healthcare_professional" in prompt
        assert "professional" in prompt
        assert "medium" in prompt

    @pytest.mark.asyncio
    async def test_get_personalization_analytics(self, personalization_engine):
        """Test personalization analytics generation."""
        # Track some preferences for multiple users
        await personalization_engine.track_user_preference("user1", "tone", "formal", 0.8)
        await personalization_engine.track_user_preference("user1", "length", "short", 0.7)
        await personalization_engine.track_user_preference("user2", "tone", "casual", 0.9)

        analytics = await personalization_engine.get_personalization_analytics()

        assert analytics["total_users_tracked"] == 2
        assert analytics["avg_preferences_per_user"] == 1.5  # 3 total / 2 users
        assert "tone" in analytics["preference_distribution"]
        assert analytics["preference_distribution"]["tone"] == 2

    @pytest.mark.asyncio
    async def test_get_personalization_analytics_user_specific(self, personalization_engine):
        """Test user-specific personalization analytics."""
        user_id = "user123"
        await personalization_engine.track_user_preference(user_id, "tone", "professional", 0.8)
        await personalization_engine.track_user_preference(user_id, "length", "medium", 0.7)

        analytics = await personalization_engine.get_personalization_analytics(user_id=user_id)

        assert "user_specific" in analytics
        user_analytics = analytics["user_specific"]
        assert user_analytics["preference_count"] == 2
        assert "tone" in user_analytics["preferences"]
        assert user_analytics["last_preference_update"] is not None

    @pytest.mark.asyncio
    async def test_error_handling_track_preference(self, personalization_engine):
        """Test error handling in preference tracking."""
        # This shouldn't cause an error, but let's test with invalid data
        success = await personalization_engine.track_user_preference(
            user_id="",  # Empty user ID
            preference_type="tone",
            value="professional",
            confidence=1.5,  # Invalid confidence (> 1.0)
            source="test"
        )

        # Should still succeed as the function is robust
        assert success is True

    @pytest.mark.asyncio
    async def test_error_handling_content_generation(self, personalization_engine):
        """Test error handling in content generation."""
        # Create context with invalid data
        invalid_segment = Mock()
        invalid_segment.segment_id = None
        invalid_segment.confidence = "invalid"

        context = PersonalizationContext(
            user_id="user123",
            user_segment=invalid_segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={}
        )

        result = await personalization_engine.generate_personalized_content(
            "Base content", context, use_ai_enhancement=False
        )

        # Should return basic result even with errors
        assert isinstance(result, PersonalizedContent)
        assert result.personalization_score >= 0

    def test_singleton_instance(self):
        """Test that get_personalization_engine returns singleton instance."""
        engine1 = get_personalization_engine()
        engine2 = get_personalization_engine()

        assert engine1 is engine2
        assert isinstance(engine1, ContentPersonalizationEngine)


class TestPersonalizationDataStructures:
    """Test personalization data structures."""

    @pytest.fixture
    def test_user_segment(self):
        """Create a test user segment."""
        return UserSegment(
            segment_id="test_segment",
            segment_name="Test Segment",
            confidence=0.8,
            characteristics={"industry": "test"},
            engagement_level="high",
            assigned_date=datetime.utcnow()
        )

    def test_user_preference_creation(self):
        """Test UserPreference data structure."""
        preference = UserPreference(
            user_id="user123",
            preference_type="tone",
            value="professional",
            confidence=0.8,
            source="explicit"
        )

        assert preference.user_id == "user123"
        assert preference.preference_type == "tone"
        assert preference.value == "professional"
        assert preference.confidence == 0.8
        assert preference.source == "explicit"
        assert isinstance(preference.last_updated, datetime)

    def test_personalization_context_creation(self, test_user_segment):
        """Test PersonalizationContext creation."""
        context = PersonalizationContext(
            user_id="user123",
            user_segment=test_user_segment,
            preferences={"tone": {"value": "professional"}},
            behavioral_data={"engagement": "high"},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.ADVANCED
        )

        assert context.user_id == "user123"
        assert context.user_segment == test_user_segment
        assert context.content_type == ContentType.EMAIL
        assert context.personalization_level == PersonalizationLevel.ADVANCED
        assert len(context.template_variables) == 0  # Default empty

    def test_personalized_content_creation(self):
        """Test PersonalizedContent data structure."""
        content = PersonalizedContent(
            content="Personalized content",
            personalization_score=0.85,
            applied_personalizations=["greeting_formal", "tone_professional"],
            segment_match_score=0.9,
            preference_match_score=0.8
        )

        assert content.content == "Personalized content"
        assert content.personalization_score == 0.85
        assert len(content.applied_personalizations) == 2
        assert content.segment_match_score == 0.9
        assert content.preference_match_score == 0.8
        assert len(content.metadata) == 0  # Default empty


class TestPersonalizationEnums:
    """Test personalization enumerations."""

    def test_personalization_level_enum(self):
        """Test PersonalizationLevel enum values."""
        assert PersonalizationLevel.BASIC.value == "basic"
        assert PersonalizationLevel.INTERMEDIATE.value == "intermediate"
        assert PersonalizationLevel.ADVANCED.value == "advanced"
        assert PersonalizationLevel.PREMIUM.value == "premium"

    def test_content_type_enum(self):
        """Test ContentType enum values."""
        assert ContentType.EMAIL.value == "email"
        assert ContentType.WEB_PAGE.value == "web_page"
        assert ContentType.SOCIAL_POST.value == "social_post"
        assert ContentType.NEWSLETTER.value == "newsletter"
        assert ContentType.PRODUCT_DESCRIPTION.value == "product_description"
        assert ContentType.BLOG_POST.value == "blog_post"