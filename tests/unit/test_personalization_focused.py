"""
Focused tests for Content Personalization Engine
Target: 70%+ coverage with efficient test design

Covers core functionality:
- Data classes and enums
- Engine initialization
- Personalization methods
- Helper functions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from halcytone_content_generator.services.personalization import (
    UserSegment,
    PersonalizationLevel,
    ContentType,
    UserPreference,
    PersonalizationContext,
    PersonalizedContent,
    ContentPersonalizationEngine,
    get_personalization_engine
)


# Test Data Classes and Enums

class TestDataClasses:
    """Test data class instantiation."""

    def test_user_segment_creation(self):
        """Test UserSegment dataclass."""
        segment = UserSegment(
            segment_id="test_segment",
            segment_name="Test Segment",
            confidence=0.85
        )
        assert segment.segment_id == "test_segment"
        assert segment.confidence == 0.85
        assert segment.engagement_level == "medium"

    def test_user_preference_creation(self):
        """Test UserPreference dataclass."""
        pref = UserPreference(
            user_id="user123",
            preference_type="tone",
            value="professional"
        )
        assert pref.user_id == "user123"
        assert pref.confidence == 1.0
        assert pref.source == "explicit"

    def test_personalization_context_creation(self):
        """Test PersonalizationContext dataclass."""
        segment = UserSegment("seg1", "Segment 1", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={"tone": "casual"},
            behavioral_data={"engagement": "high"},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.ADVANCED
        )
        assert context.user_id == "user123"
        assert context.personalization_level == PersonalizationLevel.ADVANCED

    def test_personalized_content_creation(self):
        """Test PersonalizedContent dataclass."""
        content = PersonalizedContent(
            content="Test content",
            personalization_score=0.85,
            applied_personalizations=["tone", "length"],
            segment_match_score=0.75,
            preference_match_score=0.80
        )
        assert content.content == "Test content"
        assert content.personalization_score == 0.85
        assert content.segment_match_score == 0.75
        assert content.preference_match_score == 0.80


class TestEnums:
    """Test enum values."""

    def test_personalization_level_values(self):
        """Test PersonalizationLevel enum."""
        assert PersonalizationLevel.BASIC.value == "basic"
        assert PersonalizationLevel.ADVANCED.value == "advanced"
        assert PersonalizationLevel.PREMIUM.value == "premium"

    def test_content_type_values(self):
        """Test ContentType enum."""
        assert ContentType.EMAIL.value == "email"
        assert ContentType.NEWSLETTER.value == "newsletter"
        assert ContentType.SOCIAL_POST.value == "social_post"


# Test ContentPersonalizationEngine

class TestContentPersonalizationEngine:
    """Test personalization engine."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        with patch('halcytone_content_generator.services.personalization.get_settings'):
            with patch('halcytone_content_generator.services.personalization.UserSegmentationService'):
                with patch('halcytone_content_generator.services.personalization.AIContentEnhancer'):
                    return ContentPersonalizationEngine()

    def test_engine_initialization(self, engine):
        """Test engine initializes."""
        assert engine is not None
        assert engine.personalization_templates is not None

    def test_initialize_personalization_templates(self, engine):
        """Test template initialization."""
        engine._initialize_personalization_templates()
        assert isinstance(engine.personalization_templates, dict)
        assert len(engine.personalization_templates) > 0

    def test_get_segment_specific_content(self, engine):
        """Test getting segment-specific content."""
        segment = UserSegment(
            segment_id="professionals",
            segment_name="Professionals",
            confidence=0.9
        )
        content = engine._get_segment_specific_content(segment)
        assert isinstance(content, dict)

    def test_get_preference_based_content(self, engine):
        """Test getting preference-based content."""
        preferences = {"tone": "professional", "length": "concise"}
        content = engine._get_preference_based_content(preferences)
        assert isinstance(content, dict)

    def test_calculate_segment_match_score(self, engine):
        """Test segment match score calculation."""
        segment = UserSegment("seg1", "Segment 1", 0.85)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC
        )
        score = engine._calculate_segment_match_score(context)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_calculate_preference_match_score(self, engine):
        """Test preference match score calculation."""
        segment = UserSegment("seg1", "Segment 1", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={"tone": "casual"},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC
        )
        score = engine._calculate_preference_match_score(context)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_calculate_personalization_score(self, engine):
        """Test overall personalization score."""
        score = engine._calculate_personalization_score(
            segment_score=0.8,
            preference_score=0.7,
            personalization_count=5,
            level=PersonalizationLevel.ADVANCED
        )
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_create_enhancement_prompt(self, engine):
        """Test enhancement prompt creation."""
        segment = UserSegment("professionals", "Professionals", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={
                "tone": {"value": "professional", "confidence": 1.0},
                "content_length": {"value": "medium", "confidence": 0.9}
            },
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.ADVANCED
        )
        prompt = engine._create_enhancement_prompt(context)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "professional" in prompt
        assert "medium" in prompt


# Test Edge Cases

class TestEdgeCases:
    """Test edge cases."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        with patch('halcytone_content_generator.services.personalization.get_settings'):
            with patch('halcytone_content_generator.services.personalization.UserSegmentationService'):
                with patch('halcytone_content_generator.services.personalization.AIContentEnhancer'):
                    return ContentPersonalizationEngine()

    def test_segment_with_low_confidence(self):
        """Test segment with low confidence."""
        segment = UserSegment("seg1", "Segment 1", 0.1)
        assert segment.confidence == 0.1

    def test_empty_preferences(self, engine):
        """Test with empty preferences."""
        content = engine._get_preference_based_content({})
        assert isinstance(content, dict)

    def test_personalization_context_minimal(self):
        """Test context with minimal data."""
        segment = UserSegment("seg1", "Segment 1", 0.5)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC
        )
        assert context.template_variables == {}

    def test_all_personalization_levels(self):
        """Test all personalization levels can be used."""
        levels = [
            PersonalizationLevel.BASIC,
            PersonalizationLevel.INTERMEDIATE,
            PersonalizationLevel.ADVANCED,
            PersonalizationLevel.PREMIUM
        ]
        for level in levels:
            assert level.value in ["basic", "intermediate", "advanced", "premium"]

    def test_all_content_types(self):
        """Test all content types."""
        types = [
            ContentType.EMAIL,
            ContentType.WEB_PAGE,
            ContentType.SOCIAL_POST,
            ContentType.NEWSLETTER,
            ContentType.PRODUCT_DESCRIPTION,
            ContentType.BLOG_POST
        ]
        for content_type in types:
            assert content_type.value is not None


# Test Async Methods

class TestAsyncMethods:
    """Test async personalization methods."""

    @pytest.fixture
    def engine(self):
        """Create engine instance with mocked dependencies."""
        with patch('halcytone_content_generator.services.personalization.get_settings'):
            with patch('halcytone_content_generator.services.personalization.UserSegmentationService'):
                with patch('halcytone_content_generator.services.personalization.AIContentEnhancer'):
                    return ContentPersonalizationEngine()

    @pytest.mark.asyncio
    async def test_track_user_preference_success(self, engine):
        """Test tracking user preference."""
        result = await engine.track_user_preference(
            user_id="user123",
            preference_type="tone",
            value="professional",
            confidence=0.9,
            source="explicit"
        )
        assert result is True
        assert "user123" in engine.user_preferences
        assert "tone" in engine.user_preferences["user123"]

    @pytest.mark.asyncio
    async def test_track_user_preference_multiple(self, engine):
        """Test tracking multiple preferences."""
        await engine.track_user_preference("user123", "tone", "casual")
        await engine.track_user_preference("user123", "content_length", "short")

        assert len(engine.user_preferences["user123"]) == 2
        assert engine.user_preferences["user123"]["tone"].value == "casual"
        assert engine.user_preferences["user123"]["content_length"].value == "short"

    @pytest.mark.asyncio
    async def test_get_user_preferences_empty(self, engine):
        """Test getting preferences for new user."""
        prefs = await engine.get_user_preferences("new_user")
        assert prefs == {}

    @pytest.mark.asyncio
    async def test_get_user_preferences_existing(self, engine):
        """Test getting existing user preferences."""
        await engine.track_user_preference("user123", "tone", "professional", 0.9)
        prefs = await engine.get_user_preferences("user123")

        assert "tone" in prefs
        assert prefs["tone"]["value"] == "professional"
        assert prefs["tone"]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_infer_preferences_from_read_time(self, engine):
        """Test inferring content length from read time."""
        behavioral_data = {"avg_read_time": 20}

        inferred = await engine.infer_preferences_from_behavior("user123", behavioral_data)

        assert "content_length" in inferred
        assert inferred["content_length"].value == "short"
        assert inferred["content_length"].source == "behavioral"

    @pytest.mark.asyncio
    async def test_infer_preferences_from_engagement_times(self, engine):
        """Test inferring time preference from engagement."""
        behavioral_data = {
            "engagement_times": ["08:30", "09:15", "08:45"]
        }

        inferred = await engine.infer_preferences_from_behavior("user123", behavioral_data)

        assert "preferred_time" in inferred
        assert inferred["preferred_time"].value == "morning"

    @pytest.mark.asyncio
    async def test_infer_preferences_from_interaction_types(self, engine):
        """Test inferring tone from interactions."""
        behavioral_data = {
            "interaction_types": {
                "formal": 8,
                "casual": 2
            }
        }

        inferred = await engine.infer_preferences_from_behavior("user123", behavioral_data)

        assert "tone" in inferred
        assert inferred["tone"].value == "formal"

    @pytest.mark.asyncio
    async def test_create_personalization_context_new_user(self, engine):
        """Test creating context for new user."""
        engine.segmentation_service.get_user_segments = Mock(return_value={})

        context = await engine.create_personalization_context(
            user_id="new_user",
            content_type=ContentType.EMAIL
        )

        assert context.user_id == "new_user"
        assert context.content_type == ContentType.EMAIL
        assert context.user_segment.segment_id == "general_user"

    @pytest.mark.asyncio
    async def test_create_personalization_context_with_segment(self, engine):
        """Test creating context with user segment."""
        from halcytone_content_generator.services.user_segmentation import SegmentCategory

        engine.segmentation_service.get_user_segments = Mock(
            return_value={SegmentCategory.INDUSTRY: "technology"}
        )

        context = await engine.create_personalization_context(
            user_id="user123",
            content_type=ContentType.EMAIL,
            additional_context={"user_profile": {"industry": "technology"}}
        )

        assert context.user_segment.segment_id == "technology"

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_email(self, engine):
        """Test dynamic content insertion for email."""
        segment = UserSegment("professionals", "Professionals", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={"tone": {"value": "professional", "confidence": 1.0}},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC,
            template_variables={"name": "John"}
        )

        content = "{greeting} This is a test email. {closing}"
        personalized, applied = await engine.apply_dynamic_content_insertion(content, context)

        assert "{greeting}" not in personalized
        assert "{closing}" not in personalized
        assert len(applied) > 0

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_web(self, engine):
        """Test dynamic content insertion for web page."""
        segment = UserSegment("professionals", "Professionals", 0.9,
                            characteristics={"preferred_cta_style": "action_oriented"})
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.WEB_PAGE,
            personalization_level=PersonalizationLevel.BASIC
        )

        content = "Check out our product! {cta}"
        personalized, applied = await engine.apply_dynamic_content_insertion(content, context)

        assert "{cta}" not in personalized
        assert any("cta" in p for p in applied)

    @pytest.mark.asyncio
    async def test_apply_dynamic_content_insertion_social(self, engine):
        """Test dynamic content insertion for social post."""
        segment = UserSegment("professional_services", "Professionals", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.SOCIAL_POST,
            personalization_level=PersonalizationLevel.BASIC
        )

        content = "Great news! {hashtags}"
        personalized, applied = await engine.apply_dynamic_content_insertion(content, context)

        assert "{hashtags}" not in personalized
        assert any("hashtags" in p for p in applied)

    @pytest.mark.asyncio
    async def test_generate_personalized_content_basic(self, engine):
        """Test generating personalized content."""
        segment = UserSegment("professionals", "Professionals", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={"tone": {"value": "professional", "confidence": 0.9}},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC
        )

        result = await engine.generate_personalized_content(
            "Test content",
            context,
            use_ai_enhancement=False
        )

        assert isinstance(result, PersonalizedContent)
        assert result.content is not None
        assert 0 <= result.personalization_score <= 1
        assert isinstance(result.applied_personalizations, list)

    @pytest.mark.asyncio
    async def test_generate_personalized_content_with_ai(self, engine):
        """Test generating content with AI enhancement."""
        # Mock AI enhancer
        mock_enhanced = Mock()
        mock_enhanced.enhanced_content = "Enhanced test content"
        engine.ai_enhancer.enhance_content = AsyncMock(return_value=mock_enhanced)

        segment = UserSegment("professionals", "Professionals", 0.9)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={"tone": {"value": "professional", "confidence": 0.9}},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.ADVANCED
        )

        result = await engine.generate_personalized_content(
            "Test content",
            context,
            use_ai_enhancement=True
        )

        assert "ai_enhancement" in result.applied_personalizations
        assert result.content == "Enhanced test content"

    @pytest.mark.asyncio
    async def test_generate_personalized_content_error_handling(self, engine):
        """Test error handling in content generation."""
        # Force an error by providing bad context
        segment = UserSegment("test", "Test", 0.5)
        context = PersonalizationContext(
            user_id="user123",
            user_segment=segment,
            preferences={},
            behavioral_data={},
            content_type=ContentType.EMAIL,
            personalization_level=PersonalizationLevel.BASIC
        )

        # Mock AI enhancer to raise exception
        engine.ai_enhancer.enhance_content = AsyncMock(side_effect=Exception("Test error"))

        result = await engine.generate_personalized_content(
            "Test content",
            context,
            use_ai_enhancement=True
        )

        # Should still return a result even on error
        assert isinstance(result, PersonalizedContent)

    @pytest.mark.asyncio
    async def test_get_personalization_analytics_empty(self, engine):
        """Test analytics with no users."""
        analytics = await engine.get_personalization_analytics()

        assert analytics["total_users_tracked"] == 0
        assert analytics["avg_preferences_per_user"] == 0

    @pytest.mark.asyncio
    async def test_get_personalization_analytics_with_users(self, engine):
        """Test analytics with tracked users."""
        await engine.track_user_preference("user1", "tone", "casual")
        await engine.track_user_preference("user1", "length", "short")
        await engine.track_user_preference("user2", "tone", "professional")

        analytics = await engine.get_personalization_analytics()

        assert analytics["total_users_tracked"] == 2
        assert analytics["avg_preferences_per_user"] == 1.5
        assert "tone" in analytics["preference_distribution"]

    @pytest.mark.asyncio
    async def test_get_personalization_analytics_user_specific(self, engine):
        """Test user-specific analytics."""
        await engine.track_user_preference("user123", "tone", "professional")
        await engine.track_user_preference("user123", "length", "medium")

        analytics = await engine.get_personalization_analytics(user_id="user123")

        assert "user_specific" in analytics
        assert analytics["user_specific"]["preference_count"] == 2


# Test Singleton

class TestSingleton:
    """Test singleton pattern."""

    def test_get_personalization_engine(self):
        """Test getting singleton instance."""
        with patch('halcytone_content_generator.services.personalization.get_settings'):
            with patch('halcytone_content_generator.services.personalization.UserSegmentationService'):
                with patch('halcytone_content_generator.services.personalization.AIContentEnhancer'):
                    engine1 = get_personalization_engine()
                    engine2 = get_personalization_engine()

                    assert engine1 is engine2
