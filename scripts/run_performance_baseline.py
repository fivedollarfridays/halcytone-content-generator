#!/usr/bin/env python
"""
Run performance baseline collection for Halcytone Content Generator
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from performance.baseline import BaselineCollector, MetricsAnalyzer, create_baseline_report
from performance.scenarios import (
    BaselineScenario,
    StressTestScenario,
    SpikeTestScenario,
    SoakTestScenario,
    run_complete_performance_suite
)


def setup_logging(level=logging.INFO):
    """Setup logging for performance testing"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('performance/results/performance_test.log')
        ]
    )


def check_service_health(host: str) -> bool:
    """Check if the target service is healthy before testing"""
    import requests

    try:
        response = requests.get(f"{host}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Service health check passed: {host}")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Service health check failed: {e}")
        return False


def run_baseline_only(host: str):
    """Run only baseline collection"""
    print("📊 Running baseline collection only...")

    scenario = BaselineScenario(host)
    baselines = scenario.run_baseline_collection()

    # Generate report
    report = create_baseline_report(baselines)

    # Save report
    report_file = Path("performance/results/baseline_report.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n📄 Baseline report saved to: {report_file}")
    print("\n" + "="*60)
    print("BASELINE SUMMARY")
    print("="*60)

    for baseline in baselines:
        print(f"\n{baseline.operation}:")
        print(f"  Response Time (P95): {baseline.response_time_p95:.0f}ms")
        print(f"  Throughput: {baseline.requests_per_second:.1f} RPS")
        print(f"  Error Rate: {baseline.error_rate:.2%}")
        print(f"  Concurrent Users: {baseline.concurrent_users}")


def run_stress_only(host: str):
    """Run only stress testing"""
    print("💪 Running stress testing only...")

    scenario = StressTestScenario(host)
    results = scenario.run_stress_tests()

    print("\n" + "="*60)
    print("STRESS TEST SUMMARY")
    print("="*60)

    for result in results:
        print(f"\n{result.operation}:")
        print(f"  Response Time (P95): {result.response_time_p95:.0f}ms")
        print(f"  Throughput: {result.requests_per_second:.1f} RPS")
        print(f"  Error Rate: {result.error_rate:.2%}")
        print(f"  Users: {result.concurrent_users}")


def run_spike_only(host: str):
    """Run only spike testing"""
    print("⚡ Running spike testing only...")

    scenario = SpikeTestScenario(host)
    result = scenario.run_spike_test(baseline_users=10, spike_users=50, spike_duration=60)

    print("\n" + "="*60)
    print("SPIKE TEST SUMMARY")
    print("="*60)
    print(f"Baseline: {result['baseline']['rps']:.1f} RPS, {result['baseline']['p95']:.0f}ms P95")
    print(f"Spike: {result['spike']['rps']:.1f} RPS, {result['spike']['p95']:.0f}ms P95")
    print(f"Recovery: {result['recovery']['rps']:.1f} RPS, {result['recovery']['p95']:.0f}ms P95")
    print(f"Impact: {result['degradation']['rps']:.1%} RPS reduction, {result['degradation']['p95']:.1%} P95 increase")


def run_comparison(host: str, operation: str):
    """Run comparison against previous baseline"""
    print(f"📈 Running comparison for {operation}...")

    collector = BaselineCollector(host)
    analyzer = MetricsAnalyzer(collector)

    # Get previous baseline
    previous = collector.get_latest_baseline(operation)
    if not previous:
        print(f"❌ No previous baseline found for {operation}")
        return

    print(f"📊 Found previous baseline from {previous.timestamp}")

    # Run new test
    scenario = BaselineScenario(host)
    baselines = scenario.run_baseline_collection()

    # Find matching operation
    current = None
    for baseline in baselines:
        if operation in baseline.operation:
            current = baseline
            break

    if not current:
        print(f"❌ Could not find current results for {operation}")
        return

    # Compare
    analysis = analyzer.compare_baselines(current, previous)

    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)

    print(f"\nOverall Assessment: {analysis['overall_assessment']}")

    if analysis['improvements']:
        print("\n✅ Improvements:")
        for improvement in analysis['improvements']:
            print(f"  - {improvement['metric']}: {improvement.get('improvement_percent', improvement.get('change_percent', 'N/A'))}% better")

    if analysis['regressions']:
        print("\n⚠️ Regressions:")
        for regression in analysis['regressions']:
            print(f"  - {regression['metric']}: {regression.get('change_percent', regression.get('change_absolute', 'N/A'))} worse ({regression['severity']})")

    # Detailed metrics
    print("\n📊 Detailed Comparison:")
    for metric, data in analysis['metrics_comparison'].items():
        print(f"  {metric}:")
        print(f"    Previous: {data['previous']}")
        print(f"    Current: {data['current']}")
        if 'change_percent' in data:
            print(f"    Change: {data['change_percent']:+.1f}%")
        elif 'change_absolute' in data:
            print(f"    Change: {data['change_absolute']:+.3f}")


def run_trend_analysis(host: str, operation: str, days: int = 30):
    """Run trend analysis"""
    print(f"📈 Running trend analysis for {operation} over {days} days...")

    collector = BaselineCollector(host)
    analyzer = MetricsAnalyzer(collector)

    trends = analyzer.analyze_trend(operation, days)

    if 'error' in trends:
        print(f"❌ {trends['error']}")
        return

    print("\n" + "="*60)
    print("PERFORMANCE TREND ANALYSIS")
    print("="*60)

    print(f"Operation: {trends['operation']}")
    print(f"Period: {trends['period_days']} days")
    print(f"Data Points: {trends['data_points']}")
    print(f"Date Range: {trends['date_range']['start']} to {trends['date_range']['end']}")

    print("\nTrends:")
    for metric, trend_data in trends['trends'].items():
        change = trend_data['change_percent']
        direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        print(f"  {metric}: {direction} {change:+.1f}% over period")
        print(f"    Current: {trend_data['current']}")
        print(f"    Previous: {trend_data['previous']}")


def main():
    parser = argparse.ArgumentParser(description="Run Halcytone performance baseline tests")

    parser.add_argument("--host", "-H", default="http://localhost:8000",
                       help="Target host for testing")
    parser.add_argument("--type", "-t", default="baseline",
                       choices=["baseline", "stress", "spike", "soak", "complete", "compare", "trend"],
                       help="Type of performance test to run")
    parser.add_argument("--operation", "-o",
                       help="Operation name for comparison/trend analysis")
    parser.add_argument("--days", "-d", type=int, default=30,
                       help="Days to look back for trend analysis")
    parser.add_argument("--users", "-u", type=int, default=10,
                       help="Number of concurrent users")
    parser.add_argument("--duration", "-D", type=int, default=300,
                       help="Test duration in seconds")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--no-health-check", action="store_true",
                       help="Skip health check before testing")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # Create results directory
    Path("performance/results").mkdir(parents=True, exist_ok=True)

    print(f"🚀 Halcytone Performance Testing")
    print(f"Target: {args.host}")
    print(f"Test Type: {args.type}")
    print("=" * 60)

    # Health check (unless disabled)
    if not args.no_health_check:
        if not check_service_health(args.host):
            print("❌ Service health check failed. Cannot proceed with testing.")
            print("   Make sure the application is running and accessible.")
            sys.exit(1)

    # Run appropriate test type
    try:
        if args.type == "baseline":
            run_baseline_only(args.host)

        elif args.type == "stress":
            run_stress_only(args.host)

        elif args.type == "spike":
            run_spike_only(args.host)

        elif args.type == "soak":
            print(f"🏃‍♂️ Running soak test: {args.users} users for {args.duration//3600:.1f} hours...")
            scenario = SoakTestScenario(args.host)
            result = scenario.run_soak_test(args.users, args.duration//3600)

        elif args.type == "complete":
            results = run_complete_performance_suite(args.host)
            print(f"\n🎉 Complete test suite finished! Results available in performance/results/")

        elif args.type == "compare":
            if not args.operation:
                print("❌ --operation required for comparison")
                sys.exit(1)
            run_comparison(args.host, args.operation)

        elif args.type == "trend":
            if not args.operation:
                print("❌ --operation required for trend analysis")
                sys.exit(1)
            run_trend_analysis(args.host, args.operation, args.days)

        print(f"\n✅ Performance testing completed successfully!")

    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()