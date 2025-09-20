"""
Content Quality Scoring Service
Sprint 8 - AI Enhancement & Personalization

This module provides comprehensive content quality assessment using AI analysis,
readability metrics, engagement factors, and quality thresholds.
"""
import re
import math
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging

from ..config import get_settings
from ..services.ai_content_enhancer import AIContentEnhancer, ContentType
from ..templates.ai_prompts import get_prompt_templates

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality level classifications"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class ScoreCategory(Enum):
    """Scoring categories"""
    READABILITY = "readability"
    ENGAGEMENT = "engagement"
    SEO_OPTIMIZATION = "seo_optimization"
    BRAND_ALIGNMENT = "brand_alignment"
    STRUCTURE = "structure"
    CLARITY = "clarity"
    EMOTIONAL_IMPACT = "emotional_impact"
    CALL_TO_ACTION = "call_to_action"


@dataclass
class ReadabilityMetrics:
    """Readability analysis metrics"""
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog_index: float
    automated_readability_index: float
    coleman_liau_index: float
    average_sentence_length: float
    average_syllables_per_word: float
    complex_words_percentage: float
    passive_voice_percentage: float

    @property
    def overall_readability_score(self) -> float:
        """Calculate overall readability score (0-100)"""
        # Normalize different metrics to 0-100 scale
        normalized_scores = []

        # Flesch Reading Ease (already 0-100)
        normalized_scores.append(max(0, min(100, self.flesch_reading_ease)))

        # Flesch-Kincaid Grade (convert to 0-100, target grade 8)
        fk_score = max(0, 100 - (self.flesch_kincaid_grade - 8) * 10)
        normalized_scores.append(max(0, min(100, fk_score)))

        # Gunning Fog (convert to 0-100, target index 12)
        fog_score = max(0, 100 - (self.gunning_fog_index - 12) * 8)
        normalized_scores.append(max(0, min(100, fog_score)))

        # Penalize passive voice and complex words
        passive_penalty = self.passive_voice_percentage * 2
        complex_penalty = self.complex_words_percentage

        base_score = statistics.mean(normalized_scores)
        return max(0, min(100, base_score - passive_penalty - complex_penalty))


@dataclass
class EngagementMetrics:
    """Engagement analysis metrics"""
    emotional_words_count: int
    power_words_count: int
    question_count: int
    exclamation_count: int
    personal_pronouns_count: int
    sensory_words_count: int
    urgency_indicators_count: int
    social_proof_indicators: int
    storytelling_elements: int
    curiosity_triggers: int

    @property
    def engagement_score(self) -> float:
        """Calculate engagement score (0-100)"""
        # Weight different engagement factors
        weights = {
            'emotional_words': 0.15,
            'power_words': 0.20,
            'questions': 0.10,
            'personal_pronouns': 0.10,
            'sensory_words': 0.10,
            'urgency': 0.10,
            'social_proof': 0.10,
            'storytelling': 0.10,
            'curiosity': 0.05
        }

        # Normalize counts to scores (0-10 scale)
        factors = {
            'emotional_words': min(10, self.emotional_words_count / 2),
            'power_words': min(10, self.power_words_count / 3),
            'questions': min(10, self.question_count * 2),
            'personal_pronouns': min(10, self.personal_pronouns_count / 3),
            'sensory_words': min(10, self.sensory_words_count / 2),
            'urgency': min(10, self.urgency_indicators_count * 2),
            'social_proof': min(10, self.social_proof_indicators * 2),
            'storytelling': min(10, self.storytelling_elements * 2),
            'curiosity': min(10, self.curiosity_triggers * 2)
        }

        # Calculate weighted score
        weighted_score = sum(factors[key] * weights[key] for key in factors)
        return min(100, weighted_score * 10)


@dataclass
class SEOMetrics:
    """SEO optimization metrics"""
    keyword_density: Dict[str, float]
    title_optimization_score: float
    meta_description_score: float
    header_structure_score: float
    internal_link_opportunities: int
    external_link_quality: float
    image_alt_optimization: float
    content_length_score: float
    semantic_keywords_count: int

    @property
    def seo_score(self) -> float:
        """Calculate SEO score (0-100)"""
        scores = [
            self.title_optimization_score,
            self.meta_description_score,
            self.header_structure_score,
            min(100, self.internal_link_opportunities * 10),
            self.external_link_quality,
            self.image_alt_optimization,
            self.content_length_score,
            min(100, self.semantic_keywords_count * 5)
        ]

        # Average of all SEO factors
        return statistics.mean([s for s in scores if s is not None])


@dataclass
class QualityScore:
    """Comprehensive quality assessment"""
    overall_score: float
    readability_metrics: ReadabilityMetrics
    engagement_metrics: EngagementMetrics
    seo_metrics: SEOMetrics
    brand_alignment_score: float
    structure_score: float
    clarity_score: float
    ai_assessment_score: float
    quality_level: QualityLevel
    improvement_suggestions: List[str] = field(default_factory=list)
    detailed_feedback: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def category_scores(self) -> Dict[str, float]:
        """Get scores by category"""
        return {
            ScoreCategory.READABILITY.value: self.readability_metrics.overall_readability_score,
            ScoreCategory.ENGAGEMENT.value: self.engagement_metrics.engagement_score,
            ScoreCategory.SEO_OPTIMIZATION.value: self.seo_metrics.seo_score,
            ScoreCategory.BRAND_ALIGNMENT.value: self.brand_alignment_score,
            ScoreCategory.STRUCTURE.value: self.structure_score,
            ScoreCategory.CLARITY.value: self.clarity_score,
            ScoreCategory.EMOTIONAL_IMPACT.value: self.engagement_metrics.engagement_score,
            ScoreCategory.CALL_TO_ACTION.value: self._calculate_cta_score()
        }

    def _calculate_cta_score(self) -> float:
        """Calculate call-to-action effectiveness score"""
        # Based on urgency indicators and power words in engagement metrics
        cta_elements = (
            self.engagement_metrics.urgency_indicators_count * 20 +
            self.engagement_metrics.power_words_count * 10
        )
        return min(100, cta_elements)


class QualityThresholds:
    """Quality thresholds and standards"""

    def __init__(self):
        self.thresholds = self._initialize_thresholds()
        self.content_type_adjustments = self._initialize_content_type_adjustments()

    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize quality thresholds for different levels"""
        return {
            QualityLevel.EXCELLENT.value: {
                "overall_score": 90.0,
                "readability": 85.0,
                "engagement": 80.0,
                "seo": 85.0,
                "brand_alignment": 90.0,
                "structure": 85.0,
                "clarity": 90.0
            },
            QualityLevel.GOOD.value: {
                "overall_score": 75.0,
                "readability": 70.0,
                "engagement": 65.0,
                "seo": 70.0,
                "brand_alignment": 75.0,
                "structure": 70.0,
                "clarity": 75.0
            },
            QualityLevel.FAIR.value: {
                "overall_score": 60.0,
                "readability": 55.0,
                "engagement": 50.0,
                "seo": 55.0,
                "brand_alignment": 60.0,
                "structure": 55.0,
                "clarity": 60.0
            },
            QualityLevel.POOR.value: {
                "overall_score": 40.0,
                "readability": 40.0,
                "engagement": 35.0,
                "seo": 40.0,
                "brand_alignment": 40.0,
                "structure": 40.0,
                "clarity": 40.0
            },
            QualityLevel.CRITICAL.value: {
                "overall_score": 0.0,
                "readability": 0.0,
                "engagement": 0.0,
                "seo": 0.0,
                "brand_alignment": 0.0,
                "structure": 0.0,
                "clarity": 0.0
            }
        }

    def _initialize_content_type_adjustments(self) -> Dict[ContentType, Dict[str, float]]:
        """Content type specific threshold adjustments"""
        return {
            ContentType.EMAIL: {
                "engagement": 1.1,  # 10% higher engagement expected
                "readability": 1.0,
                "structure": 0.9    # Less formal structure OK
            },
            ContentType.WEB: {
                "seo": 1.2,         # 20% higher SEO expectation
                "structure": 1.1,   # Well-structured content expected
                "readability": 1.0
            },
            ContentType.SOCIAL_TWITTER: {
                "engagement": 1.3,  # Very high engagement expected
                "clarity": 1.2,     # Must be very clear in short form
                "structure": 0.7    # Less structure needed
            },
            ContentType.SOCIAL_LINKEDIN: {
                "brand_alignment": 1.1,  # Professional alignment important
                "engagement": 1.0,
                "structure": 1.0
            }
        }

    def get_threshold(self, quality_level: QualityLevel, metric: str,
                     content_type: Optional[ContentType] = None) -> float:
        """Get threshold for specific quality level and metric"""
        base_threshold = self.thresholds[quality_level.value].get(metric, 0.0)

        if content_type and content_type in self.content_type_adjustments:
            adjustment = self.content_type_adjustments[content_type].get(metric, 1.0)
            return base_threshold * adjustment

        return base_threshold

    def classify_quality(self, score: float, metric: str = "overall_score") -> QualityLevel:
        """Classify quality level based on score"""
        for level in [QualityLevel.EXCELLENT, QualityLevel.GOOD,
                     QualityLevel.FAIR, QualityLevel.POOR]:
            if score >= self.get_threshold(level, metric):
                return level
        return QualityLevel.CRITICAL


class ContentQualityScorer:
    """Comprehensive content quality scoring service"""

    def __init__(self):
        self.settings = get_settings()
        self.ai_enhancer = None  # Lazy initialization
        self.prompt_templates = get_prompt_templates()
        self.thresholds = QualityThresholds()

        # Word lists for analysis
        self.emotional_words = self._load_emotional_words()
        self.power_words = self._load_power_words()
        self.sensory_words = self._load_sensory_words()
        self.urgency_indicators = self._load_urgency_indicators()
        self.complex_words = self._load_complex_words()

    @property
    def ai_enhancer_instance(self):
        """Lazy initialization of AI enhancer"""
        if self.ai_enhancer is None:
            from .ai_content_enhancer import get_ai_enhancer
            self.ai_enhancer = get_ai_enhancer()
        return self.ai_enhancer

    def _load_emotional_words(self) -> List[str]:
        """Load emotional words for engagement analysis"""
        return [
            "amazing", "incredible", "fantastic", "wonderful", "brilliant",
            "excited", "thrilled", "delighted", "overjoyed", "passionate",
            "love", "adore", "cherish", "treasure", "devastating", "heartbreaking",
            "shocking", "stunning", "breathtaking", "magnificent", "extraordinary",
            "revolutionary", "groundbreaking", "inspiring", "motivating", "empowering",
            "transformative", "life-changing", "breakthrough", "miracle", "magic"
        ]

    def _load_power_words(self) -> List[str]:
        """Load power words for engagement analysis"""
        return [
            "you", "because", "instantly", "new", "proven", "results", "easy",
            "guaranteed", "discover", "secret", "exclusive", "limited", "free",
            "save", "win", "gain", "boost", "increase", "improve", "enhance",
            "transform", "unlock", "reveal", "breakthrough", "ultimate", "complete",
            "perfect", "best", "top", "leading", "expert", "professional", "advanced"
        ]

    def _load_sensory_words(self) -> List[str]:
        """Load sensory words for engagement analysis"""
        return [
            "see", "hear", "feel", "touch", "taste", "smell", "bright", "colorful",
            "loud", "quiet", "smooth", "rough", "sweet", "bitter", "warm", "cool",
            "soft", "hard", "fragrant", "vivid", "clear", "crisp", "melodic",
            "whisper", "shout", "glow", "sparkle", "shine", "fresh", "stale"
        ]

    def _load_urgency_indicators(self) -> List[str]:
        """Load urgency indicator words"""
        return [
            "now", "today", "immediately", "urgent", "deadline", "limited time",
            "expires", "hurry", "act fast", "don't wait", "while supplies last",
            "final hours", "last chance", "ending soon", "quick", "instant"
        ]

    def _load_complex_words(self) -> List[str]:
        """Load complex words that may hurt readability"""
        return [
            "accommodate", "acquisition", "advantageous", "approximately", "capabilities",
            "comprehensive", "demonstrate", "development", "environment", "establish",
            "experience", "facilitate", "fundamental", "implementation", "incorporate",
            "infrastructure", "maintenance", "methodology", "opportunity", "optimization",
            "organization", "participate", "performance", "requirement", "significance",
            "substantial", "technology", "transformation", "utilization", "verification"
        ]

    async def score_content(self, content: str, content_type: ContentType,
                           include_ai_analysis: bool = True) -> QualityScore:
        """
        Comprehensive content quality scoring

        Args:
            content: Content to analyze
            content_type: Type of content for context-specific analysis
            include_ai_analysis: Whether to include AI-powered analysis

        Returns:
            Comprehensive quality score with metrics and suggestions
        """
        try:
            # Calculate individual metrics
            readability = self._calculate_readability_metrics(content)
            engagement = self._calculate_engagement_metrics(content)
            seo = self._calculate_seo_metrics(content, content_type)

            # Calculate other scores
            brand_alignment = self._calculate_brand_alignment_score(content)
            structure_score = self._calculate_structure_score(content, content_type)
            clarity_score = self._calculate_clarity_score(content)

            # AI-powered assessment (if enabled and configured)
            ai_score = 0.0
            if include_ai_analysis and self.ai_enhancer_instance.is_configured():
                ai_assessment = await self.ai_enhancer_instance.score_content_quality(
                    content, content_type
                )
                ai_score = ai_assessment.overall_score

            # Calculate overall score with weights
            category_scores = {
                ScoreCategory.READABILITY: readability.overall_readability_score,
                ScoreCategory.ENGAGEMENT: engagement.engagement_score,
                ScoreCategory.SEO_OPTIMIZATION: seo.seo_score,
                ScoreCategory.BRAND_ALIGNMENT: brand_alignment,
                ScoreCategory.STRUCTURE: structure_score,
                ScoreCategory.CLARITY: clarity_score
            }

            # Weight categories based on content type
            weights = self._get_category_weights(content_type)
            overall_score = sum(
                category_scores[category] * weights.get(category, 0.1)
                for category in category_scores
            )

            # Include AI score if available
            if ai_score > 0:
                overall_score = (overall_score * 0.8) + (ai_score * 0.2)

            # Determine quality level
            quality_level = self.thresholds.classify_quality(overall_score)

            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions(
                category_scores, content_type, quality_level
            )

            # Create detailed feedback
            detailed_feedback = self._create_detailed_feedback(
                content, category_scores, readability, engagement, seo
            )

            return QualityScore(
                overall_score=overall_score,
                readability_metrics=readability,
                engagement_metrics=engagement,
                seo_metrics=seo,
                brand_alignment_score=brand_alignment,
                structure_score=structure_score,
                clarity_score=clarity_score,
                ai_assessment_score=ai_score,
                quality_level=quality_level,
                improvement_suggestions=suggestions,
                detailed_feedback=detailed_feedback
            )

        except Exception as e:
            logger.error(f"Content quality scoring failed: {e}")
            # Return minimal score on error
            return self._create_error_score(str(e))

    def _calculate_readability_metrics(self, content: str) -> ReadabilityMetrics:
        """Calculate comprehensive readability metrics"""
        # Clean content for analysis
        sentences = self._split_sentences(content)
        words = self._split_words(content)
        syllables = [self._count_syllables(word) for word in words]

        if not sentences or not words:
            return self._create_default_readability_metrics()

        # Basic metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = sum(syllables) / len(syllables) if syllables else 1.0

        # Complex words (3+ syllables)
        complex_words = [s for s in syllables if s >= 3]
        complex_words_percentage = (len(complex_words) / len(words)) * 100

        # Passive voice detection
        passive_count = self._count_passive_voice(content)
        passive_voice_percentage = (passive_count / len(sentences)) * 100

        # Flesch Reading Ease
        flesch_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_ease = max(0, min(100, flesch_ease))

        # Flesch-Kincaid Grade Level
        fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        fk_grade = max(0, fk_grade)

        # Gunning Fog Index
        fog_index = 0.4 * (avg_sentence_length + complex_words_percentage)

        # Automated Readability Index
        characters = sum(len(word) for word in words)
        ari = 4.71 * (characters / len(words)) + 0.5 * (len(words) / len(sentences)) - 21.43
        ari = max(0, ari)

        # Coleman-Liau Index
        l_value = (characters / len(words)) * 100
        s_value = (len(sentences) / len(words)) * 100
        cli = 0.0588 * l_value - 0.296 * s_value - 15.8
        cli = max(0, cli)

        return ReadabilityMetrics(
            flesch_reading_ease=flesch_ease,
            flesch_kincaid_grade=fk_grade,
            gunning_fog_index=fog_index,
            automated_readability_index=ari,
            coleman_liau_index=cli,
            average_sentence_length=avg_sentence_length,
            average_syllables_per_word=avg_syllables_per_word,
            complex_words_percentage=complex_words_percentage,
            passive_voice_percentage=passive_voice_percentage
        )

    def _calculate_engagement_metrics(self, content: str) -> EngagementMetrics:
        """Calculate engagement-related metrics"""
        content_lower = content.lower()

        # Count various engagement factors
        emotional_words = sum(1 for word in self.emotional_words if word in content_lower)
        power_words = sum(1 for word in self.power_words if word in content_lower)
        questions = content.count('?')
        exclamations = content.count('!')

        # Personal pronouns
        pronouns = ['you', 'your', 'yours', 'we', 'our', 'ours', 'i', 'my', 'mine']
        personal_pronouns = sum(len(re.findall(rf'\b{pronoun}\b', content_lower))
                               for pronoun in pronouns)

        # Sensory words
        sensory_words = sum(1 for word in self.sensory_words if word in content_lower)

        # Urgency indicators
        urgency = sum(1 for indicator in self.urgency_indicators if indicator in content_lower)

        # Social proof indicators
        social_proof_terms = ['testimonial', 'review', 'customer', 'user', 'client',
                             'success story', 'case study', 'proven', 'trusted']
        social_proof = sum(1 for term in social_proof_terms if term in content_lower)

        # Storytelling elements
        story_elements = ['once', 'story', 'imagine', 'picture this', 'example',
                         'for instance', 'let me tell you']
        storytelling = sum(1 for element in story_elements if element in content_lower)

        # Curiosity triggers
        curiosity_triggers = ['secret', 'hidden', 'revealed', 'discover', 'unknown',
                             'mystery', 'surprise', 'shocking']
        curiosity = sum(1 for trigger in curiosity_triggers if trigger in content_lower)

        return EngagementMetrics(
            emotional_words_count=emotional_words,
            power_words_count=power_words,
            question_count=questions,
            exclamation_count=exclamations,
            personal_pronouns_count=personal_pronouns,
            sensory_words_count=sensory_words,
            urgency_indicators_count=urgency,
            social_proof_indicators=social_proof,
            storytelling_elements=storytelling,
            curiosity_triggers=curiosity
        )

    def _calculate_seo_metrics(self, content: str, content_type: ContentType) -> SEOMetrics:
        """Calculate SEO optimization metrics"""
        words = self._split_words(content.lower())

        # Basic keyword density (placeholder - would need target keywords)
        keyword_density = self._calculate_keyword_density(words)

        # Title optimization (look for title-like content at beginning)
        title_score = self._score_title_optimization(content)

        # Meta description score (if content suggests meta description)
        meta_score = self._score_meta_description(content)

        # Header structure (look for header patterns)
        header_score = self._score_header_structure(content)

        # Link opportunities
        internal_links = len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content))  # Markdown links

        # Content length optimization
        length_score = self._score_content_length(content, content_type)

        # Semantic keywords (related terms)
        semantic_count = self._count_semantic_keywords(content)

        return SEOMetrics(
            keyword_density=keyword_density,
            title_optimization_score=title_score,
            meta_description_score=meta_score,
            header_structure_score=header_score,
            internal_link_opportunities=internal_links,
            external_link_quality=75.0,  # Placeholder
            image_alt_optimization=50.0,  # Placeholder
            content_length_score=length_score,
            semantic_keywords_count=semantic_count
        )

    def _calculate_brand_alignment_score(self, content: str) -> float:
        """Calculate brand alignment score for Breathscape"""
        content_lower = content.lower()

        # Breathscape brand terms
        brand_terms = [
            'breathscape', 'wellness', 'mindfulness', 'breathing', 'meditation',
            'health', 'wellbeing', 'balance', 'calm', 'peace', 'tranquility',
            'stress relief', 'relaxation', 'mental health', 'self-care'
        ]

        # Brand values terms
        value_terms = [
            'innovation', 'technology', 'personalized', 'data-driven', 'science',
            'research', 'evidence-based', 'user-friendly', 'accessible', 'empowering'
        ]

        # Count brand-related terms
        brand_count = sum(1 for term in brand_terms if term in content_lower)
        value_count = sum(1 for term in value_terms if term in content_lower)

        # Calculate score based on presence and frequency
        total_words = len(content.split())
        brand_density = (brand_count + value_count) / max(total_words / 100, 1)

        # Base score on brand term presence and appropriate messaging
        base_score = min(100, brand_density * 20)

        # Bonus for mentioning Breathscape specifically
        if 'breathscape' in content_lower:
            base_score += 20

        return min(100, base_score)

    def _calculate_structure_score(self, content: str, content_type: ContentType) -> float:
        """Calculate content structure score"""
        # Different structure requirements by content type
        if content_type == ContentType.EMAIL:
            return self._score_email_structure(content)
        elif content_type == ContentType.WEB:
            return self._score_web_structure(content)
        elif content_type in [ContentType.SOCIAL_TWITTER, ContentType.SOCIAL_LINKEDIN,
                             ContentType.SOCIAL_FACEBOOK, ContentType.SOCIAL_INSTAGRAM]:
            return self._score_social_structure(content)
        else:
            return self._score_general_structure(content)

    def _calculate_clarity_score(self, content: str) -> float:
        """Calculate content clarity score"""
        # Factors affecting clarity
        factors = []

        # Sentence length variation
        sentences = self._split_sentences(content)
        if sentences:
            lengths = [len(sentence.split()) for sentence in sentences]
            avg_length = statistics.mean(lengths)
            variation = statistics.stdev(lengths) if len(lengths) > 1 else 0

            # Optimal sentence length is 15-20 words
            length_score = max(0, 100 - abs(avg_length - 17.5) * 4)
            factors.append(length_score)

            # Good variation in sentence length
            variation_score = min(100, variation * 10)
            factors.append(variation_score)

        # Use of transition words
        transitions = ['however', 'therefore', 'furthermore', 'meanwhile', 'consequently',
                      'additionally', 'moreover', 'nevertheless', 'subsequently', 'thus']
        transition_count = sum(1 for trans in transitions if trans in content.lower())
        transition_score = min(100, transition_count * 15)
        factors.append(transition_score)

        # Avoid jargon and complex words
        complex_count = sum(1 for word in self.complex_words
                           if word in content.lower())
        jargon_penalty = min(50, complex_count * 5)
        complexity_score = max(0, 100 - jargon_penalty)
        factors.append(complexity_score)

        return statistics.mean(factors) if factors else 50.0

    # Helper methods for detailed calculations
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]

    def _split_words(self, content: str) -> List[str]:
        """Split content into words"""
        words = re.findall(r'\b\w+\b', content.lower())
        return [w for w in words if len(w) > 0]

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)"""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count += 1
        return count

    def _count_passive_voice(self, content: str) -> int:
        """Count passive voice constructions"""
        # Simple passive voice detection
        passive_patterns = [
            r'\bis\s+\w+ed\b', r'\bare\s+\w+ed\b', r'\bwas\s+\w+ed\b',
            r'\bwere\s+\w+ed\b', r'\bbeen\s+\w+ed\b', r'\bbeing\s+\w+ed\b'
        ]
        count = 0
        for pattern in passive_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        return count

    def _calculate_keyword_density(self, words: List[str]) -> Dict[str, float]:
        """Calculate keyword density for common terms"""
        from collections import Counter
        word_counts = Counter(words)
        total_words = len(words)

        # Return density for most common words
        density = {}
        for word, count in word_counts.most_common(10):
            if len(word) > 3:  # Skip short words
                density[word] = (count / total_words) * 100

        return density

    def _score_title_optimization(self, content: str) -> float:
        """Score title optimization"""
        lines = content.split('\n')
        if not lines:
            return 0.0

        first_line = lines[0].strip()
        title_score = 0.0

        # Length optimization (50-60 characters for SEO)
        if 40 <= len(first_line) <= 70:
            title_score += 40

        # Contains power words
        if any(word in first_line.lower() for word in self.power_words[:10]):
            title_score += 30

        # Not too many capital letters
        if sum(1 for c in first_line if c.isupper()) <= len(first_line) * 0.3:
            title_score += 30

        return title_score

    def _score_meta_description(self, content: str) -> float:
        """Score meta description optimization"""
        # Look for description-like content (usually 2nd paragraph)
        paragraphs = content.split('\n\n')
        if len(paragraphs) < 2:
            return 50.0  # Default score if no clear description

        description = paragraphs[1].strip()
        score = 0.0

        # Length optimization (150-160 characters)
        if 140 <= len(description) <= 170:
            score += 50

        # Contains call to action
        if any(cta in description.lower() for cta in ['learn', 'discover', 'find out']):
            score += 25

        # Compelling language
        if any(word in description.lower() for word in self.emotional_words[:5]):
            score += 25

        return score

    def _score_header_structure(self, content: str) -> float:
        """Score header structure"""
        # Look for markdown headers or structured text
        headers = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)

        score = 0.0
        if headers:
            score += 40  # Has headers

            # Check hierarchy
            header_levels = [len(re.match(r'^#+', h).group()) for h in headers]
            if len(set(header_levels)) > 1:
                score += 30  # Multiple levels

            # Reasonable number of headers
            if 2 <= len(headers) <= 8:
                score += 30

        return score

    def _score_content_length(self, content: str, content_type: ContentType) -> float:
        """Score content length appropriateness"""
        word_count = len(content.split())

        # Optimal lengths by content type
        optimal_ranges = {
            ContentType.EMAIL: (150, 500),
            ContentType.WEB: (300, 2000),
            ContentType.SOCIAL_TWITTER: (10, 35),
            ContentType.SOCIAL_LINKEDIN: (50, 200),
            ContentType.SOCIAL_FACEBOOK: (25, 80),
            ContentType.SOCIAL_INSTAGRAM: (50, 150)
        }

        min_words, max_words = optimal_ranges.get(content_type, (100, 1000))

        if min_words <= word_count <= max_words:
            return 100.0
        elif word_count < min_words:
            return max(0, 100 - (min_words - word_count) * 2)
        else:
            return max(0, 100 - (word_count - max_words) * 0.5)

    def _count_semantic_keywords(self, content: str) -> int:
        """Count semantic keywords related to wellness/tech"""
        semantic_terms = [
            'algorithm', 'analytics', 'artificial intelligence', 'biometric',
            'breathing pattern', 'cognitive', 'data analysis', 'digital health',
            'health tracking', 'machine learning', 'mindfulness practice',
            'personalization', 'predictive', 'real-time', 'smart technology',
            'stress management', 'user experience', 'wearable', 'wellness journey'
        ]

        content_lower = content.lower()
        return sum(1 for term in semantic_terms if term in content_lower)

    # Structure scoring methods
    def _score_email_structure(self, content: str) -> float:
        """Score email-specific structure"""
        score = 0.0

        # Has clear subject line suggestion
        if content.lower().startswith('subject:') or 'subject line' in content.lower():
            score += 20

        # Has greeting/opening
        openings = ['dear', 'hello', 'hi', 'greetings', 'welcome']
        if any(opening in content.lower()[:100] for opening in openings):
            score += 15

        # Has clear call to action
        cta_terms = ['click', 'visit', 'download', 'register', 'subscribe', 'learn more']
        if any(cta in content.lower() for cta in cta_terms):
            score += 25

        # Has signature/closing
        closings = ['best regards', 'sincerely', 'thanks', 'cheers', 'team']
        if any(closing in content.lower()[-200:] for closing in closings):
            score += 15

        # Proper paragraph breaks
        paragraphs = content.split('\n\n')
        if 2 <= len(paragraphs) <= 6:
            score += 25

        return score

    def _score_web_structure(self, content: str) -> float:
        """Score web content structure"""
        score = 0.0

        # Has clear title/heading
        if content.strip().startswith('#') or re.match(r'^[A-Z][^.!?]*$', content.split('\n')[0]):
            score += 25

        # Has subheadings
        if re.search(r'^#{2,6}\s+', content, re.MULTILINE):
            score += 25

        # Has bullet points or lists
        if re.search(r'^\s*[-*+]\s+', content, re.MULTILINE) or re.search(r'^\s*\d+\.\s+', content, re.MULTILINE):
            score += 20

        # Has clear sections
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 15

        # Has conclusion/summary
        conclusion_terms = ['conclusion', 'summary', 'in summary', 'to summarize', 'final thoughts']
        if any(term in content.lower() for term in conclusion_terms):
            score += 15

        return score

    def _score_social_structure(self, content: str) -> float:
        """Score social media structure"""
        score = 0.0

        # Has attention-grabbing opening
        first_line = content.split('\n')[0] if '\n' in content else content[:50]
        if any(word in first_line.lower() for word in self.power_words[:10]):
            score += 30

        # Appropriate use of hashtags
        hashtag_count = content.count('#')
        if 1 <= hashtag_count <= 5:
            score += 25
        elif hashtag_count == 0:
            score += 10  # OK for some platforms

        # Has emoji usage (for engagement)
        if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content):
            score += 15

        # Clear call to action
        if any(cta in content.lower() for cta in ['follow', 'share', 'comment', 'like', 'tag']):
            score += 30

        return score

    def _score_general_structure(self, content: str) -> float:
        """Score general content structure"""
        score = 0.0

        # Has clear beginning, middle, end
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 40

        # Has logical flow
        transition_words = ['first', 'second', 'then', 'next', 'finally', 'however', 'therefore']
        if sum(1 for word in transition_words if word in content.lower()) >= 2:
            score += 30

        # Proper formatting
        if '\n' in content:  # Has line breaks
            score += 30

        return score

    def _get_category_weights(self, content_type: ContentType) -> Dict[ScoreCategory, float]:
        """Get category weights based on content type"""
        base_weights = {
            ScoreCategory.READABILITY: 0.15,
            ScoreCategory.ENGAGEMENT: 0.20,
            ScoreCategory.SEO_OPTIMIZATION: 0.15,
            ScoreCategory.BRAND_ALIGNMENT: 0.15,
            ScoreCategory.STRUCTURE: 0.15,
            ScoreCategory.CLARITY: 0.20
        }

        # Adjust weights based on content type
        if content_type == ContentType.EMAIL:
            base_weights[ScoreCategory.ENGAGEMENT] = 0.30
            base_weights[ScoreCategory.SEO_OPTIMIZATION] = 0.05
        elif content_type == ContentType.WEB:
            base_weights[ScoreCategory.SEO_OPTIMIZATION] = 0.25
            base_weights[ScoreCategory.STRUCTURE] = 0.20
        elif content_type in [ContentType.SOCIAL_TWITTER, ContentType.SOCIAL_LINKEDIN,
                             ContentType.SOCIAL_FACEBOOK, ContentType.SOCIAL_INSTAGRAM]:
            base_weights[ScoreCategory.ENGAGEMENT] = 0.35
            base_weights[ScoreCategory.CLARITY] = 0.25
            base_weights[ScoreCategory.SEO_OPTIMIZATION] = 0.05

        return base_weights

    def _generate_improvement_suggestions(self, category_scores: Dict[ScoreCategory, float],
                                        content_type: ContentType,
                                        quality_level: QualityLevel) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []

        # Identify lowest scoring categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])

        for category, score in sorted_categories[:3]:  # Focus on 3 lowest scores
            if score < 70:  # Only suggest improvements for scores below 70
                category_suggestions = self._get_category_suggestions(category, content_type)
                suggestions.extend(category_suggestions)

        # Add quality level specific suggestions
        if quality_level in [QualityLevel.POOR, QualityLevel.CRITICAL]:
            suggestions.append("Consider substantial rewrite to improve overall quality")
            suggestions.append("Focus on clear, simple language and strong value proposition")
        elif quality_level == QualityLevel.FAIR:
            suggestions.append("Enhance engagement with more compelling language")
            suggestions.append("Improve structure with better organization and flow")

        return suggestions[:5]  # Limit to 5 suggestions

    def _get_category_suggestions(self, category: ScoreCategory,
                                content_type: ContentType) -> List[str]:
        """Get suggestions for specific category improvements"""
        suggestions = {
            ScoreCategory.READABILITY: [
                "Shorten sentences for better readability",
                "Use simpler words and avoid jargon",
                "Break up long paragraphs",
                "Add more white space and formatting"
            ],
            ScoreCategory.ENGAGEMENT: [
                "Add more emotional and power words",
                "Include questions to engage readers",
                "Use personal pronouns (you, your)",
                "Add storytelling elements or examples"
            ],
            ScoreCategory.SEO_OPTIMIZATION: [
                "Include relevant keywords naturally",
                "Optimize title length (50-60 characters)",
                "Add internal and external links",
                "Improve meta description"
            ],
            ScoreCategory.BRAND_ALIGNMENT: [
                "Include more Breathscape-specific terms",
                "Emphasize wellness and technology benefits",
                "Align with brand values of innovation and empowerment",
                "Add user success stories or testimonials"
            ],
            ScoreCategory.STRUCTURE: [
                "Add clear headings and subheadings",
                "Improve logical flow between sections",
                "Include bullet points or numbered lists",
                "Strengthen opening and closing"
            ],
            ScoreCategory.CLARITY: [
                "Use active voice instead of passive",
                "Add transition words between ideas",
                "Define technical terms clearly",
                "Ensure consistent tone throughout"
            ]
        }

        return suggestions.get(category, ["Improve this category"])[:2]  # Max 2 per category

    def _create_detailed_feedback(self, content: str, category_scores: Dict[ScoreCategory, float],
                                readability: ReadabilityMetrics, engagement: EngagementMetrics,
                                seo: SEOMetrics) -> Dict[str, Any]:
        """Create detailed feedback dictionary"""
        return {
            "content_stats": {
                "word_count": len(content.split()),
                "sentence_count": len(self._split_sentences(content)),
                "paragraph_count": len(content.split('\n\n')),
                "character_count": len(content)
            },
            "readability_details": {
                "grade_level": readability.flesch_kincaid_grade,
                "reading_ease": readability.flesch_reading_ease,
                "avg_sentence_length": readability.average_sentence_length,
                "complex_words_pct": readability.complex_words_percentage
            },
            "engagement_details": {
                "emotional_words": engagement.emotional_words_count,
                "power_words": engagement.power_words_count,
                "questions": engagement.question_count,
                "personal_pronouns": engagement.personal_pronouns_count
            },
            "seo_details": {
                "keyword_density": seo.keyword_density,
                "internal_links": seo.internal_link_opportunities,
                "content_length_score": seo.content_length_score
            },
            "category_scores": category_scores
        }

    def _create_default_readability_metrics(self) -> ReadabilityMetrics:
        """Create default readability metrics for edge cases"""
        return ReadabilityMetrics(
            flesch_reading_ease=50.0,
            flesch_kincaid_grade=8.0,
            gunning_fog_index=10.0,
            automated_readability_index=8.0,
            coleman_liau_index=8.0,
            average_sentence_length=15.0,
            average_syllables_per_word=1.5,
            complex_words_percentage=10.0,
            passive_voice_percentage=5.0
        )

    def _create_error_score(self, error_message: str) -> QualityScore:
        """Create error quality score"""
        default_readability = self._create_default_readability_metrics()
        default_engagement = EngagementMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        default_seo = SEOMetrics({}, 0, 0, 0, 0, 0, 0, 0, 0)

        return QualityScore(
            overall_score=0.0,
            readability_metrics=default_readability,
            engagement_metrics=default_engagement,
            seo_metrics=default_seo,
            brand_alignment_score=0.0,
            structure_score=0.0,
            clarity_score=0.0,
            ai_assessment_score=0.0,
            quality_level=QualityLevel.CRITICAL,
            improvement_suggestions=[f"Scoring failed: {error_message}"],
            detailed_feedback={"error": error_message}
        )


# Singleton instance
_quality_scorer = None

def get_content_quality_scorer() -> ContentQualityScorer:
    """Get singleton instance of content quality scorer"""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = ContentQualityScorer()
    return _quality_scorer