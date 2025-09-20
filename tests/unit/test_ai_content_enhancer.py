"""
Unit tests for AI Content Enhancement Service
Sprint 8 - AI Enhancement & Personalization
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

from src.halcytone_content_generator.services.ai_content_enhancer import (
    AIContentEnhancer,
    EnhancementRequest,
    EnhancementResult,
    QualityScore,
    ContentType,
    EnhancementMode,
    PromptManager,
    get_ai_enhancer
)


class TestPromptManager:
    """Test prompt management functionality"""

    def test_prompt_manager_initialization(self):
        """Test prompt manager initializes with default prompts"""
        manager = PromptManager()
        assert manager.prompts is not None
        assert "improve_clarity" in manager.prompts
        assert "increase_engagement" in manager.prompts
        assert "optimize_seo" in manager.prompts
        assert "breathscape_focus" in manager.prompts

    def test_get_prompt_for_email_clarity(self):
        """Test getting prompt for email clarity improvement"""
        manager = PromptManager()
        prompt = manager.get_prompt(
            EnhancementMode.IMPROVE_CLARITY,
            ContentType.EMAIL
        )
        assert "email" in prompt.lower()
        assert "clarity" in prompt.lower()

    def test_get_prompt_for_twitter_engagement(self):
        """Test getting prompt for Twitter engagement"""
        manager = PromptManager()
        prompt = manager.get_prompt(
            EnhancementMode.INCREASE_ENGAGEMENT,
            ContentType.SOCIAL_TWITTER
        )
        assert "tweet" in prompt.lower()
        assert "engaging" in prompt.lower()
        assert "280 characters" in prompt

    def test_get_prompt_with_context(self):
        """Test prompt generation with context"""
        manager = PromptManager()
        context = {
            "target_audience": "wellness professionals",
            "keywords": ["breathscape", "wellness", "technology"],
            "tone": "professional",
            "max_length": 500
        }
        prompt = manager.get_prompt(
            EnhancementMode.IMPROVE_CLARITY,
            ContentType.WEB,
            context
        )
        assert "Target Audience: wellness professionals" in prompt
        assert "breathscape" in prompt
        assert "Maximum length: 500" in prompt

    def test_add_custom_prompt(self):
        """Test adding custom prompt templates"""
        manager = PromptManager()
        custom_prompt = "Custom prompt for testing"
        manager.add_custom_prompt("test_mode", "test_type", custom_prompt)

        assert "test_mode" in manager.prompts
        assert manager.prompts["test_mode"]["test_type"] == custom_prompt

    def test_breathscape_focus_prompts(self):
        """Test Breathscape-specific enhancement prompts"""
        manager = PromptManager()
        prompt = manager.get_prompt(
            EnhancementMode.BREATHSCAPE_FOCUS,
            ContentType.EMAIL
        )
        assert "breathscape" in prompt.lower()
        assert "wellness" in prompt.lower()


class TestAIContentEnhancer:
    """Test AI content enhancement functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.OPENAI_API_KEY = "test-api-key"
        settings.OPENAI_MODEL = "gpt-3.5-turbo"
        return settings

    @pytest.fixture
    def enhancer(self, mock_settings):
        """Create enhancer with mocked settings"""
        with patch('src.halcytone_content_generator.services.ai_content_enhancer.get_settings',
                  return_value=mock_settings):
            return AIContentEnhancer()

    def test_enhancer_initialization(self, enhancer):
        """Test AI enhancer initializes correctly"""
        assert enhancer.api_key == "test-api-key"
        assert enhancer.model == "gpt-3.5-turbo"
        assert enhancer.prompt_manager is not None
        assert enhancer.circuit_breaker is not None

    def test_is_configured_with_api_key(self, enhancer):
        """Test configuration check with API key"""
        with patch.object(enhancer, '_client', Mock()):
            assert enhancer.is_configured() is True

    def test_is_configured_without_api_key(self, mock_settings):
        """Test configuration check without API key"""
        mock_settings.OPENAI_API_KEY = None
        with patch('src.halcytone_content_generator.services.ai_content_enhancer.get_settings',
                  return_value=mock_settings):
            enhancer = AIContentEnhancer()
            assert enhancer.is_configured() is False

    @pytest.mark.asyncio
    async def test_enhance_content_success(self, enhancer):
        """Test successful content enhancement"""
        # Mock OpenAI API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Enhanced content here"))]

        with patch.object(enhancer, 'client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            request = EnhancementRequest(
                content="Original content",
                content_type=ContentType.EMAIL,
                mode=EnhancementMode.IMPROVE_CLARITY,
                target_audience="wellness enthusiasts"
            )

            result = await enhancer.enhance_content(request)

            assert isinstance(result, EnhancementResult)
            assert result.original_content == "Original content"
            assert result.enhanced_content == "Enhanced content here"
            assert result.mode == EnhancementMode.IMPROVE_CLARITY
            assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_enhance_content_without_configuration(self, mock_settings):
        """Test enhancement without API configuration"""
        mock_settings.OPENAI_API_KEY = None
        with patch('src.halcytone_content_generator.services.ai_content_enhancer.get_settings',
                  return_value=mock_settings):
            enhancer = AIContentEnhancer()

            request = EnhancementRequest(
                content="Original content",
                content_type=ContentType.EMAIL,
                mode=EnhancementMode.IMPROVE_CLARITY
            )

            result = await enhancer.enhance_content(request)

            assert result.enhanced_content == "Original content"  # Returns original
            assert result.confidence_score == 0.0
            assert "Configure OpenAI API key" in result.suggestions[0]

    @pytest.mark.asyncio
    async def test_enhance_content_with_error(self, enhancer):
        """Test enhancement with API error"""
        with patch.object(enhancer, '_call_openai_api',
                         side_effect=Exception("API Error")):
            request = EnhancementRequest(
                content="Original content",
                content_type=ContentType.EMAIL,
                mode=EnhancementMode.IMPROVE_CLARITY
            )

            result = await enhancer.enhance_content(request)

            assert result.enhanced_content == "Original content"  # Returns original
            assert result.confidence_score == 0.0
            assert "Enhancement failed" in result.suggestions[0]

    @pytest.mark.asyncio
    async def test_score_content_quality_success(self, enhancer):
        """Test content quality scoring"""
        mock_response = json.dumps({
            "readability": 85,
            "engagement": 75,
            "seo": 70,
            "brand": 90
        })

        with patch.object(enhancer, '_call_openai_api',
                         return_value=mock_response):
            score = await enhancer.score_content_quality(
                "Test content",
                ContentType.WEB
            )

            assert isinstance(score, QualityScore)
            assert score.readability == 0.85
            assert score.engagement_potential == 0.75
            assert score.seo_score == 0.70
            assert score.brand_alignment == 0.90
            assert score.overall_score == (85 + 75 + 70 + 90) / 4

    @pytest.mark.asyncio
    async def test_score_content_quality_parse_error(self, enhancer):
        """Test quality scoring with parse error"""
        with patch.object(enhancer, '_call_openai_api',
                         return_value="Invalid response"):
            score = await enhancer.score_content_quality(
                "Test content",
                ContentType.WEB
            )

            assert score.overall_score == 0.7  # Default score
            assert "default scores" in score.suggestions[0].lower()

    @pytest.mark.asyncio
    async def test_generate_variations(self, enhancer):
        """Test content variation generation for A/B testing"""
        with patch.object(enhancer, 'enhance_content') as mock_enhance:
            mock_enhance.return_value = AsyncMock(
                enhanced_content="Variation content"
            )()

            variations = await enhancer.generate_variations(
                "Original content",
                ContentType.EMAIL,
                num_variations=2
            )

            assert len(variations) == 2
            assert mock_enhance.call_count == 2

    @pytest.mark.asyncio
    async def test_personalize_for_segment_wellness(self, enhancer):
        """Test content personalization for wellness segment"""
        with patch.object(enhancer, 'enhance_content') as mock_enhance:
            mock_enhance.return_value = AsyncMock(
                enhanced_content="Personalized wellness content"
            )()

            result = await enhancer.personalize_for_segment(
                "Generic content",
                "wellness_enthusiast",
                ContentType.EMAIL
            )

            # Check the request was made with wellness context
            call_args = mock_enhance.call_args[0][0]
            assert call_args.mode == EnhancementMode.PERSONALIZE
            assert "wellness" in call_args.keywords
            assert call_args.tone == "inspirational"

    @pytest.mark.asyncio
    async def test_personalize_for_segment_tech(self, enhancer):
        """Test content personalization for tech segment"""
        with patch.object(enhancer, 'enhance_content') as mock_enhance:
            mock_enhance.return_value = AsyncMock(
                enhanced_content="Personalized tech content"
            )()

            result = await enhancer.personalize_for_segment(
                "Generic content",
                "tech_professional",
                ContentType.WEB
            )

            # Check the request was made with tech context
            call_args = mock_enhance.call_args[0][0]
            assert "innovation" in call_args.keywords
            assert call_args.tone == "technical and efficient"

    def test_calculate_confidence_score(self, enhancer):
        """Test confidence score calculation"""
        # Same content - low confidence
        score = enhancer._calculate_confidence("test", "test")
        assert score == 0.0

        # Reasonable change - high confidence
        score = enhancer._calculate_confidence(
            "Short content",
            "This is enhanced content with more detail"
        )
        assert score == 0.85

        # Too much change - medium confidence
        score = enhancer._calculate_confidence(
            "Short",
            "x" * 100
        )
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_generate_suggestions_twitter(self, enhancer):
        """Test suggestion generation for Twitter content"""
        suggestions = await enhancer._generate_suggestions(
            "Short wellness tip",
            "x" * 300,  # Too long for Twitter
            ContentType.SOCIAL_TWITTER
        )

        assert any("Twitter's character limit" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_suggestions_email(self, enhancer):
        """Test suggestion generation for email content"""
        long_content = "x" * 3000
        suggestions = await enhancer._generate_suggestions(
            "wellness content",
            long_content,
            ContentType.EMAIL
        )

        assert any("smaller sections" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_suggestions_breathscape(self, enhancer):
        """Test Breathscape brand suggestions"""
        suggestions = await enhancer._generate_suggestions(
            "wellness technology content",
            "Great wellness tips here",
            ContentType.WEB
        )

        assert any("Breathscape" in s for s in suggestions)

    def test_singleton_instance(self):
        """Test singleton pattern for AI enhancer"""
        instance1 = get_ai_enhancer()
        instance2 = get_ai_enhancer()
        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, enhancer):
        """Test circuit breaker protects against repeated failures"""
        with patch.object(enhancer, 'client') as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            # Make multiple failing requests
            for _ in range(6):
                request = EnhancementRequest(
                    content="Test",
                    content_type=ContentType.EMAIL,
                    mode=EnhancementMode.IMPROVE_CLARITY
                )
                result = await enhancer.enhance_content(request)
                assert result.confidence_score == 0.0

    @pytest.mark.asyncio
    async def test_enhance_with_all_modes(self, enhancer):
        """Test enhancement with all available modes"""
        modes = [
            EnhancementMode.IMPROVE_CLARITY,
            EnhancementMode.INCREASE_ENGAGEMENT,
            EnhancementMode.OPTIMIZE_SEO,
            EnhancementMode.PERSONALIZE,
            EnhancementMode.SHORTEN,
            EnhancementMode.EXPAND,
            EnhancementMode.FORMAL,
            EnhancementMode.CASUAL,
            EnhancementMode.TECHNICAL,
            EnhancementMode.BREATHSCAPE_FOCUS
        ]

        with patch.object(enhancer, '_call_openai_api',
                         return_value="Enhanced content"):
            for mode in modes:
                request = EnhancementRequest(
                    content="Test content",
                    content_type=ContentType.EMAIL,
                    mode=mode
                )
                result = await enhancer.enhance_content(request)
                assert result.mode == mode
                assert result.enhanced_content == "Enhanced content"

    @pytest.mark.asyncio
    async def test_enhance_all_content_types(self, enhancer):
        """Test enhancement with all content types"""
        content_types = [
            ContentType.EMAIL,
            ContentType.WEB,
            ContentType.SOCIAL_TWITTER,
            ContentType.SOCIAL_LINKEDIN,
            ContentType.SOCIAL_FACEBOOK,
            ContentType.SOCIAL_INSTAGRAM
        ]

        with patch.object(enhancer, '_call_openai_api',
                         return_value="Enhanced content"):
            for content_type in content_types:
                request = EnhancementRequest(
                    content="Test content",
                    content_type=content_type,
                    mode=EnhancementMode.IMPROVE_CLARITY
                )
                result = await enhancer.enhance_content(request)
                assert result.metadata["content_type"] == content_type.value