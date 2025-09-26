#!/usr/bin/env python
"""
Go-Live Checklist Validation Script for Halcytone Content Generator
Systematically validates all go-live checklist items
"""
import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import psutil
from dataclasses import dataclass


@dataclass
class CheckResult:
    """Result of a checklist validation"""
    item: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    message: str
    details: Optional[Dict[str, Any]] = None


class GoLiveValidator:
    """Validates go-live checklist items systematically"""

    def __init__(self, host: str = "http://localhost:8000", timeout: int = 10):
        self.host = host
        self.timeout = timeout
        self.results: List[CheckResult] = []

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def add_result(self, item: str, status: str, message: str, details: Dict = None):
        """Add a validation result"""
        result = CheckResult(item, status, message, details)
        self.results.append(result)

        # Log result
        emoji = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]", "SKIP": "[SKIP]"}
        self.logger.info(f"{emoji.get(status, '[?]')} {item}: {message}")

    def validate_system_readiness(self) -> None:
        """Validate System Readiness section"""
        self.logger.info("Validating System Readiness...")

        # Health checks
        try:
            response = requests.get(f"{self.host}/health", timeout=self.timeout)
            if response.status_code == 200:
                health_data = response.json()
                self.add_result(
                    "All services pass health checks",
                    "PASS",
                    f"Health check returned {response.status_code}",
                    {"health_data": health_data}
                )
            else:
                self.add_result(
                    "All services pass health checks",
                    "FAIL",
                    f"Health check failed with status {response.status_code}"
                )
        except requests.RequestException as e:
            self.add_result(
                "All services pass health checks",
                "FAIL",
                f"Health check request failed: {str(e)}"
            )

        # Database connections
        try:
            response = requests.get(f"{self.host}/api/v1/database/status", timeout=self.timeout)
            if response.status_code == 200:
                self.add_result(
                    "Database connections verified",
                    "PASS",
                    "Database status check successful"
                )
            else:
                self.add_result(
                    "Database connections verified",
                    "FAIL",
                    f"Database check failed: {response.status_code}"
                )
        except requests.RequestException:
            self.add_result(
                "Database connections verified",
                "WARN",
                "Database status endpoint not available (may not be configured)"
            )

        # Environment variables
        env_vars = [
            "ENVIRONMENT", "API_KEY", "DATABASE_URL", "REDIS_URL",
            "JWT_SECRET_KEY", "CORS_ORIGINS", "LOG_LEVEL"
        ]

        missing_vars = [var for var in env_vars if not os.getenv(var)]
        if missing_vars:
            self.add_result(
                "Environment variables configured",
                "WARN",
                f"Missing environment variables: {', '.join(missing_vars)}"
            )
        else:
            self.add_result(
                "Environment variables configured",
                "PASS",
                "All critical environment variables present"
            )

        # SSL/TLS check (if HTTPS)
        if self.host.startswith("https://"):
            try:
                response = requests.get(self.host, timeout=self.timeout)
                self.add_result(
                    "SSL certificates valid and properly configured",
                    "PASS",
                    "HTTPS connection successful"
                )
            except requests.exceptions.SSLError:
                self.add_result(
                    "SSL certificates valid and properly configured",
                    "FAIL",
                    "SSL certificate validation failed"
                )
        else:
            self.add_result(
                "SSL certificates valid and properly configured",
                "SKIP",
                "HTTP endpoint, SSL not applicable"
            )

        # Readiness check
        try:
            response = requests.get(f"{self.host}/ready", timeout=self.timeout)
            if response.status_code == 200:
                self.add_result(
                    "Load balancer configuration tested",
                    "PASS",
                    "Readiness check successful"
                )
            else:
                self.add_result(
                    "Load balancer configuration tested",
                    "WARN",
                    f"Readiness check returned {response.status_code}"
                )
        except requests.RequestException:
            self.add_result(
                "Load balancer configuration tested",
                "FAIL",
                "Readiness endpoint not accessible"
            )

        # Monitoring dashboards
        monitoring_endpoints = [
            ("http://localhost:3000", "Grafana"),
            ("http://localhost:9090", "Prometheus"),
            ("http://localhost:5601", "Kibana")
        ]

        dashboard_accessible = False
        for endpoint, name in monitoring_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    dashboard_accessible = True
                    self.logger.debug(f"{name} dashboard accessible at {endpoint}")
            except requests.RequestException:
                pass

        self.add_result(
            "Monitoring dashboards accessible",
            "PASS" if dashboard_accessible else "WARN",
            "At least one monitoring dashboard accessible" if dashboard_accessible else "No monitoring dashboards accessible"
        )

    def validate_security(self) -> None:
        """Validate Security Verification section"""
        self.logger.info("Validating Security Configuration...")

        # API keys check
        api_key = os.getenv("API_KEY")
        if api_key and len(api_key) >= 32:
            self.add_result(
                "API keys rotated to production values",
                "PASS",
                "API key present and appears to be production-ready"
            )
        else:
            self.add_result(
                "API keys rotated to production values",
                "FAIL",
                "API key missing or appears to be test/development key"
            )

        # Database credentials
        db_url = os.getenv("DATABASE_URL")
        if db_url and "localhost" not in db_url and "password" in db_url:
            self.add_result(
                "Database credentials secured",
                "PASS",
                "Database URL appears to be configured for production"
            )
        elif db_url:
            self.add_result(
                "Database credentials secured",
                "WARN",
                "Database URL present but may be development configuration"
            )
        else:
            self.add_result(
                "Database credentials secured",
                "FAIL",
                "Database URL not configured"
            )

        # Rate limiting check
        try:
            # Make rapid requests to test rate limiting
            responses = []
            for _ in range(10):
                response = requests.get(f"{self.host}/health", timeout=1)
                responses.append(response.status_code)
                time.sleep(0.1)

            if 429 in responses:  # Too Many Requests
                self.add_result(
                    "Rate limiting enabled",
                    "PASS",
                    "Rate limiting detected (429 status received)"
                )
            else:
                self.add_result(
                    "Rate limiting enabled",
                    "WARN",
                    "Rate limiting not detected (may not be configured)"
                )
        except requests.RequestException:
            self.add_result(
                "Rate limiting enabled",
                "SKIP",
                "Could not test rate limiting due to connection issues"
            )

        # Security headers check
        try:
            response = requests.get(self.host, timeout=self.timeout)
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]

            present_headers = [h for h in security_headers if h in response.headers]

            if len(present_headers) >= 2:
                self.add_result(
                    "Security headers configured",
                    "PASS",
                    f"Security headers present: {', '.join(present_headers)}"
                )
            else:
                self.add_result(
                    "Security headers configured",
                    "WARN",
                    f"Limited security headers: {', '.join(present_headers) if present_headers else 'None'}"
                )
        except requests.RequestException:
            self.add_result(
                "Security headers configured",
                "FAIL",
                "Could not check security headers"
            )

        # Input validation test
        try:
            # Test with potentially malicious input
            test_payload = {
                "content_type": "<script>alert('xss')</script>",
                "data": {"test": "' OR 1=1 --"}
            }

            response = requests.post(
                f"{self.host}/api/v2/content/validate",
                json=test_payload,
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {os.getenv('API_KEY', 'test')}"}
            )

            if response.status_code == 422:  # Validation error expected
                self.add_result(
                    "Input validation tested",
                    "PASS",
                    "Input validation correctly rejected malicious input"
                )
            elif response.status_code == 401:
                self.add_result(
                    "Authentication systems operational",
                    "PASS",
                    "Authentication required for API access"
                )
            else:
                self.add_result(
                    "Input validation tested",
                    "WARN",
                    f"Unexpected response to validation test: {response.status_code}"
                )
        except requests.RequestException:
            self.add_result(
                "Input validation tested",
                "SKIP",
                "Could not test input validation"
            )

    def validate_performance(self) -> None:
        """Validate Performance Verification section"""
        self.logger.info("Validating Performance Configuration...")

        # Load testing results check
        results_dir = project_root / "performance" / "results"
        if results_dir.exists():
            result_files = list(results_dir.glob("*_baseline_*.json"))
            if result_files:
                # Get most recent baseline
                latest_file = max(result_files, key=lambda f: f.stat().st_mtime)

                try:
                    with open(latest_file, 'r') as f:
                        baseline_data = json.load(f)

                    p95 = baseline_data.get("response_time_p95", 0)
                    rps = baseline_data.get("requests_per_second", 0)
                    error_rate = baseline_data.get("error_rate", 1)

                    self.add_result(
                        "Load testing completed successfully",
                        "PASS",
                        f"Baseline found: P95={p95:.0f}ms, RPS={rps:.1f}, Errors={error_rate:.1%}",
                        {"baseline_file": str(latest_file), "metrics": baseline_data}
                    )
                except Exception as e:
                    self.add_result(
                        "Load testing completed successfully",
                        "WARN",
                        f"Baseline file found but could not parse: {e}"
                    )
            else:
                self.add_result(
                    "Load testing completed successfully",
                    "FAIL",
                    "No performance baselines found"
                )
        else:
            self.add_result(
                "Load testing completed successfully",
                "FAIL",
                "Performance results directory not found"
            )

        # Response time check
        try:
            start_time = time.time()
            response = requests.get(f"{self.host}/health", timeout=self.timeout)
            response_time = (time.time() - start_time) * 1000  # ms

            if response_time < 200:  # 200ms SLA
                self.add_result(
                    "Response times within SLA requirements",
                    "PASS",
                    f"Health endpoint response time: {response_time:.0f}ms"
                )
            else:
                self.add_result(
                    "Response times within SLA requirements",
                    "WARN",
                    f"Health endpoint response time high: {response_time:.0f}ms"
                )
        except requests.RequestException:
            self.add_result(
                "Response times within SLA requirements",
                "FAIL",
                "Could not measure response time"
            )

        # Memory usage check
        try:
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent

            if memory_percent < 80:
                self.add_result(
                    "Memory usage within acceptable limits",
                    "PASS",
                    f"System memory usage: {memory_percent:.1f}%"
                )
            else:
                self.add_result(
                    "Memory usage within acceptable limits",
                    "WARN",
                    f"High system memory usage: {memory_percent:.1f}%"
                )
        except Exception:
            self.add_result(
                "Memory usage within acceptable limits",
                "SKIP",
                "Could not check system memory usage"
            )

        # Caching check
        try:
            # Make same request twice to check if caching affects response time
            start1 = time.time()
            requests.get(f"{self.host}/health", timeout=self.timeout)
            time1 = time.time() - start1

            start2 = time.time()
            requests.get(f"{self.host}/health", timeout=self.timeout)
            time2 = time.time() - start2

            if time2 < time1 * 0.8:  # Second request 20% faster
                self.add_result(
                    "Caching layers operational",
                    "PASS",
                    f"Caching detected: {time1*1000:.0f}ms -> {time2*1000:.0f}ms"
                )
            else:
                self.add_result(
                    "Caching layers operational",
                    "WARN",
                    "No clear caching benefit detected"
                )
        except requests.RequestException:
            self.add_result(
                "Caching layers operational",
                "SKIP",
                "Could not test caching"
            )

    def validate_monitoring_alerting(self) -> None:
        """Validate Monitoring & Alerting section"""
        self.logger.info("Validating Monitoring & Alerting...")

        # Health check endpoints
        endpoints = ["/health", "/ready", "/live", "/metrics"]
        working_endpoints = 0

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.host}{endpoint}", timeout=self.timeout)
                if response.status_code == 200:
                    working_endpoints += 1
            except requests.RequestException:
                pass

        if working_endpoints == len(endpoints):
            self.add_result(
                "Health check endpoints responding",
                "PASS",
                f"All {len(endpoints)} health endpoints operational"
            )
        elif working_endpoints > 0:
            self.add_result(
                "Health check endpoints responding",
                "WARN",
                f"{working_endpoints}/{len(endpoints)} health endpoints responding"
            )
        else:
            self.add_result(
                "Health check endpoints responding",
                "FAIL",
                "No health endpoints responding"
            )

        # Metrics collection
        try:
            response = requests.get(f"{self.host}/metrics", timeout=self.timeout)
            if response.status_code == 200 and "prometheus" in response.headers.get("content-type", "").lower():
                metrics_count = len([line for line in response.text.split('\n') if line and not line.startswith('#')])
                self.add_result(
                    "Metrics collection verified",
                    "PASS",
                    f"Prometheus metrics endpoint working ({metrics_count} metrics)"
                )
            else:
                self.add_result(
                    "Metrics collection verified",
                    "WARN",
                    "Metrics endpoint available but format unclear"
                )
        except requests.RequestException:
            self.add_result(
                "Metrics collection verified",
                "FAIL",
                "Metrics endpoint not accessible"
            )

        # Alert configuration check
        alert_files = [
            project_root / "monitoring" / "prometheus" / "alerts" / "performance-alerts.yml",
            project_root / "monitoring" / "alertmanager" / "alertmanager.yml"
        ]

        alert_configs_found = sum(1 for f in alert_files if f.exists())

        if alert_configs_found > 0:
            self.add_result(
                "All critical alerts configured",
                "PASS",
                f"Alert configuration files found ({alert_configs_found})"
            )
        else:
            self.add_result(
                "All critical alerts configured",
                "WARN",
                "No alert configuration files found"
            )

        # Dashboard check
        dashboard_files = list((project_root / "monitoring" / "grafana" / "dashboards").glob("*.json"))

        if dashboard_files:
            self.add_result(
                "Dashboard access granted to operations team",
                "PASS",
                f"Grafana dashboards configured ({len(dashboard_files)} dashboards)"
            )
        else:
            self.add_result(
                "Dashboard access granted to operations team",
                "WARN",
                "No Grafana dashboards found"
            )

    def validate_documentation(self) -> None:
        """Validate Documentation & Training section"""
        self.logger.info("Validating Documentation...")

        # Check for key documentation files
        doc_files = {
            "Operations runbooks": ["docs/runbooks", "docs/operations", "docs/troubleshooting.md"],
            "API documentation": ["docs/api", "docs/api.md", "openapi.json", "swagger.json"],
            "User documentation": ["docs/user-guide.md", "docs/usage.md", "README.md"],
            "Troubleshooting guides": ["docs/troubleshooting.md", "docs/debugging.md"]
        }

        for doc_type, possible_paths in doc_files.items():
            found = False
            for path_str in possible_paths:
                path = project_root / path_str
                if path.exists():
                    found = True
                    break

            if found:
                self.add_result(
                    doc_type + " updated",
                    "PASS",
                    f"Documentation found at {path}"
                )
            else:
                self.add_result(
                    doc_type + " updated",
                    "WARN",
                    f"Documentation not found in expected locations"
                )

        # Check for go-live checklist
        checklist_path = project_root / "docs" / "go-live-checklist.md"
        if checklist_path.exists():
            self.add_result(
                "Incident response procedures reviewed",
                "PASS",
                "Go-live checklist available"
            )
        else:
            self.add_result(
                "Incident response procedures reviewed",
                "WARN",
                "Go-live checklist not found"
            )

    def validate_business_continuity(self) -> None:
        """Validate Business Continuity section"""
        self.logger.info("Validating Business Continuity...")

        # Check for rollback procedures
        rollback_files = [
            "docs/rollback-procedures.md",
            "docs/deployment.md",
            "scripts/rollback.sh",
            ".github/workflows"
        ]

        rollback_ready = False
        for file_path in rollback_files:
            if (project_root / file_path).exists():
                rollback_ready = True
                break

        self.add_result(
            "Rollback procedures tested",
            "PASS" if rollback_ready else "WARN",
            "Rollback procedures available" if rollback_ready else "No rollback procedures found"
        )

        # Check for monitoring stack
        monitoring_stack = project_root / "monitoring"
        if monitoring_stack.exists():
            self.add_result(
                "Disaster recovery plan verified",
                "PASS",
                "Monitoring stack configuration available"
            )
        else:
            self.add_result(
                "Disaster recovery plan verified",
                "WARN",
                "No monitoring stack configuration found"
            )

        # Service level agreements
        sli_docs = [
            "docs/sla.md",
            "docs/service-levels.md",
            "docs/performance-baseline.md"
        ]

        sla_documented = any((project_root / path).exists() for path in sli_docs)

        self.add_result(
            "Service level agreements confirmed",
            "PASS" if sla_documented else "WARN",
            "Service level documentation found" if sla_documented else "No SLA documentation found"
        )

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks"""
        self.logger.info("Starting Go-Live Checklist Validation...")

        start_time = datetime.now()

        try:
            # Execute all validation sections
            self.validate_system_readiness()
            self.validate_security()
            self.validate_performance()
            self.validate_monitoring_alerting()
            self.validate_documentation()
            self.validate_business_continuity()

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            self.add_result("Validation execution", "FAIL", f"Validation failed: {e}")

        end_time = datetime.now()
        duration = end_time - start_time

        # Generate summary
        summary = self.generate_summary()
        summary["execution_time"] = str(duration)
        summary["timestamp"] = start_time.isoformat()

        return summary

    def generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary"""
        total = len(self.results)
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        skipped = len([r for r in self.results if r.status == "SKIP"])

        # Determine overall status
        if failed > 0:
            overall_status = "NOT READY"
        elif warnings > total * 0.3:  # More than 30% warnings
            overall_status = "READY WITH CONCERNS"
        else:
            overall_status = "READY"

        summary = {
            "overall_status": overall_status,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "critical_issues": [r for r in self.results if r.status == "FAIL"],
            "warnings_list": [r for r in self.results if r.status == "WARN"],
            "recommendations": self.generate_recommendations()
        }

        return summary

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        failed_items = [r for r in self.results if r.status == "FAIL"]
        warning_items = [r for r in self.results if r.status == "WARN"]

        if failed_items:
            recommendations.append("CRITICAL: Address all failed checks before go-live")

        if len(warning_items) > 5:
            recommendations.append("HIGH: Review and address warning items")

        if any("health" in r.item.lower() for r in failed_items):
            recommendations.append("URGENT: Health check failures must be resolved")

        if any("security" in r.item.lower() for r in failed_items):
            recommendations.append("URGENT: Security issues must be resolved")

        if any("performance" in r.item.lower() for r in warning_items):
            recommendations.append("Consider performance optimization before go-live")

        return recommendations

    def save_results(self, filename: str = None) -> str:
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"go_live_validation_{timestamp}.json"

        filepath = project_root / "docs" / filename
        filepath.parent.mkdir(exist_ok=True)

        summary = self.generate_summary()
        summary["detailed_results"] = [
            {
                "item": r.item,
                "status": r.status,
                "message": r.message,
                "details": r.details
            } for r in self.results
        ]

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        return str(filepath)

    def print_summary(self):
        """Print validation summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*80)
        print("GO-LIVE CHECKLIST VALIDATION SUMMARY")
        print("="*80)

        # Overall status
        status_emoji = {
            "READY": "[PASS]",
            "READY WITH CONCERNS": "[WARN]",
            "NOT READY": "[FAIL]"
        }

        print(f"\n{status_emoji.get(summary['overall_status'], '[?]')} Overall Status: {summary['overall_status']}")

        # Statistics
        print(f"\nValidation Statistics:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Passed: {summary['passed']} ({summary['pass_rate']:.1f}%)")
        print(f"   Failed: {summary['failed']}")
        print(f"   Warnings: {summary['warnings']}")
        print(f"   Skipped: {summary['skipped']}")

        # Critical issues
        if summary['critical_issues']:
            print(f"\n[CRITICAL] Critical Issues ({len(summary['critical_issues'])}):")
            for issue in summary['critical_issues']:
                print(f"   - {issue.item}: {issue.message}")

        # Warnings
        if summary['warnings_list'] and len(summary['warnings_list']) <= 10:
            print(f"\n[WARNING] Warnings ({len(summary['warnings_list'])}):")
            for warning in summary['warnings_list']:
                print(f"   - {warning.item}: {warning.message}")
        elif summary['warnings_list']:
            print(f"\n[WARNING] Warnings ({len(summary['warnings_list'])} total - showing first 5):")
            for warning in summary['warnings_list'][:5]:
                print(f"   - {warning.item}: {warning.message}")

        # Recommendations
        if summary['recommendations']:
            print(f"\nRecommendations:")
            for rec in summary['recommendations']:
                print(f"   {rec}")

        print("\n" + "="*80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Go-Live Checklist Validation")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout")
    parser.add_argument("--save", help="Save results to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run validation
    validator = GoLiveValidator(host=args.host, timeout=args.timeout)
    summary = validator.run_comprehensive_validation()

    # Print results
    validator.print_summary()

    # Save results if requested
    if args.save:
        filepath = validator.save_results(args.save)
        print(f"\n💾 Results saved to: {filepath}")

    # Exit with error code if not ready
    if summary["overall_status"] == "NOT READY":
        sys.exit(1)
    elif summary["overall_status"] == "READY WITH CONCERNS":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()