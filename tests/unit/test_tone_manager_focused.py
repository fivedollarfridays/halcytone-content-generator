"""
Focused tests for Tone Manager Service
Target: 70%+ coverage with efficient test design

Covers core functionality:
- Tone enum and dataclass
- Tone manager initialization
- Tone selection logic
- Brand consistency validation
- Channel-specific configuration
- Multi-tone content generation
"""

import pytest
from unittest.mock import Mock, patch

from halcytone_content_generator.services.tone_manager import (
    AdvancedTone,
    ToneProfile,
    ToneManager,
    get_tone_manager
)
from halcytone_content_generator.schemas.content_types import ContentType


# Test Enum and Dataclass

class TestDataStructures:
    """Test tone enum and dataclass."""

    def test_advanced_tone_values(self):
        """Test AdvancedTone enum values."""
        assert AdvancedTone.PROFESSIONAL.value == "professional"
        assert AdvancedTone.ENCOURAGING.value == "encouraging"
        assert AdvancedTone.MEDICAL_SCIENTIFIC.value == "medical_scientific"
        assert AdvancedTone.CASUAL.value == "casual"

    def test_tone_profile_creation(self):
        """Test ToneProfile dataclass."""
        profile = ToneProfile(
            tone=AdvancedTone.PROFESSIONAL,
            description="Test description",
            use_cases=["business", "email"],
            channels=["email", "web"],
            brand_guidelines={"voice": "professional"},
            content_modifiers={"technical_language": True}
        )
        assert profile.tone == AdvancedTone.PROFESSIONAL
        assert "business" in profile.use_cases
        assert "email" in profile.channels


# Test ToneManager Initialization

class TestToneManagerInit:
    """Test tone manager initialization."""

    def test_tone_manager_initialization(self):
        """Test ToneManager initializes correctly."""
        manager = ToneManager()

        assert manager.tone_profiles is not None
        assert manager.channel_tone_mapping is not None
        assert manager.brand_consistency_rules is not None
        assert manager.per_channel_config is not None
        assert manager.tone_combinations is not None

    def test_initialize_tone_profiles(self):
        """Test tone profiles initialization."""
        manager = ToneManager()
        profiles = manager.tone_profiles

        assert len(profiles) == 3
        assert AdvancedTone.PROFESSIONAL in profiles
        assert AdvancedTone.ENCOURAGING in profiles
        assert AdvancedTone.MEDICAL_SCIENTIFIC in profiles

    def test_initialize_channel_mapping(self):
        """Test channel mapping initialization."""
        manager = ToneManager()
        mapping = manager.channel_tone_mapping

        assert "email" in mapping
        assert "web" in mapping
        assert "linkedin" in mapping
        assert AdvancedTone.PROFESSIONAL in mapping["linkedin"]

    def test_initialize_brand_rules(self):
        """Test brand rules initialization."""
        manager = ToneManager()
        rules = manager.brand_consistency_rules

        assert "brand_voice_elements" in rules
        assert "prohibited_elements" in rules
        assert "required_elements" in rules

    def test_initialize_per_channel_config(self):
        """Test per-channel config initialization."""
        manager = ToneManager()
        config = manager.per_channel_config

        assert "email" in config
        assert "web" in config
        assert "research_portal" in config
        assert config["email"]["default_tone"] == AdvancedTone.ENCOURAGING

    def test_initialize_tone_combinations(self):
        """Test tone combinations initialization."""
        manager = ToneManager()
        combinations = manager.tone_combinations

        assert "professional_encouraging" in combinations
        assert "encouraging_medical" in combinations
        assert "professional_medical" in combinations


# Test Tone Selection

class TestToneSelection:
    """Test tone selection logic."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_select_tone_with_preferred_tone(self, manager):
        """Test tone selection with valid preferred tone."""
        result = manager.select_tone(
            content_type="email",
            channel="email",
            preferred_tone=AdvancedTone.ENCOURAGING
        )
        assert result == AdvancedTone.ENCOURAGING

    def test_select_tone_business_content(self, manager):
        """Test tone selection for business content."""
        result = manager.select_tone(
            content_type="business_announcement",
            channel="email"
        )
        assert result == AdvancedTone.PROFESSIONAL

    def test_select_tone_research_content(self, manager):
        """Test tone selection for research content."""
        result = manager.select_tone(
            content_type="clinical_study",
            channel="web"
        )
        assert result == AdvancedTone.MEDICAL_SCIENTIFIC

    def test_select_tone_wellness_content(self, manager):
        """Test tone selection for wellness content."""
        result = manager.select_tone(
            content_type="breathing_session",
            channel="email"
        )
        assert result == AdvancedTone.ENCOURAGING

    def test_select_tone_fallback(self, manager):
        """Test tone selection fallback."""
        result = manager.select_tone(
            content_type="unknown",
            channel="email"
        )
        assert result == AdvancedTone.ENCOURAGING

    def test_select_tone_with_string_content_type(self, manager):
        """Test tone selection with string content type."""
        result = manager.select_tone(
            content_type="newsletter",
            channel="email"
        )
        assert result in [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING]


# Test Tone Profile Methods

class TestToneProfileMethods:
    """Test tone profile retrieval methods."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_get_tone_profile(self, manager):
        """Test getting tone profile."""
        profile = manager.get_tone_profile(AdvancedTone.PROFESSIONAL)

        assert isinstance(profile, ToneProfile)
        assert profile.tone == AdvancedTone.PROFESSIONAL
        assert len(profile.use_cases) > 0

    def test_get_tone_profile_fallback(self, manager):
        """Test getting profile with invalid tone."""
        # Even invalid tone should return encouraging profile
        profile = manager.get_tone_profile(AdvancedTone.CASUAL)
        assert isinstance(profile, ToneProfile)

    def test_get_tone_modifiers(self, manager):
        """Test getting tone modifiers."""
        modifiers = manager.get_tone_modifiers(AdvancedTone.PROFESSIONAL)

        assert isinstance(modifiers, dict)
        assert "technical_language" in modifiers
        assert modifiers["technical_language"] is True

    def test_get_brand_guidelines(self, manager):
        """Test getting brand guidelines."""
        guidelines = manager.get_brand_guidelines(AdvancedTone.ENCOURAGING)

        assert isinstance(guidelines, dict)
        assert "voice" in guidelines
        assert "language" in guidelines


# Test Validation Methods

class TestValidation:
    """Test tone and content validation."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_validate_tone_for_content_valid(self, manager):
        """Test valid tone for content."""
        result = manager.validate_tone_for_content(
            tone=AdvancedTone.PROFESSIONAL,
            content_type="business",
            channel="email"
        )
        assert result is True

    def test_validate_tone_for_content_invalid_channel(self, manager):
        """Test invalid tone for channel."""
        result = manager.validate_tone_for_content(
            tone=AdvancedTone.PROFESSIONAL,
            content_type="business",
            channel="research_portal"
        )
        assert result is False

    def test_is_tone_valid_for_channel_valid(self, manager):
        """Test tone validity for channel."""
        result = manager._is_tone_valid_for_channel(
            tone=AdvancedTone.ENCOURAGING,
            channel="email"
        )
        assert result is True

    def test_is_tone_valid_for_channel_invalid(self, manager):
        """Test invalid tone for channel."""
        result = manager._is_tone_valid_for_channel(
            tone=AdvancedTone.ENCOURAGING,
            channel="research_portal"
        )
        assert result is False


# Test Brand Consistency

class TestBrandConsistency:
    """Test brand consistency validation."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_apply_brand_consistency_clean_content(self, manager):
        """Test brand consistency with clean content."""
        content = "Our research shows that users benefit from regular practice."
        result = manager.apply_brand_consistency(content, AdvancedTone.PROFESSIONAL)

        assert result["is_consistent"] is True
        assert len(result["violations"]) == 0

    def test_apply_brand_consistency_prohibited_diagnosis(self, manager):
        """Test detection of prohibited medical diagnosis language."""
        content = "This will diagnose and cure your medical condition."
        result = manager.apply_brand_consistency(content, AdvancedTone.MEDICAL_SCIENTIFIC)

        assert result["is_consistent"] is False
        assert len(result["violations"]) > 0

    def test_apply_brand_consistency_prohibited_guarantees(self, manager):
        """Test detection of prohibited guarantees."""
        content = "Guaranteed to cure all your problems with 100% effective results!"
        result = manager.apply_brand_consistency(content, AdvancedTone.ENCOURAGING)

        assert result["is_consistent"] is False
        assert any("prohibited" in v for v in result["violations"])

    def test_apply_brand_consistency_required_elements(self, manager):
        """Test suggestions for required elements."""
        content = "This product is amazing."
        result = manager.apply_brand_consistency(content, AdvancedTone.PROFESSIONAL)

        # Should have suggestions for missing required elements
        assert len(result["suggestions"]) > 0

    def test_check_tone_alignment_professional(self, manager):
        """Test tone alignment for professional content."""
        profile = manager.get_tone_profile(AdvancedTone.PROFESSIONAL)
        content = "Our clinical research and analysis demonstrates significant data-driven improvements."

        alignment = manager._check_tone_alignment(content, profile)

        assert "score" in alignment
        assert alignment["score"] > 0.5

    def test_check_tone_alignment_casual_language(self, manager):
        """Test detection of casual language."""
        profile = manager.get_tone_profile(AdvancedTone.PROFESSIONAL)
        content = "Hey, this is gonna be awesome!"

        alignment = manager._check_tone_alignment(content, profile)

        assert len(alignment["feedback"]) > 0

    def test_contains_prohibited_element_diagnosis(self, manager):
        """Test prohibited diagnosis language detection."""
        content = "we will diagnose your condition"
        result = manager._contains_prohibited_element(content, "medical_diagnosis_language")
        assert result is True

    def test_contains_prohibited_element_clean(self, manager):
        """Test clean content passes."""
        content = "we support your wellness journey"
        result = manager._contains_prohibited_element(content, "medical_diagnosis_language")
        assert result is False

    def test_contains_required_element_user_focus(self, manager):
        """Test required user-centered focus detection."""
        content = "you and your wellness journey"
        result = manager._contains_required_element(content, "user_centered_focus")
        assert result is True

    def test_contains_required_element_missing(self, manager):
        """Test missing required element."""
        content = "the product features"
        result = manager._contains_required_element(content, "user_centered_focus")
        assert result is False


# Test Channel Configuration

class TestChannelConfiguration:
    """Test channel-specific configuration."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_get_channel_config_email(self, manager):
        """Test getting email channel config."""
        config = manager.get_channel_config("email")

        assert config["default_tone"] == AdvancedTone.ENCOURAGING
        assert "content_constraints" in config

    def test_get_channel_config_unknown(self, manager):
        """Test fallback for unknown channel."""
        config = manager.get_channel_config("unknown_channel")

        # Should fallback to email config
        assert "default_tone" in config

    def test_get_channel_default_tone(self, manager):
        """Test getting channel default tone."""
        tone = manager.get_channel_default_tone("web")
        assert tone == AdvancedTone.PROFESSIONAL

    def test_get_channel_fallback_tone(self, manager):
        """Test getting channel fallback tone."""
        tone = manager.get_channel_fallback_tone("email")
        assert tone == AdvancedTone.PROFESSIONAL

    def test_get_tone_weight_for_channel(self, manager):
        """Test getting tone weight for channel."""
        weight = manager.get_tone_weight_for_channel(
            tone=AdvancedTone.ENCOURAGING,
            channel="social"
        )
        assert weight == 0.8

    def test_get_tone_weight_unknown_tone(self, manager):
        """Test weight for unknown tone returns 0."""
        weight = manager.get_tone_weight_for_channel(
            tone=AdvancedTone.CASUAL,
            channel="email"
        )
        assert weight == 0.0


# Test Content Constraints

class TestContentConstraints:
    """Test content constraint validation."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_validate_content_constraints_valid(self, manager):
        """Test validation of valid content."""
        content = "This is a professional message for your team."
        result = manager.validate_content_constraints(content, "web")

        assert result["is_valid"] is True
        assert len(result["violations"]) == 0

    def test_validate_content_constraints_too_many_exclamations(self, manager):
        """Test detection of excessive exclamation marks."""
        content = "Amazing! Great! Awesome! Fantastic!"
        result = manager.validate_content_constraints(content, "web")

        assert result["is_valid"] is False
        assert any("exclamation" in v for v in result["violations"])

    def test_validate_content_constraints_personalization(self, manager):
        """Test personalization requirement."""
        content = "The system provides features."
        result = manager.validate_content_constraints(content, "email")

        # Should have warning about personalization
        assert len(result["warnings"]) > 0

    def test_validate_content_constraints_casual_language(self, manager):
        """Test casual language detection."""
        content = "Hey, this is gonna be super awesome!"
        result = manager.validate_content_constraints(content, "web")

        # Web doesn't allow casual language
        assert len(result["warnings"]) > 0

    def test_validate_content_constraints_citations_required(self, manager):
        """Test citation requirement for research."""
        content = "Our study shows improvement."
        result = manager.validate_content_constraints(content, "research_portal")

        assert result["is_valid"] is False
        assert any("citation" in v for v in result["violations"])

    def test_validate_content_constraints_with_citations(self, manager):
        """Test content with proper citations."""
        content = "Research by Smith et al. (DOI: 10.1234) demonstrates improvements."
        result = manager.validate_content_constraints(content, "research_portal")

        assert result["is_valid"] is True


# Test Multi-Tone Content

class TestMultiTone:
    """Test multi-tone content generation."""

    @pytest.fixture
    def manager(self):
        """Create ToneManager instance."""
        return ToneManager()

    def test_generate_multi_tone_content_professional_encouraging(self, manager):
        """Test professional-encouraging blend."""
        result = manager.generate_multi_tone_content(
            base_content="Test content",
            tone_combination="professional_encouraging",
            channel="email"
        )

        assert result["primary_tone"] == "professional"
        assert result["secondary_tone"] == "encouraging"
        assert result["blend_ratio"] == 0.7
        assert result["channel_optimization"] is True

    def test_generate_multi_tone_content_encouraging_medical(self, manager):
        """Test encouraging-medical blend."""
        result = manager.generate_multi_tone_content(
            base_content="Test content",
            tone_combination="encouraging_medical",
            channel="web"
        )

        assert result["primary_tone"] == "encouraging"
        assert result["secondary_tone"] == "medical_scientific"

    def test_generate_multi_tone_content_invalid_combination(self, manager):
        """Test error for invalid combination."""
        with pytest.raises(ValueError):
            manager.generate_multi_tone_content(
                base_content="Test",
                tone_combination="invalid_combination",
                channel="email"
            )

    def test_blend_tone_modifiers(self, manager):
        """Test blending tone modifiers."""
        primary = {"technical_language": True, "sentence_length": "long"}
        secondary = {"technical_language": False, "sentence_length": "short"}

        result = manager._blend_tone_modifiers(primary, secondary, 0.7)

        assert result["technical_language"] is True
        assert "sentence_length" in result

    def test_blend_brand_guidelines(self, manager):
        """Test blending brand guidelines."""
        primary = {"voice": "Professional"}
        secondary = {"voice": "Friendly"}

        result = manager._blend_brand_guidelines(primary, secondary, 0.8)

        assert "voice" in result
        assert isinstance(result["voice"], str)

    def test_get_available_tone_combinations_all(self, manager):
        """Test getting all tone combinations."""
        combinations = manager.get_available_tone_combinations()

        assert len(combinations) == 3
        assert "professional_encouraging" in combinations

    def test_get_available_tone_combinations_filtered(self, manager):
        """Test getting combinations filtered by channel."""
        combinations = manager.get_available_tone_combinations(channel="blog")

        assert "encouraging_medical" in combinations
        assert "professional_medical" in combinations

    def test_recommend_tone_combination_onboarding(self, manager):
        """Test recommendation for onboarding content."""
        recommendation = manager.recommend_tone_combination(
            content_type="user_onboarding",
            channel="email"
        )

        assert recommendation == "professional_encouraging"

    def test_recommend_tone_combination_health_education(self, manager):
        """Test recommendation for health content."""
        recommendation = manager.recommend_tone_combination(
            content_type="health_education",
            channel="web"
        )

        assert recommendation == "encouraging_medical"

    def test_recommend_tone_combination_clinical(self, manager):
        """Test recommendation for clinical content."""
        recommendation = manager.recommend_tone_combination(
            content_type="clinical_guidelines",
            channel="blog"
        )

        assert recommendation == "professional_medical"

    def test_recommend_tone_combination_no_match(self, manager):
        """Test no recommendation for unmatched content."""
        recommendation = manager.recommend_tone_combination(
            content_type="random_content",
            channel="email"
        )

        assert recommendation is None


# Test Singleton

class TestSingleton:
    """Test singleton pattern."""

    def test_get_tone_manager(self):
        """Test getting singleton instance."""
        manager1 = get_tone_manager()
        manager2 = get_tone_manager()

        assert manager1 is manager2
