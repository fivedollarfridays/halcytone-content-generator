#!/usr/bin/env python3
"""
Monitoring and Alerting Validation Script

Validates that monitoring infrastructure, metrics collection, alerting, and
dashboards are properly configured and operational.

Usage:
    python scripts/validate_monitoring.py --environment production
    python scripts/validate_monitoring.py --environment staging --test-alerts
    python scripts/validate_monitoring.py --environment production --comprehensive
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os

try:
    import httpx
except ImportError:
    print("Error: httpx library required. Install with: pip install httpx")
    sys.exit(1)

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}→ {text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-' * 70}{Colors.RESET}")

def print_success(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str, indent: int = 0):
    prefix = "  " * indent
    print(f"{prefix}{Colors.BLUE}ℹ {text}{Colors.RESET}")


class MonitoringValidator:
    """Validates monitoring and alerting infrastructure"""

    def __init__(self, environment: str, prometheus_url: str = None, grafana_url: str = None,
                 alertmanager_url: str = None):
        self.environment = environment
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.grafana_url = grafana_url or os.getenv('GRAFANA_URL', 'http://localhost:3000')
        self.alertmanager_url = alertmanager_url or os.getenv('ALERTMANAGER_URL', 'http://localhost:9093')
        self.results = []
        self.timeout = 10

    async def validate_all(self, test_alerts: bool = False, comprehensive: bool = False):
        """Run all monitoring validations"""
        print_header("Monitoring & Alerting Validation")
        print_info(f"Environment: {self.environment}")
        print_info(f"Prometheus: {self.prometheus_url}")
        print_info(f"Grafana: {self.grafana_url}")
        print_info(f"AlertManager: {self.alertmanager_url}")
        print_info(f"Timestamp: {datetime.now().isoformat()}")

        await self.validate_prometheus()
        await self.validate_metrics_collection()
        await self.validate_alertmanager()
        await self.validate_alert_rules()

        if test_alerts:
            await self.test_alert_firing()

        await self.validate_grafana()
        await self.validate_dashboards()

        if comprehensive:
            await self.validate_metric_retention()
            await self.validate_recording_rules()

        return self.generate_report()

    async def validate_prometheus(self):
        """Validate Prometheus is accessible and healthy"""
        print_section("Prometheus Health Check")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check health
                response = await client.get(f"{self.prometheus_url}/-/healthy")
                if response.status_code == 200:
                    print_success("Prometheus is healthy")
                    self.results.append(("Prometheus Health", True, "Healthy"))
                else:
                    print_error(f"Prometheus unhealthy: {response.status_code}")
                    self.results.append(("Prometheus Health", False, f"HTTP {response.status_code}"))
                    return

                # Check ready
                response = await client.get(f"{self.prometheus_url}/-/ready")
                if response.status_code == 200:
                    print_success("Prometheus is ready")
                else:
                    print_warning(f"Prometheus not ready: {response.status_code}")

                # Get build info
                response = await client.get(f"{self.prometheus_url}/api/v1/status/buildinfo")
                if response.status_code == 200:
                    build_info = response.json()['data']
                    print_info(f"Version: {build_info.get('version', 'unknown')}", indent=1)

                # Check configuration
                response = await client.get(f"{self.prometheus_url}/api/v1/status/config")
                if response.status_code == 200:
                    print_success("Prometheus configuration accessible")
                    self.results.append(("Prometheus Config", True, "Accessible"))
                else:
                    print_warning("Prometheus configuration not accessible")

        except httpx.ConnectError:
            print_error(f"Cannot connect to Prometheus at {self.prometheus_url}")
            self.results.append(("Prometheus Health", False, "Connection failed"))
        except Exception as e:
            print_error(f"Prometheus check failed: {str(e)}")
            self.results.append(("Prometheus Health", False, str(e)))

    async def validate_metrics_collection(self):
        """Validate that application metrics are being collected"""
        print_section("Metrics Collection")

        # Key metrics to check
        critical_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "process_cpu_seconds_total",
            "process_resident_memory_bytes",
        ]

        application_metrics = [
            "content_generation_total",
            "content_generation_duration_seconds",
            "cache_hits_total",
            "cache_misses_total",
        ]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check each metric
                collected_metrics = []
                missing_metrics = []

                for metric in critical_metrics + application_metrics:
                    response = await client.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": metric}
                    )

                    if response.status_code == 200:
                        data = response.json()['data']
                        if data['result']:
                            collected_metrics.append(metric)
                        else:
                            missing_metrics.append(metric)

                print_info(f"Critical Metrics: {len([m for m in critical_metrics if m in collected_metrics])}/{len(critical_metrics)}")
                print_info(f"Application Metrics: {len([m for m in application_metrics if m in collected_metrics])}/{len(application_metrics)}")

                for metric in collected_metrics[:5]:  # Show first 5
                    print_success(f"{metric}", indent=1)

                if missing_metrics:
                    print_warning(f"{len(missing_metrics)} metrics not found:")
                    for metric in missing_metrics[:5]:  # Show first 5
                        print_warning(f"{metric}", indent=1)

                # Overall assessment
                critical_collected = len([m for m in critical_metrics if m in collected_metrics])
                if critical_collected == len(critical_metrics):
                    self.results.append(("Critical Metrics", True, "All collected"))
                else:
                    self.results.append(("Critical Metrics", False, f"{critical_collected}/{len(critical_metrics)} collected"))

        except Exception as e:
            print_error(f"Metrics collection check failed: {str(e)}")
            self.results.append(("Metrics Collection", False, str(e)))

    async def validate_alertmanager(self):
        """Validate AlertManager is accessible and configured"""
        print_section("AlertManager Health Check")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check health
                response = await client.get(f"{self.alertmanager_url}/-/healthy")
                if response.status_code == 200:
                    print_success("AlertManager is healthy")
                    self.results.append(("AlertManager Health", True, "Healthy"))
                else:
                    print_error(f"AlertManager unhealthy: {response.status_code}")
                    self.results.append(("AlertManager Health", False, f"HTTP {response.status_code}"))
                    return

                # Check ready
                response = await client.get(f"{self.alertmanager_url}/-/ready")
                if response.status_code == 200:
                    print_success("AlertManager is ready")

                # Get status
                response = await client.get(f"{self.alertmanager_url}/api/v1/status")
                if response.status_code == 200:
                    status = response.json()['data']
                    print_info(f"Version: {status.get('versionInfo', {}).get('version', 'unknown')}", indent=1)

                # Check configuration
                response = await client.get(f"{self.alertmanager_url}/api/v1/alerts")
                if response.status_code == 200:
                    alerts = response.json()['data']
                    print_info(f"Active Alerts: {len(alerts)}", indent=1)

                    if alerts:
                        for alert in alerts[:3]:  # Show first 3
                            print_info(f"  {alert.get('labels', {}).get('alertname', 'unknown')}: {alert.get('status', {}).get('state', 'unknown')}", indent=1)

        except httpx.ConnectError:
            print_error(f"Cannot connect to AlertManager at {self.alertmanager_url}")
            self.results.append(("AlertManager Health", False, "Connection failed"))
        except Exception as e:
            print_error(f"AlertManager check failed: {str(e)}")
            self.results.append(("AlertManager Health", False, str(e)))

    async def validate_alert_rules(self):
        """Validate alert rules are loaded and configured"""
        print_section("Alert Rules Validation")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prometheus_url}/api/v1/rules")

                if response.status_code == 200:
                    data = response.json()['data']
                    groups = data.get('groups', [])

                    total_rules = sum(len(g.get('rules', [])) for g in groups)
                    alerting_rules = sum(len([r for r in g.get('rules', []) if r.get('type') == 'alerting']) for g in groups)
                    recording_rules = sum(len([r for r in g.get('rules', []) if r.get('type') == 'recording']) for g in groups)

                    print_info(f"Rule Groups: {len(groups)}")
                    print_info(f"Total Rules: {total_rules}")
                    print_info(f"Alerting Rules: {alerting_rules}")
                    print_info(f"Recording Rules: {recording_rules}")

                    if alerting_rules > 0:
                        print_success(f"{alerting_rules} alerting rules configured")
                        self.results.append(("Alert Rules", True, f"{alerting_rules} rules configured"))

                        # Check for critical alert rules
                        critical_alerts = [
                            "HighErrorRate",
                            "HighResponseTime",
                            "ServiceDown",
                            "HighMemoryUsage",
                            "HighCPUUsage"
                        ]

                        found_alerts = []
                        for group in groups:
                            for rule in group.get('rules', []):
                                if rule.get('type') == 'alerting':
                                    rule_name = rule.get('name', '')
                                    if any(critical in rule_name for critical in critical_alerts):
                                        found_alerts.append(rule_name)

                        if found_alerts:
                            print_success(f"Found {len(found_alerts)} critical alert rules", indent=1)
                            for alert_name in found_alerts[:5]:
                                print_info(f"{alert_name}", indent=2)
                        else:
                            print_warning("No critical alert rules found", indent=1)

                    else:
                        print_warning("No alerting rules configured")
                        self.results.append(("Alert Rules", False, "No rules configured"))

                else:
                    print_error(f"Cannot fetch alert rules: {response.status_code}")
                    self.results.append(("Alert Rules", False, f"HTTP {response.status_code}"))

        except Exception as e:
            print_error(f"Alert rules check failed: {str(e)}")
            self.results.append(("Alert Rules", False, str(e)))

    async def test_alert_firing(self):
        """Test that alerts can be triggered (by checking for firing alerts)"""
        print_section("Alert Firing Test")

        print_warning("Testing alert firing by checking for any active alerts")
        print_info("Note: This does not create test alerts, only checks for existing ones")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prometheus_url}/api/v1/alerts")

                if response.status_code == 200:
                    data = response.json()['data']
                    alerts = data.get('alerts', [])

                    firing_alerts = [a for a in alerts if a.get('state') == 'firing']
                    pending_alerts = [a for a in alerts if a.get('state') == 'pending']

                    print_info(f"Total Alerts: {len(alerts)}")
                    print_info(f"Firing: {len(firing_alerts)}")
                    print_info(f"Pending: {len(pending_alerts)}")

                    if len(alerts) > 0:
                        print_success("Alert system is processing rules")
                        self.results.append(("Alert Firing", True, f"{len(alerts)} alerts tracked"))
                    else:
                        print_info("No alerts currently active (this is normal if system is healthy)")
                        self.results.append(("Alert Firing", True, "No active alerts"))

                    if firing_alerts:
                        print_warning(f"{len(firing_alerts)} alerts currently firing:")
                        for alert in firing_alerts[:5]:
                            labels = alert.get('labels', {})
                            print_warning(f"  {labels.get('alertname', 'unknown')}: {labels.get('severity', 'unknown')}", indent=1)

        except Exception as e:
            print_error(f"Alert firing test failed: {str(e)}")
            self.results.append(("Alert Firing", False, str(e)))

    async def validate_grafana(self):
        """Validate Grafana is accessible"""
        print_section("Grafana Health Check")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check health
                response = await client.get(f"{self.grafana_url}/api/health")
                if response.status_code == 200:
                    health = response.json()
                    print_success(f"Grafana is healthy: {health.get('database', 'unknown')}")
                    self.results.append(("Grafana Health", True, "Healthy"))
                else:
                    print_error(f"Grafana unhealthy: {response.status_code}")
                    self.results.append(("Grafana Health", False, f"HTTP {response.status_code}"))

        except httpx.ConnectError:
            print_error(f"Cannot connect to Grafana at {self.grafana_url}")
            self.results.append(("Grafana Health", False, "Connection failed"))
        except Exception as e:
            print_error(f"Grafana check failed: {str(e)}")
            self.results.append(("Grafana Health", False, str(e)))

    async def validate_dashboards(self):
        """Validate Grafana dashboards are configured"""
        print_section("Dashboard Validation")

        # Check for dashboard files locally
        import os
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        dashboard_dir = project_root / "monitoring" / "grafana" / "dashboards"

        if dashboard_dir.exists():
            dashboard_files = list(dashboard_dir.glob("*.json"))
            print_info(f"Dashboard Files: {len(dashboard_files)}")

            if dashboard_files:
                print_success(f"Found {len(dashboard_files)} dashboard definitions")
                for dashboard_file in dashboard_files[:5]:
                    print_info(f"{dashboard_file.name}", indent=1)
                self.results.append(("Dashboard Files", True, f"{len(dashboard_files)} dashboards"))
            else:
                print_warning("No dashboard files found")
                self.results.append(("Dashboard Files", False, "No dashboards"))
        else:
            print_warning(f"Dashboard directory not found: {dashboard_dir}")
            self.results.append(("Dashboard Files", False, "Directory not found"))

    async def validate_metric_retention(self):
        """Validate metric retention settings"""
        print_section("Metric Retention Validation")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Query for old metrics to check retention
                one_hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp())
                one_day_ago = int((datetime.now() - timedelta(days=1)).timestamp())

                # Check if metrics from 1 hour ago exist
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={
                        "query": f"up[1h]",
                        "time": one_hour_ago
                    }
                )

                if response.status_code == 200:
                    data = response.json()['data']
                    if data['result']:
                        print_success("Metrics retained for at least 1 hour")

                # Check if metrics from 1 day ago exist
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={
                        "query": f"up[1h]",
                        "time": one_day_ago
                    }
                )

                if response.status_code == 200:
                    data = response.json()['data']
                    if data['result']:
                        print_success("Metrics retained for at least 1 day")
                        self.results.append(("Metric Retention", True, "At least 1 day"))
                    else:
                        print_warning("Metrics may not be retained for 1 day")
                        self.results.append(("Metric Retention", True, "Less than 1 day"))

        except Exception as e:
            print_error(f"Metric retention check failed: {str(e)}")
            self.results.append(("Metric Retention", False, str(e)))

    async def validate_recording_rules(self):
        """Validate recording rules are configured"""
        print_section("Recording Rules Validation")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prometheus_url}/api/v1/rules")

                if response.status_code == 200:
                    data = response.json()['data']
                    groups = data.get('groups', [])

                    recording_rules = []
                    for group in groups:
                        for rule in group.get('rules', []):
                            if rule.get('type') == 'recording':
                                recording_rules.append(rule.get('name', 'unknown'))

                    if recording_rules:
                        print_success(f"Found {len(recording_rules)} recording rules")
                        for rule_name in recording_rules[:5]:
                            print_info(f"{rule_name}", indent=1)
                        self.results.append(("Recording Rules", True, f"{len(recording_rules)} rules"))
                    else:
                        print_info("No recording rules configured (optional)")
                        self.results.append(("Recording Rules", True, "None configured"))

        except Exception as e:
            print_error(f"Recording rules check failed: {str(e)}")
            self.results.append(("Recording Rules", False, str(e)))

    def generate_report(self) -> Dict:
        """Generate validation report"""
        print_section("Validation Summary")

        total = len(self.results)
        passed = len([r for r in self.results if r[1]])
        failed = total - passed

        print_info(f"Total Checks: {total}", indent=0)
        if passed == total:
            print_success(f"Passed: {passed}", indent=0)
        else:
            print_info(f"Passed: {passed}", indent=0)

        if failed > 0:
            print_error(f"Failed: {failed}", indent=0)
        else:
            print_success(f"Failed: {failed}", indent=0)

        if failed > 0:
            print("\n" + Colors.RED + Colors.BOLD + "Failed Checks:" + Colors.RESET)
            for name, passed, message in self.results:
                if not passed:
                    print_error(f"{name}: {message}", indent=1)

        # Overall status
        print()
        if failed == 0:
            print_header("✓ MONITORING VALIDATION PASSED")
            overall_status = "PASSED"
        else:
            print_header("✗ MONITORING VALIDATION FAILED")
            overall_status = "FAILED"

        return {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "overall_status": overall_status,
            "summary": {
                "total_checks": total,
                "passed": passed,
                "failed": failed
            },
            "results": [
                {"check": r[0], "passed": r[1], "message": r[2]}
                for r in self.results
            ]
        }


async def main():
    parser = argparse.ArgumentParser(
        description='Monitoring and Alerting Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--environment', default='production', help='Environment name')
    parser.add_argument('--prometheus-url', help='Prometheus URL')
    parser.add_argument('--grafana-url', help='Grafana URL')
    parser.add_argument('--alertmanager-url', help='AlertManager URL')
    parser.add_argument('--test-alerts', action='store_true', help='Test alert firing')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive checks')
    parser.add_argument('--save', help='Save results to JSON file')

    args = parser.parse_args()

    validator = MonitoringValidator(
        environment=args.environment,
        prometheus_url=args.prometheus_url,
        grafana_url=args.grafana_url,
        alertmanager_url=args.alertmanager_url
    )

    report = await validator.validate_all(
        test_alerts=args.test_alerts,
        comprehensive=args.comprehensive
    )

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2)
        print_info(f"\nResults saved to: {args.save}")

    sys.exit(0 if report['overall_status'] == 'PASSED' else 1)


if __name__ == '__main__':
    asyncio.run(main())
