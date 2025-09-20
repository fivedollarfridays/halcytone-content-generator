"""
User Segmentation System
Sprint 8 - AI Enhancement & Personalization

This module provides comprehensive user segmentation for personalized content delivery
based on demographics, behavior, interests, and engagement patterns.
"""
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import statistics
from collections import defaultdict, Counter

from ..config import get_settings

logger = logging.getLogger(__name__)


class SegmentCategory(Enum):
    """Main segmentation categories"""
    INDUSTRY = "industry"
    INTERESTS = "interests"
    ENGAGEMENT_LEVEL = "engagement_level"
    WELLNESS_JOURNEY = "wellness_journey"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    COMMUNICATION_PREFERENCE = "communication_preference"
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"


class IndustrySegment(Enum):
    """Industry-based segments"""
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    FITNESS = "fitness"
    EDUCATION = "education"
    CORPORATE = "corporate"
    WELLNESS_PROFESSIONAL = "wellness_professional"
    STUDENT = "student"
    ENTREPRENEUR = "entrepreneur"
    REMOTE_WORKER = "remote_worker"
    GENERAL = "general"


class InterestSegment(Enum):
    """Interest-based segments"""
    MINDFULNESS = "mindfulness"
    FITNESS = "fitness"
    MENTAL_HEALTH = "mental_health"
    TECHNOLOGY = "technology"
    WELLNESS = "wellness"
    PRODUCTIVITY = "productivity"
    STRESS_MANAGEMENT = "stress_management"
    SLEEP_OPTIMIZATION = "sleep_optimization"
    BREATHING_TECHNIQUES = "breathing_techniques"
    MEDITATION = "meditation"


class EngagementLevel(Enum):
    """User engagement levels"""
    HIGHLY_ENGAGED = "highly_engaged"
    MODERATELY_ENGAGED = "moderately_engaged"
    LIGHTLY_ENGAGED = "lightly_engaged"
    INACTIVE = "inactive"
    NEW_USER = "new_user"


class WellnessJourney(Enum):
    """Wellness journey stages"""
    BEGINNER = "beginner"
    EXPLORING = "exploring"
    COMMITTED = "committed"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TechnologyAdoption(Enum):
    """Technology adoption patterns"""
    EARLY_ADOPTER = "early_adopter"
    MAINSTREAM = "mainstream"
    LATE_ADOPTER = "late_adopter"
    TECH_SAVVY = "tech_savvy"
    CASUAL_USER = "casual_user"


class CommunicationPreference(Enum):
    """Communication channel preferences"""
    EMAIL_PREFERRED = "email_preferred"
    SOCIAL_PREFERRED = "social_preferred"
    IN_APP_PREFERRED = "in_app_preferred"
    MULTI_CHANNEL = "multi_channel"
    MINIMAL_CONTACT = "minimal_contact"


@dataclass
class UserBehavior:
    """User behavioral data"""
    app_sessions_per_week: float = 0.0
    avg_session_duration: float = 0.0  # minutes
    features_used: Set[str] = field(default_factory=set)
    content_interactions: Dict[str, int] = field(default_factory=dict)
    last_active: Optional[datetime] = None
    total_active_days: int = 0
    preferred_times: List[int] = field(default_factory=list)  # hours of day
    device_types: Set[str] = field(default_factory=set)
    sharing_frequency: float = 0.0
    feedback_given: int = 0


@dataclass
class UserDemographics:
    """User demographic information"""
    age_range: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"
    profession: Optional[str] = None
    experience_level: Optional[str] = None


@dataclass
class UserProfile:
    """Comprehensive user profile"""
    user_id: str
    demographics: UserDemographics = field(default_factory=UserDemographics)
    behavior: UserBehavior = field(default_factory=UserBehavior)
    explicit_interests: Set[str] = field(default_factory=set)
    goals: Set[str] = field(default_factory=set)
    preferences: Dict[str, Any] = field(default_factory=dict)
    segments: Dict[SegmentCategory, str] = field(default_factory=dict)
    segment_scores: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update_segments(self, new_segments: Dict[SegmentCategory, str]):
        """Update user segments"""
        self.segments.update(new_segments)
        self.updated_at = datetime.utcnow()


@dataclass
class SegmentDefinition:
    """Definition of a user segment"""
    segment_id: str
    category: SegmentCategory
    name: str
    description: str
    criteria: Dict[str, Any]
    content_preferences: Dict[str, Any]
    messaging_strategy: Dict[str, str]
    priority: int = 1  # 1-5, higher = more important


@dataclass
class ContentRoutingRule:
    """Rule for routing content to segments"""
    rule_id: str
    target_segments: List[str]
    content_type: str
    content_attributes: Dict[str, Any]
    routing_logic: str  # "include", "exclude", "prioritize"
    weight: float = 1.0
    active: bool = True


class UserSegmentationService:
    """Comprehensive user segmentation service"""

    def __init__(self):
        self.settings = get_settings()
        self.segment_definitions = self._initialize_segment_definitions()
        self.routing_rules = self._initialize_routing_rules()
        self.user_profiles: Dict[str, UserProfile] = {}
        self.segment_analytics = defaultdict(lambda: defaultdict(int))

    def _initialize_segment_definitions(self) -> Dict[str, SegmentDefinition]:
        """Initialize predefined segment definitions"""
        definitions = {}

        # Industry segments
        industry_segments = [
            ("healthcare_professional", IndustrySegment.HEALTHCARE, "Healthcare Professional",
             "Medical professionals using wellness tech",
             {"profession": ["doctor", "nurse", "therapist", "healthcare"]},
             {"tone": "professional", "evidence_based": True, "clinical_focus": True}),

            ("tech_professional", IndustrySegment.TECHNOLOGY, "Technology Professional",
             "Tech workers interested in quantified wellness",
             {"profession": ["developer", "engineer", "designer", "tech"]},
             {"tone": "technical", "data_driven": True, "innovation_focus": True}),

            ("fitness_professional", IndustrySegment.FITNESS, "Fitness Professional",
             "Trainers and fitness experts using breathing techniques",
             {"profession": ["trainer", "coach", "fitness", "yoga"]},
             {"tone": "energetic", "performance_focus": True, "practical_tips": True}),

            ("wellness_professional", IndustrySegment.WELLNESS_PROFESSIONAL, "Wellness Professional",
             "Wellness coaches and mindfulness practitioners",
             {"profession": ["coach", "therapist", "counselor", "wellness"]},
             {"tone": "empathetic", "holistic_approach": True, "client_focused": True}),
        ]

        for seg_id, enum_val, name, desc, criteria, preferences in industry_segments:
            definitions[seg_id] = SegmentDefinition(
                segment_id=seg_id,
                category=SegmentCategory.INDUSTRY,
                name=name,
                description=desc,
                criteria=criteria,
                content_preferences=preferences,
                messaging_strategy={
                    "primary_channel": "email",
                    "frequency": "weekly",
                    "content_depth": "detailed"
                }
            )

        # Interest segments
        interest_segments = [
            ("mindfulness_enthusiast", InterestSegment.MINDFULNESS, "Mindfulness Enthusiast",
             "Users focused on mindfulness and meditation practices",
             {"interests": ["mindfulness", "meditation", "awareness"]},
             {"tone": "calm", "mindfulness_focus": True, "guided_content": True}),

            ("stress_warrior", InterestSegment.STRESS_MANAGEMENT, "Stress Management Warrior",
             "Users primarily using app for stress relief",
             {"goals": ["stress_relief", "anxiety_management"]},
             {"tone": "supportive", "immediate_relief": True, "practical_techniques": True}),

            ("performance_optimizer", InterestSegment.PRODUCTIVITY, "Performance Optimizer",
             "Users optimizing productivity and performance",
             {"goals": ["productivity", "performance", "focus"]},
             {"tone": "motivational", "results_oriented": True, "efficiency_focus": True}),

            ("sleep_improver", InterestSegment.SLEEP_OPTIMIZATION, "Sleep Quality Improver",
             "Users focused on better sleep through breathing",
             {"goals": ["sleep_improvement", "relaxation"]},
             {"tone": "soothing", "evening_content": True, "sleep_techniques": True}),
        ]

        for seg_id, enum_val, name, desc, criteria, preferences in interest_segments:
            definitions[seg_id] = SegmentDefinition(
                segment_id=seg_id,
                category=SegmentCategory.INTERESTS,
                name=name,
                description=desc,
                criteria=criteria,
                content_preferences=preferences,
                messaging_strategy={
                    "primary_channel": "in_app",
                    "frequency": "bi_weekly",
                    "content_depth": "moderate"
                }
            )

        # Engagement segments
        engagement_segments = [
            ("power_user", EngagementLevel.HIGHLY_ENGAGED, "Power User",
             "Highly engaged users with daily app usage",
             {"sessions_per_week": {"min": 5}, "avg_session_duration": {"min": 10}},
             {"tone": "advanced", "detailed_content": True, "exclusive_features": True}),

            ("regular_user", EngagementLevel.MODERATELY_ENGAGED, "Regular User",
             "Consistently engaged users with weekly usage",
             {"sessions_per_week": {"min": 2, "max": 4}},
             {"tone": "encouraging", "progressive_content": True, "achievement_focus": True}),

            ("casual_user", EngagementLevel.LIGHTLY_ENGAGED, "Casual User",
             "Occasional users needing engagement boost",
             {"sessions_per_week": {"max": 1}},
             {"tone": "motivational", "simple_content": True, "reminder_focus": True}),

            ("returning_user", EngagementLevel.NEW_USER, "New User",
             "Recently joined users in onboarding phase",
             {"total_active_days": {"max": 14}},
             {"tone": "welcoming", "educational_content": True, "onboarding_focus": True}),
        ]

        for seg_id, enum_val, name, desc, criteria, preferences in engagement_segments:
            definitions[seg_id] = SegmentDefinition(
                segment_id=seg_id,
                category=SegmentCategory.ENGAGEMENT_LEVEL,
                name=name,
                description=desc,
                criteria=criteria,
                content_preferences=preferences,
                messaging_strategy={
                    "primary_channel": "multi_channel",
                    "frequency": "dynamic",
                    "content_depth": "adaptive"
                }
            )

        # Wellness journey segments
        journey_segments = [
            ("wellness_beginner", WellnessJourney.BEGINNER, "Wellness Beginner",
             "New to wellness and breathing practices",
             {"experience_level": "beginner", "total_active_days": {"max": 30}},
             {"tone": "educational", "basic_content": True, "step_by_step": True}),

            ("wellness_explorer", WellnessJourney.EXPLORING, "Wellness Explorer",
             "Exploring different wellness approaches",
             {"features_used": {"min_count": 3}},
             {"tone": "curious", "variety_content": True, "experimental": True}),

            ("wellness_committed", WellnessJourney.COMMITTED, "Wellness Committed",
             "Committed to regular wellness practice",
             {"total_active_days": {"min": 60}, "sessions_per_week": {"min": 3}},
             {"tone": "supportive", "consistent_content": True, "habit_building": True}),

            ("wellness_expert", WellnessJourney.EXPERT, "Wellness Expert",
             "Advanced practitioners seeking deeper insights",
             {"total_active_days": {"min": 180}, "feedback_given": {"min": 5}},
             {"tone": "sophisticated", "advanced_content": True, "community_focus": True}),
        ]

        for seg_id, enum_val, name, desc, criteria, preferences in journey_segments:
            definitions[seg_id] = SegmentDefinition(
                segment_id=seg_id,
                category=SegmentCategory.WELLNESS_JOURNEY,
                name=name,
                description=desc,
                criteria=criteria,
                content_preferences=preferences,
                messaging_strategy={
                    "primary_channel": "email",
                    "frequency": "bi_weekly",
                    "content_depth": "progressive"
                }
            )

        return definitions

    def _initialize_routing_rules(self) -> List[ContentRoutingRule]:
        """Initialize content routing rules"""
        rules = [
            # Industry-specific routing
            ContentRoutingRule(
                rule_id="healthcare_clinical_content",
                target_segments=["healthcare_professional"],
                content_type="educational",
                content_attributes={"evidence_based": True, "clinical_studies": True},
                routing_logic="prioritize",
                weight=2.0
            ),

            ContentRoutingRule(
                rule_id="tech_data_driven_content",
                target_segments=["tech_professional"],
                content_type="analytical",
                content_attributes={"data_visualization": True, "metrics": True},
                routing_logic="prioritize",
                weight=1.8
            ),

            # Engagement-based routing
            ContentRoutingRule(
                rule_id="power_user_advanced_content",
                target_segments=["power_user"],
                content_type="advanced",
                content_attributes={"complexity": "high", "exclusive": True},
                routing_logic="include",
                weight=2.5
            ),

            ContentRoutingRule(
                rule_id="new_user_onboarding",
                target_segments=["returning_user"],
                content_type="onboarding",
                content_attributes={"educational": True, "basic": True},
                routing_logic="prioritize",
                weight=3.0
            ),

            # Interest-based routing
            ContentRoutingRule(
                rule_id="mindfulness_meditation_content",
                target_segments=["mindfulness_enthusiast"],
                content_type="meditation",
                content_attributes={"mindfulness": True, "guided": True},
                routing_logic="prioritize",
                weight=2.0
            ),

            ContentRoutingRule(
                rule_id="stress_immediate_relief",
                target_segments=["stress_warrior"],
                content_type="stress_relief",
                content_attributes={"immediate": True, "practical": True},
                routing_logic="prioritize",
                weight=2.5
            ),

            # Journey-based routing
            ContentRoutingRule(
                rule_id="beginner_simple_content",
                target_segments=["wellness_beginner"],
                content_type="educational",
                content_attributes={"complexity": "low", "step_by_step": True},
                routing_logic="include",
                weight=2.0
            ),

            ContentRoutingRule(
                rule_id="expert_advanced_content",
                target_segments=["wellness_expert"],
                content_type="advanced",
                content_attributes={"depth": "high", "community": True},
                routing_logic="prioritize",
                weight=1.5
            ),
        ]

        return rules

    def create_user_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(user_id=user_id)

        if initial_data:
            # Set demographics
            if "demographics" in initial_data:
                demo_data = initial_data["demographics"]
                profile.demographics = UserDemographics(**demo_data)

            # Set interests and goals
            if "interests" in initial_data:
                profile.explicit_interests = set(initial_data["interests"])

            if "goals" in initial_data:
                profile.goals = set(initial_data["goals"])

            # Set preferences
            if "preferences" in initial_data:
                profile.preferences = initial_data["preferences"]

        # Initial segmentation
        self._assign_segments(profile)

        self.user_profiles[user_id] = profile
        return profile

    def update_user_behavior(self, user_id: str, behavior_data: Dict[str, Any]) -> bool:
        """Update user behavioral data"""
        if user_id not in self.user_profiles:
            logger.warning(f"User profile not found: {user_id}")
            return False

        profile = self.user_profiles[user_id]
        behavior = profile.behavior

        # Update behavioral metrics
        if "app_sessions_per_week" in behavior_data:
            behavior.app_sessions_per_week = behavior_data["app_sessions_per_week"]

        if "avg_session_duration" in behavior_data:
            behavior.avg_session_duration = behavior_data["avg_session_duration"]

        if "features_used" in behavior_data:
            behavior.features_used.update(behavior_data["features_used"])

        if "content_interactions" in behavior_data:
            for content_type, count in behavior_data["content_interactions"].items():
                behavior.content_interactions[content_type] = behavior.content_interactions.get(content_type, 0) + count

        if "last_active" in behavior_data:
            behavior.last_active = behavior_data["last_active"]

        if "total_active_days" in behavior_data:
            behavior.total_active_days = behavior_data["total_active_days"]

        if "preferred_times" in behavior_data:
            behavior.preferred_times = behavior_data["preferred_times"]

        if "device_types" in behavior_data:
            behavior.device_types.update(behavior_data["device_types"])

        if "sharing_frequency" in behavior_data:
            behavior.sharing_frequency = behavior_data["sharing_frequency"]

        if "feedback_given" in behavior_data:
            behavior.feedback_given = behavior_data["feedback_given"]

        # Re-evaluate segments based on updated behavior
        self._assign_segments(profile)

        return True

    def _assign_segments(self, profile: UserProfile) -> None:
        """Assign user to appropriate segments"""
        segment_scores = {}
        assigned_segments = {}

        for segment_id, segment_def in self.segment_definitions.items():
            score = self._calculate_segment_score(profile, segment_def)
            segment_scores[segment_id] = score

            # Assign to segment if score meets threshold
            if score > 0.5:  # 50% match threshold
                assigned_segments[segment_def.category] = segment_id

        # Ensure user has at least one segment per category
        for category in SegmentCategory:
            if category not in assigned_segments:
                # Find best matching segment in this category
                category_segments = {sid: score for sid, score in segment_scores.items()
                                   if self.segment_definitions[sid].category == category}
                if category_segments:
                    best_segment = max(category_segments.items(), key=lambda x: x[1])
                    assigned_segments[category] = best_segment[0]

        profile.update_segments(assigned_segments)
        profile.segment_scores = segment_scores

        # Update analytics
        for category, segment_id in assigned_segments.items():
            self.segment_analytics[category.value][segment_id] += 1

    def _calculate_segment_score(self, profile: UserProfile, segment_def: SegmentDefinition) -> float:
        """Calculate how well a user matches a segment"""
        score = 0.0
        total_criteria = 0

        criteria = segment_def.criteria

        # Check demographic criteria
        if "profession" in criteria:
            total_criteria += 1
            user_profession = (profile.demographics.profession or "").lower()
            if any(prof in user_profession for prof in criteria["profession"]):
                score += 1.0

        # Check interest criteria
        if "interests" in criteria:
            total_criteria += 1
            required_interests = set(criteria["interests"])
            user_interests = {interest.lower() for interest in profile.explicit_interests}
            if required_interests.intersection(user_interests):
                overlap = len(required_interests.intersection(user_interests))
                score += overlap / len(required_interests)

        # Check goal criteria
        if "goals" in criteria:
            total_criteria += 1
            required_goals = set(criteria["goals"])
            user_goals = {goal.lower() for goal in profile.goals}
            if required_goals.intersection(user_goals):
                overlap = len(required_goals.intersection(user_goals))
                score += overlap / len(required_goals)

        # Check behavioral criteria
        behavior = profile.behavior

        if "sessions_per_week" in criteria:
            total_criteria += 1
            sessions_criteria = criteria["sessions_per_week"]
            user_sessions = behavior.app_sessions_per_week

            if self._meets_numeric_criteria(user_sessions, sessions_criteria):
                score += 1.0

        if "avg_session_duration" in criteria:
            total_criteria += 1
            duration_criteria = criteria["avg_session_duration"]
            user_duration = behavior.avg_session_duration

            if self._meets_numeric_criteria(user_duration, duration_criteria):
                score += 1.0

        if "total_active_days" in criteria:
            total_criteria += 1
            days_criteria = criteria["total_active_days"]
            user_days = behavior.total_active_days

            if self._meets_numeric_criteria(user_days, days_criteria):
                score += 1.0

        if "features_used" in criteria:
            total_criteria += 1
            features_criteria = criteria["features_used"]
            user_features = len(behavior.features_used)

            if "min_count" in features_criteria and user_features >= features_criteria["min_count"]:
                score += 1.0

        if "feedback_given" in criteria:
            total_criteria += 1
            feedback_criteria = criteria["feedback_given"]
            user_feedback = behavior.feedback_given

            if self._meets_numeric_criteria(user_feedback, feedback_criteria):
                score += 1.0

        # Check experience level
        if "experience_level" in criteria:
            total_criteria += 1
            required_level = criteria["experience_level"]
            user_level = profile.demographics.experience_level

            if user_level and user_level.lower() == required_level.lower():
                score += 1.0

        return score / max(total_criteria, 1)

    def _meets_numeric_criteria(self, value: float, criteria: Dict[str, float]) -> bool:
        """Check if numeric value meets criteria"""
        if "min" in criteria and value < criteria["min"]:
            return False
        if "max" in criteria and value > criteria["max"]:
            return False
        if "exact" in criteria and value != criteria["exact"]:
            return False
        return True

    def get_user_segments(self, user_id: str) -> Dict[SegmentCategory, str]:
        """Get user's current segments"""
        if user_id not in self.user_profiles:
            return {}

        return self.user_profiles[user_id].segments

    def get_segment_content_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get content preferences based on user's segments"""
        if user_id not in self.user_profiles:
            return {}

        profile = self.user_profiles[user_id]
        combined_preferences = {}

        for segment_id in profile.segments.values():
            if segment_id in self.segment_definitions:
                segment_prefs = self.segment_definitions[segment_id].content_preferences
                # Merge preferences with priority to higher-scored segments
                for key, value in segment_prefs.items():
                    if key not in combined_preferences:
                        combined_preferences[key] = value
                    elif isinstance(value, bool) and value:
                        combined_preferences[key] = value

        return combined_preferences

    def route_content_to_segments(self, content_attributes: Dict[str, Any]) -> Dict[str, List[str]]:
        """Route content to appropriate segments based on routing rules"""
        content_routing = defaultdict(list)

        for rule in self.routing_rules:
            if not rule.active:
                continue

            # Check if content matches rule criteria
            if self._content_matches_rule(content_attributes, rule):
                for segment_id in rule.target_segments:
                    content_routing[rule.routing_logic].append({
                        "segment_id": segment_id,
                        "weight": rule.weight,
                        "rule_id": rule.rule_id
                    })

        return dict(content_routing)

    def _content_matches_rule(self, content_attributes: Dict[str, Any],
                            rule: ContentRoutingRule) -> bool:
        """Check if content matches routing rule criteria"""
        rule_attributes = rule.content_attributes

        for key, required_value in rule_attributes.items():
            if key not in content_attributes:
                continue

            content_value = content_attributes[key]

            # Boolean matching
            if isinstance(required_value, bool):
                if content_value != required_value:
                    return False

            # String matching
            elif isinstance(required_value, str):
                if content_value != required_value:
                    return False

            # List matching (any overlap)
            elif isinstance(required_value, list):
                if isinstance(content_value, list):
                    if not set(required_value).intersection(set(content_value)):
                        return False
                else:
                    if content_value not in required_value:
                        return False

        return True

    def get_personalized_content_strategy(self, user_id: str) -> Dict[str, Any]:
        """Get personalized content strategy for user"""
        if user_id not in self.user_profiles:
            return self._get_default_content_strategy()

        profile = self.user_profiles[user_id]
        strategy = {
            "user_segments": profile.segments,
            "content_preferences": self.get_segment_content_preferences(user_id),
            "messaging_strategy": {},
            "priority_topics": [],
            "channel_preferences": [],
            "frequency_recommendation": "weekly"
        }

        # Aggregate messaging strategies from segments
        for segment_id in profile.segments.values():
            if segment_id in self.segment_definitions:
                segment_strategy = self.segment_definitions[segment_id].messaging_strategy
                for key, value in segment_strategy.items():
                    if key not in strategy["messaging_strategy"]:
                        strategy["messaging_strategy"][key] = value

        # Determine priority topics based on interests and goals
        strategy["priority_topics"] = list(profile.explicit_interests) + list(profile.goals)

        # Determine preferred channels based on behavior and segments
        if profile.behavior.app_sessions_per_week > 3:
            strategy["channel_preferences"].append("in_app")
        if "email" in profile.preferences.get("channels", ["email"]):
            strategy["channel_preferences"].append("email")
        if profile.behavior.sharing_frequency > 0.1:
            strategy["channel_preferences"].append("social")

        return strategy

    def _get_default_content_strategy(self) -> Dict[str, Any]:
        """Get default content strategy for unknown users"""
        return {
            "user_segments": {SegmentCategory.ENGAGEMENT_LEVEL: "returning_user"},
            "content_preferences": {"tone": "welcoming", "educational_content": True},
            "messaging_strategy": {"primary_channel": "email", "frequency": "weekly"},
            "priority_topics": ["wellness", "breathing_techniques"],
            "channel_preferences": ["email"],
            "frequency_recommendation": "weekly"
        }

    def get_segment_analytics(self) -> Dict[str, Any]:
        """Get analytics about segment distribution"""
        total_users = len(self.user_profiles)

        analytics = {
            "total_users": total_users,
            "segment_distribution": {},
            "segment_growth": {},
            "engagement_by_segment": {}
        }

        # Calculate distribution by category
        for category, segments in self.segment_analytics.items():
            category_total = sum(segments.values())
            analytics["segment_distribution"][category] = {
                "total": category_total,
                "segments": {seg_id: count for seg_id, count in segments.items()}
            }

        # Calculate engagement metrics by segment
        for user_id, profile in self.user_profiles.items():
            for category, segment_id in profile.segments.items():
                if category.value not in analytics["engagement_by_segment"]:
                    analytics["engagement_by_segment"][category.value] = {}

                if segment_id not in analytics["engagement_by_segment"][category.value]:
                    analytics["engagement_by_segment"][category.value][segment_id] = {
                        "avg_sessions": 0,
                        "avg_duration": 0,
                        "user_count": 0
                    }

                segment_data = analytics["engagement_by_segment"][category.value][segment_id]
                segment_data["avg_sessions"] += profile.behavior.app_sessions_per_week
                segment_data["avg_duration"] += profile.behavior.avg_session_duration
                segment_data["user_count"] += 1

        # Calculate averages
        for category_data in analytics["engagement_by_segment"].values():
            for segment_data in category_data.values():
                if segment_data["user_count"] > 0:
                    segment_data["avg_sessions"] /= segment_data["user_count"]
                    segment_data["avg_duration"] /= segment_data["user_count"]

        return analytics

    def suggest_segment_migrations(self, user_id: str) -> List[Dict[str, Any]]:
        """Suggest potential segment migrations for user"""
        if user_id not in self.user_profiles:
            return []

        profile = self.user_profiles[user_id]
        suggestions = []

        # Check for segments with high scores but not currently assigned
        for segment_id, score in profile.segment_scores.items():
            if score > 0.7 and segment_id not in profile.segments.values():
                segment_def = self.segment_definitions[segment_id]
                suggestions.append({
                    "segment_id": segment_id,
                    "segment_name": segment_def.name,
                    "category": segment_def.category.value,
                    "score": score,
                    "reason": f"High compatibility score ({score:.2f})",
                    "benefits": segment_def.content_preferences
                })

        # Sort by score
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:3]  # Top 3 suggestions

    def export_user_segments(self, user_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export user segment data for analysis"""
        if user_ids is None:
            user_ids = list(self.user_profiles.keys())

        export_data = {
            "users": [],
            "segments": {seg_id: {
                "name": seg_def.name,
                "category": seg_def.category.value,
                "description": seg_def.description
            } for seg_id, seg_def in self.segment_definitions.items()},
            "export_timestamp": datetime.utcnow().isoformat()
        }

        for user_id in user_ids:
            if user_id in self.user_profiles:
                profile = self.user_profiles[user_id]
                export_data["users"].append({
                    "user_id": user_id,
                    "segments": {cat.value: seg_id for cat, seg_id in profile.segments.items()},
                    "segment_scores": profile.segment_scores,
                    "interests": list(profile.explicit_interests),
                    "goals": list(profile.goals),
                    "engagement_level": profile.behavior.app_sessions_per_week,
                    "total_active_days": profile.behavior.total_active_days,
                    "last_updated": profile.updated_at.isoformat()
                })

        return export_data


# Singleton instance
_segmentation_service = None

def get_user_segmentation_service() -> UserSegmentationService:
    """Get singleton instance of user segmentation service"""
    global _segmentation_service
    if _segmentation_service is None:
        _segmentation_service = UserSegmentationService()
    return _segmentation_service