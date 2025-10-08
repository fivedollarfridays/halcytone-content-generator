"""
Unit Tests for Tone Templates
Sprint 4: Ecosystem Integration - Tone-specific template testing
"""
import pytest
from jinja2 import Template

from halcytone_content_generator.templates.tones.professional import ProfessionalToneTemplates
from halcytone_content_generator.templates.tones.encouraging import EncouragingToneTemplates
from halcytone_content_generator.templates.tones.medical_scientific import MedicalScientificToneTemplates


class TestProfessionalToneTemplates:
    """Test suite for Professional tone templates"""

    def test_get_template_email_announcement(self):
        """Test professional email announcement template"""
        template_str = ProfessionalToneTemplates.get_template("announcement", "email")
        assert template_str == ProfessionalToneTemplates.EMAIL_ANNOUNCEMENT

        # Verify template can be rendered
        template = Template(template_str)
        rendered = template.render(
            subject="New Platform Update",
            announcement_title="Enhanced Analytics Dashboard",
            main_content="We have released new analytics capabilities.",
            key_highlights=["Real-time metrics", "Custom reporting", "Advanced insights"]
        )

        assert "New Platform Update" in rendered
        assert "Enhanced Analytics Dashboard" in rendered
        assert "Real-time metrics" in rendered

    def test_get_template_platform_update(self):
        """Test professional platform update template"""
        template_str = ProfessionalToneTemplates.get_template("platform_update", "email")
        assert template_str == ProfessionalToneTemplates.EMAIL_PLATFORM_UPDATE

        # Verify template rendering
        template = Template(template_str)
        rendered = template.render(
            update_title="API Version 2.0",
            update_overview="Comprehensive API updates with enhanced functionality.",
            implementation_timeline="Deployment scheduled for next week"
        )

        assert "API Version 2.0" in rendered
        assert "Comprehensive API updates" in rendered

    def test_get_template_web_blog(self):
        """Test professional web blog template"""
        template_str = ProfessionalToneTemplates.get_template("blog", "web")
        assert template_str == ProfessionalToneTemplates.WEB_BLOG_PROFESSIONAL

        # Verify template structure
        template = Template(template_str)
        rendered = template.render(
            title="Industry Analysis: Wellness Technology",
            introduction="The wellness technology sector continues to evolve.",
            executive_summary="Key trends and market insights.",
            industry_context="Current market dynamics and competitive landscape.",
            conclusion="Strategic recommendations for organizations."
        )

        assert "# Industry Analysis: Wellness Technology" in rendered
        assert "## Executive Summary" in rendered
        assert "## Industry Context" in rendered

    def test_get_template_social_linkedin(self):
        """Test professional LinkedIn social template"""
        template_str = ProfessionalToneTemplates.get_template("post", "linkedin")
        assert template_str == ProfessionalToneTemplates.SOCIAL_LINKEDIN

        template = Template(template_str)
        rendered = template.render(
            announcement="Excited to share our latest enterprise solution",
            key_benefits=["Improved productivity", "Enhanced wellness", "Better outcomes"],
            link="https://example.com"
        )

        assert "enterprise solution" in rendered
        assert "Improved productivity" in rendered
        assert "#EnterpriseWellness" in rendered

    def test_get_style_guidelines(self):
        """Test professional tone style guidelines"""
        guidelines = ProfessionalToneTemplates.get_style_guidelines()

        assert "voice_characteristics" in guidelines
        assert "content_structure" in guidelines
        assert "language_preferences" in guidelines
        assert "prohibited_elements" in guidelines
        assert "required_elements" in guidelines

        # Verify specific professional characteristics
        voice = guidelines["voice_characteristics"]
        assert voice["tone"] == "Authoritative yet approachable"
        assert voice["formality"] == "Professional with minimal colloquialisms"

    def test_template_fallback(self):
        """Test template fallback for unknown types"""
        template_str = ProfessionalToneTemplates.get_template("unknown_type", "unknown_channel")
        assert template_str == ProfessionalToneTemplates.EMAIL_ANNOUNCEMENT


class TestEncouragingToneTemplates:
    """Test suite for Encouraging tone templates"""

    def test_get_template_email_welcome(self):
        """Test encouraging email welcome template"""
        template_str = EncouragingToneTemplates.get_template("welcome", "email")
        assert template_str == EncouragingToneTemplates.EMAIL_WELCOME

        template = Template(template_str)
        rendered = template.render(
            user_name="Sarah",
            onboarding_content="Your personalized journey begins now!",
            sender_name="Alex",
            cta_button="Start Your First Session"
        )

        assert "Welcome to your wellness journey, Sarah!" in rendered
        assert "🌟" in rendered  # Emoji usage
        assert "absolutely thrilled" in rendered  # Encouraging language
        assert "Start Your First Session" in rendered

    def test_get_template_progress_celebration(self):
        """Test encouraging progress celebration template"""
        template_str = EncouragingToneTemplates.get_template("progress", "email")
        assert template_str == EncouragingToneTemplates.EMAIL_PROGRESS_CELEBRATION

        template = Template(template_str)
        rendered = template.render(
            user_name="John",
            achievement_summary="You've completed 50 sessions this month!",
            milestones=[
                {"description": "10-day streak achieved", "date": "2024-01-15"},
                {"description": "100 minutes of breathing", "date": "2024-01-20"}
            ],
            stats={
                "total_sessions": 50,
                "total_minutes": 500,
                "streak_days": 10,
                "hrv_improvement": 15
            },
            personalized_message="Your dedication is inspiring!",
            next_steps_content="Ready for your next milestone?",
            sender_name="Team Halcytone"
        )

        assert "Look how far you've come, John!" in rendered
        assert "🎉" in rendered
        assert "50 sessions completed" in rendered
        assert "15% improvement" in rendered
        assert "10-day streak achieved" in rendered

    def test_get_template_web_success_story(self):
        """Test encouraging web success story template"""
        template_str = EncouragingToneTemplates.get_template("success_story", "web")
        assert template_str == EncouragingToneTemplates.WEB_SUCCESS_STORY

        template = Template(template_str)
        rendered = template.render(
            success_story_title="Maria's Transformation Journey",
            user_quote="Halcytone changed my life completely",
            user_name="Maria",
            user_location="San Francisco, CA",
            user_starting_point="Maria struggled with daily stress",
            transformation_story="Through consistent practice, Maria found her calm",
            results_achieved="Reduced stress by 70% and improved sleep quality",
            user_advice="Start small and be consistent",
            cta_link="#start-journey"
        )

        assert "# Maria's Transformation Journey" in rendered
        assert "*Halcytone changed my life completely*" in rendered
        assert "— Maria, San Francisco, CA" in rendered
        assert "Start Your Journey Today" in rendered

    def test_get_template_social_motivational(self):
        """Test encouraging social motivational template"""
        template_str = EncouragingToneTemplates.get_template("motivational", "social")
        assert template_str == EncouragingToneTemplates.SOCIAL_MOTIVATIONAL

        template = Template(template_str)
        rendered = template.render(
            motivational_message="Every breath is a step toward a better you",
            hashtags="#WellnessJourney #MindfulBreathing #YouGotThis"
        )

        assert "Every breath is a step toward a better you" in rendered
        assert "Progress, not perfection" in rendered
        assert "💚" in rendered
        assert "#WellnessJourney" in rendered

    def test_get_template_app_notifications(self):
        """Test encouraging app notification templates"""
        encouragement = EncouragingToneTemplates.get_template("encouragement", "app")
        streak = EncouragingToneTemplates.get_template("streak", "app")
        reminder = EncouragingToneTemplates.get_template("reminder", "app")

        assert encouragement == EncouragingToneTemplates.NOTIFICATION_ENCOURAGEMENT
        assert streak == EncouragingToneTemplates.NOTIFICATION_STREAK
        assert reminder == EncouragingToneTemplates.NOTIFICATION_GENTLE_REMINDER

        # Test template rendering
        encouragement_template = Template(encouragement)
        rendered = encouragement_template.render(user_name="Alex")
        assert "Alex, you're doing amazing!" in rendered
        assert "🧘‍♀️" in rendered

    def test_get_style_guidelines(self):
        """Test encouraging tone style guidelines"""
        guidelines = EncouragingToneTemplates.get_style_guidelines()

        voice = guidelines["voice_characteristics"]
        assert voice["tone"] == "Warm, supportive, and empowering"
        assert voice["language"] == "Positive, inclusive, and accessible"

        # Check for encouraging-specific elements
        encouraged = guidelines["encouraged_elements"]
        assert "Personal stories and experiences" in encouraged
        assert "Celebration of small wins" in encouraged
        assert "Emojis for warmth (when appropriate)" in encouraged

        # Check prohibited elements
        prohibited = guidelines["prohibited_elements"]
        assert "Pressure or urgency" in prohibited
        assert "Judgment or criticism" in prohibited

    def test_community_templates(self):
        """Test encouraging community templates"""
        welcome = EncouragingToneTemplates.get_template("welcome", "community")
        celebration = EncouragingToneTemplates.get_template("celebration", "community")

        assert welcome == EncouragingToneTemplates.COMMUNITY_WELCOME
        assert celebration == EncouragingToneTemplates.COMMUNITY_CELEBRATION_POST

        # Test rendering
        welcome_template = Template(welcome)
        rendered = welcome_template.render(user_name="Taylor")
        assert "Welcome to our Wellness Family!" in rendered
        assert "Taylor" in rendered
        assert "👋" in rendered


class TestMedicalScientificToneTemplates:
    """Test suite for Medical/Scientific tone templates"""

    def test_get_template_email_research_update(self):
        """Test medical/scientific research update template"""
        template_str = MedicalScientificToneTemplates.get_template("research_update", "email")
        assert template_str == MedicalScientificToneTemplates.EMAIL_RESEARCH_UPDATE

        template = Template(template_str)
        rendered = template.render(
            study_title="Effects of Controlled Breathing on HRV",
            research_area="cardiovascular wellness",
            study_overview="Randomized controlled trial with 200 participants",
            methodology_summary="Double-blind, placebo-controlled study design",
            primary_findings=[
                {"description": "Significant improvement in HRV scores", "statistical_significance": "p < 0.001"},
                {"description": "Reduced cortisol levels", "statistical_significance": "p < 0.05"}
            ],
            clinical_implications="Findings support breathing interventions for stress management",
            principal_investigator="Dr. Sarah Johnson",
            institution="University Medical Center"
        )

        assert "Effects of Controlled Breathing on HRV" in rendered
        assert "cardiovascular wellness" in rendered
        assert "p < 0.001" in rendered
        assert "Dr. Sarah Johnson" in rendered
        assert "Double-blind, placebo-controlled" in rendered

    def test_get_template_clinical_advisory(self):
        """Test medical/scientific clinical advisory template"""
        template_str = MedicalScientificToneTemplates.get_template("clinical_advisory", "email")
        assert template_str == MedicalScientificToneTemplates.EMAIL_CLINICAL_ADVISORY

        template = Template(template_str)
        rendered = template.render(
            advisory_title="Breathing Techniques in Clinical Practice",
            clinical_topic="implementation of controlled breathing protocols",
            clinical_background="Evidence supports therapeutic breathing interventions",
            evidence_summary="Multiple RCTs demonstrate efficacy",
            contraindications=[
                {"condition": "Severe COPD", "rationale": "May exacerbate breathing difficulties"},
                {"condition": "Active psychosis", "rationale": "Requires clinical supervision"}
            ],
            recommendations=[
                {
                    "action": "Assess patient respiratory status before implementation",
                    "evidence_level": "Level I",
                    "rationale": "Safety screening prevents adverse events"
                }
            ],
            review_date="2024-01-15",
            medical_director="Dr. Michael Chen"
        )

        assert "Breathing Techniques in Clinical Practice" in rendered
        assert "Severe COPD" in rendered
        assert "Level I" in rendered
        assert "Dr. Michael Chen" in rendered

    def test_get_template_web_research_article(self):
        """Test medical/scientific research article template"""
        template_str = MedicalScientificToneTemplates.get_template("research_article", "web")
        assert template_str == MedicalScientificToneTemplates.WEB_RESEARCH_ARTICLE

        template = Template(template_str)
        rendered = template.render(
            article_title="Controlled Breathing and Stress Response: A Systematic Review",
            background="Stress-related disorders are increasingly common",
            objective="Evaluate effectiveness of breathing interventions",
            methods_summary="Systematic review of randomized controlled trials",
            results_summary="15 studies met inclusion criteria",
            conclusions="Strong evidence supports breathing interventions",
            keywords=["breathing", "stress", "HRV", "intervention"],
            introduction="Chronic stress poses significant health risks",
            inclusion_criteria=["RCT design", "Adult participants", "Breathing intervention"],
            exclusion_criteria=["Case studies", "Pediatric populations"],
            primary_outcome="Stress reduction measured by cortisol levels",
            corresponding_author="Dr. Research Lead",
            submission_date="2024-01-01",
            acceptance_date="2024-01-15",
            publication_date="2024-02-01"
        )

        assert "# Controlled Breathing and Stress Response" in rendered
        assert "## Abstract" in rendered
        assert "**Background:**" in rendered
        assert "**Keywords:** breathing, stress, HRV, intervention" in rendered
        assert "## Methods" in rendered
        assert "Dr. Research Lead" in rendered

    def test_get_template_clinical_guideline(self):
        """Test medical/scientific clinical guideline template"""
        template_str = MedicalScientificToneTemplates.get_template("clinical_guideline", "web")
        assert template_str == MedicalScientificToneTemplates.WEB_CLINICAL_GUIDELINE

        template = Template(template_str)
        rendered = template.render(
            guideline_title="Implementation of Breathing Interventions",
            executive_summary="Evidence-based recommendations for clinical practice",
            key_recommendations=[
                {
                    "statement": "Assess respiratory function before implementation",
                    "evidence_quality": "High",
                    "strength": "Strong"
                }
            ],
            clinical_question="When should breathing interventions be implemented?",
            target_population="Adults with stress-related conditions",
            intended_users="Healthcare providers",
            development_group="Multidisciplinary expert panel",
            last_updated="2024-01-15",
            next_review_date="2025-01-15"
        )

        assert "# Clinical Practice Guideline: Implementation of Breathing Interventions" in rendered
        assert "## Executive Summary" in rendered
        assert "**Recommendation 1:**" in rendered
        assert "*Evidence Quality:* High" in rendered
        assert "**Last Updated:** 2024-01-15" in rendered

    def test_get_style_guidelines(self):
        """Test medical/scientific tone style guidelines"""
        guidelines = MedicalScientificToneTemplates.get_style_guidelines()

        voice = guidelines["voice_characteristics"]
        assert voice["tone"] == "Objective, precise, and evidence-based"
        assert voice["formality"] == "Highly professional and clinical"

        # Check required elements
        required = guidelines["required_elements"]
        assert "Evidence citations" in required
        assert "Statistical significance reporting" in required
        assert "Clinical relevance statement" in required

        # Check prohibited elements
        prohibited = guidelines["prohibited_elements"]
        assert "Emotional or subjective language" in prohibited
        assert "Medical advice without proper context" in prohibited

    def test_get_medical_disclaimers(self):
        """Test medical disclaimers"""
        disclaimers = MedicalScientificToneTemplates.get_medical_disclaimers()

        assert "general" in disclaimers
        assert "research" in disclaimers
        assert "clinical_guidance" in disclaimers

        general = disclaimers["general"]
        assert "educational purposes only" in general
        assert "qualified healthcare professionals" in general

    def test_template_social_media_limited(self):
        """Test that medical/scientific social templates are appropriately limited"""
        template_str = MedicalScientificToneTemplates.get_template("research_highlight", "social")
        assert template_str == MedicalScientificToneTemplates.SOCIAL_RESEARCH_HIGHLIGHT

        template = Template(template_str)
        rendered = template.render(
            finding_summary="New study shows 15% improvement in HRV",
            study_citation="Smith et al. (2024)",
            key_statistic="n=200, p<0.001",
            study_link="https://example.com/study"
        )

        assert "New study shows 15% improvement" in rendered
        assert "#Research #ClinicalStudy #EvidenceBased" in rendered
        assert "Smith et al. (2024)" in rendered


class TestToneTemplateIntegration:
    """Integration tests across all tone templates"""

    @pytest.mark.parametrize("template_class,tone_name", [
        (ProfessionalToneTemplates, "professional"),
        (EncouragingToneTemplates, "encouraging"),
        (MedicalScientificToneTemplates, "medical_scientific")
    ])
    def test_all_templates_have_get_template_method(self, template_class, tone_name):
        """Test that all tone template classes have get_template method"""
        assert hasattr(template_class, 'get_template')
        assert callable(template_class.get_template)

    @pytest.mark.parametrize("template_class", [
        ProfessionalToneTemplates,
        EncouragingToneTemplates,
        MedicalScientificToneTemplates
    ])
    def test_all_templates_have_style_guidelines(self, template_class):
        """Test that all tone template classes have style guidelines"""
        assert hasattr(template_class, 'get_style_guidelines')
        guidelines = template_class.get_style_guidelines()

        # Check common structure
        assert "voice_characteristics" in guidelines
        assert "content_structure" in guidelines
        assert "language_preferences" in guidelines

    def test_template_content_consistency(self):
        """Test that templates maintain consistent variable naming"""
        # Common variables that should work across templates
        common_vars = {
            "title": "Test Title",
            "content": "Test content",
            "user_name": "TestUser"
        }

        # Test professional template
        prof_template = Template(ProfessionalToneTemplates.EMAIL_ANNOUNCEMENT)
        try:
            prof_template.render(**common_vars,
                               subject="Test",
                               announcement_title="Test",
                               main_content="Test",
                               key_highlights=[])
        except Exception as e:
            pytest.fail(f"Professional template failed with common variables: {e}")

    def test_jinja2_syntax_validity(self):
        """Test that all templates have valid Jinja2 syntax"""
        all_templates = [
            # Professional templates
            ProfessionalToneTemplates.EMAIL_ANNOUNCEMENT,
            ProfessionalToneTemplates.WEB_BLOG_PROFESSIONAL,
            ProfessionalToneTemplates.SOCIAL_LINKEDIN,

            # Encouraging templates
            EncouragingToneTemplates.EMAIL_WELCOME,
            EncouragingToneTemplates.WEB_SUCCESS_STORY,
            EncouragingToneTemplates.SOCIAL_MOTIVATIONAL,

            # Medical/Scientific templates
            MedicalScientificToneTemplates.EMAIL_RESEARCH_UPDATE,
            MedicalScientificToneTemplates.WEB_RESEARCH_ARTICLE,
            MedicalScientificToneTemplates.SOCIAL_RESEARCH_HIGHLIGHT
        ]

        for template_str in all_templates:
            try:
                Template(template_str)
            except Exception as e:
                pytest.fail(f"Invalid Jinja2 syntax in template: {e}")

    def test_template_channel_coverage(self):
        """Test that templates cover expected channels"""
        expected_channels = ["email", "web", "social"]
        template_classes = [
            ProfessionalToneTemplates,
            EncouragingToneTemplates,
            MedicalScientificToneTemplates
        ]

        for template_class in template_classes:
            for channel in expected_channels:
                # Should not raise exception
                template_str = template_class.get_template("general", channel)
                assert isinstance(template_str, str)
                assert len(template_str) > 0