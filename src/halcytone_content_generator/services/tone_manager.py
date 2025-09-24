"""
Tone Manager Service
Sprint 4: Ecosystem Integration - Advanced tone management for content generation

Manages different tone styles for content across channels while maintaining brand consistency.
Supports Professional, Encouraging, and Medical/Scientific tones with context-aware selection.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

from ..templates.ai_prompts import ToneStyle
from ..schemas.content_types import ContentType

logger = logging.getLogger(__name__)


class AdvancedTone(str, Enum):
    """Advanced tone options for Sprint 4 ecosystem integration"""
    PROFESSIONAL = "professional"
    ENCOURAGING = "encouraging"
    MEDICAL_SCIENTIFIC = "medical_scientific"
    # Keep compatibility with existing tones
    CASUAL = "casual"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"


@dataclass
class ToneProfile:
    """Profile defining tone characteristics and application contexts"""
    tone: AdvancedTone
    description: str
    use_cases: List[str]
    channels: List[str]
    brand_guidelines: Dict[str, str]
    content_modifiers: Dict[str, Any]


class ToneManager:
    """
    Advanced tone management system for content generation
    Handles tone selection, validation, and application across different channels
    """

    def __init__(self):
        self.tone_profiles = self._initialize_tone_profiles()
        self.channel_tone_mapping = self._initialize_channel_mapping()
        self.brand_consistency_rules = self._initialize_brand_rules()
        self.per_channel_config = self._initialize_per_channel_config()
        self.tone_combinations = self._initialize_tone_combinations()

    def _initialize_tone_profiles(self) -> Dict[AdvancedTone, ToneProfile]:
        """Initialize comprehensive tone profiles for different use cases"""
        return {
            AdvancedTone.PROFESSIONAL: ToneProfile(
                tone=AdvancedTone.PROFESSIONAL,
                description="Business-focused, formal, and authoritative tone for B2B content",
                use_cases=[
                    "Business announcements",
                    "Platform updates",
                    "Enterprise communications",
                    "Partnership announcements",
                    "Technical documentation",
                    "Investor relations"
                ],
                channels=["email", "web", "linkedin", "blog"],
                brand_guidelines={
                    "voice": "Authoritative yet approachable",
                    "language": "Clear, concise, and industry-appropriate",
                    "formality": "Professional with minimal colloquialisms",
                    "expertise": "Demonstrate deep knowledge and credibility"
                },
                content_modifiers={
                    "sentence_length": "medium_to_long",
                    "technical_language": True,
                    "call_to_action": "direct_and_clear",
                    "social_proof": "industry_credentials",
                    "urgency_level": "measured"
                }
            ),

            AdvancedTone.ENCOURAGING: ToneProfile(
                tone=AdvancedTone.ENCOURAGING,
                description="Supportive, motivational tone focused on user engagement and wellness",
                use_cases=[
                    "User onboarding",
                    "Progress celebrations",
                    "Wellness tips",
                    "Community building",
                    "Achievement recognition",
                    "Motivational content"
                ],
                channels=["email", "social", "app_notifications", "web"],
                brand_guidelines={
                    "voice": "Warm, supportive, and empowering",
                    "language": "Positive, inclusive, and accessible",
                    "formality": "Friendly yet respectful",
                    "expertise": "Caring guidance with expertise"
                },
                content_modifiers={
                    "sentence_length": "short_to_medium",
                    "technical_language": False,
                    "call_to_action": "encouraging_and_supportive",
                    "social_proof": "community_stories",
                    "urgency_level": "gentle"
                }
            ),

            AdvancedTone.MEDICAL_SCIENTIFIC: ToneProfile(
                tone=AdvancedTone.MEDICAL_SCIENTIFIC,
                description="Evidence-based, clinical tone for research and medical content",
                use_cases=[
                    "Research findings",
                    "Clinical studies",
                    "Health education",
                    "Scientific publications",
                    "Medical disclaimers",
                    "Evidence-based recommendations"
                ],
                channels=["web", "email", "research_portal", "blog"],
                brand_guidelines={
                    "voice": "Objective, precise, and evidence-based",
                    "language": "Medical terminology with clear explanations",
                    "formality": "Highly professional and clinical",
                    "expertise": "Demonstrate scientific rigor and accuracy"
                },
                content_modifiers={
                    "sentence_length": "long_and_detailed",
                    "technical_language": True,
                    "call_to_action": "informational_and_cautious",
                    "social_proof": "scientific_citations",
                    "urgency_level": "factual"
                }
            )
        }

    def _initialize_channel_mapping(self) -> Dict[str, List[AdvancedTone]]:
        """Map channels to their most appropriate tone options with priority ordering"""
        return {
            "email": [AdvancedTone.ENCOURAGING, AdvancedTone.PROFESSIONAL, AdvancedTone.MEDICAL_SCIENTIFIC],
            "web": [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC],
            "blog": [AdvancedTone.PROFESSIONAL, AdvancedTone.MEDICAL_SCIENTIFIC, AdvancedTone.ENCOURAGING],
            "social": [AdvancedTone.ENCOURAGING, AdvancedTone.PROFESSIONAL],
            "linkedin": [AdvancedTone.PROFESSIONAL],
            "twitter": [AdvancedTone.ENCOURAGING, AdvancedTone.PROFESSIONAL],
            "facebook": [AdvancedTone.ENCOURAGING],
            "instagram": [AdvancedTone.ENCOURAGING],
            "app_notifications": [AdvancedTone.ENCOURAGING],
            "push_notifications": [AdvancedTone.ENCOURAGING],
            "research_portal": [AdvancedTone.MEDICAL_SCIENTIFIC],
            "clinical_portal": [AdvancedTone.MEDICAL_SCIENTIFIC],
            "newsletter": [AdvancedTone.ENCOURAGING, AdvancedTone.PROFESSIONAL],
            "announcement": [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING],
            "press_release": [AdvancedTone.PROFESSIONAL],
            "documentation": [AdvancedTone.PROFESSIONAL, AdvancedTone.MEDICAL_SCIENTIFIC]
        }

    def _initialize_brand_rules(self) -> Dict[str, Any]:
        """Initialize brand consistency rules across all tones"""
        return {
            "brand_voice_elements": {
                "empathy": "Always maintain compassion for user wellness journey",
                "expertise": "Demonstrate deep understanding of breathing and wellness",
                "innovation": "Showcase cutting-edge approach to wellness technology",
                "accessibility": "Make wellness accessible to all backgrounds and levels"
            },
            "prohibited_elements": [
                "medical_diagnosis_language",
                "treatment_guarantees",
                "unrealistic_promises",
                "exclusive_or_elitist_language"
            ],
            "required_elements": [
                "user_centered_focus",
                "evidence_based_claims",
                "inclusive_language",
                "clear_next_steps"
            ]
        }

    def select_tone(
        self,
        content_type: Union[ContentType, str],
        channel: str,
        context: Optional[Dict[str, Any]] = None,
        preferred_tone: Optional[AdvancedTone] = None
    ) -> AdvancedTone:
        """
        Select the most appropriate tone based on content type, channel, and context

        Args:
            content_type: Type of content being generated
            channel: Target channel for content
            context: Additional context for tone selection
            preferred_tone: User-specified tone preference

        Returns:
            Selected tone for content generation
        """
        context = context or {}

        # Honor user preference if valid for channel
        if preferred_tone and self._is_tone_valid_for_channel(preferred_tone, channel):
            logger.info(f"Using preferred tone {preferred_tone.value} for {channel}")
            return preferred_tone

        # Get available tones for channel
        available_tones = self.channel_tone_mapping.get(channel, list(AdvancedTone))

        # Context-based selection logic
        if isinstance(content_type, str):
            content_type_str = content_type.lower()
        else:
            content_type_str = content_type.value.lower() if hasattr(content_type, 'value') else str(content_type).lower()

        # Business/Platform content -> Professional
        if any(keyword in content_type_str for keyword in ["business", "platform", "enterprise", "announcement"]):
            if AdvancedTone.PROFESSIONAL in available_tones:
                return AdvancedTone.PROFESSIONAL

        # Research/Health content -> Medical/Scientific
        if any(keyword in content_type_str for keyword in ["research", "study", "clinical", "health", "medical"]):
            if AdvancedTone.MEDICAL_SCIENTIFIC in available_tones:
                return AdvancedTone.MEDICAL_SCIENTIFIC

        # User engagement content -> Encouraging
        if any(keyword in content_type_str for keyword in ["session", "progress", "achievement", "wellness", "breathing"]):
            if AdvancedTone.ENCOURAGING in available_tones:
                return AdvancedTone.ENCOURAGING

        # Default fallback based on channel priority
        if AdvancedTone.ENCOURAGING in available_tones:
            return AdvancedTone.ENCOURAGING
        elif AdvancedTone.PROFESSIONAL in available_tones:
            return AdvancedTone.PROFESSIONAL
        else:
            return available_tones[0] if available_tones else AdvancedTone.ENCOURAGING

    def get_tone_profile(self, tone: AdvancedTone) -> ToneProfile:
        """Get complete profile for specified tone"""
        return self.tone_profiles.get(tone, self.tone_profiles[AdvancedTone.ENCOURAGING])

    def get_tone_modifiers(self, tone: AdvancedTone) -> Dict[str, Any]:
        """Get tone-specific content modifiers"""
        profile = self.get_tone_profile(tone)
        return profile.content_modifiers

    def validate_tone_for_content(
        self,
        tone: AdvancedTone,
        content_type: Union[ContentType, str],
        channel: str
    ) -> bool:
        """
        Validate if tone is appropriate for given content type and channel

        Returns:
            True if tone is appropriate, False otherwise
        """
        # Check channel compatibility
        if not self._is_tone_valid_for_channel(tone, channel):
            return False

        # Check content type compatibility
        profile = self.get_tone_profile(tone)
        content_str = str(content_type).lower()

        # Check if content type aligns with tone use cases
        use_case_match = any(
            use_case_keyword in content_str
            for use_case in profile.use_cases
            for use_case_keyword in use_case.lower().split()
        )

        return use_case_match

    def _is_tone_valid_for_channel(self, tone: AdvancedTone, channel: str) -> bool:
        """Check if tone is valid for specified channel"""
        available_tones = self.channel_tone_mapping.get(channel, [])
        return tone in available_tones

    def get_brand_guidelines(self, tone: AdvancedTone) -> Dict[str, str]:
        """Get brand guidelines for specified tone"""
        profile = self.get_tone_profile(tone)
        return profile.brand_guidelines

    def apply_brand_consistency(self, content: str, tone: AdvancedTone) -> Dict[str, Any]:
        """
        Validate content against brand consistency rules for specified tone

        Returns:
            Dict with validation results and suggestions
        """
        profile = self.get_tone_profile(tone)
        brand_rules = self.brand_consistency_rules

        validation_results = {
            "is_consistent": True,
            "violations": [],
            "suggestions": [],
            "tone_alignment": self._check_tone_alignment(content, profile)
        }

        # Check for prohibited elements
        content_lower = content.lower()
        for prohibited in brand_rules["prohibited_elements"]:
            if self._contains_prohibited_element(content_lower, prohibited):
                validation_results["is_consistent"] = False
                validation_results["violations"].append(f"Contains prohibited element: {prohibited}")

        # Check for required elements
        for required in brand_rules["required_elements"]:
            if not self._contains_required_element(content_lower, required):
                validation_results["suggestions"].append(f"Consider adding: {required}")

        return validation_results

    def _check_tone_alignment(self, content: str, profile: ToneProfile) -> Dict[str, Any]:
        """Check if content aligns with tone profile characteristics"""
        # Basic tone alignment checks
        guidelines = profile.brand_guidelines
        modifiers = profile.content_modifiers

        alignment_score = 0.5  # Base score
        feedback = []

        # Check formality level
        if guidelines["formality"] == "Professional with minimal colloquialisms":
            if any(casual_word in content.lower() for casual_word in ["gonna", "wanna", "hey", "awesome"]):
                feedback.append("Consider more professional language")
            else:
                alignment_score += 0.1

        # Check technical language usage
        if modifiers.get("technical_language"):
            technical_terms = ["clinical", "evidence", "research", "study", "data", "analysis"]
            if any(term in content.lower() for term in technical_terms):
                alignment_score += 0.2

        return {
            "score": min(alignment_score, 1.0),
            "feedback": feedback
        }

    def _contains_prohibited_element(self, content: str, prohibited_type: str) -> bool:
        """Check if content contains prohibited elements"""
        prohibited_patterns = {
            "medical_diagnosis_language": ["diagnose", "cure", "treat", "medical condition"],
            "treatment_guarantees": ["guaranteed", "will cure", "100% effective"],
            "unrealistic_promises": ["miracle", "instant results", "overnight"],
            "exclusive_or_elitist_language": ["only for", "exclusive to", "elite members"]
        }

        patterns = prohibited_patterns.get(prohibited_type, [])
        return any(pattern in content for pattern in patterns)

    def _contains_required_element(self, content: str, required_type: str) -> bool:
        """Check if content contains required elements"""
        required_patterns = {
            "user_centered_focus": ["you", "your", "user", "member"],
            "evidence_based_claims": ["research", "study", "evidence", "data"],
            "inclusive_language": ["everyone", "all", "inclusive", "accessible"],
            "clear_next_steps": ["next", "step", "action", "get started", "learn more"]
        }

        patterns = required_patterns.get(required_type, [])
        return any(pattern in content for pattern in patterns)


    def _initialize_per_channel_config(self) -> Dict[str, Dict[str, Any]]:
        """Initialize per-channel configuration with tone preferences and constraints"""
        return {
            "email": {
                "default_tone": AdvancedTone.ENCOURAGING,
                "fallback_tone": AdvancedTone.PROFESSIONAL,
                "tone_weights": {
                    AdvancedTone.ENCOURAGING: 0.6,
                    AdvancedTone.PROFESSIONAL: 0.3,
                    AdvancedTone.MEDICAL_SCIENTIFIC: 0.1
                },
                "content_constraints": {
                    "max_emoji_count": 3,
                    "max_exclamation_marks": 2,
                    "require_personalization": True,
                    "allow_casual_language": True
                }
            },
            "web": {
                "default_tone": AdvancedTone.PROFESSIONAL,
                "fallback_tone": AdvancedTone.ENCOURAGING,
                "tone_weights": {
                    AdvancedTone.PROFESSIONAL: 0.5,
                    AdvancedTone.ENCOURAGING: 0.3,
                    AdvancedTone.MEDICAL_SCIENTIFIC: 0.2
                },
                "content_constraints": {
                    "max_emoji_count": 0,
                    "max_exclamation_marks": 1,
                    "require_personalization": False,
                    "allow_casual_language": False
                }
            },
            "blog": {
                "default_tone": AdvancedTone.PROFESSIONAL,
                "fallback_tone": AdvancedTone.MEDICAL_SCIENTIFIC,
                "tone_weights": {
                    AdvancedTone.PROFESSIONAL: 0.6,
                    AdvancedTone.MEDICAL_SCIENTIFIC: 0.3,
                    AdvancedTone.ENCOURAGING: 0.1
                },
                "content_constraints": {
                    "max_emoji_count": 0,
                    "max_exclamation_marks": 0,
                    "require_personalization": False,
                    "allow_casual_language": False
                }
            },
            "social": {
                "default_tone": AdvancedTone.ENCOURAGING,
                "fallback_tone": AdvancedTone.PROFESSIONAL,
                "tone_weights": {
                    AdvancedTone.ENCOURAGING: 0.8,
                    AdvancedTone.PROFESSIONAL: 0.2
                },
                "content_constraints": {
                    "max_emoji_count": 5,
                    "max_exclamation_marks": 3,
                    "require_personalization": True,
                    "allow_casual_language": True
                }
            },
            "research_portal": {
                "default_tone": AdvancedTone.MEDICAL_SCIENTIFIC,
                "fallback_tone": AdvancedTone.PROFESSIONAL,
                "tone_weights": {
                    AdvancedTone.MEDICAL_SCIENTIFIC: 1.0
                },
                "content_constraints": {
                    "max_emoji_count": 0,
                    "max_exclamation_marks": 0,
                    "require_personalization": False,
                    "allow_casual_language": False,
                    "require_citations": True,
                    "require_disclaimers": True
                }
            }
        }

    def _initialize_tone_combinations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tone combination rules for multi-tone content generation"""
        return {
            "professional_encouraging": {
                "primary_tone": AdvancedTone.PROFESSIONAL,
                "secondary_tone": AdvancedTone.ENCOURAGING,
                "blend_ratio": 0.7,  # 70% professional, 30% encouraging
                "use_cases": ["customer_onboarding", "feature_announcements", "success_stories"],
                "channels": ["email", "web", "newsletter"]
            },
            "encouraging_medical": {
                "primary_tone": AdvancedTone.ENCOURAGING,
                "secondary_tone": AdvancedTone.MEDICAL_SCIENTIFIC,
                "blend_ratio": 0.6,  # 60% encouraging, 40% medical
                "use_cases": ["health_education", "wellness_tips", "research_summaries"],
                "channels": ["email", "web", "blog"]
            },
            "professional_medical": {
                "primary_tone": AdvancedTone.PROFESSIONAL,
                "secondary_tone": AdvancedTone.MEDICAL_SCIENTIFIC,
                "blend_ratio": 0.5,  # 50/50 blend
                "use_cases": ["clinical_guidelines", "industry_reports", "regulatory_updates"],
                "channels": ["web", "blog", "documentation"]
            }
        }

    def get_channel_config(self, channel: str) -> Dict[str, Any]:
        """Get complete configuration for a specific channel"""
        return self.per_channel_config.get(channel, self.per_channel_config["email"])

    def get_channel_default_tone(self, channel: str) -> AdvancedTone:
        """Get the default tone for a specific channel"""
        config = self.get_channel_config(channel)
        return config.get("default_tone", AdvancedTone.ENCOURAGING)

    def get_channel_fallback_tone(self, channel: str) -> AdvancedTone:
        """Get the fallback tone for a specific channel"""
        config = self.get_channel_config(channel)
        return config.get("fallback_tone", AdvancedTone.PROFESSIONAL)

    def get_tone_weight_for_channel(self, tone: AdvancedTone, channel: str) -> float:
        """Get the weight/priority of a tone for a specific channel"""
        config = self.get_channel_config(channel)
        weights = config.get("tone_weights", {})
        return weights.get(tone, 0.0)

    def validate_content_constraints(self, content: str, channel: str) -> Dict[str, Any]:
        """Validate content against channel-specific constraints"""
        config = self.get_channel_config(channel)
        constraints = config.get("content_constraints", {})

        validation_result = {
            "is_valid": True,
            "violations": [],
            "warnings": [],
            "metrics": {}
        }

        # Count emojis
        emoji_count = len([char for char in content if char.encode('utf-8') != char.encode('ascii', 'ignore')])
        validation_result["metrics"]["emoji_count"] = emoji_count

        max_emojis = constraints.get("max_emoji_count", 999)
        if emoji_count > max_emojis:
            validation_result["is_valid"] = False
            validation_result["violations"].append(f"Too many emojis: {emoji_count} > {max_emojis}")

        # Count exclamation marks
        exclamation_count = content.count("!")
        validation_result["metrics"]["exclamation_count"] = exclamation_count

        max_exclamations = constraints.get("max_exclamation_marks", 999)
        if exclamation_count > max_exclamations:
            validation_result["is_valid"] = False
            validation_result["violations"].append(f"Too many exclamations: {exclamation_count} > {max_exclamations}")

        # Check personalization requirement
        if constraints.get("require_personalization", False):
            personal_indicators = ["you", "your", "user", "member", "participant"]
            has_personalization = any(indicator in content.lower() for indicator in personal_indicators)
            if not has_personalization:
                validation_result["warnings"].append("Content may benefit from more personalization")

        # Check casual language allowance
        if not constraints.get("allow_casual_language", True):
            casual_words = ["gonna", "wanna", "hey", "awesome", "cool", "super", "amazing"]
            casual_found = [word for word in casual_words if word in content.lower()]
            if casual_found:
                validation_result["warnings"].append(f"Casual language detected: {', '.join(casual_found)}")

        # Check citations for research content
        if constraints.get("require_citations", False):
            citation_patterns = ["et al", "doi:", "pmid:", "www.", "http"]
            has_citations = any(pattern in content.lower() for pattern in citation_patterns)
            if not has_citations:
                validation_result["is_valid"] = False
                validation_result["violations"].append("Research content requires citations or references")

        return validation_result

    def generate_multi_tone_content(
        self,
        base_content: str,
        tone_combination: str,
        channel: str
    ) -> Dict[str, Any]:
        """
        Generate content using a combination of tones

        Args:
            base_content: Original content to adapt
            tone_combination: Key from tone_combinations (e.g., "professional_encouraging")
            channel: Target channel

        Returns:
            Dict with blended content and metadata
        """
        if tone_combination not in self.tone_combinations:
            raise ValueError(f"Unknown tone combination: {tone_combination}")

        combo_config = self.tone_combinations[tone_combination]
        primary_tone = combo_config["primary_tone"]
        secondary_tone = combo_config["secondary_tone"]
        blend_ratio = combo_config["blend_ratio"]

        # Validate channel compatibility
        if channel not in combo_config["channels"]:
            logger.warning(f"Tone combination {tone_combination} not optimized for channel {channel}")

        # Get tone profiles
        primary_profile = self.get_tone_profile(primary_tone)
        secondary_profile = self.get_tone_profile(secondary_tone)

        # Blend tone characteristics
        blended_modifiers = self._blend_tone_modifiers(
            primary_profile.content_modifiers,
            secondary_profile.content_modifiers,
            blend_ratio
        )

        blended_guidelines = self._blend_brand_guidelines(
            primary_profile.brand_guidelines,
            secondary_profile.brand_guidelines,
            blend_ratio
        )

        return {
            "primary_tone": primary_tone.value,
            "secondary_tone": secondary_tone.value,
            "blend_ratio": blend_ratio,
            "blended_modifiers": blended_modifiers,
            "blended_guidelines": blended_guidelines,
            "channel_optimization": channel in combo_config["channels"],
            "recommended_use_cases": combo_config["use_cases"]
        }

    def _blend_tone_modifiers(
        self,
        primary_modifiers: Dict[str, Any],
        secondary_modifiers: Dict[str, Any],
        blend_ratio: float
    ) -> Dict[str, Any]:
        """Blend content modifiers from two tones"""
        blended = {}

        # Handle boolean values
        for key in primary_modifiers:
            if isinstance(primary_modifiers[key], bool):
                primary_weight = blend_ratio
                secondary_weight = 1 - blend_ratio
                # Use primary tone's boolean if ratio > 0.5, otherwise secondary
                blended[key] = primary_modifiers[key] if primary_weight > 0.5 else secondary_modifiers.get(key, primary_modifiers[key])
            else:
                # For non-boolean values, prefer primary tone
                blended[key] = primary_modifiers[key]

        return blended

    def _blend_brand_guidelines(
        self,
        primary_guidelines: Dict[str, str],
        secondary_guidelines: Dict[str, str],
        blend_ratio: float
    ) -> Dict[str, str]:
        """Blend brand guidelines from two tones"""
        blended = {}

        for key in primary_guidelines:
            primary_text = primary_guidelines[key]
            secondary_text = secondary_guidelines.get(key, primary_text)

            # Create blended description
            if blend_ratio > 0.7:
                blended[key] = f"{primary_text} with elements of {secondary_text.lower()}"
            elif blend_ratio > 0.3:
                blended[key] = f"Balanced approach: {primary_text.lower()} combined with {secondary_text.lower()}"
            else:
                blended[key] = f"{secondary_text} with subtle {primary_text.lower()} undertones"

        return blended

    def get_available_tone_combinations(self, channel: str = None) -> List[str]:
        """Get list of available tone combinations, optionally filtered by channel"""
        if channel is None:
            return list(self.tone_combinations.keys())

        return [
            combo_key for combo_key, combo_config in self.tone_combinations.items()
            if channel in combo_config["channels"]
        ]

    def recommend_tone_combination(
        self,
        content_type: str,
        channel: str,
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """Recommend the best tone combination for given content type and channel"""
        context = context or {}

        # Analyze content type for combination hints
        content_lower = content_type.lower()

        # Business + user-friendly content
        if any(keyword in content_lower for keyword in ["onboarding", "announcement", "feature"]):
            if "professional_encouraging" in self.get_available_tone_combinations(channel):
                return "professional_encouraging"

        # Health education content
        if any(keyword in content_lower for keyword in ["health", "wellness", "education", "tips"]):
            if "encouraging_medical" in self.get_available_tone_combinations(channel):
                return "encouraging_medical"

        # Clinical/regulatory content
        if any(keyword in content_lower for keyword in ["clinical", "regulatory", "guidelines", "industry"]):
            if "professional_medical" in self.get_available_tone_combinations(channel):
                return "professional_medical"

        return None

# Global tone manager instance
tone_manager = ToneManager()

def get_tone_manager() -> ToneManager:
    """Get the global tone manager instance"""
    return tone_manager