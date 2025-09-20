"""
AI Content Enhancement Service using OpenAI GPT
Sprint 8 - AI Enhancement & Personalization
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass, field

from ..config import get_settings
from ..schemas.content import Content, SocialPost, NewsletterContent, WebUpdateContent
from ..core.resilience import RetryPolicy, CircuitBreaker
from ..templates.ai_prompts import get_prompt_templates, ToneStyle

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for AI enhancement"""
    EMAIL = "email"
    WEB = "web"
    SOCIAL_TWITTER = "twitter"
    SOCIAL_LINKEDIN = "linkedin"
    SOCIAL_FACEBOOK = "facebook"
    SOCIAL_INSTAGRAM = "instagram"


class EnhancementMode(Enum):
    """Enhancement modes for content"""
    IMPROVE_CLARITY = "improve_clarity"
    INCREASE_ENGAGEMENT = "increase_engagement"
    OPTIMIZE_SEO = "optimize_seo"
    PERSONALIZE = "personalize"
    SHORTEN = "shorten"
    EXPAND = "expand"
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    BREATHSCAPE_FOCUS = "breathscape_focus"


@dataclass
class EnhancementRequest:
    """Request for content enhancement"""
    content: str
    content_type: ContentType
    mode: EnhancementMode
    context: Dict[str, Any] = field(default_factory=dict)
    target_audience: Optional[str] = None
    max_length: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    tone: Optional[str] = None


@dataclass
class EnhancementResult:
    """Result of content enhancement"""
    original_content: str
    enhanced_content: str
    mode: EnhancementMode
    confidence_score: float
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityScore:
    """Content quality scoring"""
    overall_score: float
    readability: float
    engagement_potential: float
    seo_score: float
    brand_alignment: float
    suggestions: List[str] = field(default_factory=list)


class PromptManager:
    """Manages AI prompts for different content types and enhancement modes"""

    def __init__(self):
        self.prompts = self._initialize_prompts()

    def _initialize_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize prompt templates"""
        return {
            "improve_clarity": {
                "base": "Improve the clarity and readability of the following content while maintaining its core message and tone:",
                "email": "Improve the clarity of this email newsletter content. Make it easy to scan and understand quickly:",
                "web": "Enhance the clarity of this web content. Ensure it's well-structured with clear headings and concise paragraphs:",
                "twitter": "Make this tweet clearer and more impactful while keeping it under 280 characters:",
                "linkedin": "Improve the professional clarity of this LinkedIn post:",
                "breathscape": "Enhance the clarity of this Breathscape-related content, ensuring technical concepts are explained simply:"
            },
            "increase_engagement": {
                "base": "Rewrite this content to be more engaging and compelling to readers:",
                "email": "Make this email more engaging. Add compelling hooks, clear CTAs, and value propositions:",
                "web": "Enhance engagement for this web content. Add compelling headlines, interesting facts, and clear benefits:",
                "twitter": "Make this tweet more engaging and shareable. Add relevant hashtags if appropriate:",
                "linkedin": "Increase professional engagement for this LinkedIn post. Add thought-provoking questions or insights:",
                "breathscape": "Make this Breathscape content more engaging by highlighting user benefits and success stories:"
            },
            "optimize_seo": {
                "base": "Optimize this content for search engines while maintaining readability:",
                "web": "Optimize this web content for SEO. Include relevant keywords naturally and improve meta descriptions:",
                "breathscape": "Optimize this Breathscape content for search. Include relevant wellness and technology keywords:"
            },
            "personalize": {
                "base": "Personalize this content for the target audience:",
                "email": "Personalize this email for better connection with the recipient:",
                "breathscape": "Personalize this Breathscape content based on user wellness goals and interests:"
            },
            "breathscape_focus": {
                "base": "Enhance this content with a focus on Breathscape's wellness technology and benefits:",
                "email": "Weave Breathscape narrative into this email, highlighting its wellness impact:",
                "web": "Integrate Breathscape features and benefits naturally into this web content:",
                "social": "Create Breathscape-focused social content that highlights innovation and wellness:"
            }
        }

    def get_prompt(self, mode: EnhancementMode, content_type: ContentType,
                   context: Optional[Dict[str, Any]] = None) -> str:
        """Get appropriate prompt for enhancement request"""
        mode_prompts = self.prompts.get(mode.value, {})

        # Try to get specific prompt for content type
        if content_type == ContentType.SOCIAL_TWITTER:
            prompt = mode_prompts.get("twitter", mode_prompts.get("base", ""))
        elif content_type == ContentType.SOCIAL_LINKEDIN:
            prompt = mode_prompts.get("linkedin", mode_prompts.get("base", ""))
        elif content_type in [ContentType.SOCIAL_FACEBOOK, ContentType.SOCIAL_INSTAGRAM]:
            prompt = mode_prompts.get("social", mode_prompts.get("base", ""))
        elif content_type == ContentType.EMAIL:
            prompt = mode_prompts.get("email", mode_prompts.get("base", ""))
        elif content_type == ContentType.WEB:
            prompt = mode_prompts.get("web", mode_prompts.get("base", ""))
        else:
            prompt = mode_prompts.get("base", "")

        # Add context if provided
        if context:
            if context.get("target_audience"):
                prompt += f"\n\nTarget Audience: {context['target_audience']}"
            if context.get("keywords"):
                prompt += f"\n\nInclude these keywords naturally: {', '.join(context['keywords'])}"
            if context.get("tone"):
                prompt += f"\n\nTone: {context['tone']}"
            if context.get("max_length"):
                prompt += f"\n\nMaximum length: {context['max_length']} characters"

        return prompt

    def add_custom_prompt(self, mode: str, content_type: str, prompt: str):
        """Add a custom prompt template"""
        if mode not in self.prompts:
            self.prompts[mode] = {}
        self.prompts[mode][content_type] = prompt


class AIContentEnhancer:
    """AI-powered content enhancement service"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.OPENAI_MODEL or "gpt-3.5-turbo"
        self.prompt_manager = PromptManager()
        self.advanced_prompts = get_prompt_templates()  # Use advanced template system
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None and self.api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI library not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        return self._client

    def is_configured(self) -> bool:
        """Check if AI enhancement is properly configured"""
        return bool(self.api_key and self.client is not None)

    @RetryPolicy(max_retries=3, base_delay=2.0)
    async def enhance_content(self, request: EnhancementRequest) -> EnhancementResult:
        """
        Enhance content using AI

        Args:
            request: Enhancement request with content and parameters

        Returns:
            EnhancementResult with enhanced content and metadata
        """
        if not self.is_configured():
            logger.warning("AI enhancement not configured, returning original content")
            return EnhancementResult(
                original_content=request.content,
                enhanced_content=request.content,
                mode=request.mode,
                confidence_score=0.0,
                suggestions=["Configure OpenAI API key for AI enhancements"]
            )

        try:
            # Build context for prompt
            context = {
                "target_audience": request.target_audience,
                "keywords": request.keywords,
                "tone": request.tone,
                "max_length": request.max_length
            }

            # Get appropriate prompt
            prompt = self.prompt_manager.get_prompt(
                request.mode,
                request.content_type,
                context
            )

            # Make API call with circuit breaker
            enhanced = await self._call_openai_api(prompt, request.content)

            # Calculate confidence score based on response
            confidence = self._calculate_confidence(request.content, enhanced)

            # Generate suggestions
            suggestions = await self._generate_suggestions(
                request.content,
                enhanced,
                request.content_type
            )

            return EnhancementResult(
                original_content=request.content,
                enhanced_content=enhanced,
                mode=request.mode,
                confidence_score=confidence,
                suggestions=suggestions,
                metadata={
                    "model": self.model,
                    "timestamp": datetime.utcnow().isoformat(),
                    "content_type": request.content_type.value
                }
            )

        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            return EnhancementResult(
                original_content=request.content,
                enhanced_content=request.content,
                mode=request.mode,
                confidence_score=0.0,
                suggestions=[f"Enhancement failed: {str(e)}"]
            )

    async def _call_openai_api(self, prompt: str, content: str) -> str:
        """Make API call to OpenAI"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        def api_call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional content writer specializing in wellness technology and Breathscape products."},
                    {"role": "user", "content": f"{prompt}\n\nContent:\n{content}"}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.circuit_breaker.call, api_call)
        return result

    def _calculate_confidence(self, original: str, enhanced: str) -> float:
        """Calculate confidence score for enhancement"""
        # Simple heuristic based on content similarity and improvement
        if not enhanced or enhanced == original:
            return 0.0

        # Calculate basic metrics
        original_len = len(original)
        enhanced_len = len(enhanced)

        # Check if enhancement is reasonable
        if enhanced_len < original_len * 0.3 or enhanced_len > original_len * 3:
            return 0.5  # Too much or too little change

        # Basic confidence score (can be improved with more sophisticated metrics)
        return 0.85

    async def _generate_suggestions(self, original: str, enhanced: str,
                                   content_type: ContentType) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        # Length-based suggestions
        if content_type == ContentType.SOCIAL_TWITTER and len(enhanced) > 280:
            suggestions.append("Consider shortening for Twitter's character limit")

        if content_type == ContentType.EMAIL and len(enhanced) > 2000:
            suggestions.append("Consider breaking into smaller sections for better email readability")

        # Content-based suggestions
        if "breathscape" not in enhanced.lower() and "wellness" in original.lower():
            suggestions.append("Consider mentioning Breathscape features for brand consistency")

        if not any(cta in enhanced.lower() for cta in ["learn more", "try", "get started", "sign up"]):
            suggestions.append("Add a clear call-to-action for better engagement")

        return suggestions

    async def score_content_quality(self, content: str,
                                   content_type: ContentType) -> QualityScore:
        """
        Score content quality using AI analysis

        Args:
            content: Content to score
            content_type: Type of content

        Returns:
            QualityScore with detailed metrics
        """
        if not self.is_configured():
            return QualityScore(
                overall_score=0.0,
                readability=0.0,
                engagement_potential=0.0,
                seo_score=0.0,
                brand_alignment=0.0,
                suggestions=["Configure OpenAI API key for quality scoring"]
            )

        try:
            # Create scoring prompt
            scoring_prompt = f"""
            Analyze the following content and provide scores (0-100) for:
            1. Readability (clarity, structure, grammar)
            2. Engagement Potential (compelling, interesting, actionable)
            3. SEO Value (keyword usage, structure, meta potential)
            4. Brand Alignment (fits Breathscape/wellness tech brand)

            Provide the scores as JSON: {{"readability": X, "engagement": X, "seo": X, "brand": X}}
            Also provide 2-3 specific improvement suggestions.

            Content Type: {content_type.value}
            Content: {content}
            """

            # Get AI analysis
            response = await self._call_openai_api(scoring_prompt, "")

            # Parse response (with error handling)
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*?\}', response, re.DOTALL)
                if json_match:
                    scores = json.loads(json_match.group())
                else:
                    scores = {"readability": 70, "engagement": 70, "seo": 70, "brand": 70}

                # Extract suggestions
                suggestions = []
                lines = response.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('{') and len(line) > 20:
                        suggestions.append(line.strip())

                return QualityScore(
                    overall_score=(scores.get("readability", 70) +
                                 scores.get("engagement", 70) +
                                 scores.get("seo", 70) +
                                 scores.get("brand", 70)) / 4,
                    readability=scores.get("readability", 70) / 100,
                    engagement_potential=scores.get("engagement", 70) / 100,
                    seo_score=scores.get("seo", 70) / 100,
                    brand_alignment=scores.get("brand", 70) / 100,
                    suggestions=suggestions[:3]
                )
            except Exception as e:
                logger.warning(f"Failed to parse scoring response: {e}")
                return QualityScore(
                    overall_score=0.7,
                    readability=0.7,
                    engagement_potential=0.7,
                    seo_score=0.7,
                    brand_alignment=0.7,
                    suggestions=["Analysis completed with default scores"]
                )

        except Exception as e:
            logger.error(f"Quality scoring failed: {e}")
            return QualityScore(
                overall_score=0.0,
                readability=0.0,
                engagement_potential=0.0,
                seo_score=0.0,
                brand_alignment=0.0,
                suggestions=[f"Scoring failed: {str(e)}"]
            )

    async def generate_variations(self, content: str, content_type: ContentType,
                                 num_variations: int = 3) -> List[str]:
        """
        Generate content variations for A/B testing

        Args:
            content: Original content
            content_type: Type of content
            num_variations: Number of variations to generate

        Returns:
            List of content variations
        """
        if not self.is_configured():
            return [content]  # Return original if not configured

        variations = []
        modes = [
            EnhancementMode.INCREASE_ENGAGEMENT,
            EnhancementMode.CASUAL,
            EnhancementMode.BREATHSCAPE_FOCUS
        ]

        for i, mode in enumerate(modes[:num_variations]):
            request = EnhancementRequest(
                content=content,
                content_type=content_type,
                mode=mode,
                context={"variation_number": i + 1}
            )

            result = await self.enhance_content(request)
            variations.append(result.enhanced_content)

        return variations

    async def personalize_for_segment(self, content: str, segment: str,
                                     content_type: ContentType) -> str:
        """
        Personalize content for a specific user segment

        Args:
            content: Original content
            segment: User segment identifier
            content_type: Type of content

        Returns:
            Personalized content
        """
        # Define segment characteristics
        segment_profiles = {
            "wellness_enthusiast": {
                "tone": "inspirational",
                "keywords": ["wellness", "mindfulness", "balance", "health"],
                "audience": "health-conscious individuals seeking holistic wellness"
            },
            "tech_professional": {
                "tone": "technical and efficient",
                "keywords": ["innovation", "data", "analytics", "performance"],
                "audience": "tech-savvy professionals interested in quantified wellness"
            },
            "healthcare_provider": {
                "tone": "professional and evidence-based",
                "keywords": ["clinical", "research", "patient outcomes", "evidence"],
                "audience": "healthcare professionals and practitioners"
            },
            "fitness_focused": {
                "tone": "energetic and motivational",
                "keywords": ["performance", "training", "recovery", "goals"],
                "audience": "athletes and fitness enthusiasts"
            }
        }

        profile = segment_profiles.get(segment, {})

        request = EnhancementRequest(
            content=content,
            content_type=content_type,
            mode=EnhancementMode.PERSONALIZE,
            context=profile,
            target_audience=profile.get("audience"),
            keywords=profile.get("keywords", []),
            tone=profile.get("tone")
        )

        result = await self.enhance_content(request)
        return result.enhanced_content


# Singleton instance
_enhancer_instance = None

def get_ai_enhancer() -> AIContentEnhancer:
    """Get singleton instance of AI enhancer"""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = AIContentEnhancer()
    return _enhancer_instance