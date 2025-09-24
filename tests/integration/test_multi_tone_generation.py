"""
Integration Tests for Multi-Tone Content Generation
Sprint 4: Ecosystem Integration - Advanced tone system integration testing
"""
import pytest
from unittest.mock import patch, MagicMock
from jinja2 import Template

from src.halcytone_content_generator.services.tone_manager import tone_manager, AdvancedTone
from src.halcytone_content_generator.templates.tones.professional import ProfessionalToneTemplates
from src.halcytone_content_generator.templates.tones.encouraging import EncouragingToneTemplates
from src.halcytone_content_generator.templates.tones.medical_scientific import MedicalScientificToneTemplates


class TestMultiToneContentGeneration:
    """Integration tests for multi-tone content generation workflows"""

    def test_professional_encouraging_combination_email(self):
        """Test professional-encouraging tone combination for email content"""
        base_content = "We are excited to announce our new feature that will help users improve their wellness journey."

        result = tone_manager.generate_multi_tone_content(
            base_content=base_content,
            tone_combination="professional_encouraging",
            channel="email"
        )

        assert result["primary_tone"] == "professional"
        assert result["secondary_tone"] == "encouraging"
        assert result["blend_ratio"] == 0.7
        assert result["channel_optimization"] is True
        assert "blended_modifiers" in result
        assert "blended_guidelines" in result

        # Check that blended guidelines combine both tones appropriately
        blended_guidelines = result["blended_guidelines"]
        assert "voice" in blended_guidelines
        assert "with elements of" in blended_guidelines["voice"].lower() or "combined with" in blended_guidelines["voice"].lower()

    def test_encouraging_medical_combination_web(self):
        """Test encouraging-medical tone combination for web content"""
        base_content = "Learn about the health benefits of controlled breathing techniques backed by scientific research."

        result = tone_manager.generate_multi_tone_content(
            base_content=base_content,
            tone_combination="encouraging_medical",
            channel="web"
        )

        assert result["primary_tone"] == "encouraging"
        assert result["secondary_tone"] == "medical_scientific"
        assert result["blend_ratio"] == 0.6
        assert result["channel_optimization"] is True

        # Verify recommended use cases include health education
        assert "health_education" in result["recommended_use_cases"]

    def test_professional_medical_combination_blog(self):
        """Test professional-medical tone combination for blog content"""
        result = tone_manager.generate_multi_tone_content(
            base_content="Clinical guidelines for implementing breathing interventions in healthcare settings.",
            tone_combination="professional_medical",
            channel="blog"
        )

        assert result["primary_tone"] == "professional"
        assert result["secondary_tone"] == "medical_scientific"
        assert result["blend_ratio"] == 0.5  # Equal blend
        assert result["channel_optimization"] is True

        # Equal blend should result in balanced guidelines
        guidelines = result["blended_guidelines"]
        assert any(phrase in guidelines["voice"].lower() for phrase in ["balanced approach", "combined with"])

    def test_tone_combination_channel_optimization_warning(self):
        """Test warning when tone combination is used on non-optimized channel"""
        with patch('src.halcytone_content_generator.services.tone_manager.logger') as mock_logger:
            result = tone_manager.generate_multi_tone_content(
                base_content="Test content",
                tone_combination="professional_encouraging",
                channel="research_portal"  # Not in optimized channels
            )

            assert result["channel_optimization"] is False
            mock_logger.warning.assert_called_once()

    def test_invalid_tone_combination_raises_error(self):
        """Test that invalid tone combination raises appropriate error"""
        with pytest.raises(ValueError, match="Unknown tone combination"):
            tone_manager.generate_multi_tone_content(
                base_content="Test content",
                tone_combination="invalid_combination",
                channel="email"
            )


class TestChannelSpecificConfiguration:
    """Integration tests for per-channel tone configuration"""

    def test_email_channel_configuration(self):
        """Test email channel specific configuration"""
        config = tone_manager.get_channel_config("email")

        assert config["default_tone"] == AdvancedTone.ENCOURAGING
        assert config["fallback_tone"] == AdvancedTone.PROFESSIONAL
        assert config["content_constraints"]["max_emoji_count"] == 3
        assert config["content_constraints"]["require_personalization"] is True

    def test_web_channel_configuration(self):
        """Test web channel specific configuration"""
        config = tone_manager.get_channel_config("web")

        assert config["default_tone"] == AdvancedTone.PROFESSIONAL
        assert config["content_constraints"]["max_emoji_count"] == 0
        assert config["content_constraints"]["allow_casual_language"] is False

    def test_research_portal_configuration(self):
        """Test research portal specific configuration"""
        config = tone_manager.get_channel_config("research_portal")

        assert config["default_tone"] == AdvancedTone.MEDICAL_SCIENTIFIC
        assert config["content_constraints"]["require_citations"] is True
        assert config["content_constraints"]["require_disclaimers"] is True

    def test_channel_default_tone_retrieval(self):
        """Test retrieving default tones for different channels"""
        assert tone_manager.get_channel_default_tone("email") == AdvancedTone.ENCOURAGING
        assert tone_manager.get_channel_default_tone("web") == AdvancedTone.PROFESSIONAL
        assert tone_manager.get_channel_default_tone("research_portal") == AdvancedTone.MEDICAL_SCIENTIFIC

    def test_channel_fallback_tone_retrieval(self):
        """Test retrieving fallback tones for different channels"""
        assert tone_manager.get_channel_fallback_tone("email") == AdvancedTone.PROFESSIONAL
        assert tone_manager.get_channel_fallback_tone("blog") == AdvancedTone.MEDICAL_SCIENTIFIC

    def test_tone_weights_for_channels(self):
        """Test tone weight retrieval for different channels"""
        # Email channel heavily weights encouraging tone
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.ENCOURAGING, "email") == 0.6
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.PROFESSIONAL, "email") == 0.3

        # Social channel heavily weights encouraging tone
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.ENCOURAGING, "social") == 0.8
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.PROFESSIONAL, "social") == 0.2

        # Research portal only has medical/scientific tone
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.MEDICAL_SCIENTIFIC, "research_portal") == 1.0
        assert tone_manager.get_tone_weight_for_channel(AdvancedTone.ENCOURAGING, "research_portal") == 0.0


class TestContentConstraintValidation:
    """Integration tests for content constraint validation"""

    def test_email_content_validation_valid(self):
        """Test valid email content passes validation"""
        content = "Hi John! 😊 Your progress has been amazing. Keep up the great work! 🎉"

        result = tone_manager.validate_content_constraints(content, "email")

        assert result["is_valid"] is True
        assert len(result["violations"]) == 0
        assert result["metrics"]["emoji_count"] <= 3
        assert result["metrics"]["exclamation_count"] <= 2

    def test_email_content_validation_too_many_emojis(self):
        """Test email content with too many emojis fails validation"""
        content = "Hi! 😊 🎉 💚 ✨ 🌟 Your progress is amazing!"

        result = tone_manager.validate_content_constraints(content, "email")

        assert result["is_valid"] is False
        assert any("Too many emojis" in violation for violation in result["violations"])

    def test_web_content_validation_no_emojis_allowed(self):
        """Test web content validation rejects emojis"""
        content = "Our platform provides comprehensive wellness solutions. 😊"

        result = tone_manager.validate_content_constraints(content, "web")

        assert result["is_valid"] is False
        assert any("Too many emojis" in violation for violation in result["violations"])

    def test_web_content_validation_casual_language_warning(self):
        """Test web content validation warns about casual language"""
        content = "This is gonna be awesome for all users!"

        result = tone_manager.validate_content_constraints(content, "web")

        assert any("Casual language detected" in warning for warning in result["warnings"])

    def test_social_content_validation_allows_emojis(self):
        """Test social content allows more emojis"""
        content = "Amazing progress! 🎉 💪 ✨ 🌟 Keep going!"

        result = tone_manager.validate_content_constraints(content, "social")

        assert result["is_valid"] is True  # Should be valid for social channel

    def test_research_portal_validation_requires_citations(self):
        """Test research portal content requires citations"""
        content = "Studies show significant improvements in HRV metrics."

        result = tone_manager.validate_content_constraints(content, "research_portal")

        assert result["is_valid"] is False
        assert any("requires citations" in violation for violation in result["violations"])

    def test_research_portal_validation_with_citations(self):
        """Test research portal content with citations passes"""
        content = "Studies by Smith et al (2023) show significant improvements. See doi:10.1234/study"

        result = tone_manager.validate_content_constraints(content, "research_portal")

        assert result["is_valid"] is True

    def test_personalization_check(self):
        """Test personalization requirement checking"""
        # Content without personalization
        impersonal_content = "The platform provides wellness solutions."
        result = tone_manager.validate_content_constraints(impersonal_content, "email")
        assert any("personalization" in warning for warning in result["warnings"])

        # Content with personalization
        personal_content = "Your wellness journey starts here with our platform."
        result = tone_manager.validate_content_constraints(personal_content, "email")
        # Should not have personalization warning
        assert not any("personalization" in warning for warning in result["warnings"])


class TestToneCombinationRecommendations:
    """Integration tests for tone combination recommendations"""

    def test_recommend_professional_encouraging_for_onboarding(self):
        """Test recommendation of professional-encouraging for onboarding content"""
        recommendation = tone_manager.recommend_tone_combination(
            content_type="customer_onboarding",
            channel="email"
        )

        assert recommendation == "professional_encouraging"

    def test_recommend_encouraging_medical_for_health_education(self):
        """Test recommendation of encouraging-medical for health education"""
        recommendation = tone_manager.recommend_tone_combination(
            content_type="wellness_education",
            channel="web"
        )

        assert recommendation == "encouraging_medical"

    def test_recommend_professional_medical_for_clinical_content(self):
        """Test recommendation of professional-medical for clinical content"""
        recommendation = tone_manager.recommend_tone_combination(
            content_type="clinical_guidelines",
            channel="blog"
        )

        assert recommendation == "professional_medical"

    def test_no_recommendation_for_unclear_content(self):
        """Test no recommendation for unclear content types"""
        recommendation = tone_manager.recommend_tone_combination(
            content_type="random_content",
            channel="email"
        )

        assert recommendation is None

    def test_available_combinations_for_channel(self):
        """Test getting available combinations for specific channels"""
        email_combinations = tone_manager.get_available_tone_combinations("email")
        assert "professional_encouraging" in email_combinations
        assert "encouraging_medical" in email_combinations

        blog_combinations = tone_manager.get_available_tone_combinations("blog")
        assert "encouraging_medical" in blog_combinations
        assert "professional_medical" in blog_combinations

    def test_all_available_combinations(self):
        """Test getting all available tone combinations"""
        all_combinations = tone_manager.get_available_tone_combinations()

        expected_combinations = ["professional_encouraging", "encouraging_medical", "professional_medical"]
        assert all(combo in all_combinations for combo in expected_combinations)


class TestToneTemplateIntegration:
    """Integration tests between tone manager and templates"""

    def test_professional_tone_with_template_rendering(self):
        """Test professional tone selection works with template rendering"""
        selected_tone = tone_manager.select_tone("business_announcement", "email")
        assert selected_tone == AdvancedTone.PROFESSIONAL

        # Get appropriate template
        template_str = ProfessionalToneTemplates.get_template("announcement", "email")
        template = Template(template_str)

        # Render with professional tone characteristics
        rendered = template.render(
            subject="Platform Update",
            announcement_title="Enhanced Analytics",
            main_content="We have implemented new features for better insights.",
            key_highlights=["Real-time metrics", "Advanced reporting"]
        )

        assert "Platform Update" in rendered
        assert "Enhanced Analytics" in rendered
        assert "We have implemented" in rendered  # Professional language

    def test_encouraging_tone_with_template_rendering(self):
        """Test encouraging tone selection works with template rendering"""
        selected_tone = tone_manager.select_tone("progress_celebration", "email")
        assert selected_tone == AdvancedTone.ENCOURAGING

        # Get appropriate template
        template_str = EncouragingToneTemplates.get_template("progress", "email")
        template = Template(template_str)

        # Render with encouraging tone characteristics
        rendered = template.render(
            user_name="Sarah",
            achievement_summary="Amazing progress this month!",
            stats={"total_sessions": 25, "total_minutes": 250, "streak_days": 7}
        )

        assert "Sarah" in rendered
        assert "🎉" in rendered  # Emojis for encouraging tone
        assert "Amazing progress" in rendered

    def test_medical_tone_with_template_rendering(self):
        """Test medical/scientific tone selection works with template rendering"""
        selected_tone = tone_manager.select_tone("research_study", "web")
        assert selected_tone == AdvancedTone.MEDICAL_SCIENTIFIC

        # Get appropriate template
        template_str = MedicalScientificToneTemplates.get_template("research_article", "web")
        template = Template(template_str)

        # Render with medical/scientific tone characteristics
        rendered = template.render(
            article_title="Effects of Controlled Breathing",
            background="Stress management interventions",
            objective="Evaluate breathing technique efficacy",
            keywords=["breathing", "stress", "intervention"]
        )

        assert "Effects of Controlled Breathing" in rendered
        assert "## Abstract" in rendered
        assert "**Keywords:** breathing, stress, intervention" in rendered

    def test_tone_template_consistency_across_channels(self):
        """Test that tone selection remains consistent across different channels for same content type"""
        business_email_tone = tone_manager.select_tone("platform_announcement", "email")
        business_web_tone = tone_manager.select_tone("platform_announcement", "web")

        # Both should select professional tone for business content
        assert business_email_tone == AdvancedTone.PROFESSIONAL
        assert business_web_tone == AdvancedTone.PROFESSIONAL

        # Verify templates are available for both
        email_template = ProfessionalToneTemplates.get_template("announcement", "email")
        web_template = ProfessionalToneTemplates.get_template("announcement", "web")

        assert email_template is not None
        assert web_template is not None


class TestBrandConsistencyIntegration:
    """Integration tests for brand consistency across multi-tone generation"""

    def test_brand_consistency_maintained_across_tone_combinations(self):
        """Test that brand consistency is maintained when using tone combinations"""
        combinations = ["professional_encouraging", "encouraging_medical", "professional_medical"]

        for combination in combinations:
            result = tone_manager.generate_multi_tone_content(
                base_content="Our platform helps users achieve wellness goals through evidence-based techniques.",
                tone_combination=combination,
                channel="web"
            )

            # Check that blended guidelines maintain brand elements
            guidelines = result["blended_guidelines"]
            assert "voice" in guidelines
            assert "language" in guidelines
            assert "formality" in guidelines
            assert "expertise" in guidelines

    def test_content_validation_across_all_tones(self):
        """Test content validation works for all tone types"""
        test_content = "You can improve your wellness through our evidence-based platform."

        for tone in [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC]:
            validation = tone_manager.apply_brand_consistency(test_content, tone)

            assert "is_consistent" in validation
            assert "violations" in validation
            assert "suggestions" in validation
            assert "tone_alignment" in validation

            # Content should be generally consistent across all tones
            assert validation["is_consistent"] is True

    def test_prohibited_content_detected_across_tones(self):
        """Test that prohibited content is detected regardless of tone"""
        problematic_content = "This will cure all your problems guaranteed with instant results!"

        for tone in [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC]:
            validation = tone_manager.apply_brand_consistency(problematic_content, tone)

            # Should detect violations across all tones
            assert validation["is_consistent"] is False
            assert len(validation["violations"]) > 0


class TestEndToEndToneWorkflow:
    """End-to-end integration tests for complete tone workflow"""

    def test_complete_multi_tone_workflow_email(self):
        """Test complete workflow from content type to final validation"""
        # 1. Determine content type and channel
        content_type = "feature_announcement"
        channel = "email"

        # 2. Get tone recommendation
        recommended_combination = tone_manager.recommend_tone_combination(content_type, channel)
        assert recommended_combination == "professional_encouraging"

        # 3. Generate multi-tone content configuration
        tone_config = tone_manager.generate_multi_tone_content(
            base_content="We're excited to introduce new meditation features.",
            tone_combination=recommended_combination,
            channel=channel
        )

        assert tone_config["channel_optimization"] is True

        # 4. Validate channel constraints
        sample_content = "We're excited to introduce new meditation features! 😊 This will help you achieve better wellness outcomes."
        constraint_validation = tone_manager.validate_content_constraints(sample_content, channel)

        assert constraint_validation["is_valid"] is True  # Should pass email constraints

        # 5. Validate brand consistency
        brand_validation = tone_manager.apply_brand_consistency(
            sample_content,
            tone_config["primary_tone"]
        )

        assert brand_validation["is_consistent"] is True

    def test_complete_workflow_with_constraint_violations(self):
        """Test complete workflow when content violates constraints"""
        content_type = "research_update"
        channel = "research_portal"

        # Content without required citations
        problematic_content = "Studies show breathing techniques are effective for stress."

        # Should fail constraint validation
        validation = tone_manager.validate_content_constraints(problematic_content, channel)
        assert validation["is_valid"] is False
        assert any("citations" in violation for violation in validation["violations"])

    def test_fallback_tone_usage(self):
        """Test fallback tone is used when primary selection fails"""
        # Test with unknown channel - should use fallback logic
        selected_tone = tone_manager.select_tone("business_content", "unknown_channel")

        # Should still return a valid tone (fallback behavior)
        assert selected_tone in [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC]

        # Test channel fallback
        fallback_tone = tone_manager.get_channel_fallback_tone("email")
        assert fallback_tone == AdvancedTone.PROFESSIONAL