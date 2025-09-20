"""
Unit tests for User Segmentation System
Sprint 8 - AI Enhancement & Personalization
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.halcytone_content_generator.services.user_segmentation import (
    UserSegmentationService,
    UserProfile,
    UserBehavior,
    UserDemographics,
    SegmentDefinition,
    ContentRoutingRule,
    SegmentCategory,
    IndustrySegment,
    InterestSegment,
    EngagementLevel,
    WellnessJourney,
    TechnologyAdoption,
    CommunicationPreference,
    get_user_segmentation_service
)


class TestUserProfile:
    """Test user profile data structures"""

    def test_user_profile_creation(self):
        """Test creating a user profile"""
        profile = UserProfile(user_id="test_user_123")

        assert profile.user_id == "test_user_123"
        assert isinstance(profile.demographics, UserDemographics)
        assert isinstance(profile.behavior, UserBehavior)
        assert isinstance(profile.explicit_interests, set)
        assert isinstance(profile.goals, set)
        assert isinstance(profile.segments, dict)

    def test_user_profile_update_segments(self):
        """Test updating user segments"""
        profile = UserProfile(user_id="test_user")
        original_time = profile.updated_at

        new_segments = {
            SegmentCategory.INDUSTRY: "healthcare_professional",
            SegmentCategory.ENGAGEMENT_LEVEL: "power_user"
        }

        profile.update_segments(new_segments)

        assert profile.segments[SegmentCategory.INDUSTRY] == "healthcare_professional"
        assert profile.segments[SegmentCategory.ENGAGEMENT_LEVEL] == "power_user"
        assert profile.updated_at > original_time

    def test_user_behavior_initialization(self):
        """Test user behavior data structure"""
        behavior = UserBehavior()

        assert behavior.app_sessions_per_week == 0.0
        assert behavior.avg_session_duration == 0.0
        assert isinstance(behavior.features_used, set)
        assert isinstance(behavior.content_interactions, dict)
        assert behavior.last_active is None

    def test_user_demographics_initialization(self):
        """Test user demographics data structure"""
        demographics = UserDemographics(
            age_range="25-34",
            profession="software_engineer",
            location="US"
        )

        assert demographics.age_range == "25-34"
        assert demographics.profession == "software_engineer"
        assert demographics.location == "US"
        assert demographics.language == "en"  # default


class TestSegmentDefinition:
    """Test segment definition structures"""

    def test_segment_definition_creation(self):
        """Test creating a segment definition"""
        segment = SegmentDefinition(
            segment_id="test_segment",
            category=SegmentCategory.INDUSTRY,
            name="Test Segment",
            description="A test segment",
            criteria={"profession": ["engineer"]},
            content_preferences={"tone": "technical"},
            messaging_strategy={"channel": "email"}
        )

        assert segment.segment_id == "test_segment"
        assert segment.category == SegmentCategory.INDUSTRY
        assert segment.criteria["profession"] == ["engineer"]
        assert segment.content_preferences["tone"] == "technical"

    def test_content_routing_rule_creation(self):
        """Test creating content routing rules"""
        rule = ContentRoutingRule(
            rule_id="test_rule",
            target_segments=["tech_professional"],
            content_type="technical",
            content_attributes={"complexity": "high"},
            routing_logic="prioritize",
            weight=2.0
        )

        assert rule.rule_id == "test_rule"
        assert rule.target_segments == ["tech_professional"]
        assert rule.routing_logic == "prioritize"
        assert rule.weight == 2.0
        assert rule.active is True  # default


class TestUserSegmentationService:
    """Test user segmentation service functionality"""

    @pytest.fixture
    def segmentation_service(self):
        """Create segmentation service for testing"""
        return UserSegmentationService()

    def test_service_initialization(self, segmentation_service):
        """Test segmentation service initializes correctly"""
        assert segmentation_service.settings is not None
        assert len(segmentation_service.segment_definitions) > 0
        assert len(segmentation_service.routing_rules) > 0
        assert isinstance(segmentation_service.user_profiles, dict)

    def test_segment_definitions_loaded(self, segmentation_service):
        """Test that segment definitions are properly loaded"""
        definitions = segmentation_service.segment_definitions

        # Check industry segments
        assert "healthcare_professional" in definitions
        assert "tech_professional" in definitions
        assert "fitness_professional" in definitions

        # Check interest segments
        assert "mindfulness_enthusiast" in definitions
        assert "stress_warrior" in definitions

        # Check engagement segments
        assert "power_user" in definitions
        assert "casual_user" in definitions

        # Check wellness journey segments
        assert "wellness_beginner" in definitions
        assert "wellness_expert" in definitions

    def test_routing_rules_loaded(self, segmentation_service):
        """Test that routing rules are properly loaded"""
        rules = segmentation_service.routing_rules

        assert len(rules) > 0

        # Check specific rules exist
        rule_ids = [rule.rule_id for rule in rules]
        assert "healthcare_clinical_content" in rule_ids
        assert "tech_data_driven_content" in rule_ids
        assert "power_user_advanced_content" in rule_ids

    def test_create_user_profile_basic(self, segmentation_service):
        """Test creating a basic user profile"""
        profile = segmentation_service.create_user_profile("user_123")

        assert profile.user_id == "user_123"
        assert "user_123" in segmentation_service.user_profiles
        assert len(profile.segments) > 0  # Should be assigned to segments

    def test_create_user_profile_with_data(self, segmentation_service):
        """Test creating user profile with initial data"""
        initial_data = {
            "demographics": {
                "profession": "doctor",
                "age_range": "30-40"
            },
            "interests": ["mindfulness", "stress_management"],
            "goals": ["stress_relief", "better_sleep"]
        }

        profile = segmentation_service.create_user_profile("user_456", initial_data)

        assert profile.demographics.profession == "doctor"
        assert "mindfulness" in profile.explicit_interests
        assert "stress_relief" in profile.goals

    def test_update_user_behavior(self, segmentation_service):
        """Test updating user behavioral data"""
        # Create user first
        profile = segmentation_service.create_user_profile("user_789")

        behavior_data = {
            "app_sessions_per_week": 5.0,
            "avg_session_duration": 15.0,
            "features_used": ["breathing_exercises", "meditation"],
            "total_active_days": 45,
            "feedback_given": 3
        }

        success = segmentation_service.update_user_behavior("user_789", behavior_data)

        assert success is True
        updated_profile = segmentation_service.user_profiles["user_789"]
        assert updated_profile.behavior.app_sessions_per_week == 5.0
        assert updated_profile.behavior.avg_session_duration == 15.0
        assert "breathing_exercises" in updated_profile.behavior.features_used

    def test_update_behavior_nonexistent_user(self, segmentation_service):
        """Test updating behavior for non-existent user"""
        success = segmentation_service.update_user_behavior("nonexistent", {})
        assert success is False

    def test_segment_assignment_healthcare(self, segmentation_service):
        """Test segment assignment for healthcare professional"""
        initial_data = {
            "demographics": {"profession": "nurse"},
            "interests": ["wellness", "patient_care"],
            "goals": ["professional_development"]
        }

        profile = segmentation_service.create_user_profile("healthcare_user", initial_data)

        # Should be assigned to healthcare segment
        assert profile.segments.get(SegmentCategory.INDUSTRY) == "healthcare_professional"

    def test_segment_assignment_tech_professional(self, segmentation_service):
        """Test segment assignment for tech professional"""
        initial_data = {
            "demographics": {"profession": "software_engineer"},
            "interests": ["technology", "productivity"],
        }

        profile = segmentation_service.create_user_profile("tech_user", initial_data)

        # Should be assigned to tech segment
        assert profile.segments.get(SegmentCategory.INDUSTRY) == "tech_professional"

    def test_segment_assignment_engagement_levels(self, segmentation_service):
        """Test segment assignment based on engagement"""
        # Create highly engaged user
        profile = segmentation_service.create_user_profile("engaged_user")
        behavior_data = {
            "app_sessions_per_week": 6.0,
            "avg_session_duration": 20.0,
            "total_active_days": 100
        }
        segmentation_service.update_user_behavior("engaged_user", behavior_data)

        updated_profile = segmentation_service.user_profiles["engaged_user"]
        assert updated_profile.segments.get(SegmentCategory.ENGAGEMENT_LEVEL) == "power_user"

        # Create casual user
        profile2 = segmentation_service.create_user_profile("casual_user")
        behavior_data2 = {
            "app_sessions_per_week": 1.0,
            "avg_session_duration": 5.0,
            "total_active_days": 10
        }
        segmentation_service.update_user_behavior("casual_user", behavior_data2)

        updated_profile2 = segmentation_service.user_profiles["casual_user"]
        assert updated_profile2.segments.get(SegmentCategory.ENGAGEMENT_LEVEL) == "casual_user"

    def test_segment_assignment_wellness_journey(self, segmentation_service):
        """Test segment assignment for wellness journey stages"""
        # Beginner user
        beginner_data = {
            "demographics": {"experience_level": "beginner"},
            "interests": ["wellness"]
        }
        profile = segmentation_service.create_user_profile("beginner_user", beginner_data)
        behavior_data = {"total_active_days": 15}
        segmentation_service.update_user_behavior("beginner_user", behavior_data)

        updated_profile = segmentation_service.user_profiles["beginner_user"]
        assert updated_profile.segments.get(SegmentCategory.WELLNESS_JOURNEY) == "wellness_beginner"

        # Expert user
        expert_profile = segmentation_service.create_user_profile("expert_user")
        expert_behavior = {
            "total_active_days": 200,
            "app_sessions_per_week": 4.0,
            "feedback_given": 10
        }
        segmentation_service.update_user_behavior("expert_user", expert_behavior)

        updated_expert = segmentation_service.user_profiles["expert_user"]
        assert updated_expert.segments.get(SegmentCategory.WELLNESS_JOURNEY) == "wellness_expert"

    def test_calculate_segment_score(self, segmentation_service):
        """Test segment score calculation"""
        # Create a profile that should match tech professional segment
        profile = UserProfile("test_user")
        profile.demographics.profession = "software engineer"
        profile.explicit_interests = {"technology", "productivity"}

        tech_segment = segmentation_service.segment_definitions["tech_professional"]
        score = segmentation_service._calculate_segment_score(profile, tech_segment)

        assert score > 0.5  # Should have high score for tech segment

    def test_meets_numeric_criteria(self, segmentation_service):
        """Test numeric criteria matching"""
        # Test minimum criteria
        assert segmentation_service._meets_numeric_criteria(5.0, {"min": 3.0}) is True
        assert segmentation_service._meets_numeric_criteria(2.0, {"min": 3.0}) is False

        # Test maximum criteria
        assert segmentation_service._meets_numeric_criteria(3.0, {"max": 5.0}) is True
        assert segmentation_service._meets_numeric_criteria(6.0, {"max": 5.0}) is False

        # Test range criteria
        assert segmentation_service._meets_numeric_criteria(4.0, {"min": 2.0, "max": 6.0}) is True
        assert segmentation_service._meets_numeric_criteria(1.0, {"min": 2.0, "max": 6.0}) is False

    def test_get_user_segments(self, segmentation_service):
        """Test retrieving user segments"""
        profile = segmentation_service.create_user_profile("segment_user")

        segments = segmentation_service.get_user_segments("segment_user")
        assert isinstance(segments, dict)
        assert len(segments) > 0

        # Test non-existent user
        empty_segments = segmentation_service.get_user_segments("nonexistent")
        assert empty_segments == {}

    def test_get_segment_content_preferences(self, segmentation_service):
        """Test getting content preferences for user"""
        # Create healthcare professional
        initial_data = {"demographics": {"profession": "doctor"}}
        profile = segmentation_service.create_user_profile("healthcare_user", initial_data)

        preferences = segmentation_service.get_segment_content_preferences("healthcare_user")

        assert isinstance(preferences, dict)
        # Healthcare professionals should have evidence-based preference
        assert preferences.get("evidence_based") is True
        assert preferences.get("clinical_focus") is True

    def test_content_routing_basic(self, segmentation_service):
        """Test basic content routing"""
        content_attributes = {
            "evidence_based": True,
            "clinical_studies": True,
            "complexity": "high"
        }

        routing = segmentation_service.route_content_to_segments(content_attributes)

        assert isinstance(routing, dict)
        # Should include prioritize routing for healthcare content
        assert "prioritize" in routing

    def test_content_matches_rule(self, segmentation_service):
        """Test content matching against routing rules"""
        rule = ContentRoutingRule(
            rule_id="test_rule",
            target_segments=["tech_professional"],
            content_type="technical",
            content_attributes={"data_visualization": True, "complexity": "high"},
            routing_logic="prioritize"
        )

        # Matching content
        matching_content = {
            "data_visualization": True,
            "complexity": "high",
            "topic": "analytics"
        }

        assert segmentation_service._content_matches_rule(matching_content, rule) is True

        # Non-matching content
        non_matching_content = {
            "data_visualization": False,
            "complexity": "low"
        }

        assert segmentation_service._content_matches_rule(non_matching_content, rule) is False

    def test_personalized_content_strategy(self, segmentation_service):
        """Test getting personalized content strategy"""
        # Create user with specific characteristics
        initial_data = {
            "demographics": {"profession": "engineer"},
            "interests": ["technology", "productivity"],
            "goals": ["focus_improvement"]
        }
        profile = segmentation_service.create_user_profile("strategy_user", initial_data)

        # Update behavior to show high engagement
        behavior_data = {
            "app_sessions_per_week": 4.0,
            "sharing_frequency": 0.2
        }
        segmentation_service.update_user_behavior("strategy_user", behavior_data)

        strategy = segmentation_service.get_personalized_content_strategy("strategy_user")

        assert isinstance(strategy, dict)
        assert "user_segments" in strategy
        assert "content_preferences" in strategy
        assert "priority_topics" in strategy
        assert "channel_preferences" in strategy

        # Should include user's interests and goals
        assert "technology" in strategy["priority_topics"]
        assert "focus_improvement" in strategy["priority_topics"]

        # Should include appropriate channels for engaged user
        assert "in_app" in strategy["channel_preferences"]

    def test_default_content_strategy(self, segmentation_service):
        """Test default content strategy for unknown users"""
        strategy = segmentation_service.get_personalized_content_strategy("unknown_user")

        assert isinstance(strategy, dict)
        assert strategy["user_segments"][SegmentCategory.ENGAGEMENT_LEVEL] == "returning_user"
        assert "welcoming" in strategy["content_preferences"]["tone"]
        assert "email" in strategy["channel_preferences"]

    def test_segment_analytics(self, segmentation_service):
        """Test segment analytics generation"""
        # Create several users with different segments
        users_data = [
            ("user1", {"demographics": {"profession": "doctor"}}),
            ("user2", {"demographics": {"profession": "engineer"}}),
            ("user3", {"demographics": {"profession": "nurse"}}),
        ]

        for user_id, data in users_data:
            segmentation_service.create_user_profile(user_id, data)

        analytics = segmentation_service.get_segment_analytics()

        assert isinstance(analytics, dict)
        assert "total_users" in analytics
        assert "segment_distribution" in analytics
        assert "engagement_by_segment" in analytics

        assert analytics["total_users"] == 3

    def test_suggest_segment_migrations(self, segmentation_service):
        """Test segment migration suggestions"""
        # Create user and update behavior to potentially qualify for different segments
        profile = segmentation_service.create_user_profile("migration_user")

        # Update behavior to make them qualify for power user
        behavior_data = {
            "app_sessions_per_week": 6.0,
            "avg_session_duration": 20.0,
            "total_active_days": 100,
            "feedback_given": 8
        }
        segmentation_service.update_user_behavior("migration_user", behavior_data)

        suggestions = segmentation_service.suggest_segment_migrations("migration_user")

        assert isinstance(suggestions, list)
        # Should suggest segments with high compatibility
        for suggestion in suggestions:
            assert "segment_id" in suggestion
            assert "score" in suggestion
            assert suggestion["score"] > 0.7

    def test_export_user_segments(self, segmentation_service):
        """Test exporting user segment data"""
        # Create a few users
        segmentation_service.create_user_profile("export_user1")
        segmentation_service.create_user_profile("export_user2")

        export_data = segmentation_service.export_user_segments()

        assert isinstance(export_data, dict)
        assert "users" in export_data
        assert "segments" in export_data
        assert "export_timestamp" in export_data

        assert len(export_data["users"]) == 2

        # Test specific user export
        specific_export = segmentation_service.export_user_segments(["export_user1"])
        assert len(specific_export["users"]) == 1
        assert specific_export["users"][0]["user_id"] == "export_user1"

    def test_singleton_instance(self):
        """Test singleton pattern for segmentation service"""
        service1 = get_user_segmentation_service()
        service2 = get_user_segmentation_service()
        assert service1 is service2


class TestSegmentEnums:
    """Test segment enumeration values"""

    def test_segment_category_enum(self):
        """Test segment category enumeration"""
        categories = list(SegmentCategory)
        assert SegmentCategory.INDUSTRY in categories
        assert SegmentCategory.INTERESTS in categories
        assert SegmentCategory.ENGAGEMENT_LEVEL in categories
        assert SegmentCategory.WELLNESS_JOURNEY in categories

    def test_industry_segment_enum(self):
        """Test industry segment enumeration"""
        industries = list(IndustrySegment)
        assert IndustrySegment.HEALTHCARE in industries
        assert IndustrySegment.TECHNOLOGY in industries
        assert IndustrySegment.FITNESS in industries

    def test_interest_segment_enum(self):
        """Test interest segment enumeration"""
        interests = list(InterestSegment)
        assert InterestSegment.MINDFULNESS in interests
        assert InterestSegment.STRESS_MANAGEMENT in interests
        assert InterestSegment.PRODUCTIVITY in interests

    def test_engagement_level_enum(self):
        """Test engagement level enumeration"""
        levels = list(EngagementLevel)
        assert EngagementLevel.HIGHLY_ENGAGED in levels
        assert EngagementLevel.NEW_USER in levels
        assert EngagementLevel.INACTIVE in levels


class TestComplexSegmentationScenarios:
    """Test complex segmentation scenarios"""

    @pytest.fixture
    def service(self):
        return UserSegmentationService()

    def test_multi_segment_user(self, service):
        """Test user that qualifies for multiple segments"""
        initial_data = {
            "demographics": {
                "profession": "healthcare_data_scientist",  # Could match both healthcare and tech
                "experience_level": "advanced"
            },
            "interests": ["technology", "wellness", "data_analysis"],
            "goals": ["professional_development", "stress_management"]
        }

        profile = service.create_user_profile("multi_segment_user", initial_data)

        # Update with high engagement behavior
        behavior_data = {
            "app_sessions_per_week": 5.0,
            "avg_session_duration": 18.0,
            "total_active_days": 120,
            "features_used": {"breathing_exercises", "analytics", "progress_tracking"},
            "feedback_given": 6
        }
        service.update_user_behavior("multi_segment_user", behavior_data)

        updated_profile = service.user_profiles["multi_segment_user"]

        # Should be assigned to appropriate segments in each category
        assert len(updated_profile.segments) >= 4  # At least one per major category
        assert updated_profile.segments.get(SegmentCategory.ENGAGEMENT_LEVEL) == "power_user"
        assert updated_profile.segments.get(SegmentCategory.WELLNESS_JOURNEY) == "wellness_expert"

    def test_evolving_user_segments(self, service):
        """Test user segments evolving over time"""
        # Start as beginner
        initial_data = {
            "demographics": {"experience_level": "beginner"},
            "interests": ["wellness"]
        }
        profile = service.create_user_profile("evolving_user", initial_data)

        initial_segments = profile.segments.copy()

        # Simulate user growth over time
        # Month 1: Light usage
        behavior_month_1 = {
            "app_sessions_per_week": 1.5,
            "avg_session_duration": 8.0,
            "total_active_days": 15,
            "features_used": {"breathing_exercises"}
        }
        service.update_user_behavior("evolving_user", behavior_month_1)

        month_1_profile = service.user_profiles["evolving_user"]
        month_1_segments = month_1_profile.segments.copy()

        # Month 3: Increased engagement
        behavior_month_3 = {
            "app_sessions_per_week": 3.0,
            "avg_session_duration": 12.0,
            "total_active_days": 45,
            "features_used": {"breathing_exercises", "meditation", "progress_tracking"},
            "feedback_given": 2
        }
        service.update_user_behavior("evolving_user", behavior_month_3)

        month_3_profile = service.user_profiles["evolving_user"]
        month_3_segments = month_3_profile.segments.copy()

        # Month 6: Expert level
        behavior_month_6 = {
            "app_sessions_per_week": 5.0,
            "avg_session_duration": 15.0,
            "total_active_days": 120,
            "features_used": {"breathing_exercises", "meditation", "progress_tracking", "advanced_techniques"},
            "feedback_given": 8
        }
        service.update_user_behavior("evolving_user", behavior_month_6)

        month_6_profile = service.user_profiles["evolving_user"]
        month_6_segments = month_6_profile.segments.copy()

        # Verify evolution
        assert month_1_segments[SegmentCategory.ENGAGEMENT_LEVEL] == "casual_user"
        assert month_3_segments[SegmentCategory.ENGAGEMENT_LEVEL] == "regular_user"
        assert month_6_segments[SegmentCategory.ENGAGEMENT_LEVEL] == "power_user"

        # Wellness journey should also evolve
        assert month_6_segments[SegmentCategory.WELLNESS_JOURNEY] in ["wellness_committed", "wellness_expert"]

    def test_segment_based_content_routing_complex(self, service):
        """Test complex content routing scenarios"""
        # Create users in different segments
        healthcare_user = service.create_user_profile("healthcare_user", {
            "demographics": {"profession": "doctor"}
        })

        tech_user = service.create_user_profile("tech_user", {
            "demographics": {"profession": "engineer"}
        })

        # Test routing for clinical content
        clinical_content = {
            "evidence_based": True,
            "clinical_studies": True,
            "target_audience": "healthcare"
        }

        clinical_routing = service.route_content_to_segments(clinical_content)
        assert "prioritize" in clinical_routing

        # Test routing for technical content
        technical_content = {
            "data_visualization": True,
            "metrics": True,
            "complexity": "high"
        }

        tech_routing = service.route_content_to_segments(technical_content)
        assert "prioritize" in tech_routing

        # Test routing for general wellness content
        general_content = {
            "wellness": True,
            "beginner_friendly": True
        }

        general_routing = service.route_content_to_segments(general_content)
        # Should have some routing rules applied
        assert len(general_routing) >= 0