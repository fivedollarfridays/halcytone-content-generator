"""
Load testing scenarios for different performance testing objectives
"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from locust import HttpUser
from locust.env import Environment

from .load_tests import (
    HealthCheckUser,
    ContentGenerationUser,
    APIExplorationUser,
    HeavyWorkloadUser,
    MixedWorkloadUser
)
from .baseline import BaselineCollector, PerformanceBaseline


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    description: str
    user_classes: List[HttpUser]
    users: int
    spawn_rate: float
    run_time: int
    objectives: List[str]
    success_criteria: Dict[str, float]


class BaselineScenario:
    """Baseline establishment scenario"""

    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.collector = BaselineCollector(host=host)

    def get_scenarios(self) -> List[TestScenario]:
        """Get baseline testing scenarios"""
        return [
            TestScenario(
                name="health_check_baseline",
                description="Establish baseline for health endpoints",
                user_classes=[HealthCheckUser],
                users=5,
                spawn_rate=1,
                run_time=180,  # 3 minutes
                objectives=[
                    "Establish baseline response times for health endpoints",
                    "Measure health check throughput capacity",
                    "Document normal error rates"
                ],
                success_criteria={
                    "response_time_p95": 100,  # 100ms max
                    "error_rate": 0.001,       # 0.1% max
                    "min_rps": 50              # At least 50 RPS
                }
            ),

            TestScenario(
                name="content_generation_baseline",
                description="Establish baseline for content generation",
                user_classes=[ContentGenerationUser],
                users=10,
                spawn_rate=2,
                run_time=300,  # 5 minutes
                objectives=[
                    "Measure content generation performance",
                    "Establish response time baselines for different content types",
                    "Document throughput capacity for content operations"
                ],
                success_criteria={
                    "response_time_p95": 5000,  # 5s for content generation
                    "error_rate": 0.05,         # 5% max for baseline
                    "min_rps": 5                # At least 5 content generations per second
                }
            ),

            TestScenario(
                name="mixed_workload_baseline",
                description="Establish baseline for realistic mixed usage",
                user_classes=[MixedWorkloadUser],
                users=20,
                spawn_rate=3,
                run_time=600,  # 10 minutes
                objectives=[
                    "Measure performance under realistic usage patterns",
                    "Establish baselines for typical user workflows",
                    "Document system behavior with mixed operations"
                ],
                success_criteria={
                    "response_time_p95": 3000,  # 3s for mixed operations
                    "error_rate": 0.02,         # 2% max
                    "min_rps": 10               # At least 10 operations per second
                }
            )
        ]

    def run_baseline_collection(self) -> List[PerformanceBaseline]:
        """Run all baseline scenarios and collect results"""
        scenarios = self.get_scenarios()
        baselines = []

        print("🔍 Starting baseline collection...")

        for scenario in scenarios:
            print(f"\n📊 Running scenario: {scenario.name}")
            print(f"   Description: {scenario.description}")
            print(f"   Users: {scenario.users}, Duration: {scenario.run_time}s")

            # Run the scenario
            baseline = self.collector.collect_baseline(
                user_class=scenario.user_classes[0],  # Use first user class
                users=scenario.users,
                spawn_rate=scenario.spawn_rate,
                run_time=scenario.run_time,
                operation_name=scenario.name
            )

            baselines.append(baseline)

            # Check against success criteria
            self._validate_baseline(baseline, scenario)

            # Brief pause between scenarios
            time.sleep(30)

        print("\n✅ Baseline collection complete!")
        return baselines

    def _validate_baseline(self, baseline: PerformanceBaseline, scenario: TestScenario):
        """Validate baseline against success criteria"""
        print(f"   📋 Validating against success criteria...")

        issues = []

        if baseline.response_time_p95 > scenario.success_criteria["response_time_p95"]:
            issues.append(f"P95 response time {baseline.response_time_p95:.0f}ms exceeds {scenario.success_criteria['response_time_p95']}ms")

        if baseline.error_rate > scenario.success_criteria["error_rate"]:
            issues.append(f"Error rate {baseline.error_rate:.3%} exceeds {scenario.success_criteria['error_rate']:.1%}")

        if baseline.requests_per_second < scenario.success_criteria["min_rps"]:
            issues.append(f"RPS {baseline.requests_per_second:.1f} below minimum {scenario.success_criteria['min_rps']}")

        if issues:
            print(f"   ⚠️  Issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print(f"   ✅ All success criteria met")


class StressTestScenario:
    """Stress testing scenario to find breaking points"""

    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.collector = BaselineCollector(host=host, results_dir="performance/results/stress")

    def get_scenarios(self) -> List[TestScenario]:
        """Get stress testing scenarios"""
        return [
            TestScenario(
                name="content_generation_stress",
                description="Find breaking point for content generation",
                user_classes=[ContentGenerationUser],
                users=50,  # Start high
                spawn_rate=5,
                run_time=300,
                objectives=[
                    "Find maximum sustainable content generation load",
                    "Identify resource bottlenecks",
                    "Document degradation patterns"
                ],
                success_criteria={
                    "response_time_p95": 10000,  # 10s acceptable under stress
                    "error_rate": 0.10,          # 10% errors acceptable
                    "min_rps": 2                 # Minimum viable throughput
                }
            ),

            TestScenario(
                name="heavy_workload_stress",
                description="Stress test with heavy concurrent operations",
                user_classes=[HeavyWorkloadUser],
                users=25,
                spawn_rate=3,
                run_time=240,
                objectives=[
                    "Test system under heavy concurrent load",
                    "Find memory and CPU limits",
                    "Document failure modes"
                ],
                success_criteria={
                    "response_time_p95": 15000,  # 15s under heavy stress
                    "error_rate": 0.15,          # 15% errors acceptable
                    "min_rps": 1                 # System should not completely fail
                }
            )
        ]

    def run_stress_tests(self) -> List[PerformanceBaseline]:
        """Run stress testing scenarios"""
        scenarios = self.get_scenarios()
        results = []

        print("💪 Starting stress testing...")

        for scenario in scenarios:
            print(f"\n🔥 Running stress test: {scenario.name}")

            # Run stress test
            result = self.collector.collect_baseline(
                user_class=scenario.user_classes[0],
                users=scenario.users,
                spawn_rate=scenario.spawn_rate,
                run_time=scenario.run_time,
                operation_name=scenario.name
            )

            results.append(result)

            # Analysis
            print(f"   📊 Results:")
            print(f"      RPS: {result.requests_per_second:.1f}")
            print(f"      P95: {result.response_time_p95:.0f}ms")
            print(f"      Error rate: {result.error_rate:.1%}")

            # Recovery time
            print("   😴 Allowing system recovery...")
            time.sleep(60)

        return results


class SpikeTestScenario:
    """Spike testing for sudden load increases"""

    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.collector = BaselineCollector(host=host, results_dir="performance/results/spike")

    def run_spike_test(self, baseline_users: int = 10, spike_users: int = 50, spike_duration: int = 60):
        """Run spike test scenario"""

        print(f"⚡ Starting spike test: {baseline_users} -> {spike_users} users")

        # Setup environment
        env = Environment(user_classes=[MixedWorkloadUser], host=self.host)
        env.create_local_runner()

        # Phase 1: Baseline load
        print(f"   📈 Phase 1: Baseline load ({baseline_users} users)")
        env.runner.start(baseline_users, spawn_rate=2)
        time.sleep(120)  # 2 minutes baseline

        baseline_stats = env.stats.total
        baseline_rps = baseline_stats.current_rps
        baseline_p95 = baseline_stats.get_response_time_percentile(0.95)

        # Phase 2: Spike
        print(f"   🚀 Phase 2: Spike load ({spike_users} users)")
        env.runner.start(spike_users, spawn_rate=10)  # Fast ramp up
        time.sleep(spike_duration)

        spike_stats = env.stats.total
        spike_rps = spike_stats.current_rps
        spike_p95 = spike_stats.get_response_time_percentile(0.95)

        # Phase 3: Recovery
        print(f"   📉 Phase 3: Recovery ({baseline_users} users)")
        env.runner.start(baseline_users, spawn_rate=5)
        time.sleep(120)  # 2 minutes recovery

        recovery_stats = env.stats.total
        recovery_rps = recovery_stats.current_rps
        recovery_p95 = recovery_stats.get_response_time_percentile(0.95)

        env.runner.stop()

        # Analysis
        print("\n📊 Spike test analysis:")
        print(f"   Baseline:  {baseline_rps:.1f} RPS, {baseline_p95:.0f}ms P95")
        print(f"   Spike:     {spike_rps:.1f} RPS, {spike_p95:.0f}ms P95")
        print(f"   Recovery:  {recovery_rps:.1f} RPS, {recovery_p95:.0f}ms P95")

        # Calculate impact
        rps_degradation = (baseline_rps - spike_rps) / baseline_rps if baseline_rps > 0 else 0
        p95_degradation = (spike_p95 - baseline_p95) / baseline_p95 if baseline_p95 > 0 else 0

        print(f"   Impact: {rps_degradation:.1%} RPS reduction, {p95_degradation:.1%} P95 increase")

        return {
            "baseline": {"rps": baseline_rps, "p95": baseline_p95},
            "spike": {"rps": spike_rps, "p95": spike_p95},
            "recovery": {"rps": recovery_rps, "p95": recovery_p95},
            "degradation": {"rps": rps_degradation, "p95": p95_degradation}
        }


class SoakTestScenario:
    """Soak testing for sustained load over time"""

    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.collector = BaselineCollector(host=host, results_dir="performance/results/soak")

    def run_soak_test(self, users: int = 15, duration_hours: int = 2):
        """Run soak test for extended duration"""

        duration_seconds = duration_hours * 3600

        print(f"🏃‍♂️ Starting soak test: {users} users for {duration_hours} hours")

        # Use mixed workload for realistic long-term testing
        result = self.collector.collect_baseline(
            user_class=MixedWorkloadUser,
            users=users,
            spawn_rate=1,
            run_time=duration_seconds,
            operation_name="soak_test"
        )

        # Additional analysis for soak test
        print(f"\n📊 Soak test completed:")
        print(f"   Duration: {duration_hours} hours")
        print(f"   Final RPS: {result.requests_per_second:.1f}")
        print(f"   Final P95: {result.response_time_p95:.0f}ms")
        print(f"   Error rate: {result.error_rate:.3%}")
        print(f"   Total requests: {result.total_requests:,}")

        return result


def run_complete_performance_suite(host: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run complete performance testing suite"""

    print("🏁 Starting complete performance testing suite...\n")

    results = {
        "timestamp": time.time(),
        "host": host,
        "baselines": [],
        "stress_results": [],
        "spike_results": None,
        "soak_results": None
    }

    # 1. Baseline establishment
    print("=" * 50)
    print("PHASE 1: BASELINE ESTABLISHMENT")
    print("=" * 50)

    baseline_scenario = BaselineScenario(host)
    results["baselines"] = baseline_scenario.run_baseline_collection()

    # 2. Stress testing
    print("\n" + "=" * 50)
    print("PHASE 2: STRESS TESTING")
    print("=" * 50)

    stress_scenario = StressTestScenario(host)
    results["stress_results"] = stress_scenario.run_stress_tests()

    # 3. Spike testing
    print("\n" + "=" * 50)
    print("PHASE 3: SPIKE TESTING")
    print("=" * 50)

    spike_scenario = SpikeTestScenario(host)
    results["spike_results"] = spike_scenario.run_spike_test()

    # 4. Brief soak test (reduced for demo)
    print("\n" + "=" * 50)
    print("PHASE 4: SOAK TESTING (30 minutes)")
    print("=" * 50)

    soak_scenario = SoakTestScenario(host)
    results["soak_results"] = soak_scenario.run_soak_test(users=10, duration_hours=0.5)

    print("\n🎉 Complete performance testing suite finished!")

    return results