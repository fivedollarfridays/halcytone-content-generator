"""
Comprehensive tests for A/B Testing Framework.

Tests cover test creation, variation generation, user assignment, event tracking,
statistical analysis, and test lifecycle management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from statistics import mean

from halcytone_content_generator.services.ab_testing import (
    ABTestingFramework,
    ABTestStatus,
    ABTestType,
    VariationType,
    MetricType,
    ABTestVariation,
    ABTestMetric,
    UserAssignment,
    ABTestEvent,
    ABTestResults,
    ABTest,
    get_ab_testing_framework
)


class TestABTestingFrameworkInitialization:
    """Test framework initialization and setup."""

    @pytest.fixture
    def ab_framework(self):
        """Create A/B testing framework instance."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                AI_ENABLE_AB_TESTING=True,
                AI_MODEL_NAME="gpt-4"
            )
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    framework = ABTestingFramework()
                    return framework

    def test_initialization(self, ab_framework):
        """Test framework initializes correctly."""
        assert ab_framework.tests == {}
        assert ab_framework.user_assignments == {}
        assert ab_framework.test_events == {}
        assert ab_framework.test_results == {}
        assert ab_framework.config is not None

    def test_singleton_pattern(self):
        """Test singleton pattern for framework instance."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings'):
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    instance1 = get_ab_testing_framework()
                    instance2 = get_ab_testing_framework()
                    assert instance1 is instance2


class TestTestCreation:
    """Test A/B test creation functionality."""

    @pytest.fixture
    def ab_framework(self):
        """Create A/B testing framework instance."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_create_basic_test(self, ab_framework):
        """Test creating a basic A/B test."""
        metrics = [
            ABTestMetric(
                metric_type=MetricType.CLICK_THROUGH_RATE,
                name="CTR",
                description="Click through rate",
                primary=True
            )
        ]

        test = await ab_framework.create_test(
            name="Test Email Subject",
            description="Testing different subject lines",
            test_type=ABTestType.SUBJECT_LINE,
            base_content="Check out our new product",
            metrics=metrics,
            variation_count=2
        )

        assert test is not None
        assert test.name == "Test Email Subject"
        assert test.test_type == ABTestType.SUBJECT_LINE
        assert test.status == ABTestStatus.DRAFT
        assert len(test.variations) == 2
        assert test.test_id in ab_framework.tests

    @pytest.mark.asyncio
    async def test_create_test_with_custom_params(self, ab_framework):
        """Test creating test with custom parameters."""
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "Conversion rate", True)]

        test = await ab_framework.create_test(
            name="Landing Page Test",
            description="Test landing page variations",
            test_type=ABTestType.LANDING_PAGE,
            base_content="Original landing page content",
            metrics=metrics,
            variation_count=3,
            traffic_allocation=0.8,
            min_sample_size=200,
            max_duration_days=45,
            metadata={"campaign": "summer_2024"}
        )

        assert test.traffic_allocation == 0.8
        assert test.min_sample_size == 200
        assert test.max_duration_days == 45
        assert test.metadata["campaign"] == "summer_2024"
        assert len(test.variations) == 3

    @pytest.mark.asyncio
    async def test_create_test_generates_unique_id(self, ab_framework):
        """Test that each test gets a unique ID."""
        import asyncio
        metrics = [ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)]

        test1 = await ab_framework.create_test(
            "Test 1", "Desc", ABTestType.CONTENT_VARIATION, "Content", metrics
        )
        # Add tiny delay to ensure different microseconds
        await asyncio.sleep(0.001)
        test2 = await ab_framework.create_test(
            "Test 1", "Desc", ABTestType.CONTENT_VARIATION, "Content", metrics
        )

        assert test1.test_id != test2.test_id
        assert test1.test_id.startswith("test_")
        assert test2.test_id.startswith("test_")

    @pytest.mark.asyncio
    async def test_create_test_initializes_storage(self, ab_framework):
        """Test that test creation initializes storage structures."""
        metrics = [ABTestMetric(MetricType.OPEN_RATE, "OR", "Open rate", True)]

        test = await ab_framework.create_test(
            "Email Test", "Test", ABTestType.EMAIL_TEMPLATE, "Content", metrics
        )

        assert test.test_id in ab_framework.tests
        assert test.test_id in ab_framework.user_assignments
        assert test.test_id in ab_framework.test_events
        assert ab_framework.user_assignments[test.test_id] == []
        assert ab_framework.test_events[test.test_id] == []


class TestVariationGeneration:
    """Test variation generation (both AI and rule-based)."""

    @pytest.fixture
    def ab_framework_ai_enabled(self):
        """Create framework with AI enabled."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=True)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer') as mock_ai:
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    framework = ABTestingFramework()
                    framework.ai_enhancer = mock_ai.return_value
                    return framework

    @pytest.fixture
    def ab_framework_ai_disabled(self):
        """Create framework with AI disabled."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_rule_based_subject_line_variations(self, ab_framework_ai_disabled):
        """Test rule-based subject line variations."""
        variations = ab_framework_ai_disabled._generate_rule_based_variations(
            test_id="test_123",
            test_type=ABTestType.SUBJECT_LINE,
            base_content="New Product Launch",
            variation_count=4
        )

        assert len(variations) == 4
        assert any("🎯" in v.content for v in variations)  # Emoji variant
        assert any("Limited Time" in v.content for v in variations)  # Urgency variant
        assert any(v.content.isupper() for v in variations)  # Uppercase variant
        assert any("Exclusive" in v.content for v in variations)  # Exclusivity variant

    @pytest.mark.asyncio
    async def test_rule_based_cta_variations(self, ab_framework_ai_disabled):
        """Test rule-based CTA button variations."""
        variations = ab_framework_ai_disabled._generate_rule_based_variations(
            test_id="test_123",
            test_type=ABTestType.CTA_BUTTON,
            base_content="Click Here",
            variation_count=3
        )

        assert len(variations) == 3
        cta_texts = [v.content for v in variations]
        assert "Get Started Now" in cta_texts
        assert "Try It Free" in cta_texts
        assert "Learn More" in cta_texts

    @pytest.mark.asyncio
    async def test_rule_based_content_variations(self, ab_framework_ai_disabled):
        """Test rule-based content variations."""
        variations = ab_framework_ai_disabled._generate_rule_based_variations(
            test_id="test_123",
            test_type=ABTestType.CONTENT_VARIATION,
            base_content="This is great content.",
            variation_count=4
        )

        assert len(variations) == 4
        assert variations[0].content == "**Enhanced:** This is great content."
        assert "!" in variations[1].content  # Exclamation variant
        assert "Don't miss out" in variations[2].content  # Urgency variant
        assert "🌟" in variations[3].content  # Emoji variant

    @pytest.mark.asyncio
    async def test_ai_variation_generation_success(self, ab_framework_ai_enabled):
        """Test successful AI variation generation."""
        mock_enhanced = Mock()
        mock_enhanced.enhanced_content = "AI-enhanced content variation"
        mock_enhanced.enhancement_score = 0.85
        ab_framework_ai_enabled.ai_enhancer.enhance_content = AsyncMock(return_value=mock_enhanced)

        variations = await ab_framework_ai_enabled._generate_ai_variations(
            test_id="test_ai",
            test_type=ABTestType.CONTENT_VARIATION,
            base_content="Original content",
            variation_count=2
        )

        assert len(variations) == 2
        assert all(v.content == "AI-enhanced content variation" for v in variations)
        assert all(v.metadata["generation_method"] == "ai_enhanced" for v in variations)
        assert all(v.metadata["enhancement_score"] == 0.85 for v in variations)

    @pytest.mark.asyncio
    async def test_ai_variation_fallback_to_rule_based(self, ab_framework_ai_enabled):
        """Test fallback to rule-based when AI fails."""
        ab_framework_ai_enabled.ai_enhancer.enhance_content = AsyncMock(side_effect=Exception("AI Error"))

        variations = await ab_framework_ai_enabled._generate_ai_variations(
            test_id="test_fallback",
            test_type=ABTestType.SUBJECT_LINE,
            base_content="Test Subject",
            variation_count=2
        )

        assert len(variations) == 2
        # Should have fallen back to rule-based generation
        assert all(v.metadata.get("generation_method") == "rule_based" for v in variations)

    def test_create_variation_prompt(self, ab_framework_ai_disabled):
        """Test variation prompt creation."""
        prompt1 = ab_framework_ai_disabled._create_variation_prompt(ABTestType.CONTENT_VARIATION, 1)
        prompt2 = ab_framework_ai_disabled._create_variation_prompt(ABTestType.SUBJECT_LINE, 2)
        prompt3 = ab_framework_ai_disabled._create_variation_prompt(ABTestType.EMAIL_TEMPLATE, 1)

        assert "engaging" in prompt1.lower() or "emotional" in prompt1.lower()
        assert "benefit" in prompt2.lower() or "subject" in prompt2.lower()
        assert "structure" in prompt3.lower() or "flow" in prompt3.lower() or "visual" in prompt3.lower()

    def test_generate_test_id(self, ab_framework_ai_disabled):
        """Test test ID generation."""
        test_id = ab_framework_ai_disabled._generate_test_id("My Test Name")

        assert test_id.startswith("test_")
        assert len(test_id) > 20  # Should include timestamp and hash


class TestUserAssignment:
    """Test user assignment to test variations."""

    @pytest.fixture
    def ab_framework(self):
        """Create framework with active test."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_assign_user_to_active_test(self, ab_framework):
        """Test assigning user to active test."""
        metrics = [ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)]
        test = await ab_framework.create_test(
            "Test", "Test", ABTestType.CONTENT_VARIATION, "Content", metrics
        )
        await ab_framework.start_test(test.test_id)

        assignment = await ab_framework.assign_user_to_test("user_123", test.test_id)

        assert assignment is not None
        assert assignment.user_id == "user_123"
        assert assignment.test_id == test.test_id
        assert assignment.variation_id in [v.variation_id for v in test.variations]

    @pytest.mark.asyncio
    async def test_assign_user_returns_none_for_inactive_test(self, ab_framework):
        """Test that assignment returns None for draft test."""
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", True)]
        test = await ab_framework.create_test(
            "Test", "Test", ABTestType.LANDING_PAGE, "Content", metrics
        )

        # Test is in DRAFT status
        assignment = await ab_framework.assign_user_to_test("user_456", test.test_id)

        assert assignment is None

    @pytest.mark.asyncio
    async def test_assign_user_returns_none_for_nonexistent_test(self, ab_framework):
        """Test that assignment returns None for non-existent test."""
        assignment = await ab_framework.assign_user_to_test("user_789", "nonexistent_test")

        assert assignment is None

    @pytest.mark.asyncio
    async def test_user_assignment_consistency(self, ab_framework):
        """Test that user gets same variation on multiple assignments."""
        metrics = [ABTestMetric(MetricType.ENGAGEMENT_RATE, "ER", "ER", True)]
        test = await ab_framework.create_test(
            "Test", "Test", ABTestType.EMAIL_TEMPLATE, "Content", metrics
        )
        await ab_framework.start_test(test.test_id)

        assignment1 = await ab_framework.assign_user_to_test("user_consistent", test.test_id)
        assignment2 = await ab_framework.assign_user_to_test("user_consistent", test.test_id)

        assert assignment1.variation_id == assignment2.variation_id

    @pytest.mark.asyncio
    async def test_force_variation_assignment(self, ab_framework):
        """Test forcing user to specific variation."""
        metrics = [ABTestMetric(MetricType.OPEN_RATE, "OR", "OR", True)]
        test = await ab_framework.create_test(
            "Test", "Test", ABTestType.SUBJECT_LINE, "Content", metrics
        )
        await ab_framework.start_test(test.test_id)

        forced_variation_id = test.variations[0].variation_id
        assignment = await ab_framework.assign_user_to_test(
            "user_forced", test.test_id, force_variation=forced_variation_id
        )

        assert assignment is not None
        assert assignment.variation_id == forced_variation_id
        assert assignment.metadata["assignment_method"] == "forced"

    @pytest.mark.asyncio
    async def test_traffic_allocation_controls_inclusion(self, ab_framework):
        """Test that traffic allocation controls user inclusion."""
        metrics = [ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)]
        test = await ab_framework.create_test(
            "Test", "Test", ABTestType.CONTENT_VARIATION, "Content", metrics,
            traffic_allocation=0.5  # 50% of users
        )
        await ab_framework.start_test(test.test_id)

        # Test multiple users - some should be included, some not
        assignments = []
        for i in range(20):
            assignment = await ab_framework.assign_user_to_test(f"user_{i}", test.test_id)
            assignments.append(assignment)

        # With 50% allocation, approximately half should be assigned (allow some variance)
        assigned_count = sum(1 for a in assignments if a is not None)
        assert 5 <= assigned_count <= 15  # Reasonable range for 20 users at 50%

    def test_should_include_user_deterministic(self, ab_framework):
        """Test that user inclusion is deterministic."""
        test = ABTest(
            test_id="test_deterministic",
            name="Test",
            description="Test",
            test_type=ABTestType.CONTENT_VARIATION,
            variations=[],
            metrics=[],
            traffic_allocation=0.5
        )

        # Same user should always get same inclusion decision
        result1 = ab_framework._should_include_user("user_det_123", test)
        result2 = ab_framework._should_include_user("user_det_123", test)

        assert result1 == result2

    def test_select_variation_deterministic(self, ab_framework):
        """Test that variation selection is deterministic."""
        variations = [
            ABTestVariation("v1", VariationType.CONTROL, "Control", "Content", traffic_allocation=0.5),
            ABTestVariation("v2", VariationType.VARIANT_A, "Variant A", "Content", traffic_allocation=0.5)
        ]
        test = ABTest(
            test_id="test_var_selection",
            name="Test",
            description="Test",
            test_type=ABTestType.CONTENT_VARIATION,
            variations=variations,
            metrics=[]
        )

        # Same user should always get same variation
        var1 = ab_framework._select_variation("user_var_456", test)
        var2 = ab_framework._select_variation("user_var_456", test)

        assert var1 == var2

    def test_get_user_assignment(self, ab_framework):
        """Test retrieving user assignment."""
        assignment = UserAssignment("user_get", "test_get", "var_get")
        ab_framework.user_assignments["test_get"] = [assignment]

        retrieved = ab_framework._get_user_assignment("user_get", "test_get")

        assert retrieved == assignment
        assert retrieved.user_id == "user_get"

    def test_get_user_assignment_returns_none_when_not_found(self, ab_framework):
        """Test that get_user_assignment returns None when not found."""
        ab_framework.user_assignments["test_empty"] = []

        retrieved = ab_framework._get_user_assignment("user_missing", "test_empty")

        assert retrieved is None

    def test_get_user_test_assignment(self, ab_framework):
        """Test get_user_test_assignment method."""
        assignment = UserAssignment("user_public", "test_public", "var_public")
        ab_framework.user_assignments["test_public"] = [assignment]

        variation_id = ab_framework.get_user_test_assignment("user_public", "test_public")

        assert variation_id == "var_public"

    def test_get_user_test_assignment_returns_none_when_not_assigned(self, ab_framework):
        """Test get_user_test_assignment returns None for unassigned user."""
        ab_framework.user_assignments["test_none"] = []

        variation_id = ab_framework.get_user_test_assignment("user_none", "test_none")

        assert variation_id is None


class TestEventTracking:
    """Test event tracking functionality."""

    @pytest.fixture
    def ab_framework_with_assignment(self):
        """Create framework with test and user assignment."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    framework = ABTestingFramework()
                    # Setup test with assignment
                    framework.tests["test_events"] = ABTest(
                        test_id="test_events",
                        name="Event Test",
                        description="Test",
                        test_type=ABTestType.CONTENT_VARIATION,
                        variations=[],
                        metrics=[],
                        status=ABTestStatus.ACTIVE
                    )
                    framework.user_assignments["test_events"] = [
                        UserAssignment("user_event", "test_events", "var_event")
                    ]
                    framework.test_events["test_events"] = []
                    return framework

    @pytest.mark.asyncio
    async def test_track_event_successfully(self, ab_framework_with_assignment):
        """Test successful event tracking."""
        result = await ab_framework_with_assignment.track_event(
            user_id="user_event",
            test_id="test_events",
            metric_type=MetricType.CLICK_THROUGH_RATE,
            value=1.0
        )

        assert result is True
        assert len(ab_framework_with_assignment.test_events["test_events"]) == 1
        event = ab_framework_with_assignment.test_events["test_events"][0]
        assert event.user_id == "user_event"
        assert event.test_id == "test_events"
        assert event.metric_type == MetricType.CLICK_THROUGH_RATE
        assert event.value == 1.0

    @pytest.mark.asyncio
    async def test_track_event_with_metadata(self, ab_framework_with_assignment):
        """Test tracking event with metadata."""
        metadata = {"source": "email", "campaign": "summer"}

        result = await ab_framework_with_assignment.track_event(
            user_id="user_event",
            test_id="test_events",
            metric_type=MetricType.CONVERSION_RATE,
            value=2.5,
            metadata=metadata
        )

        assert result is True
        event = ab_framework_with_assignment.test_events["test_events"][0]
        assert event.metadata == metadata

    @pytest.mark.asyncio
    async def test_track_event_returns_false_for_nonexistent_test(self, ab_framework_with_assignment):
        """Test that tracking returns False for non-existent test."""
        result = await ab_framework_with_assignment.track_event(
            user_id="user_event",
            test_id="nonexistent_test",
            metric_type=MetricType.ENGAGEMENT_RATE,
            value=1.0
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_track_event_returns_false_for_unassigned_user(self, ab_framework_with_assignment):
        """Test that tracking returns False for user not assigned to test."""
        result = await ab_framework_with_assignment.track_event(
            user_id="user_not_assigned",
            test_id="test_events",
            metric_type=MetricType.CLICK_THROUGH_RATE,
            value=1.0
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_track_multiple_events(self, ab_framework_with_assignment):
        """Test tracking multiple events for same user."""
        await ab_framework_with_assignment.track_event(
            "user_event", "test_events", MetricType.OPEN_RATE, 1.0
        )
        await ab_framework_with_assignment.track_event(
            "user_event", "test_events", MetricType.CLICK_THROUGH_RATE, 1.0
        )
        await ab_framework_with_assignment.track_event(
            "user_event", "test_events", MetricType.CONVERSION_RATE, 1.0
        )

        assert len(ab_framework_with_assignment.test_events["test_events"]) == 3

    def test_generate_event_id(self, ab_framework_with_assignment):
        """Test event ID generation."""
        event_id = ab_framework_with_assignment._generate_event_id()

        assert event_id.startswith("event_")
        assert len(event_id) > 10


class TestStatisticalAnalysis:
    """Test statistical analysis and results calculation."""

    @pytest.fixture
    def ab_framework_with_results(self):
        """Create framework with test, assignments, and events."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    framework = ABTestingFramework()

                    # Create test with variations
                    variations = [
                        ABTestVariation("control", VariationType.CONTROL, "Control", "Control content", traffic_allocation=0.5),
                        ABTestVariation("variant_a", VariationType.VARIANT_A, "Variant A", "Variant A content", traffic_allocation=0.5)
                    ]
                    metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "Conversion Rate", primary=True)]

                    framework.tests["test_analysis"] = ABTest(
                        test_id="test_analysis",
                        name="Analysis Test",
                        description="Test for analysis",
                        test_type=ABTestType.CONTENT_VARIATION,
                        variations=variations,
                        metrics=metrics,
                        status=ABTestStatus.ACTIVE,
                        started_at=datetime.utcnow() - timedelta(days=7)
                    )

                    # Create assignments (50 control, 50 variant)
                    framework.user_assignments["test_analysis"] = []
                    for i in range(50):
                        framework.user_assignments["test_analysis"].append(
                            UserAssignment(f"user_control_{i}", "test_analysis", "control")
                        )
                    for i in range(50):
                        framework.user_assignments["test_analysis"].append(
                            UserAssignment(f"user_variant_{i}", "test_analysis", "variant_a")
                        )

                    # Create events (20% conversion for control, 30% for variant)
                    framework.test_events["test_analysis"] = []
                    for i in range(10):  # 10 conversions out of 50
                        framework.test_events["test_analysis"].append(
                            ABTestEvent(f"event_c_{i}", f"user_control_{i}", "test_analysis", "control",
                                      MetricType.CONVERSION_RATE, 1.0)
                        )
                    for i in range(15):  # 15 conversions out of 50
                        framework.test_events["test_analysis"].append(
                            ABTestEvent(f"event_v_{i}", f"user_variant_{i}", "test_analysis", "variant_a",
                                      MetricType.CONVERSION_RATE, 1.0)
                        )

                    return framework

    @pytest.mark.asyncio
    async def test_analyze_test_results(self, ab_framework_with_results):
        """Test analyzing test results."""
        results = await ab_framework_with_results.analyze_test_results("test_analysis")

        assert results is not None
        assert results.test_id == "test_analysis"
        assert "control" in results.variation_results
        assert "variant_a" in results.variation_results
        assert results.sample_sizes["control"] == 50
        assert results.sample_sizes["variant_a"] == 50

    @pytest.mark.asyncio
    async def test_analyze_returns_none_for_nonexistent_test(self, ab_framework_with_results):
        """Test that analyze returns None for non-existent test."""
        results = await ab_framework_with_results.analyze_test_results("nonexistent")

        assert results is None

    def test_calculate_variation_metrics_conversion_rate(self, ab_framework_with_results):
        """Test calculation of conversion rate metric."""
        # 10 unique users converted out of 50
        events = [
            ABTestEvent(f"e{i}", f"user_{i}", "test", "var", MetricType.CONVERSION_RATE, 1.0)
            for i in range(10)
        ]
        assignments = [UserAssignment(f"user_{i}", "test", "var") for i in range(50)]
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", True)]

        results = ab_framework_with_results._calculate_variation_metrics(events, assignments, metrics)

        assert results["conversion_rate"] == 10 / 50  # 0.2 or 20%

    def test_calculate_variation_metrics_revenue(self, ab_framework_with_results):
        """Test calculation of revenue metric."""
        events = [
            ABTestEvent("e1", "user_1", "test", "var", MetricType.REVENUE, 100.0),
            ABTestEvent("e2", "user_2", "test", "var", MetricType.REVENUE, 150.0),
            ABTestEvent("e3", "user_3", "test", "var", MetricType.REVENUE, 200.0),
        ]
        assignments = [UserAssignment(f"user_{i}", "test", "var") for i in range(10)]
        metrics = [ABTestMetric(MetricType.REVENUE, "Revenue", "Total Revenue")]

        results = ab_framework_with_results._calculate_variation_metrics(events, assignments, metrics)

        assert results["revenue"] == 450.0  # Sum of all revenue

    def test_calculate_variation_metrics_time_on_page(self, ab_framework_with_results):
        """Test calculation of time on page metric."""
        events = [
            ABTestEvent("e1", "user_1", "test", "var", MetricType.TIME_ON_PAGE, 30.0),
            ABTestEvent("e2", "user_2", "test", "var", MetricType.TIME_ON_PAGE, 45.0),
            ABTestEvent("e3", "user_3", "test", "var", MetricType.TIME_ON_PAGE, 60.0),
        ]
        assignments = [UserAssignment(f"user_{i}", "test", "var") for i in range(10)]
        metrics = [ABTestMetric(MetricType.TIME_ON_PAGE, "Time", "Avg Time")]

        results = ab_framework_with_results._calculate_variation_metrics(events, assignments, metrics)

        assert results["time_on_page"] == 45.0  # Average of 30, 45, 60

    def test_calculate_statistical_significance(self, ab_framework_with_results):
        """Test statistical significance calculation."""
        control_results = {"conversion_rate": 0.10}  # 10%
        variant_results = {"conversion_rate": 0.25}   # 25% - significant difference
        control_sample = 100
        variant_sample = 100

        is_significant = ab_framework_with_results._calculate_statistical_significance(
            control_results, variant_results, control_sample, variant_sample, 0.05
        )

        # With 10% vs 25% conversion rate and 100 samples each, should be significant
        assert is_significant is True

    def test_calculate_statistical_significance_insufficient_sample(self, ab_framework_with_results):
        """Test statistical significance with insufficient sample size."""
        control_results = {"conversion_rate": 0.10}
        variant_results = {"conversion_rate": 0.25}

        is_significant = ab_framework_with_results._calculate_statistical_significance(
            control_results, variant_results, 20, 20, 0.05
        )

        assert is_significant is False  # Sample size too small

    def test_calculate_confidence_intervals(self, ab_framework_with_results):
        """Test confidence interval calculation."""
        results = {"conversion_rate": 0.20}  # 20% conversion
        sample_size = 100

        intervals = ab_framework_with_results._calculate_confidence_intervals(results, sample_size)

        assert "conversion_rate" in intervals
        lower, upper = intervals["conversion_rate"]
        assert lower < 0.20  # Lower bound below point estimate
        assert upper > 0.20  # Upper bound above point estimate
        assert 0 <= lower <= 1
        assert 0 <= upper <= 1

    def test_calculate_confidence_intervals_insufficient_sample(self, ab_framework_with_results):
        """Test confidence intervals with insufficient sample."""
        results = {"conversion_rate": 0.20}
        sample_size = 20  # Too small

        intervals = ab_framework_with_results._calculate_confidence_intervals(results, sample_size)

        assert intervals == {}  # Should return empty dict

    def test_determine_winner_with_significance(self, ab_framework_with_results):
        """Test winner determination with statistical significance."""
        variation_results = {
            "control": {"conversion_rate": 0.10},
            "variant_a": {"conversion_rate": 0.25}
        }
        statistical_significance = {"variant_a": True}
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", primary=True)]

        winner, recommendation = ab_framework_with_results._determine_winner(
            variation_results, statistical_significance, metrics
        )

        assert winner == "variant_a"
        assert "Significant winner" in recommendation
        assert "improvement" in recommendation.lower()

    def test_determine_winner_without_significance(self, ab_framework_with_results):
        """Test winner determination without statistical significance."""
        variation_results = {
            "control": {"conversion_rate": 0.10},
            "variant_a": {"conversion_rate": 0.11}
        }
        statistical_significance = {"variant_a": False}
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", primary=True)]

        winner, recommendation = ab_framework_with_results._determine_winner(
            variation_results, statistical_significance, metrics
        )

        assert winner is None
        assert "No statistically significant difference" in recommendation


class TestLifecycle:
    """Test test lifecycle management."""

    @pytest.fixture
    def ab_framework(self):
        """Create framework instance."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_start_test_successfully(self, ab_framework):
        """Test starting a draft test."""
        metrics = [ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)]
        test = await ab_framework.create_test(
            "Start Test", "Test", ABTestType.CONTENT_VARIATION, "Content", metrics
        )

        result = await ab_framework.start_test(test.test_id)

        assert result is True
        assert test.status == ABTestStatus.ACTIVE
        assert test.started_at is not None

    @pytest.mark.asyncio
    async def test_start_test_returns_false_for_nonexistent_test(self, ab_framework):
        """Test starting non-existent test returns False."""
        result = await ab_framework.start_test("nonexistent_test")

        assert result is False

    @pytest.mark.asyncio
    async def test_start_test_returns_false_for_non_draft_test(self, ab_framework):
        """Test starting already active test returns False."""
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", True)]
        test = await ab_framework.create_test(
            "Active Test", "Test", ABTestType.LANDING_PAGE, "Content", metrics
        )
        await ab_framework.start_test(test.test_id)

        # Try to start again
        result = await ab_framework.start_test(test.test_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_test_successfully(self, ab_framework):
        """Test stopping an active test."""
        metrics = [ABTestMetric(MetricType.OPEN_RATE, "OR", "OR", True)]
        test = await ab_framework.create_test(
            "Stop Test", "Test", ABTestType.EMAIL_TEMPLATE, "Content", metrics
        )
        await ab_framework.start_test(test.test_id)

        result = await ab_framework.stop_test(test.test_id, reason="Test complete")

        assert result is True
        assert test.status == ABTestStatus.COMPLETED
        assert test.ended_at is not None
        assert test.metadata["stop_reason"] == "Test complete"

    @pytest.mark.asyncio
    async def test_stop_test_returns_false_for_nonexistent_test(self, ab_framework):
        """Test stopping non-existent test returns False."""
        result = await ab_framework.stop_test("nonexistent_test")

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_test_returns_false_for_draft_test(self, ab_framework):
        """Test stopping draft test returns False."""
        metrics = [ABTestMetric(MetricType.ENGAGEMENT_RATE, "ER", "ER", True)]
        test = await ab_framework.create_test(
            "Draft Test", "Test", ABTestType.CTA_BUTTON, "Content", metrics
        )

        result = await ab_framework.stop_test(test.test_id)

        assert result is False

    def test_get_active_tests(self, ab_framework):
        """Test retrieving active tests."""
        test1 = ABTest("t1", "Test 1", "Desc", ABTestType.CONTENT_VARIATION, [], [], status=ABTestStatus.ACTIVE)
        test2 = ABTest("t2", "Test 2", "Desc", ABTestType.SUBJECT_LINE, [], [], status=ABTestStatus.DRAFT)
        test3 = ABTest("t3", "Test 3", "Desc", ABTestType.EMAIL_TEMPLATE, [], [], status=ABTestStatus.ACTIVE)
        test4 = ABTest("t4", "Test 4", "Desc", ABTestType.CTA_BUTTON, [], [], status=ABTestStatus.COMPLETED)

        ab_framework.tests = {"t1": test1, "t2": test2, "t3": test3, "t4": test4}

        active_tests = ab_framework.get_active_tests()

        assert len(active_tests) == 2
        assert all(t.status == ABTestStatus.ACTIVE for t in active_tests)

    def test_get_test_summary(self, ab_framework):
        """Test getting test summary."""
        ab_framework.tests = {
            "t1": ABTest("t1", "T1", "D", ABTestType.CONTENT_VARIATION, [], [], status=ABTestStatus.ACTIVE),
            "t2": ABTest("t2", "T2", "D", ABTestType.SUBJECT_LINE, [], [], status=ABTestStatus.COMPLETED),
            "t3": ABTest("t3", "T3", "D", ABTestType.EMAIL_TEMPLATE, [], [], status=ABTestStatus.ACTIVE),
        }
        ab_framework.user_assignments = {
            "t1": [UserAssignment("u1", "t1", "v1"), UserAssignment("u2", "t1", "v1")],
            "t2": [UserAssignment("u3", "t2", "v2")]
        }
        ab_framework.test_events = {
            "t1": [ABTestEvent("e1", "u1", "t1", "v1", MetricType.CLICK_THROUGH_RATE, 1.0)],
            "t2": [ABTestEvent("e2", "u3", "t2", "v2", MetricType.CONVERSION_RATE, 1.0),
                   ABTestEvent("e3", "u3", "t2", "v2", MetricType.OPEN_RATE, 1.0)]
        }

        summary = ab_framework.get_test_summary()

        assert summary["total_tests"] == 3
        assert summary["active_tests"] == 2
        assert summary["completed_tests"] == 1
        assert summary["total_assignments"] == 3
        assert summary["total_events"] == 3


class TestAnalyticsReporting:
    """Test analytics and reporting functionality."""

    @pytest.fixture
    def ab_framework_with_analytics(self):
        """Create framework with test data for analytics."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    framework = ABTestingFramework()

                    # Create test
                    variations = [
                        ABTestVariation("v1", VariationType.CONTROL, "Control", "Content"),
                        ABTestVariation("v2", VariationType.VARIANT_A, "Variant A", "Content")
                    ]
                    framework.tests["test_analytics"] = ABTest(
                        test_id="test_analytics",
                        name="Analytics Test",
                        description="Test for analytics",
                        test_type=ABTestType.CONTENT_VARIATION,
                        variations=variations,
                        metrics=[ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)],
                        status=ABTestStatus.ACTIVE,
                        started_at=datetime.utcnow() - timedelta(hours=10)
                    )

                    # Add assignments
                    framework.user_assignments["test_analytics"] = [
                        UserAssignment("u1", "test_analytics", "v1"),
                        UserAssignment("u2", "test_analytics", "v1"),
                        UserAssignment("u3", "test_analytics", "v2")
                    ]

                    # Add events
                    framework.test_events["test_analytics"] = [
                        ABTestEvent("e1", "u1", "test_analytics", "v1", MetricType.CLICK_THROUGH_RATE, 1.0),
                        ABTestEvent("e2", "u3", "test_analytics", "v2", MetricType.CLICK_THROUGH_RATE, 1.0)
                    ]

                    # Add results
                    framework.test_results["test_analytics"] = ABTestResults(
                        test_id="test_analytics",
                        variation_results={"v1": {"click_through_rate": 0.5}, "v2": {"click_through_rate": 0.33}},
                        statistical_significance={"v2": False},
                        confidence_intervals={},
                        sample_sizes={"v1": 2, "v2": 1},
                        test_duration=timedelta(hours=10),
                        winner="v1"
                    )

                    return framework

    @pytest.mark.asyncio
    async def test_get_test_analytics(self, ab_framework_with_analytics):
        """Test getting comprehensive test analytics."""
        analytics = await ab_framework_with_analytics.get_test_analytics("test_analytics")

        assert analytics is not None
        assert "test_info" in analytics
        assert "participation" in analytics
        assert "performance" in analytics

    @pytest.mark.asyncio
    async def test_analytics_test_info(self, ab_framework_with_analytics):
        """Test analytics test info section."""
        analytics = await ab_framework_with_analytics.get_test_analytics("test_analytics")

        assert analytics["test_info"]["name"] == "Analytics Test"
        assert analytics["test_info"]["status"] == "active"
        assert analytics["test_info"]["type"] == "content_variation"
        assert analytics["test_info"]["started_at"] is not None
        assert analytics["test_info"]["duration_hours"] > 0

    @pytest.mark.asyncio
    async def test_analytics_participation(self, ab_framework_with_analytics):
        """Test analytics participation section."""
        analytics = await ab_framework_with_analytics.get_test_analytics("test_analytics")

        assert analytics["participation"]["total_assignments"] == 3
        assert analytics["participation"]["total_events"] == 2
        assert "Control" in analytics["participation"]["assignment_by_variation"]
        assert analytics["participation"]["assignment_by_variation"]["Control"] == 2

    @pytest.mark.asyncio
    async def test_analytics_performance(self, ab_framework_with_analytics):
        """Test analytics performance section."""
        analytics = await ab_framework_with_analytics.get_test_analytics("test_analytics")

        assert analytics["performance"]["winner"] == "v1"
        assert "v1" in analytics["performance"]["variation_results"]
        assert "v2" in analytics["performance"]["statistical_significance"]

    @pytest.mark.asyncio
    async def test_get_analytics_returns_empty_for_nonexistent_test(self, ab_framework_with_analytics):
        """Test that analytics returns empty dict for non-existent test."""
        analytics = await ab_framework_with_analytics.get_test_analytics("nonexistent")

        assert analytics == {}


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def ab_framework(self):
        """Create framework instance."""
        with patch('halcytone_content_generator.services.ab_testing.get_settings') as mock_settings:
            mock_settings.return_value = Mock(AI_ENABLE_AB_TESTING=False)
            with patch('halcytone_content_generator.services.ab_testing.AIContentEnhancer'):
                with patch('halcytone_content_generator.services.ab_testing.ContentPersonalizationEngine'):
                    return ABTestingFramework()

    @pytest.mark.asyncio
    async def test_create_test_exception_handling(self, ab_framework):
        """Test that test creation handles exceptions gracefully."""
        # Force an exception during variation generation
        with patch.object(ab_framework, '_generate_variations', side_effect=Exception("Generation error")):
            with pytest.raises(Exception):
                await ab_framework.create_test(
                    "Error Test", "Test", ABTestType.CONTENT_VARIATION, "Content",
                    [ABTestMetric(MetricType.CLICK_THROUGH_RATE, "CTR", "CTR", True)]
                )

    @pytest.mark.asyncio
    async def test_assign_user_exception_handling(self, ab_framework):
        """Test user assignment exception handling."""
        test = ABTest("test_err", "Test", "Desc", ABTestType.CONTENT_VARIATION, [], [], status=ABTestStatus.ACTIVE)
        ab_framework.tests["test_err"] = test

        # Force exception during variation selection
        with patch.object(ab_framework, '_select_variation', side_effect=Exception("Selection error")):
            assignment = await ab_framework.assign_user_to_test("user_err", "test_err")

            assert assignment is None  # Should return None on error

    @pytest.mark.asyncio
    async def test_track_event_exception_handling(self, ab_framework):
        """Test event tracking exception handling."""
        ab_framework.tests["test_event_err"] = ABTest("test_event_err", "T", "D", ABTestType.CONTENT_VARIATION, [], [])
        ab_framework.user_assignments["test_event_err"] = [UserAssignment("u", "test_event_err", "v")]

        # Force exception
        with patch.object(ab_framework, '_generate_event_id', side_effect=Exception("Event ID error")):
            result = await ab_framework.track_event("u", "test_event_err", MetricType.CLICK_THROUGH_RATE)

            assert result is False

    @pytest.mark.asyncio
    async def test_analyze_results_exception_handling(self, ab_framework):
        """Test results analysis exception handling."""
        ab_framework.tests["test_analysis_err"] = ABTest(
            "test_analysis_err", "T", "D", ABTestType.CONTENT_VARIATION,
            [], [], status=ABTestStatus.ACTIVE
        )

        # Force exception during metrics calculation
        with patch.object(ab_framework, '_calculate_variation_metrics', side_effect=Exception("Calc error")):
            results = await ab_framework.analyze_test_results("test_analysis_err")

            # Should still return results but with empty data
            assert results is not None
            assert results.variation_results == {}
            assert results.recommendation == "Insufficient data for analysis"

    @pytest.mark.asyncio
    async def test_stop_test_exception_handling(self, ab_framework):
        """Test stop test exception handling."""
        test = ABTest("test_stop_err", "T", "D", ABTestType.CONTENT_VARIATION, [], [], status=ABTestStatus.ACTIVE)
        ab_framework.tests["test_stop_err"] = test

        # Force exception during analysis
        with patch.object(ab_framework, 'analyze_test_results', side_effect=Exception("Analysis error")):
            result = await ab_framework.stop_test("test_stop_err")

            assert result is False

    def test_calculate_metrics_with_empty_assignments(self, ab_framework):
        """Test metrics calculation with no assignments."""
        results = ab_framework._calculate_variation_metrics(
            [], [], [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR")]
        )

        assert results == {}

    def test_statistical_significance_with_zero_standard_error(self, ab_framework):
        """Test significance calculation when standard error is zero."""
        # When both proportions are 0, SE is 0
        result = ab_framework._calculate_statistical_significance(
            {"metric": 0.0}, {"metric": 0.0}, 100, 100, 0.05
        )

        assert result is False

    def test_determine_winner_with_no_results(self, ab_framework):
        """Test winner determination with no results."""
        winner, recommendation = ab_framework._determine_winner({}, {}, [])

        assert winner is None
        assert "Insufficient data" in recommendation

    def test_determine_winner_with_no_metrics(self, ab_framework):
        """Test winner determination with no metrics defined."""
        winner, recommendation = ab_framework._determine_winner(
            {"v1": {"some_metric": 0.5}}, {}, []
        )

        assert winner is None
        assert "No metrics defined" in recommendation

    def test_determine_winner_control_variation_fallback(self, ab_framework):
        """Test winner determination when control variation not found."""
        variation_results = {"variant_a": {"conversion_rate": 0.25}}
        statistical_significance = {}
        metrics = [ABTestMetric(MetricType.CONVERSION_RATE, "CR", "CR", primary=True)]

        winner, recommendation = ab_framework._determine_winner(
            variation_results, statistical_significance, metrics
        )

        # Should still work without explicit control
        assert winner is None or winner == "variant_a"

    def test_confidence_intervals_for_large_values(self, ab_framework):
        """Test confidence interval calculation for values > 1."""
        results = {"revenue": 1000.0}  # Large value
        sample_size = 100

        intervals = ab_framework._calculate_confidence_intervals(results, sample_size)

        assert "revenue" in intervals
        lower, upper = intervals["revenue"]
        assert lower >= 0  # Should not be negative
        assert lower < 1000.0 < upper  # Should bracket the value

    def test_select_variation_fallback_to_control(self, ab_framework):
        """Test that variation selection falls back to control."""
        # Create test with variations
        variations = [
            ABTestVariation("control", VariationType.CONTROL, "Control", "Content", traffic_allocation=1.0)
        ]
        test = ABTest("test", "T", "D", ABTestType.CONTENT_VARIATION, variations, [])

        # Should always return control when it's the only option
        variation_id = ab_framework._select_variation("any_user", test)

        assert variation_id == "control"
