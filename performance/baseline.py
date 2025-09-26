"""
Performance baseline collection and analysis for Halcytone Content Generator
"""
import json
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

import requests
import numpy as np
from locust import HttpUser
from locust.env import Environment
from locust.stats import RequestStats

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    percentile: Optional[float] = None
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class PerformanceBaseline:
    """Performance baseline for a specific operation"""
    operation: str
    environment: str
    version: str
    timestamp: datetime

    # Response time metrics (ms)
    response_time_mean: float
    response_time_median: float
    response_time_p95: float
    response_time_p99: float
    response_time_max: float

    # Throughput metrics
    requests_per_second: float
    concurrent_users: int
    total_requests: int

    # Error metrics
    error_rate: float
    error_count: int

    # Resource metrics (if available)
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

    # Additional context
    test_duration: int = 0
    notes: str = ""
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}


class BaselineCollector:
    """Collect performance baselines from load tests"""

    def __init__(self, host: str = "http://localhost:8000", results_dir: str = "performance/results"):
        self.host = host
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def collect_baseline(
        self,
        user_class: HttpUser,
        users: int = 10,
        spawn_rate: float = 2,
        run_time: int = 300,
        operation_name: str = None
    ) -> PerformanceBaseline:
        """Collect performance baseline for a specific user scenario"""

        operation = operation_name or user_class.__name__
        logger.info(f"Collecting baseline for {operation} with {users} users")

        # Setup Locust environment
        env = Environment(user_classes=[user_class], host=self.host)

        # Start the test
        env.create_local_runner()
        env.runner.start(users, spawn_rate=spawn_rate)

        start_time = time.time()

        # Let the test run
        time.sleep(run_time)

        # Stop the test
        env.runner.stop()

        # Collect metrics
        stats = env.stats
        total_stats = stats.total

        # Calculate baseline metrics
        baseline = PerformanceBaseline(
            operation=operation,
            environment="baseline",
            version="0.1.0",
            timestamp=datetime.now(),

            # Response times
            response_time_mean=total_stats.avg_response_time,
            response_time_median=total_stats.median_response_time,
            response_time_p95=total_stats.get_response_time_percentile(0.95),
            response_time_p99=total_stats.get_response_time_percentile(0.99),
            response_time_max=total_stats.max_response_time,

            # Throughput
            requests_per_second=total_stats.current_rps,
            concurrent_users=users,
            total_requests=total_stats.num_requests,

            # Errors
            error_rate=total_stats.failure_ratio,
            error_count=total_stats.num_failures,

            # Test context
            test_duration=run_time,
            raw_data=self._extract_detailed_stats(stats)
        )

        # Save baseline
        self._save_baseline(baseline)

        logger.info(f"Baseline collected: {baseline.requests_per_second:.1f} RPS, "
                   f"{baseline.response_time_p95:.0f}ms p95")

        return baseline

    def _extract_detailed_stats(self, stats: RequestStats) -> Dict[str, Any]:
        """Extract detailed statistics from Locust stats"""
        detailed_stats = {
            "endpoints": {},
            "timeline": [],
            "errors": []
        }

        # Endpoint-specific stats
        for name, stat in stats.entries.items():
            if name != "Aggregated":
                detailed_stats["endpoints"][name] = {
                    "method": stat.method,
                    "name": stat.name,
                    "num_requests": stat.num_requests,
                    "num_failures": stat.num_failures,
                    "avg_response_time": stat.avg_response_time,
                    "median_response_time": stat.median_response_time,
                    "max_response_time": stat.max_response_time,
                    "min_response_time": stat.min_response_time,
                    "current_rps": stat.current_rps,
                    "failure_ratio": stat.failure_ratio
                }

        # Error details
        for error in stats.errors.values():
            detailed_stats["errors"].append({
                "method": error.method,
                "name": error.name,
                "error": error.error,
                "occurrences": error.occurrences
            })

        return detailed_stats

    def _save_baseline(self, baseline: PerformanceBaseline):
        """Save baseline to disk"""
        filename = f"{baseline.operation}_{baseline.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_dir / filename

        # Convert to dict for JSON serialization
        data = asdict(baseline)
        data["timestamp"] = baseline.timestamp.isoformat()

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Baseline saved to {filepath}")

    def load_baseline(self, filepath: Path) -> PerformanceBaseline:
        """Load baseline from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Convert timestamp back
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        return PerformanceBaseline(**data)

    def get_latest_baseline(self, operation: str) -> Optional[PerformanceBaseline]:
        """Get the most recent baseline for an operation"""
        pattern = f"{operation}_*.json"
        files = list(self.results_dir.glob(pattern))

        if not files:
            return None

        # Get most recent
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return self.load_baseline(latest_file)


class MetricsAnalyzer:
    """Analyze performance metrics and detect regressions"""

    def __init__(self, baseline_collector: BaselineCollector):
        self.collector = baseline_collector

    def compare_baselines(
        self,
        current: PerformanceBaseline,
        previous: PerformanceBaseline,
        thresholds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """Compare current performance against previous baseline"""

        default_thresholds = {
            "response_time_regression": 0.20,  # 20% increase is a regression
            "throughput_regression": 0.15,     # 15% decrease is a regression
            "error_rate_increase": 0.05        # 5% absolute increase is concerning
        }

        thresholds = {**default_thresholds, **(thresholds or {})}

        analysis = {
            "comparison_timestamp": datetime.now().isoformat(),
            "current_operation": current.operation,
            "previous_operation": previous.operation,
            "metrics_comparison": {},
            "regressions": [],
            "improvements": [],
            "overall_assessment": "PASS"
        }

        # Response time comparison
        rt_change = (current.response_time_p95 - previous.response_time_p95) / previous.response_time_p95
        analysis["metrics_comparison"]["response_time_p95"] = {
            "current": current.response_time_p95,
            "previous": previous.response_time_p95,
            "change_percent": rt_change * 100,
            "regression": rt_change > thresholds["response_time_regression"]
        }

        if rt_change > thresholds["response_time_regression"]:
            analysis["regressions"].append({
                "metric": "response_time_p95",
                "change_percent": rt_change * 100,
                "severity": "HIGH" if rt_change > 0.5 else "MEDIUM"
            })
        elif rt_change < -0.10:  # 10% improvement
            analysis["improvements"].append({
                "metric": "response_time_p95",
                "improvement_percent": abs(rt_change) * 100
            })

        # Throughput comparison
        rps_change = (current.requests_per_second - previous.requests_per_second) / previous.requests_per_second
        analysis["metrics_comparison"]["requests_per_second"] = {
            "current": current.requests_per_second,
            "previous": previous.requests_per_second,
            "change_percent": rps_change * 100,
            "regression": rps_change < -thresholds["throughput_regression"]
        }

        if rps_change < -thresholds["throughput_regression"]:
            analysis["regressions"].append({
                "metric": "requests_per_second",
                "change_percent": rps_change * 100,
                "severity": "HIGH" if rps_change < -0.3 else "MEDIUM"
            })
        elif rps_change > 0.15:  # 15% improvement
            analysis["improvements"].append({
                "metric": "requests_per_second",
                "improvement_percent": rps_change * 100
            })

        # Error rate comparison
        error_change = current.error_rate - previous.error_rate
        analysis["metrics_comparison"]["error_rate"] = {
            "current": current.error_rate,
            "previous": previous.error_rate,
            "change_absolute": error_change,
            "regression": error_change > thresholds["error_rate_increase"]
        }

        if error_change > thresholds["error_rate_increase"]:
            analysis["regressions"].append({
                "metric": "error_rate",
                "change_absolute": error_change,
                "severity": "CRITICAL" if error_change > 0.10 else "HIGH"
            })

        # Overall assessment
        if analysis["regressions"]:
            critical_regressions = [r for r in analysis["regressions"] if r["severity"] == "CRITICAL"]
            high_regressions = [r for r in analysis["regressions"] if r["severity"] == "HIGH"]

            if critical_regressions:
                analysis["overall_assessment"] = "CRITICAL"
            elif high_regressions:
                analysis["overall_assessment"] = "FAIL"
            else:
                analysis["overall_assessment"] = "WARN"

        return analysis

    def analyze_trend(self, operation: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        pattern = f"{operation}_*.json"
        files = list(self.collector.results_dir.glob(pattern))

        if len(files) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Load recent baselines
        cutoff_date = datetime.now() - timedelta(days=days)
        baselines = []

        for file in files:
            baseline = self.collector.load_baseline(file)
            if baseline.timestamp >= cutoff_date:
                baselines.append(baseline)

        if len(baselines) < 2:
            return {"error": "Insufficient recent data for trend analysis"}

        # Sort by timestamp
        baselines.sort(key=lambda b: b.timestamp)

        # Calculate trends
        timestamps = [b.timestamp for b in baselines]
        response_times = [b.response_time_p95 for b in baselines]
        throughputs = [b.requests_per_second for b in baselines]
        error_rates = [b.error_rate for b in baselines]

        # Simple linear trend calculation
        def calculate_trend(values):
            if len(values) < 2:
                return 0
            x = list(range(len(values)))
            return np.polyfit(x, values, 1)[0]  # slope of linear fit

        return {
            "operation": operation,
            "period_days": days,
            "data_points": len(baselines),
            "date_range": {
                "start": baselines[0].timestamp.isoformat(),
                "end": baselines[-1].timestamp.isoformat()
            },
            "trends": {
                "response_time_p95": {
                    "trend_ms_per_day": calculate_trend(response_times),
                    "current": response_times[-1],
                    "previous": response_times[0],
                    "change_percent": ((response_times[-1] - response_times[0]) / response_times[0]) * 100
                },
                "requests_per_second": {
                    "trend_rps_per_day": calculate_trend(throughputs),
                    "current": throughputs[-1],
                    "previous": throughputs[0],
                    "change_percent": ((throughputs[-1] - throughputs[0]) / throughputs[0]) * 100
                },
                "error_rate": {
                    "trend_per_day": calculate_trend(error_rates),
                    "current": error_rates[-1],
                    "previous": error_rates[0],
                    "change_absolute": error_rates[-1] - error_rates[0]
                }
            }
        }


def create_baseline_report(baselines: List[PerformanceBaseline], output_file: str = None) -> str:
    """Create a comprehensive baseline report"""

    if not baselines:
        return "No baseline data available"

    # Sort by timestamp
    baselines.sort(key=lambda b: b.timestamp)
    latest = baselines[-1]

    report_lines = [
        "# Performance Baseline Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- **Operations analyzed**: {len(set(b.operation for b in baselines))}",
        f"- **Total baselines**: {len(baselines)}",
        f"- **Latest baseline**: {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Key Performance Indicators",
        ""
    ]

    # Group by operation
    operations = {}
    for baseline in baselines:
        if baseline.operation not in operations:
            operations[baseline.operation] = []
        operations[baseline.operation].append(baseline)

    for operation, op_baselines in operations.items():
        latest_baseline = max(op_baselines, key=lambda b: b.timestamp)

        report_lines.extend([
            f"### {operation}",
            f"- **Response Time (P95)**: {latest_baseline.response_time_p95:.0f}ms",
            f"- **Throughput**: {latest_baseline.requests_per_second:.1f} RPS",
            f"- **Error Rate**: {latest_baseline.error_rate:.2%}",
            f"- **Concurrent Users**: {latest_baseline.concurrent_users}",
            f"- **Test Duration**: {latest_baseline.test_duration}s",
            ""
        ])

        if len(op_baselines) > 1:
            # Add trend information
            sorted_baselines = sorted(op_baselines, key=lambda b: b.timestamp)
            first, last = sorted_baselines[0], sorted_baselines[-1]

            rt_change = ((last.response_time_p95 - first.response_time_p95) / first.response_time_p95) * 100
            rps_change = ((last.requests_per_second - first.requests_per_second) / first.requests_per_second) * 100

            report_lines.extend([
                "**Trends:**",
                f"- Response time trend: {rt_change:+.1f}%",
                f"- Throughput trend: {rps_change:+.1f}%",
                ""
            ])

    # SLI recommendations
    report_lines.extend([
        "## Service Level Indicator (SLI) Recommendations",
        "",
        "Based on the baseline data, consider these SLIs:",
        ""
    ])

    for operation, op_baselines in operations.items():
        latest_baseline = max(op_baselines, key=lambda b: b.timestamp)

        # Conservative SLI recommendations (add buffer to baselines)
        sli_p95 = latest_baseline.response_time_p95 * 1.5  # 50% buffer
        sli_error_rate = max(latest_baseline.error_rate * 2, 0.01)  # 2x or 1% minimum

        report_lines.extend([
            f"### {operation} SLIs",
            f"- **Availability**: 99.9% (error rate < {sli_error_rate:.1%})",
            f"- **Latency**: P95 < {sli_p95:.0f}ms",
            f"- **Throughput**: > {latest_baseline.requests_per_second * 0.8:.0f} RPS",
            ""
        ])

    report_lines.extend([
        "## Alert Thresholds",
        "",
        "Recommended alert thresholds based on baselines:",
        ""
    ])

    for operation, op_baselines in operations.items():
        latest_baseline = max(op_baselines, key=lambda b: b.timestamp)

        warn_p95 = latest_baseline.response_time_p95 * 1.25  # 25% above baseline
        critical_p95 = latest_baseline.response_time_p95 * 1.5  # 50% above baseline

        report_lines.extend([
            f"### {operation} Alerts",
            f"- **Warning**: P95 > {warn_p95:.0f}ms or RPS < {latest_baseline.requests_per_second * 0.9:.0f}",
            f"- **Critical**: P95 > {critical_p95:.0f}ms or RPS < {latest_baseline.requests_per_second * 0.8:.0f}",
            f"- **Error rate**: Warning > {latest_baseline.error_rate + 0.02:.1%}, Critical > {latest_baseline.error_rate + 0.05:.1%}",
            ""
        ])

    report_content = "\n".join(report_lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_content)
        logger.info(f"Report saved to {output_file}")

    return report_content