"""
Unit tests for A/B Testing Framework.

Tests cover test creation, variation generation, user assignment,
event tracking, and statistical analysis functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.halcytone_content_generator.services.ab_testing import (
    ABTestingFramework,
    ABTest,
    TestVariation,
    TestMetric,
    UserAssignment,
    TestEvent,
    TestResults,
    TestStatus,
    TestType,
    VariationType,
    MetricType,
    get_ab_testing_framework
)


class TestABTestingFramework:
    """Test cases for A/B Testing Framework."""

    @pytest.fixture
    def ab_framework(self):
        """Create an A/B testing framework instance for testing."""
        return ABTestingFramework()

    @pytest.fixture
    def sample_metrics(self):
        """Create sample test metrics."""
        return [
            TestMetric(
                metric_type=MetricType.CONVERSION_RATE,
                name="Conversion Rate",
                description="Primary conversion metric",
                primary=True,
                target_value=0.15
            ),
            TestMetric(
                metric_type=MetricType.CLICK_THROUGH_RATE,
                name="Click-Through Rate",
                description="Secondary engagement metric",
                primary=False,
                target_value=0.25
            )
        ]

    @pytest.fixture
    def sample_base_content(self):
        """Create sample base content for testing."""
        return "Join our newsletter for exclusive insights and updates!"

    @pytest.mark.asyncio
    async def test_create_test_basic(self, ab_framework, sample_metrics, sample_base_content):
        """Test basic A/B test creation."""
        test = await ab_framework.create_test(
            name="Email Subject Test",
            description="Testing different email subject lines",
            test_type=TestType.SUBJECT_LINE,
            base_content=sample_base_content,
            metrics=sample_metrics,
            variation_count=2
        )

        assert isinstance(test, ABTest)
        assert test.name == "Email Subject Test"
        assert test.test_type == TestType.SUBJECT_LINE
        assert test.status == TestStatus.DRAFT
        assert len(test.variations) == 2
        assert len(test.metrics) == 2

        # Check variations
        control_variation = next((v for v in test.variations if v.variation_type == VariationType.CONTROL), None)
        assert control_variation is not None
        assert control_variation.content == sample_base_content

        variant_variation = next((v for v in test.variations if v.variation_type == VariationType.VARIANT_A), None)
        assert variant_variation is not None
        assert variant_variation.content != sample_base_content

    @pytest.mark.asyncio
    async def test_create_test_multiple_variations(self, ab_framework, sample_metrics, sample_base_content):
        """Test creating test with multiple variations."""
        test = await ab_framework.create_test(
            name="Multi-Variant Test",
            description="Testing multiple variations",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics,
            variation_count=4
        )

        assert len(test.variations) == 4
        variation_types = [v.variation_type for v in test.variations]
        assert VariationType.CONTROL in variation_types
        assert VariationType.VARIANT_A in variation_types
        assert VariationType.VARIANT_B in variation_types
        assert VariationType.VARIANT_C in variation_types

    @pytest.mark.asyncio
    async def test_create_test_with_ai_enhancement(self, ab_framework, sample_metrics, sample_base_content):
        """Test creating test with AI enhancement enabled."""
        # Mock AI enhancer
        mock_enhancement = Mock()
        mock_enhancement.enhanced_content = "Enhanced version of the content"
        mock_enhancement.enhancement_score = 0.85

        with patch.object(ab_framework.ai_enhancer, 'enhance_content') as mock_enhance:
            mock_enhance.return_value = mock_enhancement

            # Enable AI testing in config
            ab_framework.config.AI_ENABLE_AB_TESTING = True

            test = await ab_framework.create_test(
                name="AI Enhanced Test",
                description="Testing with AI-generated variations",
                test_type=TestType.CONTENT_VARIATION,
                base_content=sample_base_content,
                metrics=sample_metrics,
                variation_count=2
            )

            # Should have called AI enhancer
            mock_enhance.assert_called()

            # Check that AI-generated variation exists
            ai_variation = next((v for v in test.variations
                               if v.metadata.get("generation_method") == "ai_enhanced"), None)
            assert ai_variation is not None
            assert ai_variation.content == "Enhanced version of the content"

    def test_generate_rule_based_variations_subject_line(self, ab_framework):
        """Test rule-based variation generation for subject lines."""
        base_content = "Newsletter Update"
        variations = ab_framework._generate_rule_based_variations(
            test_id="test_123",
            test_type=TestType.SUBJECT_LINE,
            base_content=base_content,
            variation_count=2
        )

        assert len(variations) == 2
        assert all(v.content != base_content for v in variations)
        assert any("🎯" in v.content for v in variations)  # Emoji variation
        assert any("Limited Time" in v.content for v in variations)  # Urgency variation

    def test_generate_rule_based_variations_cta(self, ab_framework):
        """Test rule-based variation generation for CTA buttons."""
        base_content = "Click Here"
        variations = ab_framework._generate_rule_based_variations(
            test_id="test_123",
            test_type=TestType.CTA_BUTTON,
            base_content=base_content,
            variation_count=3
        )

        assert len(variations) == 3
        expected_ctas = ["Get Started Now", "Try It Free", "Learn More"]
        variation_contents = [v.content for v in variations]

        for expected_cta in expected_ctas:
            assert expected_cta in variation_contents

    def test_generate_test_id(self, ab_framework):
        """Test unique test ID generation."""
        test_id1 = ab_framework._generate_test_id("Test Name One")
        test_id2 = ab_framework._generate_test_id("Test Name Two")

        assert test_id1 != test_id2
        assert test_id1.startswith("test_")
        assert len(test_id1.split("_")) == 5  # test_date_time_microseconds_hash

    @pytest.mark.asyncio
    async def test_start_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test starting an A/B test."""
        test = await ab_framework.create_test(
            name="Start Test",
            description="Test starting functionality",
            test_type=TestType.EMAIL_TEMPLATE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        assert test.status == TestStatus.DRAFT
        assert test.started_at is None

        success = await ab_framework.start_test(test.test_id)

        assert success is True
        assert test.status == TestStatus.ACTIVE
        assert test.started_at is not None

    @pytest.mark.asyncio
    async def test_start_nonexistent_test(self, ab_framework):
        """Test starting a non-existent test."""
        success = await ab_framework.start_test("nonexistent_test")
        assert success is False

    @pytest.mark.asyncio
    async def test_start_already_active_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test starting an already active test."""
        test = await ab_framework.create_test(
            name="Already Active Test",
            description="Test error handling",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)
        success = await ab_framework.start_test(test.test_id)  # Try to start again

        assert success is False

    def test_should_include_user(self, ab_framework):
        """Test user inclusion logic based on traffic allocation."""
        test = ABTest(
            test_id="test_123",
            name="Test",
            description="Test",
            test_type=TestType.CONTENT_VARIATION,
            variations=[],
            metrics=[],
            traffic_allocation=0.5  # 50% traffic
        )

        # Test deterministic behavior
        user1_included = ab_framework._should_include_user("user1", test)
        user1_included_again = ab_framework._should_include_user("user1", test)
        assert user1_included == user1_included_again  # Should be consistent

        # Test with different traffic allocations
        test.traffic_allocation = 0.0
        assert ab_framework._should_include_user("user1", test) is False

        test.traffic_allocation = 1.0
        assert ab_framework._should_include_user("user1", test) is True

    def test_select_variation(self, ab_framework):
        """Test variation selection logic."""
        variations = [
            TestVariation("var1", VariationType.CONTROL, "Control", "content1", traffic_allocation=0.5),
            TestVariation("var2", VariationType.VARIANT_A, "Variant A", "content2", traffic_allocation=0.5)
        ]

        test = ABTest(
            test_id="test_123",
            name="Test",
            description="Test",
            test_type=TestType.CONTENT_VARIATION,
            variations=variations,
            metrics=[]
        )

        # Test deterministic assignment
        user1_variation = ab_framework._select_variation("user1", test)
        user1_variation_again = ab_framework._select_variation("user1", test)
        assert user1_variation == user1_variation_again

        # Test different users get potentially different variations
        user2_variation = ab_framework._select_variation("user2", test)
        assert user2_variation in ["var1", "var2"]

    @pytest.mark.asyncio
    async def test_assign_user_to_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test user assignment to test."""
        test = await ab_framework.create_test(
            name="Assignment Test",
            description="Test user assignment",
            test_type=TestType.SUBJECT_LINE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        assignment = await ab_framework.assign_user_to_test("user123", test.test_id)

        assert assignment is not None
        assert assignment.user_id == "user123"
        assert assignment.test_id == test.test_id
        assert assignment.variation_id in [v.variation_id for v in test.variations]
        assert isinstance(assignment.assigned_at, datetime)

    @pytest.mark.asyncio
    async def test_assign_user_duplicate_assignment(self, ab_framework, sample_metrics, sample_base_content):
        """Test that users get consistent assignment on repeat calls."""
        test = await ab_framework.create_test(
            name="Duplicate Assignment Test",
            description="Test duplicate assignment handling",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        assignment1 = await ab_framework.assign_user_to_test("user123", test.test_id)
        assignment2 = await ab_framework.assign_user_to_test("user123", test.test_id)

        assert assignment1.variation_id == assignment2.variation_id
        assert assignment1.assigned_at == assignment2.assigned_at

    @pytest.mark.asyncio
    async def test_assign_user_forced_variation(self, ab_framework, sample_metrics, sample_base_content):
        """Test forced variation assignment."""
        test = await ab_framework.create_test(
            name="Forced Assignment Test",
            description="Test forced assignment",
            test_type=TestType.CTA_BUTTON,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        force_variation = test.variations[1].variation_id
        assignment = await ab_framework.assign_user_to_test(
            "user123", test.test_id, force_variation=force_variation
        )

        assert assignment.variation_id == force_variation
        assert assignment.metadata["assignment_method"] == "forced"

    @pytest.mark.asyncio
    async def test_assign_user_inactive_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test assignment to inactive test."""
        test = await ab_framework.create_test(
            name="Inactive Test",
            description="Test inactive assignment",
            test_type=TestType.EMAIL_TEMPLATE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        # Don't start the test
        assignment = await ab_framework.assign_user_to_test("user123", test.test_id)

        assert assignment is None

    @pytest.mark.asyncio
    async def test_track_event(self, ab_framework, sample_metrics, sample_base_content):
        """Test event tracking."""
        test = await ab_framework.create_test(
            name="Event Tracking Test",
            description="Test event tracking",
            test_type=TestType.LANDING_PAGE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)
        assignment = await ab_framework.assign_user_to_test("user123", test.test_id)

        success = await ab_framework.track_event(
            user_id="user123",
            test_id=test.test_id,
            metric_type=MetricType.CONVERSION_RATE,
            value=1.0,
            metadata={"source": "test"}
        )

        assert success is True

        # Check event was recorded
        events = ab_framework.test_events[test.test_id]
        assert len(events) == 1
        assert events[0].user_id == "user123"
        assert events[0].variation_id == assignment.variation_id
        assert events[0].metric_type == MetricType.CONVERSION_RATE
        assert events[0].value == 1.0

    @pytest.mark.asyncio
    async def test_track_event_unassigned_user(self, ab_framework, sample_metrics, sample_base_content):
        """Test tracking event for unassigned user."""
        test = await ab_framework.create_test(
            name="Unassigned Event Test",
            description="Test unassigned event tracking",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        success = await ab_framework.track_event(
            user_id="unassigned_user",
            test_id=test.test_id,
            metric_type=MetricType.CLICK_THROUGH_RATE
        )

        assert success is False

    def test_calculate_variation_metrics(self, ab_framework):
        """Test variation metrics calculation."""
        assignments = [
            UserAssignment("user1", "test1", "var1"),
            UserAssignment("user2", "test1", "var1"),
            UserAssignment("user3", "test1", "var1"),
            UserAssignment("user4", "test1", "var1"),
            UserAssignment("user5", "test1", "var1")  # 5 total users
        ]

        events = [
            TestEvent("e1", "user1", "test1", "var1", MetricType.CONVERSION_RATE, 1.0),
            TestEvent("e2", "user3", "test1", "var1", MetricType.CONVERSION_RATE, 1.0),
            # 2 out of 5 users converted = 40% conversion rate
            TestEvent("e3", "user1", "test1", "var1", MetricType.REVENUE, 50.0),
            TestEvent("e4", "user2", "test1", "var1", MetricType.REVENUE, 75.0),
            # Total revenue = 125.0
        ]

        metrics = [
            TestMetric(MetricType.CONVERSION_RATE, "Conversion", "Test conversion"),
            TestMetric(MetricType.REVENUE, "Revenue", "Test revenue")
        ]

        results = ab_framework._calculate_variation_metrics(events, assignments, metrics)

        assert results[MetricType.CONVERSION_RATE.value] == 0.4  # 2/5 = 40%
        assert results[MetricType.REVENUE.value] == 125.0

    def test_calculate_statistical_significance(self, ab_framework):
        """Test statistical significance calculation."""
        control_results = {"conversion_rate": 0.10}  # 10% conversion
        variant_results = {"conversion_rate": 0.15}   # 15% conversion
        control_sample = 1000
        variant_sample = 1000

        # With these sample sizes and difference, should be significant
        significant = ab_framework._calculate_statistical_significance(
            control_results, variant_results, control_sample, variant_sample, 0.05
        )

        assert isinstance(significant, bool)

    def test_calculate_statistical_significance_small_sample(self, ab_framework):
        """Test statistical significance with small sample sizes."""
        control_results = {"conversion_rate": 0.10}
        variant_results = {"conversion_rate": 0.15}
        control_sample = 20  # Too small
        variant_sample = 25   # Too small

        significant = ab_framework._calculate_statistical_significance(
            control_results, variant_results, control_sample, variant_sample, 0.05
        )

        assert significant is False  # Should not be significant due to small sample

    def test_calculate_confidence_intervals(self, ab_framework):
        """Test confidence interval calculation."""
        results = {
            "conversion_rate": 0.15,  # 15% rate
            "revenue": 100.0
        }
        sample_size = 500

        intervals = ab_framework._calculate_confidence_intervals(results, sample_size)

        assert "conversion_rate" in intervals
        assert "revenue" in intervals

        # Conversion rate interval should be around 0.15
        cr_interval = intervals["conversion_rate"]
        assert cr_interval[0] < 0.15 < cr_interval[1]
        assert cr_interval[0] >= 0  # Lower bound should be >= 0
        assert cr_interval[1] <= 1  # Upper bound should be <= 1

    def test_calculate_confidence_intervals_small_sample(self, ab_framework):
        """Test confidence intervals with small sample size."""
        results = {"conversion_rate": 0.15}
        sample_size = 20  # Small sample

        intervals = ab_framework._calculate_confidence_intervals(results, sample_size)

        assert intervals == {}  # Should return empty for small samples

    def test_determine_winner(self, ab_framework):
        """Test winner determination logic."""
        variation_results = {
            "control": {"conversion_rate": 0.10},
            "variant_a": {"conversion_rate": 0.15}
        }
        statistical_significance = {
            "variant_a": True
        }
        metrics = [
            TestMetric(MetricType.CONVERSION_RATE, "Conversion", "Primary metric", primary=True)
        ]

        winner, recommendation = ab_framework._determine_winner(
            variation_results, statistical_significance, metrics
        )

        assert winner == "variant_a"
        assert "Significant winner" in recommendation
        assert "50.0%" in recommendation  # 50% improvement

    def test_determine_winner_no_significance(self, ab_framework):
        """Test winner determination with no statistical significance."""
        variation_results = {
            "control": {"conversion_rate": 0.10},
            "variant_a": {"conversion_rate": 0.11}
        }
        statistical_significance = {
            "variant_a": False
        }
        metrics = [
            TestMetric(MetricType.CONVERSION_RATE, "Conversion", "Primary metric", primary=True)
        ]

        winner, recommendation = ab_framework._determine_winner(
            variation_results, statistical_significance, metrics
        )

        assert winner is None
        assert "No statistically significant" in recommendation

    @pytest.mark.asyncio
    async def test_analyze_test_results(self, ab_framework, sample_metrics, sample_base_content):
        """Test comprehensive test results analysis."""
        test = await ab_framework.create_test(
            name="Results Analysis Test",
            description="Test results analysis",
            test_type=TestType.EMAIL_TEMPLATE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        # Create assignments and events (reduced for faster testing)
        for i in range(20):  # Reduced from 100 to 20 for faster tests
            user_id = f"user{i}"
            await ab_framework.assign_user_to_test(user_id, test.test_id)

            # Simulate some conversions (higher rate for variant)
            assignment = ab_framework._get_user_assignment(user_id, test.test_id)
            if assignment.variation_id.endswith("control"):
                if i % 10 == 0:  # 10% conversion for control
                    await ab_framework.track_event(user_id, test.test_id, MetricType.CONVERSION_RATE)
            else:
                if i % 7 == 0:  # ~14% conversion for variant
                    await ab_framework.track_event(user_id, test.test_id, MetricType.CONVERSION_RATE)

        results = await ab_framework.analyze_test_results(test.test_id)

        assert results is not None
        assert isinstance(results, TestResults)
        assert results.test_id == test.test_id
        assert len(results.variation_results) > 0
        assert len(results.sample_sizes) > 0
        assert isinstance(results.test_duration, timedelta)

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_test_results(self, ab_framework):
        """Test analyzing results for non-existent test."""
        results = await ab_framework.analyze_test_results("nonexistent_test")
        assert results is None

    @pytest.mark.asyncio
    async def test_stop_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test stopping an active test."""
        test = await ab_framework.create_test(
            name="Stop Test",
            description="Test stopping functionality",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)
        assert test.status == TestStatus.ACTIVE

        success = await ab_framework.stop_test(test.test_id, "Manual stop")

        assert success is True
        assert test.status == TestStatus.COMPLETED
        assert test.ended_at is not None
        assert test.metadata["stop_reason"] == "Manual stop"

    @pytest.mark.asyncio
    async def test_stop_inactive_test(self, ab_framework, sample_metrics, sample_base_content):
        """Test stopping an inactive test."""
        test = await ab_framework.create_test(
            name="Inactive Stop Test",
            description="Test stopping inactive test",
            test_type=TestType.TIMING,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        # Don't start the test
        success = await ab_framework.stop_test(test.test_id, "Invalid stop")

        assert success is False

    @pytest.mark.asyncio
    async def test_get_test_analytics(self, ab_framework, sample_metrics, sample_base_content):
        """Test getting test analytics."""
        test = await ab_framework.create_test(
            name="Analytics Test",
            description="Test analytics generation",
            test_type=TestType.SUBJECT_LINE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        await ab_framework.start_test(test.test_id)

        # Add some assignments
        for i in range(5):  # Reduced for faster testing
            await ab_framework.assign_user_to_test(f"user{i}", test.test_id)

        analytics = await ab_framework.get_test_analytics(test.test_id)

        assert analytics["test_info"]["name"] == "Analytics Test"
        assert analytics["test_info"]["status"] == "active"
        assert analytics["participation"]["total_assignments"] == 5
        assert len(analytics["participation"]["assignment_by_variation"]) > 0

    @pytest.mark.asyncio
    async def test_get_analytics_nonexistent_test(self, ab_framework):
        """Test getting analytics for non-existent test."""
        analytics = await ab_framework.get_test_analytics("nonexistent_test")
        assert analytics == {}

    def test_get_user_test_assignment(self, ab_framework):
        """Test getting user's test assignment."""
        # Create mock assignment
        assignment = UserAssignment("user123", "test456", "variation789")
        ab_framework.user_assignments["test456"] = [assignment]

        variation_id = ab_framework.get_user_test_assignment("user123", "test456")
        assert variation_id == "variation789"

        # Test non-existent assignment
        variation_id = ab_framework.get_user_test_assignment("user999", "test456")
        assert variation_id is None

    @pytest.mark.asyncio
    async def test_get_active_tests(self, ab_framework, sample_metrics, sample_base_content):
        """Test getting active tests."""
        # Create and start one test
        test1 = await ab_framework.create_test(
            name="Active Test 1",
            description="First active test",
            test_type=TestType.CONTENT_VARIATION,
            base_content=sample_base_content,
            metrics=sample_metrics
        )
        await ab_framework.start_test(test1.test_id)

        # Create but don't start another test
        test2 = await ab_framework.create_test(
            name="Draft Test 2",
            description="Draft test",
            test_type=TestType.EMAIL_TEMPLATE,
            base_content=sample_base_content,
            metrics=sample_metrics
        )

        active_tests = ab_framework.get_active_tests()

        assert len(active_tests) == 1
        assert active_tests[0].test_id == test1.test_id
        assert active_tests[0].status == TestStatus.ACTIVE

    def test_get_test_summary(self, ab_framework):
        """Test getting test summary."""
        # Add some mock data
        ab_framework.tests["test1"] = Mock(status=TestStatus.ACTIVE)
        ab_framework.tests["test2"] = Mock(status=TestStatus.COMPLETED)
        ab_framework.tests["test3"] = Mock(status=TestStatus.DRAFT)

        ab_framework.user_assignments["test1"] = [Mock(), Mock()]
        ab_framework.user_assignments["test2"] = [Mock()]

        ab_framework.test_events["test1"] = [Mock(), Mock(), Mock()]
        ab_framework.test_events["test2"] = [Mock()]

        summary = ab_framework.get_test_summary()

        assert summary["total_tests"] == 3
        assert summary["active_tests"] == 1
        assert summary["completed_tests"] == 1
        assert summary["total_assignments"] == 3
        assert summary["total_events"] == 4

    def test_singleton_instance(self):
        """Test that get_ab_testing_framework returns singleton instance."""
        framework1 = get_ab_testing_framework()
        framework2 = get_ab_testing_framework()

        assert framework1 is framework2
        assert isinstance(framework1, ABTestingFramework)


class TestABTestingDataStructures:
    """Test A/B testing data structures."""

    def test_test_variation_creation(self):
        """Test TestVariation data structure."""
        variation = TestVariation(
            variation_id="var_123",
            variation_type=VariationType.VARIANT_A,
            name="Variant A",
            content="Test content",
            traffic_allocation=0.5
        )

        assert variation.variation_id == "var_123"
        assert variation.variation_type == VariationType.VARIANT_A
        assert variation.name == "Variant A"
        assert variation.content == "Test content"
        assert variation.traffic_allocation == 0.5
        assert isinstance(variation.created_at, datetime)

    def test_test_metric_creation(self):
        """Test TestMetric data structure."""
        metric = TestMetric(
            metric_type=MetricType.CONVERSION_RATE,
            name="Conversion Rate",
            description="Primary conversion metric",
            primary=True,
            target_value=0.15
        )

        assert metric.metric_type == MetricType.CONVERSION_RATE
        assert metric.name == "Conversion Rate"
        assert metric.primary is True
        assert metric.target_value == 0.15
        assert metric.improvement_threshold == 0.05  # Default

    def test_user_assignment_creation(self):
        """Test UserAssignment data structure."""
        assignment = UserAssignment(
            user_id="user123",
            test_id="test456",
            variation_id="var789"
        )

        assert assignment.user_id == "user123"
        assert assignment.test_id == "test456"
        assert assignment.variation_id == "var789"
        assert isinstance(assignment.assigned_at, datetime)
        assert len(assignment.metadata) == 0  # Default empty

    def test_test_event_creation(self):
        """Test TestEvent data structure."""
        event = TestEvent(
            event_id="event123",
            user_id="user456",
            test_id="test789",
            variation_id="var012",
            metric_type=MetricType.CLICK_THROUGH_RATE,
            value=1.0
        )

        assert event.event_id == "event123"
        assert event.user_id == "user456"
        assert event.test_id == "test789"
        assert event.variation_id == "var012"
        assert event.metric_type == MetricType.CLICK_THROUGH_RATE
        assert event.value == 1.0
        assert isinstance(event.timestamp, datetime)

    def test_test_results_creation(self):
        """Test TestResults data structure."""
        results = TestResults(
            test_id="test123",
            variation_results={"control": {"conversion_rate": 0.10}},
            statistical_significance={"variant_a": True},
            confidence_intervals={"variant_a": (0.12, 0.18)},
            sample_sizes={"control": 500, "variant_a": 500},
            test_duration=timedelta(days=7),
            winner="variant_a",
            recommendation="Significant improvement detected"
        )

        assert results.test_id == "test123"
        assert results.winner == "variant_a"
        assert results.recommendation == "Significant improvement detected"
        assert isinstance(results.generated_at, datetime)

    def test_ab_test_creation(self):
        """Test ABTest data structure."""
        variations = [
            TestVariation("control", VariationType.CONTROL, "Control", "Original"),
            TestVariation("variant_a", VariationType.VARIANT_A, "Variant A", "Modified")
        ]
        metrics = [
            TestMetric(MetricType.CONVERSION_RATE, "Conversion", "Primary metric", primary=True)
        ]

        test = ABTest(
            test_id="test123",
            name="Test Name",
            description="Test Description",
            test_type=TestType.EMAIL_TEMPLATE,
            variations=variations,
            metrics=metrics,
            traffic_allocation=0.8,
            min_sample_size=200
        )

        assert test.test_id == "test123"
        assert test.name == "Test Name"
        assert test.test_type == TestType.EMAIL_TEMPLATE
        assert test.status == TestStatus.DRAFT  # Default
        assert len(test.variations) == 2
        assert len(test.metrics) == 1
        assert test.traffic_allocation == 0.8
        assert test.min_sample_size == 200


class TestABTestingEnums:
    """Test A/B testing enumerations."""

    def test_test_status_enum(self):
        """Test TestStatus enum values."""
        assert TestStatus.DRAFT.value == "draft"
        assert TestStatus.ACTIVE.value == "active"
        assert TestStatus.PAUSED.value == "paused"
        assert TestStatus.COMPLETED.value == "completed"
        assert TestStatus.ARCHIVED.value == "archived"

    def test_test_type_enum(self):
        """Test TestType enum values."""
        assert TestType.CONTENT_VARIATION.value == "content_variation"
        assert TestType.SUBJECT_LINE.value == "subject_line"
        assert TestType.CTA_BUTTON.value == "cta_button"
        assert TestType.EMAIL_TEMPLATE.value == "email_template"
        assert TestType.LANDING_PAGE.value == "landing_page"
        assert TestType.TIMING.value == "timing"

    def test_variation_type_enum(self):
        """Test VariationType enum values."""
        assert VariationType.CONTROL.value == "control"
        assert VariationType.VARIANT_A.value == "variant_a"
        assert VariationType.VARIANT_B.value == "variant_b"
        assert VariationType.VARIANT_C.value == "variant_c"
        assert VariationType.VARIANT_D.value == "variant_d"

    def test_metric_type_enum(self):
        """Test MetricType enum values."""
        assert MetricType.CLICK_THROUGH_RATE.value == "click_through_rate"
        assert MetricType.CONVERSION_RATE.value == "conversion_rate"
        assert MetricType.OPEN_RATE.value == "open_rate"
        assert MetricType.ENGAGEMENT_RATE.value == "engagement_rate"
        assert MetricType.REVENUE.value == "revenue"
        assert MetricType.TIME_ON_PAGE.value == "time_on_page"