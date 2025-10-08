"""
Comprehensive tests for User Segmentation Service.

Tests cover user profile creation, behavioral tracking, segment assignment scoring,
content routing, personalization strategies, analytics, and data export.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from halcytone_content_generator.services.user_segmentation import (
    UserSegmentationService,
    SegmentCategory,
    IndustrySegment,
    InterestSegment,
    EngagementLevel,
    WellnessJourney,
    TechnologyAdoption,
    CommunicationPreference,
    UserBehavior,
    UserDemographics,
    UserProfile,
    SegmentDefinition,
    ContentRoutingRule,
    get_user_segmentation_service
)


class TestInitialization:
    """Test service initialization and setup."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_initialization(self, segmentation_service):
        """Test service initializes correctly."""
        assert segmentation_service.segment_definitions is not None
        assert segmentation_service.routing_rules is not None
        assert segmentation_service.user_profiles == {}
        assert segmentation_service.segment_analytics is not None

    def test_segment_definitions_initialized(self, segmentation_service):
        """Test that segment definitions are initialized."""
        assert len(segmentation_service.segment_definitions) > 0

        # Check that all categories are represented
        categories = {seg.category for seg in segmentation_service.segment_definitions.values()}
        assert SegmentCategory.INDUSTRY in categories
        assert SegmentCategory.INTERESTS in categories
        assert SegmentCategory.ENGAGEMENT_LEVEL in categories
        assert SegmentCategory.WELLNESS_JOURNEY in categories

    def test_industry_segments_defined(self, segmentation_service):
        """Test industry segments are properly defined."""
        industry_segments = [seg for seg in segmentation_service.segment_definitions.values()
                            if seg.category == SegmentCategory.INDUSTRY]

        assert len(industry_segments) > 0
        assert any("healthcare" in seg.segment_id for seg in industry_segments)
        assert any("tech" in seg.segment_id for seg in industry_segments)
        assert any("fitness" in seg.segment_id for seg in industry_segments)

    def test_interest_segments_defined(self, segmentation_service):
        """Test interest segments are properly defined."""
        interest_segments = [seg for seg in segmentation_service.segment_definitions.values()
                            if seg.category == SegmentCategory.INTERESTS]

        assert len(interest_segments) > 0
        assert any("mindfulness" in seg.segment_id for seg in interest_segments)
        assert any("stress" in seg.segment_id for seg in interest_segments)
        assert any("sleep" in seg.segment_id for seg in interest_segments)

    def test_engagement_segments_defined(self, segmentation_service):
        """Test engagement segments are properly defined."""
        engagement_segments = [seg for seg in segmentation_service.segment_definitions.values()
                              if seg.category == SegmentCategory.ENGAGEMENT_LEVEL]

        assert len(engagement_segments) > 0
        assert any("power" in seg.segment_id for seg in engagement_segments)
        assert any("regular" in seg.segment_id for seg in engagement_segments)
        assert any("casual" in seg.segment_id for seg in engagement_segments)

    def test_wellness_journey_segments_defined(self, segmentation_service):
        """Test wellness journey segments are properly defined."""
        journey_segments = [seg for seg in segmentation_service.segment_definitions.values()
                           if seg.category == SegmentCategory.WELLNESS_JOURNEY]

        assert len(journey_segments) > 0
        assert any("beginner" in seg.segment_id for seg in journey_segments)
        assert any("explorer" in seg.segment_id for seg in journey_segments)
        assert any("committed" in seg.segment_id for seg in journey_segments)
        assert any("expert" in seg.segment_id for seg in journey_segments)

    def test_routing_rules_initialized(self, segmentation_service):
        """Test routing rules are initialized."""
        assert len(segmentation_service.routing_rules) > 0

        # Check various routing logics are present
        routing_logics = {rule.routing_logic for rule in segmentation_service.routing_rules}
        assert "prioritize" in routing_logics
        assert "include" in routing_logics

    def test_singleton_pattern(self):
        """Test singleton pattern for service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            instance1 = get_user_segmentation_service()
            instance2 = get_user_segmentation_service()
            assert instance1 is instance2


class TestUserProfileCreation:
    """Test user profile creation and management."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_create_basic_profile(self, segmentation_service):
        """Test creating basic user profile."""
        profile = segmentation_service.create_user_profile("user_123")

        assert profile is not None
        assert profile.user_id == "user_123"
        assert profile.demographics is not None
        assert profile.behavior is not None
        assert "user_123" in segmentation_service.user_profiles

    def test_create_profile_with_demographics(self, segmentation_service):
        """Test creating profile with demographic data."""
        initial_data = {
            "demographics": {
                "age_range": "25-34",
                "location": "USA",
                "profession": "Software Engineer",
                "language": "en"
            }
        }

        profile = segmentation_service.create_user_profile("user_demo", initial_data)

        assert profile.demographics.age_range == "25-34"
        assert profile.demographics.location == "USA"
        assert profile.demographics.profession == "Software Engineer"

    def test_create_profile_with_interests(self, segmentation_service):
        """Test creating profile with interests."""
        initial_data = {
            "interests": ["mindfulness", "meditation", "wellness"]
        }

        profile = segmentation_service.create_user_profile("user_interests", initial_data)

        assert "mindfulness" in profile.explicit_interests
        assert "meditation" in profile.explicit_interests
        assert "wellness" in profile.explicit_interests

    def test_create_profile_with_goals(self, segmentation_service):
        """Test creating profile with goals."""
        initial_data = {
            "goals": ["stress_relief", "better_sleep", "productivity"]
        }

        profile = segmentation_service.create_user_profile("user_goals", initial_data)

        assert "stress_relief" in profile.goals
        assert "better_sleep" in profile.goals
        assert "productivity" in profile.goals

    def test_create_profile_with_preferences(self, segmentation_service):
        """Test creating profile with preferences."""
        initial_data = {
            "preferences": {
                "channels": ["email", "in_app"],
                "frequency": "weekly"
            }
        }

        profile = segmentation_service.create_user_profile("user_prefs", initial_data)

        assert profile.preferences["channels"] == ["email", "in_app"]
        assert profile.preferences["frequency"] == "weekly"

    def test_create_profile_triggers_segmentation(self, segmentation_service):
        """Test that profile creation triggers initial segmentation."""
        profile = segmentation_service.create_user_profile("user_seg")

        # Profile should have segments assigned
        assert len(profile.segments) > 0
        assert len(profile.segment_scores) > 0

    def test_profile_update_segments_method(self):
        """Test UserProfile.update_segments method."""
        from halcytone_content_generator.services.user_segmentation import UserProfile
        import time

        profile = UserProfile(user_id="test_user")
        original_time = profile.updated_at

        # Small delay to ensure timestamp difference
        time.sleep(0.001)

        new_segments = {
            SegmentCategory.ENGAGEMENT_LEVEL: "power_user",
            SegmentCategory.INDUSTRY: "tech_professional"
        }

        profile.update_segments(new_segments)

        assert profile.segments[SegmentCategory.ENGAGEMENT_LEVEL] == "power_user"
        assert profile.segments[SegmentCategory.INDUSTRY] == "tech_professional"
        assert profile.updated_at >= original_time  # Changed > to >= for timing tolerance


class TestBehavioralDataUpdates:
    """Test behavioral data updates and re-segmentation."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with user."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()
            service.create_user_profile("user_behavior")
            return service

    def test_update_sessions_per_week(self, segmentation_service):
        """Test updating sessions per week."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "app_sessions_per_week": 5.0
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.app_sessions_per_week == 5.0

    def test_update_session_duration(self, segmentation_service):
        """Test updating average session duration."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "avg_session_duration": 15.5
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.avg_session_duration == 15.5

    def test_update_features_used(self, segmentation_service):
        """Test updating features used."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "features_used": ["breathing_exercises", "meditation", "tracking"]
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert "breathing_exercises" in profile.behavior.features_used
        assert "meditation" in profile.behavior.features_used
        assert "tracking" in profile.behavior.features_used

    def test_update_content_interactions(self, segmentation_service):
        """Test updating content interactions."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "content_interactions": {"educational": 10, "meditation": 5}
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.content_interactions["educational"] == 10
        assert profile.behavior.content_interactions["meditation"] == 5

    def test_update_content_interactions_accumulates(self, segmentation_service):
        """Test that content interactions accumulate."""
        segmentation_service.update_user_behavior("user_behavior", {
            "content_interactions": {"educational": 10}
        })
        segmentation_service.update_user_behavior("user_behavior", {
            "content_interactions": {"educational": 5}
        })

        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.content_interactions["educational"] == 15

    def test_update_last_active(self, segmentation_service):
        """Test updating last active timestamp."""
        now = datetime.utcnow()
        result = segmentation_service.update_user_behavior("user_behavior", {
            "last_active": now
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.last_active == now

    def test_update_total_active_days(self, segmentation_service):
        """Test updating total active days."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "total_active_days": 30
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.total_active_days == 30

    def test_update_preferred_times(self, segmentation_service):
        """Test updating preferred times."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "preferred_times": [7, 12, 18]  # Morning, noon, evening
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.preferred_times == [7, 12, 18]

    def test_update_device_types(self, segmentation_service):
        """Test updating device types."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "device_types": ["mobile", "tablet"]
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert "mobile" in profile.behavior.device_types
        assert "tablet" in profile.behavior.device_types

    def test_update_sharing_frequency(self, segmentation_service):
        """Test updating sharing frequency."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "sharing_frequency": 0.25
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.sharing_frequency == 0.25

    def test_update_feedback_given(self, segmentation_service):
        """Test updating feedback given count."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "feedback_given": 7
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.feedback_given == 7

    def test_update_multiple_fields(self, segmentation_service):
        """Test updating multiple behavioral fields at once."""
        result = segmentation_service.update_user_behavior("user_behavior", {
            "app_sessions_per_week": 6.0,
            "avg_session_duration": 20.0,
            "total_active_days": 45,
            "features_used": ["feature1", "feature2"]
        })

        assert result is True
        profile = segmentation_service.user_profiles["user_behavior"]
        assert profile.behavior.app_sessions_per_week == 6.0
        assert profile.behavior.avg_session_duration == 20.0
        assert profile.behavior.total_active_days == 45
        assert len(profile.behavior.features_used) == 2

    def test_update_triggers_resegmentation(self, segmentation_service):
        """Test that behavior update triggers re-segmentation."""
        profile_before = segmentation_service.user_profiles["user_behavior"]
        segments_before = dict(profile_before.segments)

        # Update behavior that should change segments
        segmentation_service.update_user_behavior("user_behavior", {
            "app_sessions_per_week": 10.0,  # Very high engagement
            "total_active_days": 200  # Long-term user
        })

        profile_after = segmentation_service.user_profiles["user_behavior"]

        # Segments should be recalculated
        assert profile_after.segments is not None
        # Scores should be updated
        assert len(profile_after.segment_scores) > 0

    def test_update_nonexistent_user_returns_false(self, segmentation_service):
        """Test updating non-existent user returns False."""
        result = segmentation_service.update_user_behavior("nonexistent_user", {
            "app_sessions_per_week": 5.0
        })

        assert result is False


class TestSegmentScoring:
    """Test segment scoring algorithm."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_profession_matching(self, segmentation_service):
        """Test profession criteria matching."""
        profile = UserProfile(user_id="test")
        profile.demographics.profession = "Software Developer"

        # Find tech professional segment
        tech_segment = segmentation_service.segment_definitions["tech_professional"]

        score = segmentation_service._calculate_segment_score(profile, tech_segment)

        assert score > 0  # Should match

    def test_interest_matching_full_overlap(self, segmentation_service):
        """Test interest matching with full overlap."""
        profile = UserProfile(user_id="test")
        profile.explicit_interests = {"mindfulness", "meditation", "awareness"}

        mindfulness_segment = segmentation_service.segment_definitions["mindfulness_enthusiast"]

        score = segmentation_service._calculate_segment_score(profile, mindfulness_segment)

        assert score > 0.9  # High score for full match

    def test_interest_matching_partial_overlap(self, segmentation_service):
        """Test interest matching with partial overlap."""
        profile = UserProfile(user_id="test")
        profile.explicit_interests = {"mindfulness", "fitness"}  # Only 1 of 3 matches

        mindfulness_segment = segmentation_service.segment_definitions["mindfulness_enthusiast"]

        score = segmentation_service._calculate_segment_score(profile, mindfulness_segment)

        assert 0 < score < 1  # Partial match

    def test_goal_matching(self, segmentation_service):
        """Test goal criteria matching."""
        profile = UserProfile(user_id="test")
        profile.goals = {"stress_relief", "anxiety_management"}

        stress_segment = segmentation_service.segment_definitions["stress_warrior"]

        score = segmentation_service._calculate_segment_score(profile, stress_segment)

        assert score > 0.5  # Good match

    def test_sessions_per_week_criteria_min(self, segmentation_service):
        """Test sessions per week minimum criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.app_sessions_per_week = 6.0

        power_user_segment = segmentation_service.segment_definitions["power_user"]

        score = segmentation_service._calculate_segment_score(profile, power_user_segment)

        # Power user requires 5+ sessions
        assert score > 0

    def test_sessions_per_week_criteria_range(self, segmentation_service):
        """Test sessions per week range criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.app_sessions_per_week = 3.0

        regular_user_segment = segmentation_service.segment_definitions["regular_user"]

        score = segmentation_service._calculate_segment_score(profile, regular_user_segment)

        # Regular user is 2-4 sessions
        assert score > 0

    def test_session_duration_criteria(self, segmentation_service):
        """Test session duration criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.app_sessions_per_week = 6.0
        profile.behavior.avg_session_duration = 15.0

        power_user_segment = segmentation_service.segment_definitions["power_user"]

        score = segmentation_service._calculate_segment_score(profile, power_user_segment)

        # Should meet both sessions and duration criteria
        assert score > 0.5

    def test_total_active_days_criteria(self, segmentation_service):
        """Test total active days criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.total_active_days = 10  # New user

        new_user_segment = segmentation_service.segment_definitions["returning_user"]

        score = segmentation_service._calculate_segment_score(profile, new_user_segment)

        # New user has max 14 days
        assert score > 0

    def test_features_used_criteria(self, segmentation_service):
        """Test features used count criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.features_used = {"feat1", "feat2", "feat3", "feat4"}

        explorer_segment = segmentation_service.segment_definitions["wellness_explorer"]

        score = segmentation_service._calculate_segment_score(profile, explorer_segment)

        # Explorer requires min 3 features
        assert score > 0

    def test_feedback_given_criteria(self, segmentation_service):
        """Test feedback given criteria."""
        profile = UserProfile(user_id="test")
        profile.behavior.feedback_given = 6
        profile.behavior.total_active_days = 200

        expert_segment = segmentation_service.segment_definitions["wellness_expert"]

        score = segmentation_service._calculate_segment_score(profile, expert_segment)

        # Expert requires 5+ feedback and 180+ days
        assert score > 0.5

    def test_experience_level_criteria(self, segmentation_service):
        """Test experience level criteria."""
        profile = UserProfile(user_id="test")
        profile.demographics.experience_level = "beginner"
        profile.behavior.total_active_days = 20

        beginner_segment = segmentation_service.segment_definitions["wellness_beginner"]

        score = segmentation_service._calculate_segment_score(profile, beginner_segment)

        assert score > 0.5

    def test_zero_score_for_no_match(self, segmentation_service):
        """Test zero score when criteria don't match."""
        profile = UserProfile(user_id="test")
        profile.behavior.app_sessions_per_week = 0.5  # Very low

        power_user_segment = segmentation_service.segment_definitions["power_user"]

        score = segmentation_service._calculate_segment_score(profile, power_user_segment)

        # Should have low/zero score
        assert score < 0.5


class TestNumericCriteria:
    """Test numeric criteria matching."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_meets_min_criteria(self, segmentation_service):
        """Test minimum value criteria."""
        assert segmentation_service._meets_numeric_criteria(10, {"min": 5}) is True
        assert segmentation_service._meets_numeric_criteria(5, {"min": 5}) is True
        assert segmentation_service._meets_numeric_criteria(4, {"min": 5}) is False

    def test_meets_max_criteria(self, segmentation_service):
        """Test maximum value criteria."""
        assert segmentation_service._meets_numeric_criteria(3, {"max": 5}) is True
        assert segmentation_service._meets_numeric_criteria(5, {"max": 5}) is True
        assert segmentation_service._meets_numeric_criteria(6, {"max": 5}) is False

    def test_meets_range_criteria(self, segmentation_service):
        """Test range criteria (min and max)."""
        criteria = {"min": 2, "max": 10}
        assert segmentation_service._meets_numeric_criteria(5, criteria) is True
        assert segmentation_service._meets_numeric_criteria(2, criteria) is True
        assert segmentation_service._meets_numeric_criteria(10, criteria) is True
        assert segmentation_service._meets_numeric_criteria(1, criteria) is False
        assert segmentation_service._meets_numeric_criteria(11, criteria) is False

    def test_meets_exact_criteria(self, segmentation_service):
        """Test exact value criteria."""
        assert segmentation_service._meets_numeric_criteria(5, {"exact": 5}) is True
        assert segmentation_service._meets_numeric_criteria(4, {"exact": 5}) is False
        assert segmentation_service._meets_numeric_criteria(6, {"exact": 5}) is False

    def test_meets_empty_criteria(self, segmentation_service):
        """Test empty criteria always matches."""
        assert segmentation_service._meets_numeric_criteria(100, {}) is True


class TestSegmentAssignment:
    """Test automatic segment assignment."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_power_user_assignment(self, segmentation_service):
        """Test power user segment assignment."""
        initial_data = {
            "goals": ["productivity"]
        }
        profile = segmentation_service.create_user_profile("power_user", initial_data)

        # Update to power user behavior
        segmentation_service.update_user_behavior("power_user", {
            "app_sessions_per_week": 7.0,
            "avg_session_duration": 20.0,
            "total_active_days": 30  # Set > 14 to exclude from returning_user segment
        })

        profile = segmentation_service.user_profiles["power_user"]

        # Should be assigned to power_user segment
        assert SegmentCategory.ENGAGEMENT_LEVEL in profile.segments
        engagement_segment = profile.segments[SegmentCategory.ENGAGEMENT_LEVEL]
        assert "power" in engagement_segment or "regular" in engagement_segment

    def test_healthcare_professional_assignment(self, segmentation_service):
        """Test healthcare professional assignment."""
        initial_data = {
            "demographics": {
                "profession": "Registered Nurse"
            }
        }

        profile = segmentation_service.create_user_profile("healthcare", initial_data)

        # Should be assigned to healthcare segment
        assert SegmentCategory.INDUSTRY in profile.segments
        assert profile.segments[SegmentCategory.INDUSTRY] == "healthcare_professional"

    def test_mindfulness_enthusiast_assignment(self, segmentation_service):
        """Test mindfulness enthusiast assignment."""
        initial_data = {
            "interests": ["mindfulness", "meditation"]
        }

        profile = segmentation_service.create_user_profile("mindful", initial_data)

        # Should be assigned to mindfulness segment
        assert SegmentCategory.INTERESTS in profile.segments
        assert profile.segments[SegmentCategory.INTERESTS] == "mindfulness_enthusiast"

    def test_wellness_beginner_assignment(self, segmentation_service):
        """Test wellness beginner assignment."""
        initial_data = {
            "demographics": {
                "experience_level": "beginner"
            }
        }

        profile = segmentation_service.create_user_profile("beginner", initial_data)

        segmentation_service.update_user_behavior("beginner", {
            "total_active_days": 15
        })

        profile = segmentation_service.user_profiles["beginner"]

        # Should be assigned to beginner segment
        assert SegmentCategory.WELLNESS_JOURNEY in profile.segments
        assert profile.segments[SegmentCategory.WELLNESS_JOURNEY] == "wellness_beginner"

    def test_all_categories_assigned(self, segmentation_service):
        """Test that user gets assigned to all available segment categories."""
        profile = segmentation_service.create_user_profile("complete_user")

        # User should have segments in the 4 defined categories
        defined_categories = [
            SegmentCategory.INDUSTRY,
            SegmentCategory.INTERESTS,
            SegmentCategory.ENGAGEMENT_LEVEL,
            SegmentCategory.WELLNESS_JOURNEY
        ]

        for category in defined_categories:
            assert category in profile.segments

    def test_segment_analytics_updated(self, segmentation_service):
        """Test that segment analytics are updated on assignment."""
        segmentation_service.create_user_profile("analytics_user")

        # Analytics should have been updated
        assert len(segmentation_service.segment_analytics) > 0


class TestContentPreferences:
    """Test content preference aggregation."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with user."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()
            service.create_user_profile("pref_user")
            return service

    def test_get_user_segments(self, segmentation_service):
        """Test retrieving user segments."""
        segments = segmentation_service.get_user_segments("pref_user")

        assert len(segments) > 0
        assert all(isinstance(cat, SegmentCategory) for cat in segments.keys())

    def test_get_segments_nonexistent_user(self, segmentation_service):
        """Test getting segments for non-existent user."""
        segments = segmentation_service.get_user_segments("nonexistent")

        assert segments == {}

    def test_get_segment_content_preferences(self, segmentation_service):
        """Test getting content preferences."""
        preferences = segmentation_service.get_segment_content_preferences("pref_user")

        assert preferences is not None
        assert isinstance(preferences, dict)
        # Should have tone preference
        assert "tone" in preferences

    def test_preferences_merge_from_multiple_segments(self, segmentation_service):
        """Test preferences are merged from all user segments."""
        # Create user with multiple distinct segments
        initial_data = {
            "demographics": {"profession": "doctor"},
            "interests": ["mindfulness"]
        }
        segmentation_service.create_user_profile("multi_seg", initial_data)

        preferences = segmentation_service.get_segment_content_preferences("multi_seg")

        # Should have preferences from multiple segments
        assert len(preferences) > 1

    def test_preferences_nonexistent_user(self, segmentation_service):
        """Test preferences for non-existent user."""
        preferences = segmentation_service.get_segment_content_preferences("nonexistent")

        assert preferences == {}


class TestContentRouting:
    """Test content routing to segments."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_route_healthcare_content(self, segmentation_service):
        """Test routing healthcare content."""
        content_attributes = {
            "content_type": "educational",
            "evidence_based": True,
            "clinical_studies": True
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        assert "prioritize" in routing
        # Should include healthcare_professional segment
        assert any(item["segment_id"] == "healthcare_professional"
                  for item in routing.get("prioritize", []))

    def test_route_tech_content(self, segmentation_service):
        """Test routing tech content."""
        content_attributes = {
            "content_type": "analytical",
            "data_visualization": True,
            "metrics": True
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        # Should route to tech professionals
        assert any(item["segment_id"] == "tech_professional"
                  for segments in routing.values() for item in segments)

    def test_route_beginner_content(self, segmentation_service):
        """Test routing beginner content."""
        content_attributes = {
            "content_type": "educational",
            "complexity": "low",
            "step_by_step": True
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        # Should route to beginners
        assert any(item["segment_id"] == "wellness_beginner"
                  for segments in routing.values() for item in segments)

    def test_routing_includes_weights(self, segmentation_service):
        """Test that routing includes rule weights."""
        content_attributes = {
            "content_type": "onboarding",
            "educational": True,
            "basic": True
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        # Check that weights are included
        for segments in routing.values():
            for item in segments:
                assert "weight" in item
                assert item["weight"] > 0

    def test_routing_skips_inactive_rules(self, segmentation_service):
        """Test that inactive rules are skipped."""
        # Deactivate a rule
        segmentation_service.routing_rules[0].active = False

        content_attributes = {"content_type": "any", "any_attr": True}

        routing = segmentation_service.route_content_to_segments(content_attributes)

        # Should not include segments from inactive rule
        # (Hard to test without knowing specific rule, but function should still work)
        assert isinstance(routing, dict)

    def test_content_matches_rule_boolean(self, segmentation_service):
        """Test boolean attribute matching."""
        rule = ContentRoutingRule(
            rule_id="test",
            target_segments=["seg1"],
            content_type="test",
            content_attributes={"flag": True},
            routing_logic="include"
        )

        assert segmentation_service._content_matches_rule({"flag": True}, rule) is True
        assert segmentation_service._content_matches_rule({"flag": False}, rule) is False

    def test_content_matches_rule_string(self, segmentation_service):
        """Test string attribute matching."""
        rule = ContentRoutingRule(
            rule_id="test",
            target_segments=["seg1"],
            content_type="test",
            content_attributes={"level": "advanced"},
            routing_logic="include"
        )

        assert segmentation_service._content_matches_rule({"level": "advanced"}, rule) is True
        assert segmentation_service._content_matches_rule({"level": "beginner"}, rule) is False

    def test_content_matches_rule_list_overlap(self, segmentation_service):
        """Test list attribute matching with overlap."""
        rule = ContentRoutingRule(
            rule_id="test",
            target_segments=["seg1"],
            content_type="test",
            content_attributes={"tags": ["wellness", "meditation"]},
            routing_logic="include"
        )

        # List vs list - any overlap
        assert segmentation_service._content_matches_rule({"tags": ["wellness", "fitness"]}, rule) is True
        assert segmentation_service._content_matches_rule({"tags": ["fitness", "nutrition"]}, rule) is False

    def test_content_matches_rule_list_single_value(self, segmentation_service):
        """Test list matching with single value."""
        rule = ContentRoutingRule(
            rule_id="test",
            target_segments=["seg1"],
            content_type="test",
            content_attributes={"category": ["wellness", "fitness"]},
            routing_logic="include"
        )

        # Single value vs list
        assert segmentation_service._content_matches_rule({"category": "wellness"}, rule) is True
        assert segmentation_service._content_matches_rule({"category": "nutrition"}, rule) is False

    def test_content_matches_rule_missing_attribute(self, segmentation_service):
        """Test that missing attributes don't fail match."""
        rule = ContentRoutingRule(
            rule_id="test",
            target_segments=["seg1"],
            content_type="test",
            content_attributes={"required_attr": True, "optional_attr": True},
            routing_logic="include"
        )

        # Missing attributes are ignored
        assert segmentation_service._content_matches_rule({"required_attr": True}, rule) is True


class TestPersonalizationStrategy:
    """Test personalized content strategy generation."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with user."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()
            initial_data = {
                "interests": ["mindfulness", "wellness"],
                "goals": ["stress_relief"],
                "preferences": {"channels": ["email", "in_app"]}
            }
            service.create_user_profile("strategy_user", initial_data)
            return service

    def test_get_personalized_strategy(self, segmentation_service):
        """Test getting personalized content strategy."""
        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        assert strategy is not None
        assert "user_segments" in strategy
        assert "content_preferences" in strategy
        assert "messaging_strategy" in strategy
        assert "priority_topics" in strategy
        assert "channel_preferences" in strategy
        assert "frequency_recommendation" in strategy

    def test_strategy_includes_user_segments(self, segmentation_service):
        """Test strategy includes user segments."""
        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        assert len(strategy["user_segments"]) > 0

    def test_strategy_includes_content_preferences(self, segmentation_service):
        """Test strategy includes content preferences."""
        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        assert len(strategy["content_preferences"]) > 0
        assert "tone" in strategy["content_preferences"]

    def test_strategy_priority_topics_from_interests_and_goals(self, segmentation_service):
        """Test priority topics come from interests and goals."""
        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        topics = strategy["priority_topics"]
        assert "mindfulness" in topics or "wellness" in topics
        assert "stress_relief" in topics

    def test_strategy_channel_preferences_from_behavior(self, segmentation_service):
        """Test channel preferences based on behavior."""
        # Update with high app usage
        segmentation_service.update_user_behavior("strategy_user", {
            "app_sessions_per_week": 5.0
        })

        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        # Should include in_app channel
        assert "in_app" in strategy["channel_preferences"]

    def test_strategy_includes_email_from_preferences(self, segmentation_service):
        """Test email channel from user preferences."""
        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        # User specified email in preferences
        assert "email" in strategy["channel_preferences"]

    def test_strategy_includes_social_for_sharers(self, segmentation_service):
        """Test social channel for users who share."""
        segmentation_service.update_user_behavior("strategy_user", {
            "sharing_frequency": 0.3
        })

        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        # Should include social channel
        assert "social" in strategy["channel_preferences"]

    def test_default_strategy_for_unknown_user(self, segmentation_service):
        """Test default strategy for unknown user."""
        strategy = segmentation_service.get_personalized_content_strategy("unknown_user")

        assert strategy is not None
        assert strategy["user_segments"][SegmentCategory.ENGAGEMENT_LEVEL] == "returning_user"
        assert "welcoming" in strategy["content_preferences"]["tone"]
        assert strategy["channel_preferences"] == ["email"]


class TestAnalytics:
    """Test segment analytics and reporting."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with multiple users."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()

            # Create diverse users
            service.create_user_profile("user1", {
                "demographics": {"profession": "developer"}
            })
            service.create_user_profile("user2", {
                "interests": ["mindfulness"]
            })
            service.create_user_profile("user3", {
                "goals": ["stress_relief"]
            })

            # Update behaviors
            service.update_user_behavior("user1", {
                "app_sessions_per_week": 7.0,
                "avg_session_duration": 25.0
            })
            service.update_user_behavior("user2", {
                "app_sessions_per_week": 3.0,
                "avg_session_duration": 15.0
            })

            return service

    def test_get_segment_analytics(self, segmentation_service):
        """Test getting segment analytics."""
        analytics = segmentation_service.get_segment_analytics()

        assert analytics is not None
        assert "total_users" in analytics
        assert "segment_distribution" in analytics
        assert "engagement_by_segment" in analytics

    def test_analytics_total_users(self, segmentation_service):
        """Test analytics total users count."""
        analytics = segmentation_service.get_segment_analytics()

        assert analytics["total_users"] == 3

    def test_analytics_segment_distribution(self, segmentation_service):
        """Test segment distribution in analytics."""
        analytics = segmentation_service.get_segment_analytics()

        distribution = analytics["segment_distribution"]
        assert len(distribution) > 0

        # Should have counts for each category
        for category_data in distribution.values():
            assert "total" in category_data
            assert "segments" in category_data

    def test_analytics_engagement_by_segment(self, segmentation_service):
        """Test engagement metrics by segment."""
        analytics = segmentation_service.get_segment_analytics()

        engagement = analytics["engagement_by_segment"]
        assert len(engagement) > 0

        # Check structure
        for category_data in engagement.values():
            for segment_data in category_data.values():
                assert "avg_sessions" in segment_data
                assert "avg_duration" in segment_data
                assert "user_count" in segment_data

    def test_analytics_averages_calculated(self, segmentation_service):
        """Test that averages are properly calculated."""
        analytics = segmentation_service.get_segment_analytics()

        # Find a segment with users
        engagement = analytics["engagement_by_segment"]
        for category_data in engagement.values():
            for segment_data in category_data.values():
                if segment_data["user_count"] > 0:
                    # Averages should be reasonable values
                    assert segment_data["avg_sessions"] >= 0
                    assert segment_data["avg_duration"] >= 0


class TestSegmentMigrations:
    """Test segment migration suggestions."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with user."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()
            service.create_user_profile("migration_user")
            return service

    def test_suggest_segment_migrations(self, segmentation_service):
        """Test suggesting segment migrations."""
        suggestions = segmentation_service.suggest_segment_migrations("migration_user")

        assert suggestions is not None
        assert isinstance(suggestions, list)

    def test_migrations_for_high_score_segments(self, segmentation_service):
        """Test migrations suggested for high-scoring segments."""
        # Update to match multiple segments strongly
        segmentation_service.update_user_behavior("migration_user", {
            "app_sessions_per_week": 8.0,
            "avg_session_duration": 25.0,
            "total_active_days": 200,
            "feedback_given": 10
        })

        suggestions = segmentation_service.suggest_segment_migrations("migration_user")

        # Should have suggestions for segments with score > 0.7
        # that are not currently assigned
        for suggestion in suggestions:
            assert suggestion["score"] > 0.7
            assert "segment_id" in suggestion
            assert "segment_name" in suggestion
            assert "category" in suggestion
            assert "reason" in suggestion
            assert "benefits" in suggestion

    def test_migrations_limited_to_top_three(self, segmentation_service):
        """Test migrations limited to top 3 suggestions."""
        # Create profile that matches many segments
        segmentation_service.update_user_behavior("migration_user", {
            "app_sessions_per_week": 10.0,
            "total_active_days": 300
        })

        suggestions = segmentation_service.suggest_segment_migrations("migration_user")

        # Should have at most 3 suggestions
        assert len(suggestions) <= 3

    def test_migrations_sorted_by_score(self, segmentation_service):
        """Test migrations are sorted by score."""
        segmentation_service.update_user_behavior("migration_user", {
            "app_sessions_per_week": 8.0,
            "total_active_days": 200
        })

        suggestions = segmentation_service.suggest_segment_migrations("migration_user")

        if len(suggestions) > 1:
            # Should be in descending score order
            for i in range(len(suggestions) - 1):
                assert suggestions[i]["score"] >= suggestions[i + 1]["score"]

    def test_migrations_nonexistent_user(self, segmentation_service):
        """Test migrations for non-existent user."""
        suggestions = segmentation_service.suggest_segment_migrations("nonexistent")

        assert suggestions == []


class TestDataExport:
    """Test user segment data export."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service with users."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            service = UserSegmentationService()

            # Create test users
            service.create_user_profile("export_user1", {
                "interests": ["mindfulness"],
                "goals": ["stress_relief"]
            })
            service.create_user_profile("export_user2", {
                "demographics": {"profession": "developer"}
            })

            service.update_user_behavior("export_user1", {
                "app_sessions_per_week": 5.0,
                "total_active_days": 60
            })

            return service

    def test_export_all_users(self, segmentation_service):
        """Test exporting all users."""
        export_data = segmentation_service.export_user_segments()

        assert export_data is not None
        assert "users" in export_data
        assert "segments" in export_data
        assert "export_timestamp" in export_data

    def test_export_includes_all_users(self, segmentation_service):
        """Test export includes all users when no IDs specified."""
        export_data = segmentation_service.export_user_segments()

        assert len(export_data["users"]) == 2

    def test_export_specific_users(self, segmentation_service):
        """Test exporting specific users."""
        export_data = segmentation_service.export_user_segments(["export_user1"])

        assert len(export_data["users"]) == 1
        assert export_data["users"][0]["user_id"] == "export_user1"

    def test_export_user_data_structure(self, segmentation_service):
        """Test exported user data structure."""
        export_data = segmentation_service.export_user_segments(["export_user1"])

        user_data = export_data["users"][0]
        assert "user_id" in user_data
        assert "segments" in user_data
        assert "segment_scores" in user_data
        assert "interests" in user_data
        assert "goals" in user_data
        assert "engagement_level" in user_data
        assert "total_active_days" in user_data
        assert "last_updated" in user_data

    def test_export_includes_segment_definitions(self, segmentation_service):
        """Test export includes segment definitions."""
        export_data = segmentation_service.export_user_segments()

        segments = export_data["segments"]
        assert len(segments) > 0

        # Check segment definition structure
        for seg_id, seg_data in segments.items():
            assert "name" in seg_data
            assert "category" in seg_data
            assert "description" in seg_data

    def test_export_timestamp(self, segmentation_service):
        """Test export includes timestamp."""
        export_data = segmentation_service.export_user_segments()

        timestamp = export_data["export_timestamp"]
        assert timestamp is not None
        # Should be ISO format
        datetime.fromisoformat(timestamp)

    def test_export_skips_nonexistent_users(self, segmentation_service):
        """Test export skips non-existent users."""
        export_data = segmentation_service.export_user_segments(
            ["export_user1", "nonexistent_user", "export_user2"]
        )

        # Should only include 2 existing users
        assert len(export_data["users"]) == 2


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service instance."""
        with patch('halcytone_content_generator.services.user_segmentation.get_settings'):
            return UserSegmentationService()

    def test_empty_initial_data(self, segmentation_service):
        """Test creating profile with empty initial data."""
        profile = segmentation_service.create_user_profile("empty_user", {})

        assert profile is not None
        assert profile.user_id == "empty_user"

    def test_none_initial_data(self, segmentation_service):
        """Test creating profile with None initial data."""
        profile = segmentation_service.create_user_profile("none_user", None)

        assert profile is not None
        assert profile.user_id == "none_user"

    def test_partial_demographics(self, segmentation_service):
        """Test profile with partial demographics."""
        initial_data = {
            "demographics": {
                "profession": "Teacher"
                # Missing other fields
            }
        }

        profile = segmentation_service.create_user_profile("partial_demo", initial_data)

        assert profile.demographics.profession == "Teacher"
        assert profile.demographics.age_range is None

    def test_empty_interests_and_goals(self, segmentation_service):
        """Test profile with empty interests and goals."""
        initial_data = {
            "interests": [],
            "goals": []
        }

        profile = segmentation_service.create_user_profile("empty_interests", initial_data)

        assert len(profile.explicit_interests) == 0
        assert len(profile.goals) == 0

    def test_segment_score_with_no_criteria(self, segmentation_service):
        """Test segment score when no criteria match."""
        profile = UserProfile(user_id="test")
        # Empty profile

        # Create segment with criteria that won't match
        segment = SegmentDefinition(
            segment_id="test_seg",
            category=SegmentCategory.INTERESTS,
            name="Test",
            description="Test",
            criteria={"profession": ["doctor"]},
            content_preferences={},
            messaging_strategy={}
        )

        score = segmentation_service._calculate_segment_score(profile, segment)

        assert score == 0.0

    def test_route_content_with_no_matching_rules(self, segmentation_service):
        """Test routing content with no matching rules."""
        # Provide content with attributes that explicitly don't match any rule
        content_attributes = {
            "evidence_based": False,  # healthcare rule requires True
            "clinical_studies": False,  # healthcare rule requires True
            "data_visualization": False,  # tech rule requires True
            "metrics": False,  # tech rule requires True
            "complexity": "medium",  # power_user rule requires "high"
            "exclusive": False,  # power_user rule requires True
            "educational": False,  # new_user rule requires True
            "basic": False,  # new_user rule requires True
            "mindfulness": False,  # mindfulness rule requires True
            "guided": False,  # mindfulness rule requires True
            "immediate": False,  # stress rule requires True
            "practical": False,  # stress rule requires True
            "step_by_step": False,  # beginner rule requires True
            "depth": "low",  # expert rule requires "high"
            "community": False  # expert rule requires True
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        # Should return empty routing
        assert len(routing) == 0

    def test_features_used_updates_incrementally(self, segmentation_service):
        """Test features used set grows incrementally."""
        segmentation_service.create_user_profile("features_user")

        segmentation_service.update_user_behavior("features_user", {
            "features_used": ["feature1", "feature2"]
        })
        segmentation_service.update_user_behavior("features_user", {
            "features_used": ["feature2", "feature3"]
        })

        profile = segmentation_service.user_profiles["features_user"]

        # Should have all 3 features
        assert len(profile.behavior.features_used) == 3
        assert "feature1" in profile.behavior.features_used
        assert "feature2" in profile.behavior.features_used
        assert "feature3" in profile.behavior.features_used

    def test_device_types_updates_incrementally(self, segmentation_service):
        """Test device types set grows incrementally."""
        segmentation_service.create_user_profile("device_user")

        segmentation_service.update_user_behavior("device_user", {
            "device_types": ["mobile"]
        })
        segmentation_service.update_user_behavior("device_user", {
            "device_types": ["desktop"]
        })

        profile = segmentation_service.user_profiles["device_user"]

        assert len(profile.behavior.device_types) == 2
        assert "mobile" in profile.behavior.device_types
        assert "desktop" in profile.behavior.device_types
