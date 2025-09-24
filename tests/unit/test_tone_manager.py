"""
Unit Tests for Tone Manager
Sprint 4: Ecosystem Integration - Advanced tone management testing
"""
import pytest
from unittest.mock import patch, MagicMock

from src.halcytone_content_generator.services.tone_manager import (
    ToneManager,
    AdvancedTone,
    ToneProfile
)
from src.halcytone_content_generator.schemas.content_types import ContentType


class TestToneManager:
    """Test suite for ToneManager service"""

    @pytest.fixture
    def tone_manager(self):
        """Create tone manager instance for testing"""
        return ToneManager()

    def test_tone_manager_initialization(self, tone_manager):
        """Test proper initialization of tone manager"""
        assert tone_manager is not None
        assert len(tone_manager.tone_profiles) == 3
        assert len(tone_manager.channel_tone_mapping) > 0
        assert tone_manager.brand_consistency_rules is not None

        # Verify all expected tones are initialized
        expected_tones = {AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC}
        assert set(tone_manager.tone_profiles.keys()) == expected_tones

    def test_tone_profiles_structure(self, tone_manager):
        """Test that tone profiles have correct structure"""
        for tone, profile in tone_manager.tone_profiles.items():
            assert isinstance(profile, ToneProfile)
            assert profile.tone == tone
            assert profile.description != ""
            assert len(profile.use_cases) > 0
            assert len(profile.channels) > 0
            assert len(profile.brand_guidelines) > 0
            assert len(profile.content_modifiers) > 0

    def test_select_tone_auto_selection(self, tone_manager):
        """Test automatic tone selection based on content type"""
        # Business content should get professional tone
        tone = tone_manager.select_tone("business_announcement", "email")
        assert tone == AdvancedTone.PROFESSIONAL

        # Research content should get medical/scientific tone
        tone = tone_manager.select_tone("research_study", "web")
        assert tone == AdvancedTone.MEDICAL_SCIENTIFIC

        # Session content should get encouraging tone
        tone = tone_manager.select_tone("session_progress", "email")
        assert tone == AdvancedTone.ENCOURAGING

    def test_select_tone_with_preferred_tone(self, tone_manager):
        """Test tone selection with user preference"""
        # Valid preference for channel
        tone = tone_manager.select_tone(
            "general_content",
            "email",
            preferred_tone=AdvancedTone.PROFESSIONAL
        )
        assert tone == AdvancedTone.PROFESSIONAL

        # Invalid preference for channel (should fall back to auto-selection)
        tone = tone_manager.select_tone(
            "general_content",
            "linkedin",  # Only supports professional
            preferred_tone=AdvancedTone.ENCOURAGING
        )
        assert tone == AdvancedTone.PROFESSIONAL  # LinkedIn default

    def test_select_tone_channel_constraints(self, tone_manager):
        """Test that tone selection respects channel constraints"""
        # LinkedIn only supports professional tone
        tone = tone_manager.select_tone("any_content", "linkedin")
        assert tone == AdvancedTone.PROFESSIONAL

        # Research portal only supports medical/scientific
        tone = tone_manager.select_tone("any_content", "research_portal")
        assert tone == AdvancedTone.MEDICAL_SCIENTIFIC

    def test_select_tone_with_content_type_enum(self, tone_manager):
        """Test tone selection with ContentType enum"""
        # Mock ContentType enum
        class MockContentType:
            value = "session_update"

        mock_content_type = MockContentType()
        tone = tone_manager.select_tone(mock_content_type, "email")
        assert tone == AdvancedTone.ENCOURAGING

    def test_get_tone_profile(self, tone_manager):
        """Test retrieving tone profiles"""
        # Valid tone
        profile = tone_manager.get_tone_profile(AdvancedTone.PROFESSIONAL)
        assert profile.tone == AdvancedTone.PROFESSIONAL
        assert profile.description != ""

        # Test all tones have profiles
        for tone in AdvancedTone:
            if tone in [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC]:
                profile = tone_manager.get_tone_profile(tone)
                assert profile is not None

    def test_get_tone_modifiers(self, tone_manager):
        """Test retrieving tone-specific modifiers"""
        modifiers = tone_manager.get_tone_modifiers(AdvancedTone.PROFESSIONAL)
        assert "sentence_length" in modifiers
        assert "technical_language" in modifiers
        assert "call_to_action" in modifiers

        # Professional tone should use technical language
        assert modifiers["technical_language"] is True

        # Encouraging tone should not use technical language
        encouraging_modifiers = tone_manager.get_tone_modifiers(AdvancedTone.ENCOURAGING)
        assert encouraging_modifiers["technical_language"] is False

    def test_validate_tone_for_content(self, tone_manager):
        """Test content type and tone validation"""
        # Valid combinations
        assert tone_manager.validate_tone_for_content(
            AdvancedTone.PROFESSIONAL, "business", "email"
        ) is True

        assert tone_manager.validate_tone_for_content(
            AdvancedTone.MEDICAL_SCIENTIFIC, "research", "web"
        ) is True

        assert tone_manager.validate_tone_for_content(
            AdvancedTone.ENCOURAGING, "wellness", "social"
        ) is True

        # Invalid channel combination
        assert tone_manager.validate_tone_for_content(
            AdvancedTone.ENCOURAGING, "any_content", "research_portal"
        ) is False

    def test_is_tone_valid_for_channel(self, tone_manager):
        """Test channel-tone compatibility validation"""
        # Professional tone valid for most channels
        assert tone_manager._is_tone_valid_for_channel(
            AdvancedTone.PROFESSIONAL, "email"
        ) is True

        # Encouraging tone not valid for research portal
        assert tone_manager._is_tone_valid_for_channel(
            AdvancedTone.ENCOURAGING, "research_portal"
        ) is False

        # Medical/scientific not typically valid for social
        social_tones = tone_manager.channel_tone_mapping.get("social", [])
        assert AdvancedTone.MEDICAL_SCIENTIFIC not in social_tones

    def test_get_brand_guidelines(self, tone_manager):
        """Test retrieving brand guidelines"""
        guidelines = tone_manager.get_brand_guidelines(AdvancedTone.PROFESSIONAL)
        assert "voice" in guidelines
        assert "language" in guidelines
        assert "formality" in guidelines
        assert "expertise" in guidelines

        # Each tone should have different guidelines
        prof_guidelines = tone_manager.get_brand_guidelines(AdvancedTone.PROFESSIONAL)
        enc_guidelines = tone_manager.get_brand_guidelines(AdvancedTone.ENCOURAGING)
        assert prof_guidelines["formality"] != enc_guidelines["formality"]

    def test_apply_brand_consistency_valid_content(self, tone_manager):
        """Test brand consistency validation with valid content"""
        valid_professional_content = """
        We are pleased to announce our new enterprise platform feature.
        This development provides enhanced analytics capabilities for organizations.
        For more information, contact our enterprise team.
        """

        result = tone_manager.apply_brand_consistency(
            valid_professional_content,
            AdvancedTone.PROFESSIONAL
        )

        assert isinstance(result, dict)
        assert "is_consistent" in result
        assert "violations" in result
        assert "suggestions" in result
        assert "tone_alignment" in result

    def test_apply_brand_consistency_violations(self, tone_manager):
        """Test brand consistency validation with policy violations"""
        problematic_content = """
        This miracle cure will diagnose and treat all your health problems guaranteed!
        Only for elite members who want instant overnight results.
        """

        result = tone_manager.apply_brand_consistency(
            problematic_content,
            AdvancedTone.MEDICAL_SCIENTIFIC
        )

        assert result["is_consistent"] is False
        assert len(result["violations"]) > 0

    def test_prohibited_element_detection(self, tone_manager):
        """Test detection of prohibited content elements"""
        # Test medical diagnosis language
        assert tone_manager._contains_prohibited_element(
            "we will diagnose your condition", "medical_diagnosis_language"
        ) is True

        # Test treatment guarantees
        assert tone_manager._contains_prohibited_element(
            "guaranteed to cure all problems", "treatment_guarantees"
        ) is True

        # Test acceptable content
        assert tone_manager._contains_prohibited_element(
            "research suggests potential benefits", "treatment_guarantees"
        ) is False

    def test_required_element_detection(self, tone_manager):
        """Test detection of required content elements"""
        # Test user-centered focus
        assert tone_manager._contains_required_element(
            "this will help you achieve your goals", "user_centered_focus"
        ) is True

        # Test evidence-based claims
        assert tone_manager._contains_required_element(
            "research shows significant improvements", "evidence_based_claims"
        ) is True

        # Test missing elements
        assert tone_manager._contains_required_element(
            "this is amazing content", "evidence_based_claims"
        ) is False

    def test_tone_alignment_scoring(self, tone_manager):
        """Test tone alignment scoring functionality"""
        professional_profile = tone_manager.get_tone_profile(AdvancedTone.PROFESSIONAL)

        # Professional content with technical terms
        technical_content = "Our clinical research demonstrates evidence-based improvements in wellness outcomes."
        alignment = tone_manager._check_tone_alignment(technical_content, professional_profile)

        assert "score" in alignment
        assert "feedback" in alignment
        assert isinstance(alignment["score"], (int, float))
        assert 0 <= alignment["score"] <= 1

        # Casual content should score lower for professional tone
        casual_content = "Hey guys! This is gonna be awesome and super cool!"
        casual_alignment = tone_manager._check_tone_alignment(casual_content, professional_profile)

        # Should provide feedback about professional language
        assert len(casual_alignment["feedback"]) > 0

    def test_channel_tone_mapping_completeness(self, tone_manager):
        """Test that channel tone mapping covers expected channels"""
        expected_channels = [
            "email", "web", "blog", "social", "linkedin",
            "twitter", "facebook", "app_notifications", "research_portal"
        ]

        for channel in expected_channels:
            assert channel in tone_manager.channel_tone_mapping
            assert len(tone_manager.channel_tone_mapping[channel]) > 0

    def test_brand_consistency_rules_structure(self, tone_manager):
        """Test brand consistency rules have proper structure"""
        rules = tone_manager.brand_consistency_rules

        assert "brand_voice_elements" in rules
        assert "prohibited_elements" in rules
        assert "required_elements" in rules

        # Check that brand voice elements are defined
        brand_elements = rules["brand_voice_elements"]
        expected_elements = ["empathy", "expertise", "innovation", "accessibility"]
        for element in expected_elements:
            assert element in brand_elements

    def test_edge_case_empty_content(self, tone_manager):
        """Test handling of edge cases like empty content"""
        result = tone_manager.apply_brand_consistency("", AdvancedTone.PROFESSIONAL)
        assert result is not None
        assert "is_consistent" in result

    def test_edge_case_unknown_channel(self, tone_manager):
        """Test handling of unknown channels"""
        tone = tone_manager.select_tone("any_content", "unknown_channel")
        # Should default to encouraging tone
        assert tone == AdvancedTone.ENCOURAGING

    def test_edge_case_none_values(self, tone_manager):
        """Test handling of None values"""
        tone = tone_manager.select_tone(None, "email")
        assert tone in AdvancedTone

        tone = tone_manager.select_tone("content", None)
        assert tone in AdvancedTone

    @pytest.mark.parametrize("content_type,expected_tone", [
        ("business_announcement", AdvancedTone.PROFESSIONAL),
        ("platform_update", AdvancedTone.PROFESSIONAL),
        ("enterprise_communication", AdvancedTone.PROFESSIONAL),
        ("research_findings", AdvancedTone.MEDICAL_SCIENTIFIC),
        ("clinical_study", AdvancedTone.MEDICAL_SCIENTIFIC),
        ("health_education", AdvancedTone.MEDICAL_SCIENTIFIC),
        ("session_summary", AdvancedTone.ENCOURAGING),
        ("progress_celebration", AdvancedTone.ENCOURAGING),
        ("wellness_tip", AdvancedTone.ENCOURAGING),
    ])
    def test_content_type_tone_mapping(self, tone_manager, content_type, expected_tone):
        """Test that different content types map to expected tones"""
        # Use a channel that supports all tones
        tone = tone_manager.select_tone(content_type, "email")
        assert tone == expected_tone


class TestToneProfile:
    """Test suite for ToneProfile data class"""

    def test_tone_profile_creation(self):
        """Test creation of ToneProfile instances"""
        profile = ToneProfile(
            tone=AdvancedTone.PROFESSIONAL,
            description="Test description",
            use_cases=["test_case"],
            channels=["email"],
            brand_guidelines={"voice": "professional"},
            content_modifiers={"technical_language": True}
        )

        assert profile.tone == AdvancedTone.PROFESSIONAL
        assert profile.description == "Test description"
        assert profile.use_cases == ["test_case"]
        assert profile.channels == ["email"]
        assert profile.brand_guidelines == {"voice": "professional"}
        assert profile.content_modifiers == {"technical_language": True}


class TestAdvancedTone:
    """Test suite for AdvancedTone enum"""

    def test_tone_enum_values(self):
        """Test that AdvancedTone enum has expected values"""
        expected_tones = {
            "professional", "encouraging", "medical_scientific",
            "casual", "inspirational", "educational"
        }

        actual_tones = {tone.value for tone in AdvancedTone}

        # Check that our new tones are included
        assert "professional" in actual_tones
        assert "encouraging" in actual_tones
        assert "medical_scientific" in actual_tones

    def test_tone_enum_string_conversion(self):
        """Test string conversion of tone enums"""
        assert AdvancedTone.PROFESSIONAL.value == "professional"
        assert str(AdvancedTone.PROFESSIONAL.value) == "professional"


# Integration tests for tone manager with other components
class TestToneManagerIntegration:
    """Integration tests for tone manager with other system components"""

    @pytest.fixture
    def tone_manager(self):
        return ToneManager()

    def test_tone_manager_with_content_types(self, tone_manager):
        """Test tone manager integration with content type schemas"""
        # This would test integration with actual ContentType enum if available
        # For now, test with string representations
        test_cases = [
            ("business_post", "web", AdvancedTone.PROFESSIONAL),  # Should trigger business logic
            ("session_update", "email", AdvancedTone.ENCOURAGING),
            ("research_paper", "web", AdvancedTone.MEDICAL_SCIENTIFIC)
        ]

        for content_type, channel, expected_tone in test_cases:
            selected_tone = tone_manager.select_tone(content_type, channel)
            assert selected_tone == expected_tone

    @patch('src.halcytone_content_generator.services.tone_manager.logger')
    def test_tone_manager_logging(self, mock_logger, tone_manager):
        """Test that tone manager logs appropriate messages"""
        tone_manager.select_tone(
            "test_content",
            "email",
            preferred_tone=AdvancedTone.PROFESSIONAL
        )

        # Verify that info log was called
        mock_logger.info.assert_called()

    def test_global_tone_manager_instance(self):
        """Test that global tone manager instance is properly initialized"""
        from src.halcytone_content_generator.services.tone_manager import tone_manager as global_manager

        assert global_manager is not None
        assert isinstance(global_manager, ToneManager)
        assert len(global_manager.tone_profiles) == 3