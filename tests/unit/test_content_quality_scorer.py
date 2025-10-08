"""
Unit tests for Content Quality Scoring Service
Sprint 8 - AI Enhancement & Personalization
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import statistics

from halcytone_content_generator.services.content_quality_scorer import (
    ContentQualityScorer,
    QualityScore,
    QualityLevel,
    QualityThresholds,
    ReadabilityMetrics,
    EngagementMetrics,
    SEOMetrics,
    ScoreCategory,
    get_content_quality_scorer
)
from halcytone_content_generator.services.ai_content_enhancer import ContentType


class TestReadabilityMetrics:
    """Test readability metrics calculations"""

    def test_readability_metrics_initialization(self):
        """Test readability metrics can be created"""
        metrics = ReadabilityMetrics(
            flesch_reading_ease=75.0,
            flesch_kincaid_grade=8.0,
            gunning_fog_index=10.0,
            automated_readability_index=8.5,
            coleman_liau_index=9.0,
            average_sentence_length=15.0,
            average_syllables_per_word=1.5,
            complex_words_percentage=10.0,
            passive_voice_percentage=5.0
        )

        assert metrics.flesch_reading_ease == 75.0
        assert metrics.flesch_kincaid_grade == 8.0

    def test_overall_readability_score_calculation(self):
        """Test overall readability score calculation"""
        metrics = ReadabilityMetrics(
            flesch_reading_ease=75.0,
            flesch_kincaid_grade=8.0,
            gunning_fog_index=10.0,
            automated_readability_index=8.5,
            coleman_liau_index=9.0,
            average_sentence_length=15.0,
            average_syllables_per_word=1.5,
            complex_words_percentage=10.0,
            passive_voice_percentage=5.0
        )

        score = metrics.overall_readability_score
        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_readability_score_with_penalties(self):
        """Test readability score with high passive voice and complex words"""
        metrics = ReadabilityMetrics(
            flesch_reading_ease=75.0,
            flesch_kincaid_grade=8.0,
            gunning_fog_index=10.0,
            automated_readability_index=8.5,
            coleman_liau_index=9.0,
            average_sentence_length=15.0,
            average_syllables_per_word=1.5,
            complex_words_percentage=50.0,  # High complex words
            passive_voice_percentage=30.0   # High passive voice
        )

        score = metrics.overall_readability_score
        assert score < 75.0  # Should be penalized


class TestEngagementMetrics:
    """Test engagement metrics calculations"""

    def test_engagement_metrics_initialization(self):
        """Test engagement metrics can be created"""
        metrics = EngagementMetrics(
            emotional_words_count=5,
            power_words_count=3,
            question_count=2,
            exclamation_count=1,
            personal_pronouns_count=8,
            sensory_words_count=2,
            urgency_indicators_count=1,
            social_proof_indicators=1,
            storytelling_elements=2,
            curiosity_triggers=1
        )

        assert metrics.emotional_words_count == 5
        assert metrics.power_words_count == 3

    def test_engagement_score_calculation(self):
        """Test engagement score calculation with various factors"""
        metrics = EngagementMetrics(
            emotional_words_count=5,
            power_words_count=6,
            question_count=2,
            exclamation_count=1,
            personal_pronouns_count=9,
            sensory_words_count=3,
            urgency_indicators_count=1,
            social_proof_indicators=2,
            storytelling_elements=1,
            curiosity_triggers=1
        )

        score = metrics.engagement_score
        assert 0 <= score <= 100
        assert score > 50  # Should be reasonably high with these factors

    def test_engagement_score_low_factors(self):
        """Test engagement score with low factor counts"""
        metrics = EngagementMetrics(
            emotional_words_count=0,
            power_words_count=0,
            question_count=0,
            exclamation_count=0,
            personal_pronouns_count=0,
            sensory_words_count=0,
            urgency_indicators_count=0,
            social_proof_indicators=0,
            storytelling_elements=0,
            curiosity_triggers=0
        )

        score = metrics.engagement_score
        assert score == 0.0


class TestSEOMetrics:
    """Test SEO metrics calculations"""

    def test_seo_metrics_initialization(self):
        """Test SEO metrics can be created"""
        metrics = SEOMetrics(
            keyword_density={'wellness': 2.5, 'breathscape': 1.8},
            title_optimization_score=85.0,
            meta_description_score=75.0,
            header_structure_score=80.0,
            internal_link_opportunities=3,
            external_link_quality=70.0,
            image_alt_optimization=60.0,
            content_length_score=90.0,
            semantic_keywords_count=5
        )

        assert metrics.keyword_density['wellness'] == 2.5
        assert metrics.title_optimization_score == 85.0

    def test_seo_score_calculation(self):
        """Test SEO score calculation"""
        metrics = SEOMetrics(
            keyword_density={'wellness': 2.5},
            title_optimization_score=85.0,
            meta_description_score=75.0,
            header_structure_score=80.0,
            internal_link_opportunities=3,
            external_link_quality=70.0,
            image_alt_optimization=60.0,
            content_length_score=90.0,
            semantic_keywords_count=5
        )

        score = metrics.seo_score
        assert 0 <= score <= 100


class TestQualityThresholds:
    """Test quality threshold system"""

    @pytest.fixture
    def thresholds(self):
        """Create quality thresholds for testing"""
        return QualityThresholds()

    def test_threshold_initialization(self, thresholds):
        """Test threshold system initializes correctly"""
        assert QualityLevel.EXCELLENT.value in thresholds.thresholds
        assert QualityLevel.GOOD.value in thresholds.thresholds
        assert QualityLevel.FAIR.value in thresholds.thresholds
        assert QualityLevel.POOR.value in thresholds.thresholds

    def test_get_threshold_basic(self, thresholds):
        """Test getting basic threshold"""
        threshold = thresholds.get_threshold(QualityLevel.EXCELLENT, "overall_score")
        assert threshold == 90.0

    def test_get_threshold_with_content_type_adjustment(self, thresholds):
        """Test threshold adjustment for content type"""
        # Email should have higher engagement threshold
        email_threshold = thresholds.get_threshold(
            QualityLevel.GOOD, "engagement", ContentType.EMAIL
        )
        base_threshold = thresholds.get_threshold(QualityLevel.GOOD, "engagement")

        assert email_threshold > base_threshold

    def test_classify_quality_excellent(self, thresholds):
        """Test quality classification for excellent score"""
        quality = thresholds.classify_quality(95.0, "overall_score")
        assert quality == QualityLevel.EXCELLENT

    def test_classify_quality_poor(self, thresholds):
        """Test quality classification for poor score"""
        quality = thresholds.classify_quality(30.0, "overall_score")
        assert quality == QualityLevel.POOR

    def test_classify_quality_critical(self, thresholds):
        """Test quality classification for critical score"""
        quality = thresholds.classify_quality(10.0, "overall_score")
        assert quality == QualityLevel.CRITICAL


class TestContentQualityScorer:
    """Test content quality scoring service"""

    @pytest.fixture
    def scorer(self):
        """Create content quality scorer for testing"""
        return ContentQualityScorer()

    def test_scorer_initialization(self, scorer):
        """Test scorer initializes correctly"""
        assert scorer.settings is not None
        assert scorer.thresholds is not None
        assert scorer.emotional_words is not None
        assert scorer.power_words is not None
        assert len(scorer.emotional_words) > 0
        assert len(scorer.power_words) > 0

    def test_word_lists_loaded(self, scorer):
        """Test that word lists are properly loaded"""
        assert "amazing" in scorer.emotional_words
        assert "you" in scorer.power_words
        assert "see" in scorer.sensory_words
        assert "now" in scorer.urgency_indicators

    @pytest.mark.asyncio
    async def test_score_content_basic(self, scorer):
        """Test basic content scoring"""
        content = """
        Amazing Wellness Journey with Breathscape

        Discover how Breathscape technology can transform your wellness routine.
        Our innovative breathing exercises help you achieve better health and mindfulness.

        Join thousands of users who have improved their wellbeing with our app.
        Start your journey today and feel the difference!
        """

        with patch.object(scorer, 'ai_enhancer_instance') as mock_ai:
            mock_ai.is_configured.return_value = False

            score = await scorer.score_content(content, ContentType.WEB, include_ai_analysis=False)

            assert isinstance(score, QualityScore)
            assert 0 <= score.overall_score <= 100
            assert score.quality_level in QualityLevel
            assert len(score.improvement_suggestions) > 0

    @pytest.mark.asyncio
    async def test_score_content_with_ai_analysis(self, scorer):
        """Test content scoring with AI analysis"""
        content = "Test content for AI analysis"

        # Mock AI enhancer
        mock_ai_score = Mock()
        mock_ai_score.overall_score = 85.0

        with patch.object(scorer, 'ai_enhancer_instance') as mock_ai:
            mock_ai.is_configured.return_value = True
            mock_ai.score_content_quality = AsyncMock(return_value=mock_ai_score)

            score = await scorer.score_content(content, ContentType.EMAIL, include_ai_analysis=True)

            assert score.ai_assessment_score == 85.0
            mock_ai.score_content_quality.assert_called_once()

    def test_calculate_readability_metrics_simple(self, scorer):
        """Test readability metrics calculation with simple content"""
        content = "This is a simple sentence. This is another simple sentence."

        metrics = scorer._calculate_readability_metrics(content)

        assert isinstance(metrics, ReadabilityMetrics)
        assert metrics.average_sentence_length > 0
        assert metrics.average_syllables_per_word > 0
        assert 0 <= metrics.flesch_reading_ease <= 100

    def test_calculate_readability_metrics_complex(self, scorer):
        """Test readability metrics with complex content"""
        content = """
        The implementation of sophisticated technological methodologies necessitates
        comprehensive understanding of multifaceted algorithmic processes that facilitate
        optimization of user experience through revolutionary advancement in wellness analytics.
        """

        metrics = scorer._calculate_readability_metrics(content)

        # Should have lower readability due to complex words and long sentences
        assert metrics.complex_words_percentage > 10
        assert metrics.average_sentence_length > 15

    def test_calculate_engagement_metrics(self, scorer):
        """Test engagement metrics calculation"""
        content = """
        You will be amazed by this incredible breakthrough!
        Discover the secret to transforming your wellness journey.
        Can you imagine feeling this energetic every day?
        Join thousands who have experienced remarkable results.
        """

        metrics = scorer._calculate_engagement_metrics(content)

        assert metrics.emotional_words_count > 0  # "amazed", "incredible"
        assert metrics.power_words_count > 0      # "you", "discover", "secret"
        assert metrics.question_count > 0         # "Can you imagine..."
        assert metrics.personal_pronouns_count > 0 # "you", "your"

    def test_calculate_seo_metrics(self, scorer):
        """Test SEO metrics calculation"""
        content = """
        # Ultimate Guide to Wellness Technology

        ## Introduction to Breathscape

        Breathscape offers innovative wellness solutions for modern users.
        Our technology helps you track breathing patterns and improve mindfulness.

        ### Key Features
        - Real-time analysis
        - Personalized recommendations
        - Progress tracking
        """

        metrics = scorer._calculate_seo_metrics(content, ContentType.WEB)

        assert isinstance(metrics, SEOMetrics)
        assert metrics.header_structure_score > 0  # Has headers
        assert metrics.content_length_score > 0
        assert metrics.semantic_keywords_count >= 0

    def test_calculate_brand_alignment_score(self, scorer):
        """Test brand alignment scoring"""
        breathscape_content = """
        Breathscape wellness technology empowers users with innovative mindfulness solutions.
        Our data-driven approach to mental health creates personalized experiences for better wellbeing.
        """

        generic_content = """
        This is generic content about random topics that have nothing to do with wellness,
        technology, or any specific brand values.
        """

        breathscape_score = scorer._calculate_brand_alignment_score(breathscape_content)
        generic_score = scorer._calculate_brand_alignment_score(generic_content)

        assert breathscape_score > generic_score
        assert breathscape_score > 50  # Should score well for brand alignment

    def test_calculate_structure_score_email(self, scorer):
        """Test structure scoring for email content"""
        well_structured_email = """
        Subject: Transform Your Wellness Journey Today

        Hi [Name],

        I hope this email finds you well. I wanted to share an exciting opportunity
        to enhance your wellness routine with Breathscape technology.

        Here's what you'll discover:
        - Personalized breathing exercises
        - Real-time progress tracking
        - Mindfulness insights

        Ready to get started? Click here to begin your free trial.

        Best regards,
        The Breathscape Team
        """

        score = scorer._calculate_structure_score(well_structured_email, ContentType.EMAIL)
        assert score > 70  # Should score well for good email structure

    def test_calculate_clarity_score(self, scorer):
        """Test clarity scoring"""
        clear_content = """
        Our app helps you breathe better. It tracks your patterns.
        You get personalized tips. This improves your wellness.
        """

        unclear_content = """
        The implementation of our sophisticated algorithmic methodology facilitates
        the optimization of respiratory functionalities through comprehensive analysis
        of biometric indicators, consequently enabling personalized recommendations.
        """

        clear_score = scorer._calculate_clarity_score(clear_content)
        unclear_score = scorer._calculate_clarity_score(unclear_content)

        assert clear_score > unclear_score

    def test_split_sentences(self, scorer):
        """Test sentence splitting functionality"""
        content = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = scorer._split_sentences(content)

        assert len(sentences) == 4
        assert "First sentence" in sentences[0]

    def test_split_words(self, scorer):
        """Test word splitting functionality"""
        content = "Hello world, this is a test!"
        words = scorer._split_words(content)

        assert "hello" in words
        assert "world" in words
        assert "test" in words
        assert "," not in words  # Punctuation should be removed

    def test_count_syllables(self, scorer):
        """Test syllable counting"""
        assert scorer._count_syllables("cat") == 1
        assert scorer._count_syllables("jumping") == 2
        assert scorer._count_syllables("beautiful") == 3
        assert scorer._count_syllables("technology") == 4

    def test_count_passive_voice(self, scorer):
        """Test passive voice detection"""
        active_content = "We develop innovative solutions. Users love our technology."
        passive_content = "Solutions are developed by us. Our technology is loved by users."

        active_count = scorer._count_passive_voice(active_content)
        passive_count = scorer._count_passive_voice(passive_content)

        assert passive_count > active_count

    def test_score_content_length_appropriate(self, scorer):
        """Test content length scoring for different types"""
        # Twitter content (should be short)
        twitter_content = "Amazing wellness tip for your day! #breathscape #wellness"
        twitter_score = scorer._score_content_length(twitter_content, ContentType.SOCIAL_TWITTER)
        assert twitter_score > 70  # Appropriate length

        # Web content (should be longer)
        web_content = " ".join(["Comprehensive wellness guide."] * 100)  # ~300 words
        web_score = scorer._score_content_length(web_content, ContentType.WEB)
        assert web_score > 70  # Appropriate length

    def test_generate_improvement_suggestions(self, scorer):
        """Test improvement suggestion generation"""
        # Low scoring categories
        category_scores = {
            ScoreCategory.READABILITY: 30.0,
            ScoreCategory.ENGAGEMENT: 40.0,
            ScoreCategory.SEO_OPTIMIZATION: 80.0,
            ScoreCategory.BRAND_ALIGNMENT: 85.0,
            ScoreCategory.STRUCTURE: 35.0,
            ScoreCategory.CLARITY: 45.0
        }

        suggestions = scorer._generate_improvement_suggestions(
            category_scores, ContentType.WEB, QualityLevel.FAIR
        )

        assert len(suggestions) > 0
        assert len(suggestions) <= 5  # Should be limited
        # Should focus on lowest scoring categories
        suggestion_text = " ".join(suggestions).lower()
        assert any(word in suggestion_text for word in ["readability", "structure", "sentences"])

    @pytest.mark.asyncio
    async def test_score_content_error_handling(self, scorer):
        """Test error handling in content scoring"""
        # Test with None content
        with patch.object(scorer, '_calculate_readability_metrics', side_effect=Exception("Test error")):
            score = await scorer.score_content("test content", ContentType.EMAIL)

            assert score.overall_score == 0.0
            assert score.quality_level == QualityLevel.CRITICAL
            assert "Test error" in score.improvement_suggestions[0]

    def test_get_category_weights(self, scorer):
        """Test category weight calculation for different content types"""
        email_weights = scorer._get_category_weights(ContentType.EMAIL)
        web_weights = scorer._get_category_weights(ContentType.WEB)
        twitter_weights = scorer._get_category_weights(ContentType.SOCIAL_TWITTER)

        # Email should prioritize engagement
        assert email_weights[ScoreCategory.ENGAGEMENT] > web_weights[ScoreCategory.ENGAGEMENT]

        # Web should prioritize SEO
        assert web_weights[ScoreCategory.SEO_OPTIMIZATION] > email_weights[ScoreCategory.SEO_OPTIMIZATION]

        # Twitter should prioritize engagement and clarity
        assert twitter_weights[ScoreCategory.ENGAGEMENT] > web_weights[ScoreCategory.ENGAGEMENT]

    def test_create_detailed_feedback(self, scorer):
        """Test detailed feedback creation"""
        content = "Test content for feedback creation."
        category_scores = {ScoreCategory.READABILITY: 75.0}

        # Create mock metrics
        readability = ReadabilityMetrics(75, 8, 10, 8, 8, 15, 1.5, 10, 5)
        engagement = EngagementMetrics(5, 3, 2, 1, 8, 2, 1, 1, 2, 1)
        seo = SEOMetrics({'test': 2.0}, 75, 70, 80, 2, 70, 60, 85, 3)

        feedback = scorer._create_detailed_feedback(content, category_scores, readability, engagement, seo)

        assert "content_stats" in feedback
        assert "readability_details" in feedback
        assert "engagement_details" in feedback
        assert "seo_details" in feedback
        assert feedback["content_stats"]["word_count"] > 0

    def test_singleton_instance(self):
        """Test singleton pattern for quality scorer"""
        scorer1 = get_content_quality_scorer()
        scorer2 = get_content_quality_scorer()
        assert scorer1 is scorer2


class TestQualityScoreIntegration:
    """Test integration of quality scoring components"""

    @pytest.mark.asyncio
    async def test_comprehensive_scoring_flow(self):
        """Test complete scoring flow with realistic content"""
        scorer = ContentQualityScorer()

        content = """
        # Transform Your Wellness Journey with Breathscape

        Are you ready to revolutionize your approach to mindfulness and breathing?
        Breathscape's innovative technology empowers you to achieve optimal wellness
        through personalized breathing exercises and real-time analytics.

        ## Key Benefits:
        - Personalized breathing programs
        - Real-time biometric tracking
        - Progress insights and recommendations
        - Seamless integration with your routine

        Join thousands of users who have transformed their wellness journey.
        Start your free trial today and experience the Breathscape difference!

        [Get Started Now]
        """

        with patch.object(scorer, 'ai_enhancer_instance') as mock_ai:
            mock_ai.is_configured.return_value = False

            score = await scorer.score_content(content, ContentType.WEB)

            # Verify comprehensive scoring
            assert isinstance(score, QualityScore)
            assert score.overall_score > 0
            assert isinstance(score.readability_metrics, ReadabilityMetrics)
            assert isinstance(score.engagement_metrics, EngagementMetrics)
            assert isinstance(score.seo_metrics, SEOMetrics)

            # Should score reasonably well
            assert score.overall_score > 50
            assert score.brand_alignment_score > 50  # Mentions Breathscape
            assert score.engagement_metrics.engagement_score > 0
            assert score.readability_metrics.overall_readability_score > 0

    @pytest.mark.asyncio
    async def test_scoring_different_content_types(self):
        """Test scoring across different content types"""
        scorer = ContentQualityScorer()

        email_content = """
        Subject: Your Weekly Wellness Update

        Hi Sarah,

        Hope you're having a great week! Here's your personalized wellness insight
        from Breathscape: Your breathing patterns show 15% improvement this week.

        Keep up the amazing progress!

        Best,
        Team Breathscape
        """

        twitter_content = """
        🌟 Amazing breathing tip: Try the 4-7-8 technique for instant calm!
        Breathe in for 4, hold for 7, out for 8. Perfect for stressful moments.
        #Breathscape #Wellness #Mindfulness
        """

        with patch.object(scorer, 'ai_enhancer_instance') as mock_ai:
            mock_ai.is_configured.return_value = False

            email_score = await scorer.score_content(email_content, ContentType.EMAIL)
            twitter_score = await scorer.score_content(twitter_content, ContentType.SOCIAL_TWITTER)

            # Both should score, but with different emphasis
            assert email_score.overall_score > 0
            assert twitter_score.overall_score > 0

            # Twitter should have higher engagement expectations
            assert twitter_score.engagement_metrics.engagement_score >= 0

    def test_quality_level_progression(self):
        """Test that quality levels progress logically"""
        thresholds = QualityThresholds()

        excellent_threshold = thresholds.get_threshold(QualityLevel.EXCELLENT, "overall_score")
        good_threshold = thresholds.get_threshold(QualityLevel.GOOD, "overall_score")
        fair_threshold = thresholds.get_threshold(QualityLevel.FAIR, "overall_score")
        poor_threshold = thresholds.get_threshold(QualityLevel.POOR, "overall_score")

        assert excellent_threshold > good_threshold
        assert good_threshold > fair_threshold
        assert fair_threshold > poor_threshold