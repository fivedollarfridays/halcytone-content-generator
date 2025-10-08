"""
Unit tests for SessionContentStrict validation
Sprint 3: Halcytone Live Support - Session content validation tests
"""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from halcytone_content_generator.schemas.content_types import (
    SessionContentStrict,
    ContentType,
    ContentPriority
)


class TestSessionContentStrict:
    """Test SessionContentStrict model validation"""

    def test_valid_session_creation(self):
        """Test creating a valid session"""
        session = SessionContentStrict(
            title="Morning Breathing Session",
            content="A wonderful group breathing session",
            session_id="test-001",
            session_duration=1800,  # 30 minutes
            participant_count=25,
            breathing_techniques=["Box Breathing", "4-7-8 Breathing"],
            average_hrv_improvement=12.5,
            key_achievements=["Perfect attendance", "Group synchronization"],
            session_type="live",
            instructor_name="Sarah Chen",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert session.type == ContentType.SESSION
        assert session.session_id == "test-001"
        assert session.participant_count == 25
        assert len(session.breathing_techniques) == 2
        assert session.average_hrv_improvement == 12.5

    def test_session_duration_validation(self):
        """Test session duration constraints"""
        # Test maximum duration (2 hours)
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Too Long Session",
                content="Session content for testing",
                session_id="test-002",
                session_duration=7201,  # Over 2 hours
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "less than or equal to 7200" in str(exc_info.value)

        # Test minimum duration
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Too Short Session",
                content="Session content for testing",
                session_id="test-003",
                session_duration=0,  # Zero duration
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "greater than 0" in str(exc_info.value)

    def test_participant_count_validation(self):
        """Test participant count constraints"""
        # Test minimum participants
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Empty Session",
                content="Session content for testing",
                session_id="test-004",
                session_duration=1800,
                participant_count=0,  # Zero participants
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "greater than or equal to 1" in str(exc_info.value)

        # Test maximum participants
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Massive Session",
                content="Session content for testing",
                session_id="test-005",
                session_duration=1800,
                participant_count=1001,  # Over 1000 participants
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "less than or equal to 1000" in str(exc_info.value)

    def test_breathing_techniques_validation(self):
        """Test breathing techniques validation"""
        # Test empty techniques list
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="No Techniques Session",
                content="Session content for testing",
                session_id="test-006",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=[],  # Empty list
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "at least 1 item" in str(exc_info.value)

        # Test custom techniques
        session = SessionContentStrict(
            title="Custom Techniques",
            content="Session with custom techniques",
            session_id="test-007",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["My Custom Technique", "Box Breathing"],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        # Custom techniques should be prefixed
        assert any("Custom:" in t for t in session.breathing_techniques)

    def test_session_date_validation(self):
        """Test session date validation"""
        # Test future date
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Future Session",
                content="Session content for testing",
                session_id="test-008",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=future_date,
                published=True
            )

        assert "cannot be in the future" in str(exc_info.value)

        # Test old date (>30 days)
        old_date = datetime.now(timezone.utc) - timedelta(days=31)
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Old Session",
                content="Session content for testing",
                session_id="test-009",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                session_type="guided",
                session_date=old_date,
                published=True
            )

        assert "too old" in str(exc_info.value)

    def test_session_type_validation(self):
        """Test session type specific validation"""
        # Test live session without instructor
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Live Without Instructor",
                content="Session content for testing",
                session_id="test-010",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                session_type="live",
                instructor_name=None,  # Missing instructor for live session
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "Live sessions must have an instructor" in str(exc_info.value)

        # Test workshop with insufficient participants
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Small Workshop",
                content="Session content for testing",
                session_id="test-011",
                session_duration=1800,
                participant_count=3,  # Too few for workshop
                breathing_techniques=["Box Breathing"],
                session_type="workshop",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "Workshop sessions should have at least 5 participants" in str(exc_info.value)

    def test_hrv_improvement_validation(self):
        """Test HRV improvement constraints and quality scoring"""
        # Test valid HRV improvement
        session = SessionContentStrict(
            title="High HRV Session",
            content="Session with great HRV improvement",
            session_id="test-012",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Coherent Breathing"],
            average_hrv_improvement=15.5,
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert session.average_hrv_improvement == 15.5
        # Should calculate quality score
        assert session.metrics_summary is not None
        assert session.metrics_summary.get('quality_score') == 5.0

        # Test exceptional HRV improvement triggers featured
        session = SessionContentStrict(
            title="Exceptional HRV Session",
            content="Session with exceptional HRV improvement",
            session_id="test-013",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Coherent Breathing"],
            average_hrv_improvement=20.0,  # >15% should trigger featured
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert session.featured is True

    def test_priority_auto_assignment(self):
        """Test automatic priority assignment based on session type"""
        # Test live session gets HIGH priority
        live_session = SessionContentStrict(
            title="Live Session",
            content="Live breathing session",
            session_id="test-014",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            session_type="live",
            instructor_name="John Doe",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert live_session.priority == ContentPriority.HIGH

        # Test workshop gets HIGH priority
        workshop_session = SessionContentStrict(
            title="Workshop Session",
            content="Workshop breathing session",
            session_id="test-015",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            session_type="workshop",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert workshop_session.priority == ContentPriority.HIGH

        # Test guided session gets NORMAL priority
        guided_session = SessionContentStrict(
            title="Guided Session",
            content="Guided breathing session",
            session_id="test-016",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert guided_session.priority == ContentPriority.NORMAL

    def test_key_achievements_validation(self):
        """Test key achievements list validation"""
        # Test with valid achievements
        session = SessionContentStrict(
            title="Achievement Session",
            content="Session with achievements",
            session_id="test-017",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            key_achievements=[
                "Perfect synchronization",
                "100% completion rate",
                "Average HRV improvement of 15%"
            ],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        assert len(session.key_achievements) == 3

        # Test achievement length limits
        long_achievement = "x" * 501  # Over 500 chars
        with pytest.raises(ValidationError) as exc_info:
            SessionContentStrict(
                title="Long Achievement",
                content="Session content for testing",
                session_id="test-018",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                key_achievements=[long_achievement],
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

        assert "at most 500 characters" in str(exc_info.value)

    def test_quality_score_calculation(self):
        """Test quality score calculation based on HRV improvement"""
        test_cases = [
            (20.0, 5.0),  # >10% = score 5
            (8.0, 4.0),   # >5% = score 4
            (2.0, 3.0),   # >0% = score 3
            (0.0, 0.0),   # 0% = score 0
            (-5.0, 0.0),  # negative = score 0
        ]

        for hrv_improvement, expected_score in test_cases:
            session = SessionContentStrict(
                title=f"Session with {hrv_improvement}% HRV",
                content="Test session for quality score",
                session_id=f"test-hrv-{hrv_improvement}",
                session_duration=1800,
                participant_count=10,
                breathing_techniques=["Box Breathing"],
                average_hrv_improvement=hrv_improvement,
                session_type="guided",
                session_date=datetime.now(timezone.utc),
                published=True
            )

            if hrv_improvement > 0:
                assert session.metrics_summary['quality_score'] == expected_score
            else:
                # For 0 or negative, quality_score might not be set
                score = session.metrics_summary.get('quality_score', 0.0) if session.metrics_summary else 0.0
                assert score == expected_score

    def test_metadata_fields(self):
        """Test optional metadata fields"""
        session = SessionContentStrict(
            title="Metadata Session",
            content="Session with metadata",
            session_id="test-019",
            session_duration=1800,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            metrics_summary={
                "custom_metric": 42,
                "another_metric": "value"
            },
            participant_feedback={
                "average_rating": 4.8,
                "items": [
                    {"participant_name": "Alice", "comment": "Great session!"}
                ]
            },
            published=True
        )

        assert session.metrics_summary["custom_metric"] == 42
        assert session.participant_feedback["average_rating"] == 4.8