"""
A/B Testing Framework for Halcytone Content Generator.

This module provides comprehensive A/B testing capabilities including test creation,
variation generation, user assignment, and statistical analysis of results.
"""

import asyncio
import hashlib
import json
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, stdev

from ..config import get_settings
from .ai_content_enhancer import AIContentEnhancer
from .personalization import ContentPersonalizationEngine


logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Status of an A/B test."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TestType(Enum):
    """Types of A/B tests."""
    CONTENT_VARIATION = "content_variation"
    PERSONALIZATION = "personalization"
    SUBJECT_LINE = "subject_line"
    CTA_BUTTON = "cta_button"
    EMAIL_TEMPLATE = "email_template"
    LANDING_PAGE = "landing_page"
    TIMING = "timing"


class VariationType(Enum):
    """Types of variations in A/B tests."""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"
    VARIANT_D = "variant_d"


class MetricType(Enum):
    """Types of metrics to track."""
    CLICK_THROUGH_RATE = "click_through_rate"
    CONVERSION_RATE = "conversion_rate"
    OPEN_RATE = "open_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    BOUNCE_RATE = "bounce_rate"
    TIME_ON_PAGE = "time_on_page"
    REVENUE = "revenue"
    UNSUBSCRIBE_RATE = "unsubscribe_rate"


@dataclass
class TestVariation:
    """A variation in an A/B test."""
    variation_id: str
    variation_type: VariationType
    name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    traffic_allocation: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestMetric:
    """A metric to track in an A/B test."""
    metric_type: MetricType
    name: str
    description: str
    primary: bool = False
    target_value: Optional[float] = None
    improvement_threshold: float = 0.05  # 5% improvement threshold


@dataclass
class UserAssignment:
    """Assignment of a user to a test variation."""
    user_id: str
    test_id: str
    variation_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestEvent:
    """An event recorded for A/B test tracking."""
    event_id: str
    user_id: str
    test_id: str
    variation_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResults:
    """Results of an A/B test."""
    test_id: str
    variation_results: Dict[str, Dict[str, float]]
    statistical_significance: Dict[str, bool]
    confidence_intervals: Dict[str, Tuple[float, float]]
    sample_sizes: Dict[str, int]
    test_duration: timedelta
    winner: Optional[str] = None
    recommendation: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ABTest:
    """An A/B test configuration."""
    test_id: str
    name: str
    description: str
    test_type: TestType
    variations: List[TestVariation]
    metrics: List[TestMetric]
    status: TestStatus = TestStatus.DRAFT
    traffic_allocation: float = 1.0
    min_sample_size: int = 100
    max_duration_days: int = 30
    significance_level: float = 0.05
    power: float = 0.8
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTestingFramework:
    """
    Comprehensive A/B testing framework with variation generation,
    user assignment, and statistical analysis capabilities.
    """

    def __init__(self):
        self.config = get_settings()
        self.ai_enhancer = AIContentEnhancer()
        self.personalization_engine = ContentPersonalizationEngine()

        # In-memory storage (in production, this would be a database)
        self.tests: Dict[str, ABTest] = {}
        self.user_assignments: Dict[str, List[UserAssignment]] = {}
        self.test_events: Dict[str, List[TestEvent]] = {}
        self.test_results: Dict[str, TestResults] = {}

    async def create_test(
        self,
        name: str,
        description: str,
        test_type: TestType,
        base_content: str,
        metrics: List[TestMetric],
        variation_count: int = 2,
        traffic_allocation: float = 1.0,
        min_sample_size: int = 100,
        max_duration_days: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ABTest:
        """
        Create a new A/B test with generated variations.

        Args:
            name: Test name
            description: Test description
            test_type: Type of test
            base_content: Base content for variations
            metrics: Metrics to track
            variation_count: Number of variations to generate
            traffic_allocation: Percentage of traffic to include
            min_sample_size: Minimum sample size per variation
            max_duration_days: Maximum test duration
            metadata: Additional test metadata

        Returns:
            Created A/B test
        """
        test_id = self._generate_test_id(name)

        try:
            # Generate variations
            variations = await self._generate_variations(
                test_id=test_id,
                test_type=test_type,
                base_content=base_content,
                variation_count=variation_count
            )

            # Create test
            test = ABTest(
                test_id=test_id,
                name=name,
                description=description,
                test_type=test_type,
                variations=variations,
                metrics=metrics,
                traffic_allocation=traffic_allocation,
                min_sample_size=min_sample_size,
                max_duration_days=max_duration_days,
                metadata=metadata or {}
            )

            self.tests[test_id] = test
            self.user_assignments[test_id] = []
            self.test_events[test_id] = []

            logger.info(f"Created A/B test '{name}' with {len(variations)} variations")
            return test

        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise

    async def _generate_variations(
        self,
        test_id: str,
        test_type: TestType,
        base_content: str,
        variation_count: int
    ) -> List[TestVariation]:
        """
        Generate test variations based on test type and base content.

        Args:
            test_id: Test identifier
            test_type: Type of test
            base_content: Base content
            variation_count: Number of variations

        Returns:
            List of generated variations
        """
        variations = []

        # Control variation (original)
        control = TestVariation(
            variation_id=f"{test_id}_control",
            variation_type=VariationType.CONTROL,
            name="Control",
            content=base_content,
            traffic_allocation=1.0 / variation_count
        )
        variations.append(control)

        # Generate AI-powered variations if enabled
        if (self.config.AI_ENABLE_AB_TESTING and
            variation_count > 1 and
            test_type in [TestType.CONTENT_VARIATION, TestType.SUBJECT_LINE, TestType.EMAIL_TEMPLATE]):

            ai_variations = await self._generate_ai_variations(
                test_id=test_id,
                test_type=test_type,
                base_content=base_content,
                variation_count=variation_count - 1
            )
            variations.extend(ai_variations)
        else:
            # Generate rule-based variations
            rule_variations = self._generate_rule_based_variations(
                test_id=test_id,
                test_type=test_type,
                base_content=base_content,
                variation_count=variation_count - 1
            )
            variations.extend(rule_variations)

        return variations

    async def _generate_ai_variations(
        self,
        test_id: str,
        test_type: TestType,
        base_content: str,
        variation_count: int
    ) -> List[TestVariation]:
        """Generate AI-powered content variations."""
        variations = []
        variation_types = [VariationType.VARIANT_A, VariationType.VARIANT_B,
                          VariationType.VARIANT_C, VariationType.VARIANT_D]

        for i in range(min(variation_count, len(variation_types))):
            try:
                # Create enhancement prompt for A/B testing
                enhancement_prompt = self._create_variation_prompt(test_type, i + 1)

                # Generate variation using AI enhancer
                enhanced_content = await self.ai_enhancer.enhance_content(
                    content=base_content,
                    enhancement_type="ab_testing",
                    context_data={
                        "test_type": test_type.value,
                        "variation_number": i + 1,
                        "enhancement_prompt": enhancement_prompt
                    }
                )

                if enhanced_content and enhanced_content.enhanced_content:
                    variation = TestVariation(
                        variation_id=f"{test_id}_{variation_types[i].value}",
                        variation_type=variation_types[i],
                        name=f"AI Variant {chr(65 + i)}",
                        content=enhanced_content.enhanced_content,
                        traffic_allocation=1.0 / (variation_count + 1),
                        metadata={
                            "generation_method": "ai_enhanced",
                            "enhancement_score": enhanced_content.enhancement_score
                        }
                    )
                    variations.append(variation)

            except Exception as e:
                logger.warning(f"Failed to generate AI variation {i + 1}: {e}")
                # Fallback to rule-based generation
                rule_variation = self._generate_single_rule_variation(
                    test_id, test_type, base_content, i + 1
                )
                variations.append(rule_variation)

        return variations

    def _generate_rule_based_variations(
        self,
        test_id: str,
        test_type: TestType,
        base_content: str,
        variation_count: int
    ) -> List[TestVariation]:
        """Generate rule-based content variations."""
        variations = []
        variation_types = [VariationType.VARIANT_A, VariationType.VARIANT_B,
                          VariationType.VARIANT_C, VariationType.VARIANT_D]

        for i in range(min(variation_count, len(variation_types))):
            variation = self._generate_single_rule_variation(
                test_id, test_type, base_content, i + 1
            )
            variations.append(variation)

        return variations

    def _generate_single_rule_variation(
        self,
        test_id: str,
        test_type: TestType,
        base_content: str,
        variation_number: int
    ) -> TestVariation:
        """Generate a single rule-based variation."""
        variation_types = [VariationType.VARIANT_A, VariationType.VARIANT_B,
                          VariationType.VARIANT_C, VariationType.VARIANT_D]

        variation_type = variation_types[variation_number - 1]
        modified_content = base_content

        if test_type == TestType.SUBJECT_LINE:
            modifications = [
                lambda x: f"🎯 {x}",  # Add emoji
                lambda x: f"{x} - Limited Time!",  # Add urgency
                lambda x: x.upper(),  # Uppercase
                lambda x: f"Exclusive: {x}"  # Add exclusivity
            ]
            modified_content = modifications[variation_number - 1](base_content)

        elif test_type == TestType.CTA_BUTTON:
            cta_variations = [
                "Get Started Now",
                "Try It Free",
                "Learn More",
                "Join Today"
            ]
            modified_content = cta_variations[(variation_number - 1) % len(cta_variations)]

        elif test_type == TestType.CONTENT_VARIATION:
            if variation_number == 1:
                modified_content = f"**Enhanced:** {base_content}"
            elif variation_number == 2:
                modified_content = base_content.replace(".", "!")
            elif variation_number == 3:
                modified_content = f"{base_content}\n\n*Don't miss out on this opportunity!*"
            else:
                modified_content = f"🌟 {base_content} 🌟"

        return TestVariation(
            variation_id=f"{test_id}_{variation_type.value}",
            variation_type=variation_type,
            name=f"Variant {chr(64 + variation_number)}",
            content=modified_content,
            metadata={"generation_method": "rule_based"}
        )

    def _create_variation_prompt(self, test_type: TestType, variation_number: int) -> str:
        """Create AI enhancement prompt for generating variations."""
        base_prompts = {
            TestType.CONTENT_VARIATION: [
                "Create a more engaging version with stronger emotional appeal",
                "Rewrite with a more professional and authoritative tone",
                "Make it more conversational and friendly",
                "Add urgency and scarcity elements"
            ],
            TestType.SUBJECT_LINE: [
                "Create a more compelling subject line with curiosity gap",
                "Write a benefit-focused subject line",
                "Create an urgent, time-sensitive subject line",
                "Write a personalized, direct subject line"
            ],
            TestType.EMAIL_TEMPLATE: [
                "Redesign with better structure and flow",
                "Create a more visual, scannable version",
                "Make it more concise and action-oriented",
                "Add social proof and credibility elements"
            ]
        }

        prompts = base_prompts.get(test_type, ["Create an improved version"])
        return prompts[(variation_number - 1) % len(prompts)]

    def _generate_test_id(self, name: str) -> str:
        """Generate a unique test ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"test_{timestamp}_{name_hash}"

    async def start_test(self, test_id: str) -> bool:
        """
        Start an A/B test.

        Args:
            test_id: Test identifier

        Returns:
            Success status
        """
        if test_id not in self.tests:
            logger.error(f"Test {test_id} not found")
            return False

        test = self.tests[test_id]

        if test.status != TestStatus.DRAFT:
            logger.error(f"Test {test_id} is not in draft status")
            return False

        try:
            test.status = TestStatus.ACTIVE
            test.started_at = datetime.utcnow()

            logger.info(f"Started A/B test: {test.name}")
            return True

        except Exception as e:
            logger.error(f"Error starting test {test_id}: {e}")
            return False

    async def assign_user_to_test(
        self,
        user_id: str,
        test_id: str,
        force_variation: Optional[str] = None
    ) -> Optional[UserAssignment]:
        """
        Assign a user to a test variation.

        Args:
            user_id: User identifier
            test_id: Test identifier
            force_variation: Force assignment to specific variation

        Returns:
            User assignment or None if not eligible
        """
        if test_id not in self.tests:
            return None

        test = self.tests[test_id]

        if test.status != TestStatus.ACTIVE:
            return None

        # Check if user already assigned
        existing_assignment = self._get_user_assignment(user_id, test_id)
        if existing_assignment:
            return existing_assignment

        try:
            # Determine if user should be included in test
            if not self._should_include_user(user_id, test):
                return None

            # Select variation
            if force_variation:
                variation_id = force_variation
            else:
                variation_id = self._select_variation(user_id, test)

            # Create assignment
            assignment = UserAssignment(
                user_id=user_id,
                test_id=test_id,
                variation_id=variation_id,
                metadata={
                    "assignment_method": "hash_based" if not force_variation else "forced"
                }
            )

            self.user_assignments[test_id].append(assignment)

            logger.debug(f"Assigned user {user_id} to test {test_id}, variation {variation_id}")
            return assignment

        except Exception as e:
            logger.error(f"Error assigning user to test: {e}")
            return None

    def _get_user_assignment(self, user_id: str, test_id: str) -> Optional[UserAssignment]:
        """Get existing user assignment for a test."""
        if test_id not in self.user_assignments:
            return None

        for assignment in self.user_assignments[test_id]:
            if assignment.user_id == user_id:
                return assignment

        return None

    def _should_include_user(self, user_id: str, test: ABTest) -> bool:
        """Determine if user should be included in test based on traffic allocation."""
        # Use deterministic hash-based assignment
        hash_input = f"{user_id}_{test.test_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 100) / 100.0

        return bucket < test.traffic_allocation

    def _select_variation(self, user_id: str, test: ABTest) -> str:
        """Select variation for user using consistent hash-based assignment."""
        # Create hash for variation selection
        hash_input = f"{user_id}_{test.test_id}_variation"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Calculate cumulative allocation
        cumulative_allocation = 0.0
        normalized_hash = (hash_value % 10000) / 10000.0

        for variation in test.variations:
            cumulative_allocation += variation.traffic_allocation
            if normalized_hash <= cumulative_allocation:
                return variation.variation_id

        # Fallback to control
        return test.variations[0].variation_id

    async def track_event(
        self,
        user_id: str,
        test_id: str,
        metric_type: MetricType,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an event for A/B test analysis.

        Args:
            user_id: User identifier
            test_id: Test identifier
            metric_type: Type of metric
            value: Metric value
            metadata: Additional event metadata

        Returns:
            Success status
        """
        if test_id not in self.tests:
            return False

        # Get user assignment
        assignment = self._get_user_assignment(user_id, test_id)
        if not assignment:
            return False

        try:
            event = TestEvent(
                event_id=self._generate_event_id(),
                user_id=user_id,
                test_id=test_id,
                variation_id=assignment.variation_id,
                metric_type=metric_type,
                value=value,
                metadata=metadata or {}
            )

            self.test_events[test_id].append(event)

            logger.debug(f"Tracked event {metric_type.value} for user {user_id} in test {test_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"event_{timestamp}"

    async def analyze_test_results(self, test_id: str) -> Optional[TestResults]:
        """
        Analyze A/B test results with statistical significance testing.

        Args:
            test_id: Test identifier

        Returns:
            Test results with statistical analysis
        """
        if test_id not in self.tests:
            return None

        test = self.tests[test_id]
        events = self.test_events.get(test_id, [])
        assignments = self.user_assignments.get(test_id, [])

        try:
            # Calculate results for each variation
            variation_results = {}
            sample_sizes = {}
            statistical_significance = {}
            confidence_intervals = {}

            for variation in test.variations:
                variation_events = [e for e in events if e.variation_id == variation.variation_id]
                variation_assignments = [a for a in assignments if a.variation_id == variation.variation_id]

                sample_sizes[variation.variation_id] = len(variation_assignments)
                variation_results[variation.variation_id] = self._calculate_variation_metrics(
                    variation_events, variation_assignments, test.metrics
                )

            # Calculate statistical significance
            control_variation = next((v for v in test.variations if v.variation_type == VariationType.CONTROL), None)
            if control_variation:
                for variation in test.variations:
                    if variation.variation_type != VariationType.CONTROL:
                        significance = self._calculate_statistical_significance(
                            variation_results.get(control_variation.variation_id, {}),
                            variation_results.get(variation.variation_id, {}),
                            sample_sizes.get(control_variation.variation_id, 0),
                            sample_sizes.get(variation.variation_id, 0),
                            test.significance_level
                        )
                        statistical_significance[variation.variation_id] = significance

                        # Calculate confidence intervals
                        ci = self._calculate_confidence_intervals(
                            variation_results.get(variation.variation_id, {}),
                            sample_sizes.get(variation.variation_id, 0)
                        )
                        confidence_intervals[variation.variation_id] = ci

            # Determine winner and recommendation
            winner, recommendation = self._determine_winner(
                variation_results, statistical_significance, test.metrics
            )

            # Calculate test duration
            duration = timedelta(0)
            if test.started_at:
                end_time = test.ended_at or datetime.utcnow()
                duration = end_time - test.started_at

            results = TestResults(
                test_id=test_id,
                variation_results=variation_results,
                statistical_significance=statistical_significance,
                confidence_intervals=confidence_intervals,
                sample_sizes=sample_sizes,
                test_duration=duration,
                winner=winner,
                recommendation=recommendation
            )

            self.test_results[test_id] = results

            logger.info(f"Analyzed results for test {test_id}: winner={winner}")
            return results

        except Exception as e:
            logger.error(f"Error analyzing test results: {e}")
            return None

    def _calculate_variation_metrics(
        self,
        events: List[TestEvent],
        assignments: List[UserAssignment],
        metrics: List[TestMetric]
    ) -> Dict[str, float]:
        """Calculate metrics for a variation."""
        results = {}

        if not assignments:
            return results

        user_count = len(assignments)

        for metric in metrics:
            metric_events = [e for e in events if e.metric_type == metric.metric_type]

            if metric.metric_type in [MetricType.CLICK_THROUGH_RATE, MetricType.CONVERSION_RATE,
                                    MetricType.OPEN_RATE, MetricType.ENGAGEMENT_RATE]:
                # Rate metrics: unique users who performed action / total users
                unique_users = len(set(e.user_id for e in metric_events))
                results[metric.metric_type.value] = unique_users / user_count if user_count > 0 else 0.0

            elif metric.metric_type == MetricType.REVENUE:
                # Revenue metrics: sum of all revenue events
                results[metric.metric_type.value] = sum(e.value for e in metric_events)

            elif metric.metric_type == MetricType.TIME_ON_PAGE:
                # Time metrics: average time
                if metric_events:
                    results[metric.metric_type.value] = mean(e.value for e in metric_events)
                else:
                    results[metric.metric_type.value] = 0.0

            else:
                # Default: average value
                if metric_events:
                    results[metric.metric_type.value] = mean(e.value for e in metric_events)
                else:
                    results[metric.metric_type.value] = 0.0

        return results

    def _calculate_statistical_significance(
        self,
        control_results: Dict[str, float],
        variant_results: Dict[str, float],
        control_sample_size: int,
        variant_sample_size: int,
        significance_level: float
    ) -> bool:
        """Calculate statistical significance using two-proportion z-test."""
        if control_sample_size < 30 or variant_sample_size < 30:
            return False

        try:
            # Use primary metric for significance testing
            primary_metric = None
            for key in control_results.keys():
                if any(key.endswith(m.value) for m in [MetricType.CONVERSION_RATE, MetricType.CLICK_THROUGH_RATE]):
                    primary_metric = key
                    break

            if not primary_metric:
                primary_metric = list(control_results.keys())[0] if control_results else None

            if not primary_metric:
                return False

            p1 = control_results.get(primary_metric, 0.0)
            p2 = variant_results.get(primary_metric, 0.0)

            # Pooled proportion
            p_pool = (p1 * control_sample_size + p2 * variant_sample_size) / (control_sample_size + variant_sample_size)

            # Standard error
            se = math.sqrt(p_pool * (1 - p_pool) * (1/control_sample_size + 1/variant_sample_size))

            if se == 0:
                return False

            # Z-score
            z = (p2 - p1) / se

            # Critical value for two-tailed test
            critical_value = 1.96  # For 95% confidence (α = 0.05)

            return abs(z) > critical_value

        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return False

    def _calculate_confidence_intervals(
        self,
        results: Dict[str, float],
        sample_size: int
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for metrics."""
        intervals = {}

        if sample_size < 30:
            return intervals

        for metric, value in results.items():
            try:
                # For proportions (rates)
                if value <= 1.0:
                    se = math.sqrt(value * (1 - value) / sample_size)
                    margin = 1.96 * se
                    intervals[metric] = (max(0, value - margin), min(1, value + margin))
                else:
                    # For other metrics, use normal approximation
                    se = value / math.sqrt(sample_size)
                    margin = 1.96 * se
                    intervals[metric] = (max(0, value - margin), value + margin)

            except Exception as e:
                logger.error(f"Error calculating confidence interval for {metric}: {e}")
                intervals[metric] = (value, value)

        return intervals

    def _determine_winner(
        self,
        variation_results: Dict[str, Dict[str, float]],
        statistical_significance: Dict[str, bool],
        metrics: List[TestMetric]
    ) -> Tuple[Optional[str], str]:
        """Determine test winner and provide recommendation."""
        if not variation_results:
            return None, "Insufficient data for analysis"

        # Find primary metric
        primary_metric = None
        for metric in metrics:
            if metric.primary:
                primary_metric = metric.metric_type.value
                break

        if not primary_metric and metrics:
            primary_metric = metrics[0].metric_type.value

        if not primary_metric:
            return None, "No metrics defined for comparison"

        # Find best performing variation
        best_variation = None
        best_value = -1

        for variation_id, results in variation_results.items():
            if primary_metric in results:
                value = results[primary_metric]
                if value > best_value:
                    best_value = value
                    best_variation = variation_id

        # Check statistical significance
        if best_variation and best_variation in statistical_significance:
            if statistical_significance[best_variation]:
                improvement = ((best_value - variation_results.get("control", {}).get(primary_metric, 0)) /
                             variation_results.get("control", {}).get(primary_metric, 1)) * 100
                return best_variation, f"Significant winner with {improvement:.1f}% improvement"
            else:
                return None, "No statistically significant difference detected"
        else:
            return None, "Insufficient data for statistical significance testing"

    async def stop_test(self, test_id: str, reason: str = "") -> bool:
        """
        Stop an active A/B test.

        Args:
            test_id: Test identifier
            reason: Reason for stopping

        Returns:
            Success status
        """
        if test_id not in self.tests:
            return False

        test = self.tests[test_id]

        if test.status != TestStatus.ACTIVE:
            return False

        try:
            test.status = TestStatus.COMPLETED
            test.ended_at = datetime.utcnow()
            test.metadata["stop_reason"] = reason

            # Generate final results
            await self.analyze_test_results(test_id)

            logger.info(f"Stopped A/B test: {test.name} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Error stopping test {test_id}: {e}")
            return False

    async def get_test_analytics(self, test_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a test.

        Args:
            test_id: Test identifier

        Returns:
            Test analytics data
        """
        if test_id not in self.tests:
            return {}

        test = self.tests[test_id]
        events = self.test_events.get(test_id, [])
        assignments = self.user_assignments.get(test_id, [])
        results = self.test_results.get(test_id)

        analytics = {
            "test_info": {
                "name": test.name,
                "status": test.status.value,
                "type": test.test_type.value,
                "started_at": test.started_at.isoformat() if test.started_at else None,
                "duration_hours": (datetime.utcnow() - test.started_at).total_seconds() / 3600 if test.started_at else 0
            },
            "participation": {
                "total_assignments": len(assignments),
                "total_events": len(events),
                "assignment_by_variation": {}
            },
            "performance": {
                "variation_results": results.variation_results if results else {},
                "statistical_significance": results.statistical_significance if results else {},
                "winner": results.winner if results else None
            }
        }

        # Calculate assignment distribution
        for variation in test.variations:
            variation_assignments = [a for a in assignments if a.variation_id == variation.variation_id]
            analytics["participation"]["assignment_by_variation"][variation.name] = len(variation_assignments)

        return analytics

    def get_user_test_assignment(self, user_id: str, test_id: str) -> Optional[str]:
        """
        Get user's current test assignment.

        Args:
            user_id: User identifier
            test_id: Test identifier

        Returns:
            Variation ID if assigned, None otherwise
        """
        assignment = self._get_user_assignment(user_id, test_id)
        return assignment.variation_id if assignment else None

    def get_active_tests(self) -> List[ABTest]:
        """Get all active tests."""
        return [test for test in self.tests.values() if test.status == TestStatus.ACTIVE]

    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all tests."""
        summary = {
            "total_tests": len(self.tests),
            "active_tests": len([t for t in self.tests.values() if t.status == TestStatus.ACTIVE]),
            "completed_tests": len([t for t in self.tests.values() if t.status == TestStatus.COMPLETED]),
            "total_assignments": sum(len(assignments) for assignments in self.user_assignments.values()),
            "total_events": sum(len(events) for events in self.test_events.values())
        }
        return summary


# Singleton instance
_ab_testing_framework = None


def get_ab_testing_framework() -> ABTestingFramework:
    """Get the singleton A/B testing framework instance."""
    global _ab_testing_framework
    if _ab_testing_framework is None:
        _ab_testing_framework = ABTestingFramework()
    return _ab_testing_framework