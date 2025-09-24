"""
Integration tests for SessionSummaryGenerator
Sprint 3: Halcytone Live Support - Session summary generation tests
"""
import pytest
from datetime import datetime, timezone
import json

from src.halcytone_content_generator.schemas.content_types import SessionContentStrict
from src.halcytone_content_generator.services.session_summary_generator import SessionSummaryGenerator


class TestSessionSummaryGenerator:
    """Test SessionSummaryGenerator service"""

    @pytest.fixture
    def generator(self):
        """Create a SessionSummaryGenerator instance"""
        return SessionSummaryGenerator()

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing"""
        return SessionContentStrict(
            title="Morning Mindfulness Session",
            content="A rejuvenating breathing session to start the day",
            session_id="test-session-001",
            session_duration=1800,  # 30 minutes
            participant_count=25,
            breathing_techniques=["Box Breathing", "4-7-8 Breathing", "Coherent Breathing"],
            average_hrv_improvement=12.5,
            key_achievements=[
                "Perfect group synchronization achieved",
                "All participants completed the full session",
                "Average stress reduction of 35%"
            ],
            session_type="live",
            instructor_name="Sarah Chen",
            session_date=datetime.now(timezone.utc),
            metrics_summary={
                "quality_score": 4.5,
                "engagement_rate": 0.92,
                "completion_rate": 1.0
            },
            participant_feedback={
                "items": [
                    {"participant_name": "John D.", "comment": "Best session yet!"},
                    {"participant_name": "Alice M.", "comment": "Feeling so relaxed"},
                    {"participant_name": "Bob S.", "comment": "Great instruction"}
                ]
            },
            published=True
        )

    def test_generate_email_summary(self, generator, sample_session):
        """Test email summary generation"""
        result = generator.generate_session_summary(sample_session, ['email'])

        assert 'email' in result
        email_content = result['email']

        # Check email structure
        assert 'subject' in email_content
        assert 'html' in email_content
        assert 'text' in email_content

        # Verify subject line
        assert email_content['subject'] == "Session Summary: Morning Mindfulness Session"

        # Verify HTML content includes key elements
        html = email_content['html']
        assert sample_session.title in html
        assert str(sample_session.participant_count) in html
        assert sample_session.instructor_name in html
        assert "30" in html  # Duration in minutes

        # Verify plain text content
        text = email_content['text']
        assert "Morning Mindfulness Session" in text
        assert "25" in text  # Participants
        assert "Box Breathing, 4-7-8 Breathing, Coherent Breathing" in text
        assert "+12.5%" in text  # HRV improvement

    def test_generate_web_summary(self, generator, sample_session):
        """Test web summary generation"""
        result = generator.generate_session_summary(sample_session, ['web'])

        assert 'web' in result
        web_content = result['web']

        # Check web content structure
        assert 'content' in web_content
        assert 'title' in web_content
        assert 'slug' in web_content
        assert 'seo_description' in web_content
        assert 'keywords' in web_content

        # Verify content
        assert web_content['title'] == "Morning Mindfulness Session"
        assert web_content['slug'] == "session-test-session-001-summary"

        # Check SEO description
        seo_desc = web_content['seo_description']
        assert "25 participants" in seo_desc
        assert "30 minutes" in seo_desc
        assert "12.5%" in seo_desc

        # Verify keywords
        assert 'breathing session' in web_content['keywords']
        assert 'HRV improvement' in web_content['keywords']

    def test_generate_social_summaries(self, generator, sample_session):
        """Test social media summary generation"""
        result = generator.generate_session_summary(sample_session, ['social'])

        assert 'social' in result
        social_content = result['social']

        # Test Twitter content
        assert 'twitter' in social_content
        twitter = social_content['twitter']
        assert 'content' in twitter
        assert 'hashtags' in twitter
        assert len(twitter['content']) <= 280  # Twitter character limit
        assert "#Breathwork" in twitter['hashtags']

        # Test LinkedIn content
        assert 'linkedin' in social_content
        linkedin = social_content['linkedin']
        assert "Morning Mindfulness Session" in linkedin['content']
        assert "25 participants" in linkedin['content']
        assert "#CorporateWellness" in linkedin['hashtags']

        # Test Facebook content
        assert 'facebook' in social_content
        facebook = social_content['facebook']
        assert "Morning Mindfulness Session" in facebook['content']
        assert "#BreathingCommunity" in facebook['hashtags']

    def test_multi_channel_generation(self, generator, sample_session):
        """Test generating content for multiple channels"""
        result = generator.generate_session_summary(
            sample_session,
            ['email', 'web', 'social']
        )

        # Verify all channels are present
        assert 'email' in result
        assert 'web' in result
        assert 'social' in result
        assert 'metadata' in result

        # Check metadata
        metadata = result['metadata']
        assert metadata['session_id'] == 'test-session-001'
        assert metadata['session_type'] == 'live'
        assert metadata['quality_score'] == 4.5
        assert metadata['featured'] is True  # HRV > 10%
        assert 'generated_at' in metadata

    def test_technique_formatting(self, generator, sample_session):
        """Test breathing technique formatting"""
        result = generator.generate_session_summary(sample_session, ['email'])

        # The generator should format techniques with icons
        html = result['email']['html']

        # Check that techniques are included
        assert "Box Breathing" in html
        assert "4-7-8 Breathing" in html
        assert "Coherent Breathing" in html

    def test_participant_feedback_inclusion(self, generator, sample_session):
        """Test participant feedback is included in summaries"""
        result = generator.generate_session_summary(sample_session, ['email', 'social'])

        # Check email includes feedback
        email_html = result['email']['html']
        assert "Best session yet!" in email_html
        assert "John D." in email_html

        # Check social includes at least first feedback
        facebook = result['social']['facebook']['content']
        assert "Best session yet!" in facebook

    def test_achievement_formatting(self, generator, sample_session):
        """Test key achievements formatting"""
        result = generator.generate_session_summary(sample_session, ['email', 'web'])

        # Check email includes achievements
        email_html = result['email']['html']
        assert "Perfect group synchronization achieved" in email_html
        assert "All participants completed the full session" in email_html

        # Check web includes achievements
        web_content = result['web']['content']
        assert "Perfect group synchronization achieved" in web_content

    def test_custom_technique_handling(self, generator):
        """Test handling of custom breathing techniques"""
        session = SessionContentStrict(
            title="Custom Technique Session",
            content="Testing custom techniques",
            session_id="test-custom",
            session_duration=1200,
            participant_count=10,
            breathing_techniques=["Custom: Ocean Breathing", "Box Breathing"],
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        result = generator.generate_session_summary(session, ['email'])

        # Custom techniques should be handled gracefully
        email_html = result['email']['html']
        assert "Ocean Breathing" in email_html or "Custom: Ocean Breathing" in email_html

    def test_no_hrv_improvement_handling(self, generator):
        """Test handling sessions without HRV improvement data"""
        session = SessionContentStrict(
            title="Session Without HRV",
            content="Testing without HRV data",
            session_id="test-no-hrv",
            session_duration=1200,
            participant_count=10,
            breathing_techniques=["Box Breathing"],
            average_hrv_improvement=None,  # No HRV data
            session_type="guided",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        result = generator.generate_session_summary(session, ['web'])

        # Should handle missing HRV gracefully
        web_content = result['web']
        seo_desc = web_content['seo_description']
        assert "N/A" in seo_desc or "HRV" not in seo_desc

    def test_session_type_specific_content(self, generator):
        """Test different content for different session types"""
        # Test workshop session
        workshop = SessionContentStrict(
            title="Breathing Workshop",
            content="Advanced breathing techniques workshop",
            session_id="test-workshop",
            session_duration=3600,
            participant_count=15,
            breathing_techniques=["Advanced Pranayama"],
            session_type="workshop",
            session_date=datetime.now(timezone.utc),
            published=True
        )

        result = generator.generate_session_summary(workshop, ['social'])

        # LinkedIn content should mention workshop
        linkedin = result['social']['linkedin']['content']
        assert "workshop" in linkedin.lower()

    def test_hashtag_generation(self, generator, sample_session):
        """Test platform-specific hashtag generation"""
        result = generator.generate_session_summary(sample_session, ['social'])

        # Twitter should have limited hashtags
        twitter_hashtags = result['social']['twitter']['hashtags']
        assert len(twitter_hashtags) <= 2

        # LinkedIn should have professional hashtags
        linkedin_hashtags = result['social']['linkedin']['hashtags']
        assert any('#CorporateWellness' in tag or '#StressManagement' in tag
                  for tag in linkedin_hashtags)

        # Facebook should have community hashtags
        facebook_hashtags = result['social']['facebook']['hashtags']
        assert any('#BreathingCommunity' in tag or '#HealthyLiving' in tag
                  for tag in facebook_hashtags)

    @pytest.mark.asyncio
    async def test_live_update_generation(self, generator):
        """Test real-time update generation"""
        # Test participant joined update
        update = await generator.generate_live_update(
            "test-session",
            "participant_joined",
            {"name": "Alice", "count": 26}
        )

        assert update['session_id'] == "test-session"
        assert update['update_type'] == "participant_joined"
        assert "Alice just joined" in update['message']
        assert "26 participants" in update['message']

        # Test HRV milestone update
        update = await generator.generate_live_update(
            "test-session",
            "hrv_update",
            {"improvement": 15.5}
        )

        assert "+15.5%" in update['message']

    def test_format_session_metrics(self, generator, sample_session):
        """Test session metrics formatting"""
        metrics = generator.format_session_metrics(sample_session)

        assert metrics['duration']['value'] == 30
        assert metrics['duration']['display'] == "30 min"

        assert metrics['participants']['value'] == 25
        assert metrics['participants']['display'] == "25 participants"

        assert metrics['hrv_improvement']['value'] == 12.5
        assert metrics['hrv_improvement']['display'] == "+12.5%"

        assert metrics['techniques']['count'] == 3
        assert len(metrics['techniques']['list']) == 3

        assert metrics['quality_score']['value'] == 4.5
        assert metrics['quality_score']['display'] == "4.5/5"