"""
Comprehensive unit tests for AI content enhancer service
Targeting 244 lines of code with 0% coverage for significant improvement
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from datetime import datetime

from src.halcytone_content_generator.services.ai_content_enhancer import (
    AIContentEnhancer, PromptManager, EnhancementMode, ContentType, QualityMetrics
)


class TestPromptManager:
    """Test prompt management functionality"""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt manager instance"""
        return PromptManager()

    def test_prompt_manager_initialization(self, prompt_manager):
        """Test prompt manager initializes correctly"""
        assert prompt_manager is not None
        assert hasattr(prompt_manager, 'get_prompt')
        assert hasattr(prompt_manager, 'add_custom_prompt')

    def test_get_prompt_for_email_clarity(self, prompt_manager):
        """Test getting prompt for email clarity enhancement"""
        prompt = prompt_manager.get_prompt('email', 'clarity')
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'email' in prompt.lower() or 'clarity' in prompt.lower()

    def test_get_prompt_for_twitter_engagement(self, prompt_manager):
        """Test getting prompt for Twitter engagement"""
        prompt = prompt_manager.get_prompt('social', 'engagement', platform='twitter')
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_prompt_with_context(self, prompt_manager):
        """Test getting prompt with context variables"""
        context = {
            'brand': 'Halcytone',
            'tone': 'professional',
            'audience': 'wellness practitioners'
        }
        prompt = prompt_manager.get_prompt('blog', 'clarity', context=context)
        assert isinstance(prompt, str)
        # Context variables should be replaced
        assert 'Halcytone' in prompt or '{brand}' not in prompt

    def test_add_custom_prompt(self, prompt_manager):
        """Test adding custom prompts"""
        custom_prompt = "Enhance this content for {audience} with {tone} tone focusing on {topic}."
        prompt_manager.add_custom_prompt('custom_test', custom_prompt)

        retrieved = prompt_manager.get_prompt('custom_test', 'enhancement')
        assert custom_prompt in retrieved

    def test_breathscape_focus_prompts(self, prompt_manager):
        """Test Breathscape-specific prompts"""
        prompt = prompt_manager.get_prompt('breathscape', 'wellness')
        assert isinstance(prompt, str)
        assert 'breath' in prompt.lower() or 'wellness' in prompt.lower()

    def test_prompt_templates_loaded(self, prompt_manager):
        """Test that all required prompt templates are loaded"""
        content_types = ['email', 'social', 'blog', 'web', 'breathscape']
        enhancement_types = ['clarity', 'engagement', 'seo', 'tone']

        for content_type in content_types:
            for enhancement_type in enhancement_types:
                prompt = prompt_manager.get_prompt(content_type, enhancement_type)
                assert isinstance(prompt, str)
                assert len(prompt) > 10  # Reasonable minimum length

    def test_prompt_caching(self, prompt_manager):
        """Test prompt caching for performance"""
        # First call should cache the prompt
        prompt1 = prompt_manager.get_prompt('email', 'clarity')
        # Second call should return cached version
        prompt2 = prompt_manager.get_prompt('email', 'clarity')
        assert prompt1 == prompt2

    def test_prompt_validation(self, prompt_manager):
        """Test prompt validation"""
        # Valid prompt should work
        valid_prompt = "Enhance this {content_type} for better {enhancement_goal}."
        assert prompt_manager.validate_prompt(valid_prompt) is True

        # Invalid prompt should fail validation
        invalid_prompt = ""
        assert prompt_manager.validate_prompt(invalid_prompt) is False


class TestAIContentEnhancer:
    """Test AI content enhancement functionality"""

    @pytest.fixture
    def ai_enhancer(self):
        """Create AI content enhancer with mock configuration"""
        config = {
            'openai_api_key': 'test_key',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 1000,
            'temperature': 0.7
        }
        return AIContentEnhancer(config)

    @pytest.fixture
    def ai_enhancer_no_key(self):
        """Create AI content enhancer without API key"""
        config = {}
        return AIContentEnhancer(config)

    def test_enhancer_initialization(self, ai_enhancer):
        """Test AI enhancer initialization"""
        assert ai_enhancer is not None
        assert ai_enhancer.is_configured() is True

    def test_is_configured_with_api_key(self, ai_enhancer):
        """Test configuration check with API key"""
        assert ai_enhancer.is_configured() is True

    def test_is_configured_without_api_key(self, ai_enhancer_no_key):
        """Test configuration check without API key"""
        assert ai_enhancer_no_key.is_configured() is False

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_enhance_content_success(self, mock_openai, ai_enhancer):
        """Test successful content enhancement"""
        # Mock OpenAI response
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Enhanced content with improved clarity and engagement.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        original_content = "This is basic content about breathing techniques."
        result = await ai_enhancer.enhance_content(
            content=original_content,
            content_type=ContentType.BLOG,
            mode=EnhancementMode.CLARITY
        )

        assert result['enhanced_content'] == 'Enhanced content with improved clarity and engagement.'
        assert result['success'] is True
        mock_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhance_content_without_configuration(self, ai_enhancer_no_key):
        """Test content enhancement without API configuration"""
        content = "Test content"
        result = await ai_enhancer_no_key.enhance_content(
            content=content,
            content_type=ContentType.EMAIL,
            mode=EnhancementMode.ENGAGEMENT
        )

        assert result['success'] is False
        assert 'not configured' in result['error'].lower()

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_enhance_content_with_error(self, mock_openai, ai_enhancer):
        """Test content enhancement with API error"""
        mock_openai.side_effect = Exception("API rate limit exceeded")

        content = "Test content"
        result = await ai_enhancer.enhance_content(
            content=content,
            content_type=ContentType.SOCIAL,
            mode=EnhancementMode.SEO
        )

        assert result['success'] is False
        assert 'error' in result

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_score_content_quality_success(self, mock_openai, ai_enhancer):
        """Test content quality scoring"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': '{"clarity": 8.5, "engagement": 7.0, "readability": 9.0, "overall": 8.2}'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Well-written content about breathing techniques with clear structure."
        result = await ai_enhancer.score_content_quality(content, ContentType.BLOG)

        assert result['success'] is True
        assert 'quality_score' in result
        assert result['quality_score']['overall'] == 8.2

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_score_content_quality_parse_error(self, mock_openai, ai_enhancer):
        """Test content quality scoring with JSON parse error"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Invalid JSON response'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Test content"
        result = await ai_enhancer.score_content_quality(content, ContentType.EMAIL)

        assert result['success'] is False
        assert 'parse error' in result['error'].lower()

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_generate_variations(self, mock_openai, ai_enhancer):
        """Test generating content variations"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': '["Variation 1", "Variation 2", "Variation 3"]'
                }
            }]
        }
        mock_openai.return_value = mock_response

        original_content = "Original content"
        result = await ai_enhancer.generate_variations(
            content=original_content,
            content_type=ContentType.SOCIAL,
            count=3
        )

        assert result['success'] is True
        assert len(result['variations']) == 3
        assert 'Variation 1' in result['variations']

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_personalize_for_segment_wellness(self, mock_openai, ai_enhancer):
        """Test content personalization for wellness segment"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Personalized wellness content focusing on mindful breathing practices.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Generic breathing content"
        segment = {
            'name': 'wellness_practitioners',
            'interests': ['mindfulness', 'breathing', 'meditation'],
            'tone_preference': 'professional'
        }

        result = await ai_enhancer.personalize_for_segment(content, segment)

        assert result['success'] is True
        assert 'wellness' in result['personalized_content'].lower()

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_personalize_for_segment_tech(self, mock_openai, ai_enhancer):
        """Test content personalization for tech segment"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Tech-focused content about breathing algorithms and sensor technology.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Breathing technology content"
        segment = {
            'name': 'tech_enthusiasts',
            'interests': ['technology', 'sensors', 'algorithms'],
            'tone_preference': 'technical'
        }

        result = await ai_enhancer.personalize_for_segment(content, segment)

        assert result['success'] is True
        assert 'tech' in result['personalized_content'].lower()

    def test_calculate_confidence_score(self, ai_enhancer):
        """Test confidence score calculation"""
        # High confidence factors
        high_confidence_factors = {
            'content_length': 500,
            'response_time': 1.2,
            'api_success': True,
            'quality_indicators': ['coherent', 'relevant', 'engaging']
        }

        score = ai_enhancer.calculate_confidence_score(high_confidence_factors)
        assert score > 0.7

        # Low confidence factors
        low_confidence_factors = {
            'content_length': 50,
            'response_time': 15.0,
            'api_success': False,
            'quality_indicators': []
        }

        score = ai_enhancer.calculate_confidence_score(low_confidence_factors)
        assert score < 0.5

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_generate_suggestions_twitter(self, mock_openai, ai_enhancer):
        """Test generating suggestions for Twitter content"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': '["Add relevant hashtags", "Include emoji for engagement", "Keep under 280 characters"]'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Tweet about breathing techniques"
        result = await ai_enhancer.generate_suggestions(content, 'twitter')

        assert result['success'] is True
        assert len(result['suggestions']) >= 1
        assert any('hashtag' in suggestion.lower() for suggestion in result['suggestions'])

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_generate_suggestions_email(self, mock_openai, ai_enhancer):
        """Test generating suggestions for email content"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': '["Improve subject line", "Add clear call-to-action", "Optimize for mobile"]'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Email about breathing wellness"
        result = await ai_enhancer.generate_suggestions(content, 'email')

        assert result['success'] is True
        assert any('subject' in suggestion.lower() for suggestion in result['suggestions'])

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_generate_suggestions_breathscape(self, mock_openai, ai_enhancer):
        """Test generating suggestions for Breathscape content"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': '["Focus on wellness benefits", "Include breathing exercise", "Add mindfulness element"]'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Breathscape feature content"
        result = await ai_enhancer.generate_suggestions(content, 'breathscape')

        assert result['success'] is True
        assert any('wellness' in suggestion.lower() or 'breathing' in suggestion.lower()
                  for suggestion in result['suggestions'])

    def test_singleton_instance(self):
        """Test singleton pattern implementation"""
        config = {'openai_api_key': 'test_key'}

        enhancer1 = AIContentEnhancer.get_instance(config)
        enhancer2 = AIContentEnhancer.get_instance(config)

        assert enhancer1 is enhancer2

    def test_circuit_breaker_activation(self, ai_enhancer):
        """Test circuit breaker activation on repeated failures"""
        # Simulate multiple failures
        for _ in range(5):
            ai_enhancer._record_failure()

        assert ai_enhancer._circuit_breaker_open() is True

        # Test circuit breaker reset after cooldown
        ai_enhancer._reset_circuit_breaker()
        assert ai_enhancer._circuit_breaker_open() is False

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_enhance_with_all_modes(self, mock_openai, ai_enhancer):
        """Test enhancement with all available modes"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Enhanced content with comprehensive improvements.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Basic content about breathing"

        modes = [
            EnhancementMode.CLARITY,
            EnhancementMode.ENGAGEMENT,
            EnhancementMode.SEO,
            EnhancementMode.TONE
        ]

        for mode in modes:
            result = await ai_enhancer.enhance_content(
                content=content,
                content_type=ContentType.BLOG,
                mode=mode
            )
            assert result['success'] is True

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_enhance_all_content_types(self, mock_openai, ai_enhancer):
        """Test enhancement for all content types"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Enhanced content adapted for specific type.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content = "Generic content"

        content_types = [
            ContentType.EMAIL,
            ContentType.BLOG,
            ContentType.SOCIAL,
            ContentType.WEB,
            ContentType.BREATHSCAPE
        ]

        for content_type in content_types:
            result = await ai_enhancer.enhance_content(
                content=content,
                content_type=content_type,
                mode=EnhancementMode.CLARITY
            )
            assert result['success'] is True

    def test_quality_metrics_calculation(self, ai_enhancer):
        """Test quality metrics calculation"""
        content = """
        This is a well-structured article about breathing techniques.
        It provides clear instructions and helpful tips for beginners.
        The content is engaging and informative with good readability.
        """

        metrics = ai_enhancer.calculate_quality_metrics(content)

        assert isinstance(metrics, QualityMetrics)
        assert metrics.readability_score > 0
        assert metrics.engagement_score > 0
        assert metrics.clarity_score > 0

    def test_content_analysis_features(self, ai_enhancer):
        """Test content analysis features"""
        content = "Breathing techniques for stress relief and mindfulness practice."

        analysis = ai_enhancer.analyze_content_features(content)

        assert 'keyword_density' in analysis
        assert 'sentiment_score' in analysis
        assert 'reading_time' in analysis
        assert 'word_count' in analysis

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_batch_enhancement(self, mock_openai, ai_enhancer):
        """Test batch content enhancement"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Enhanced content item.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        content_items = [
            "First piece of content",
            "Second piece of content",
            "Third piece of content"
        ]

        results = await ai_enhancer.enhance_batch(
            content_items=content_items,
            content_type=ContentType.SOCIAL,
            mode=EnhancementMode.ENGAGEMENT
        )

        assert len(results) == 3
        assert all(result['success'] for result in results)

    def test_enhancement_history_tracking(self, ai_enhancer):
        """Test enhancement history tracking"""
        # Record some enhancements
        ai_enhancer.record_enhancement_history(
            original="Original content",
            enhanced="Enhanced content",
            mode=EnhancementMode.CLARITY,
            quality_score=8.5
        )

        history = ai_enhancer.get_enhancement_history()
        assert len(history) >= 1
        assert history[0]['mode'] == EnhancementMode.CLARITY
        assert history[0]['quality_score'] == 8.5

    def test_performance_metrics(self, ai_enhancer):
        """Test performance metrics tracking"""
        # Simulate API calls
        ai_enhancer._record_api_call(response_time=1.5, success=True)
        ai_enhancer._record_api_call(response_time=2.0, success=True)
        ai_enhancer._record_api_call(response_time=0.8, success=False)

        metrics = ai_enhancer.get_performance_metrics()

        assert metrics['total_calls'] == 3
        assert metrics['success_rate'] < 1.0  # Due to one failure
        assert metrics['average_response_time'] > 0

    def test_rate_limiting(self, ai_enhancer):
        """Test rate limiting functionality"""
        # Configure rate limit
        ai_enhancer.set_rate_limit(requests_per_minute=60)

        # Check rate limit status
        can_make_request = ai_enhancer.can_make_request()
        assert can_make_request is True

        # Simulate hitting rate limit
        for _ in range(61):
            ai_enhancer._record_request()

        can_make_request = ai_enhancer.can_make_request()
        assert can_make_request is False

    @patch('openai.ChatCompletion.acreate')
    @pytest.mark.asyncio
    async def test_content_optimization_workflow(self, mock_openai, ai_enhancer):
        """Test complete content optimization workflow"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Fully optimized content with all enhancements applied.'
                }
            }]
        }
        mock_openai.return_value = mock_response

        original_content = "Basic content about breathing techniques."

        # Complete optimization workflow
        result = await ai_enhancer.optimize_content_workflow(
            content=original_content,
            content_type=ContentType.BLOG,
            target_audience='wellness_practitioners',
            optimization_goals=['clarity', 'engagement', 'seo']
        )

        assert result['success'] is True
        assert 'optimized_content' in result
        assert 'optimization_report' in result
        assert len(result['optimization_report']['applied_enhancements']) > 0