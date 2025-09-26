#!/usr/bin/env python
"""
Pre-production environment checks and final validation
Comprehensive validation script for production deployment readiness
"""
import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests


class PreProductionValidator:
    """Comprehensive pre-production validation system"""

    def __init__(self, target_host: str, environment: str = "production"):
        self.target_host = target_host
        self.environment = environment
        self.validation_results = []
        self.start_time = datetime.now()

    def log_result(self, check: str, status: str, details: str, data: Any = None):
        """Log validation result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "check": check,
            "status": status,  # PASS, FAIL, WARN, INFO
            "details": details,
            "data": data
        }
        self.validation_results.append(result)

        status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
        print(f"{status_icon.get(status, '?')} {check}: {details}")

    def check_environment_readiness(self) -> bool:
        """Check production environment readiness"""
        print("\n🔧 Environment Readiness Validation")
        print("=" * 50)

        # Critical environment variables
        required_vars = {
            "ENVIRONMENT": "production",
            "API_KEY": None,  # Should be set
            "DATABASE_URL": None,  # Should be set
            "JWT_SECRET_KEY": None,  # Should be set
            "REDIS_URL": None,  # Should be set
            "CORS_ORIGINS": None,  # Should be set
            "LOG_LEVEL": ["INFO", "WARNING", "ERROR"],
            "MONITORING_ENABLED": "true"
        }

        env_ready = True
        for var, expected in required_vars.items():
            value = os.getenv(var)

            if not value:
                self.log_result(f"Environment Variable: {var}", "FAIL", "Not configured")
                env_ready = False
            elif expected == "production" and value != "production":
                self.log_result(f"Environment Variable: {var}", "WARN", f"Set to '{value}', expected 'production'")
            elif isinstance(expected, list) and value not in expected:
                self.log_result(f"Environment Variable: {var}", "WARN", f"Set to '{value}', expected one of {expected}")
            else:
                self.log_result(f"Environment Variable: {var}", "PASS", f"Configured: {value[:20]}..." if len(str(value)) > 20 else f"Configured: {value}")

        return env_ready

    def check_application_health(self) -> bool:
        """Comprehensive application health validation"""
        print("\n🏥 Application Health Validation")
        print("=" * 50)

        health_checks = [
            ("/health", "Basic Health Check"),
            ("/ready", "Readiness Probe"),
            ("/live", "Liveness Probe"),
            ("/metrics", "Metrics Collection")
        ]

        all_healthy = True
        health_data = {}

        for endpoint, description in health_checks:
            try:
                start_time = time.time()
                response = requests.get(f"{self.target_host}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    self.log_result(
                        f"Health Check: {description}",
                        "PASS",
                        f"Response: {response.status_code}, Time: {response_time:.0f}ms"
                    )

                    # Store health data for analysis
                    if endpoint == "/health":
                        try:
                            health_data = response.json()
                        except:
                            pass

                else:
                    self.log_result(
                        f"Health Check: {description}",
                        "FAIL",
                        f"HTTP {response.status_code}"
                    )
                    all_healthy = False

            except requests.RequestException as e:
                self.log_result(
                    f"Health Check: {description}",
                    "FAIL",
                    f"Request failed: {str(e)[:100]}"
                )
                all_healthy = False

        # Analyze health check data
        if health_data:
            self.log_result(
                "Health Data Analysis",
                "INFO",
                f"Health check data: {json.dumps(health_data, indent=2)[:200]}...",
                health_data
            )

        return all_healthy

    def check_performance_readiness(self) -> bool:
        """Validate performance readiness for production"""
        print("\n⚡ Performance Readiness Validation")
        print("=" * 50)

        performance_ready = True

        # Check for performance baselines
        baseline_files = list((project_root / "performance" / "results").glob("*_baseline_*.json"))

        if not baseline_files:
            self.log_result(
                "Performance Baselines",
                "FAIL",
                "No performance baselines found"
            )
            return False

        # Analyze most recent baselines
        baselines = {}
        for file in baseline_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    operation = data.get("operation", "unknown")
                    baselines[operation] = data
            except Exception as e:
                self.log_result(
                    f"Baseline File: {file.name}",
                    "WARN",
                    f"Could not parse: {e}"
                )

        # Validate against production readiness criteria
        readiness_criteria = {
            "health_check_baseline": {
                "max_p95": 200,  # 200ms
                "min_rps": 50,   # 50 RPS
                "max_error_rate": 0.01  # 1%
            },
            "content_generation_baseline": {
                "max_p95": 8000,  # 8s (relaxed for production)
                "min_rps": 3,     # 3 RPS
                "max_error_rate": 0.05  # 5%
            },
            "mixed_workload_baseline": {
                "max_p95": 5000,  # 5s
                "min_rps": 8,     # 8 RPS
                "max_error_rate": 0.03  # 3%
            }
        }

        for operation, criteria in readiness_criteria.items():
            if operation in baselines:
                baseline = baselines[operation]
                p95 = baseline.get("response_time_p95", 0)
                rps = baseline.get("requests_per_second", 0)
                error_rate = baseline.get("error_rate", 1)

                # Check P95 response time
                if p95 <= criteria["max_p95"]:
                    self.log_result(
                        f"Performance: {operation} P95",
                        "PASS",
                        f"{p95:.0f}ms (≤ {criteria['max_p95']}ms)"
                    )
                else:
                    self.log_result(
                        f"Performance: {operation} P95",
                        "WARN",
                        f"{p95:.0f}ms (> {criteria['max_p95']}ms target)"
                    )
                    performance_ready = False

                # Check throughput
                if rps >= criteria["min_rps"]:
                    self.log_result(
                        f"Performance: {operation} RPS",
                        "PASS",
                        f"{rps:.1f} RPS (≥ {criteria['min_rps']} RPS)"
                    )
                else:
                    self.log_result(
                        f"Performance: {operation} RPS",
                        "FAIL",
                        f"{rps:.1f} RPS (< {criteria['min_rps']} RPS)"
                    )
                    performance_ready = False

                # Check error rate
                if error_rate <= criteria["max_error_rate"]:
                    self.log_result(
                        f"Performance: {operation} Error Rate",
                        "PASS",
                        f"{error_rate:.1%} (≤ {criteria['max_error_rate']:.1%})"
                    )
                else:
                    self.log_result(
                        f"Performance: {operation} Error Rate",
                        "FAIL",
                        f"{error_rate:.1%} (> {criteria['max_error_rate']:.1%})"
                    )
                    performance_ready = False

            else:
                self.log_result(
                    f"Performance: {operation}",
                    "FAIL",
                    "Baseline not found"
                )
                performance_ready = False

        return performance_ready

    def check_security_readiness(self) -> bool:
        """Validate security configuration for production"""
        print("\n🔒 Security Readiness Validation")
        print("=" * 50)

        security_ready = True

        # API Security Test
        try:
            # Test authentication requirement
            response = requests.get(f"{self.target_host}/api/v2/content/validate", timeout=10)

            if response.status_code == 401:
                self.log_result(
                    "API Authentication",
                    "PASS",
                    "API correctly requires authentication"
                )
            elif response.status_code == 403:
                self.log_result(
                    "API Authentication",
                    "PASS",
                    "API correctly requires authorization"
                )
            else:
                self.log_result(
                    "API Authentication",
                    "FAIL",
                    f"API does not require authentication (status: {response.status_code})"
                )
                security_ready = False

        except requests.RequestException:
            self.log_result(
                "API Authentication",
                "WARN",
                "Could not test API authentication (service unavailable)"
            )

        # Security Headers Check
        try:
            response = requests.get(self.target_host, timeout=10)

            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": None,  # Just needs to be present
                "Content-Security-Policy": None
            }

            for header, expected in security_headers.items():
                value = response.headers.get(header)

                if value:
                    if expected is None:
                        self.log_result(
                            f"Security Header: {header}",
                            "PASS",
                            f"Present: {value}"
                        )
                    elif isinstance(expected, list):
                        if value in expected:
                            self.log_result(
                                f"Security Header: {header}",
                                "PASS",
                                f"Correct: {value}"
                            )
                        else:
                            self.log_result(
                                f"Security Header: {header}",
                                "WARN",
                                f"Present but unexpected value: {value}"
                            )
                    elif value == expected:
                        self.log_result(
                            f"Security Header: {header}",
                            "PASS",
                            f"Correct: {value}"
                        )
                    else:
                        self.log_result(
                            f"Security Header: {header}",
                            "WARN",
                            f"Present but incorrect: {value} (expected: {expected})"
                        )
                else:
                    self.log_result(
                        f"Security Header: {header}",
                        "FAIL",
                        "Missing"
                    )
                    security_ready = False

        except requests.RequestException:
            self.log_result(
                "Security Headers",
                "WARN",
                "Could not check security headers (service unavailable)"
            )

        return security_ready

    def check_monitoring_readiness(self) -> bool:
        """Validate monitoring system readiness"""
        print("\n📊 Monitoring System Validation")
        print("=" * 50)

        monitoring_ready = True

        # Check dashboard files
        dashboard_dir = project_root / "monitoring" / "grafana" / "dashboards"
        if dashboard_dir.exists():
            dashboard_files = list(dashboard_dir.glob("*.json"))
            if dashboard_files:
                self.log_result(
                    "Grafana Dashboards",
                    "PASS",
                    f"{len(dashboard_files)} dashboards configured"
                )
            else:
                self.log_result(
                    "Grafana Dashboards",
                    "FAIL",
                    "No dashboard configurations found"
                )
                monitoring_ready = False
        else:
            self.log_result(
                "Grafana Dashboards",
                "FAIL",
                "Dashboard directory not found"
            )
            monitoring_ready = False

        # Check alert configurations
        alert_dir = project_root / "monitoring" / "prometheus" / "alerts"
        if alert_dir.exists():
            alert_files = list(alert_dir.glob("*.yml"))
            if alert_files:
                self.log_result(
                    "Prometheus Alerts",
                    "PASS",
                    f"{len(alert_files)} alert rule files configured"
                )
            else:
                self.log_result(
                    "Prometheus Alerts",
                    "FAIL",
                    "No alert rule files found"
                )
                monitoring_ready = False
        else:
            self.log_result(
                "Prometheus Alerts",
                "FAIL",
                "Alert configuration directory not found"
            )
            monitoring_ready = False

        # Test metrics endpoint
        try:
            response = requests.get(f"{self.target_host}/metrics", timeout=10)
            if response.status_code == 200:
                metrics_count = len([line for line in response.text.split('\n')
                                   if line and not line.startswith('#')])
                self.log_result(
                    "Metrics Collection",
                    "PASS",
                    f"Metrics endpoint operational ({metrics_count} metrics)"
                )
            else:
                self.log_result(
                    "Metrics Collection",
                    "FAIL",
                    f"Metrics endpoint error: {response.status_code}"
                )
                monitoring_ready = False
        except requests.RequestException:
            self.log_result(
                "Metrics Collection",
                "WARN",
                "Metrics endpoint not accessible"
            )

        return monitoring_ready

    def check_deployment_readiness(self) -> bool:
        """Check deployment artifacts and procedures"""
        print("\n🚀 Deployment Readiness Validation")
        print("=" * 50)

        deployment_ready = True

        # Check for deployment configurations
        deployment_files = [
            "docker-compose.yml",
            "Dockerfile",
            ".github/workflows",
            "requirements.txt",
            "pyproject.toml"
        ]

        for file_path in deployment_files:
            path = project_root / file_path
            if path.exists():
                if path.is_file():
                    self.log_result(
                        f"Deployment File: {file_path}",
                        "PASS",
                        "Configuration available"
                    )
                else:  # Directory
                    files = list(path.glob("*.yml")) + list(path.glob("*.yaml"))
                    if files:
                        self.log_result(
                            f"Deployment Config: {file_path}",
                            "PASS",
                            f"{len(files)} workflow files found"
                        )
                    else:
                        self.log_result(
                            f"Deployment Config: {file_path}",
                            "WARN",
                            "Directory exists but no workflows found"
                        )
            else:
                self.log_result(
                    f"Deployment File: {file_path}",
                    "WARN",
                    "Not found (may not be required)"
                )

        # Check documentation
        docs_required = [
            "README.md",
            "docs/deployment.md",
            "docs/go-live-checklist.md"
        ]

        for doc_path in docs_required:
            path = project_root / doc_path
            if path.exists():
                self.log_result(
                    f"Documentation: {doc_path}",
                    "PASS",
                    "Available"
                )
            else:
                self.log_result(
                    f"Documentation: {doc_path}",
                    "FAIL" if "checklist" in doc_path else "WARN",
                    "Missing"
                )
                if "checklist" in doc_path:
                    deployment_ready = False

        return deployment_ready

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete pre-production validation"""
        print("🏁 PRE-PRODUCTION READINESS VALIDATION")
        print("=" * 60)
        print(f"Target: {self.target_host}")
        print(f"Environment: {self.environment}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Run all validation checks
        results = {
            "environment_ready": self.check_environment_readiness(),
            "application_healthy": self.check_application_health(),
            "performance_ready": self.check_performance_readiness(),
            "security_ready": self.check_security_readiness(),
            "monitoring_ready": self.check_monitoring_readiness(),
            "deployment_ready": self.check_deployment_readiness()
        }

        # Calculate overall readiness
        passed = sum(1 for ready in results.values() if ready)
        total = len(results)
        overall_ready = all(results.values())

        end_time = datetime.now()
        duration = end_time - self.start_time

        print(f"\n{'=' * 60}")
        print("🎯 PRE-PRODUCTION READINESS SUMMARY")
        print(f"{'=' * 60}")

        for check, ready in results.items():
            status = "✅ READY" if ready else "❌ NOT READY"
            print(f"{status:<12} {check.replace('_', ' ').title()}")

        print(f"\nOverall Status: {'🟢 PRODUCTION READY' if overall_ready else '🔴 NOT READY'}")
        print(f"Readiness Score: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"Validation Duration: {duration}")
        print(f"Total Checks: {len(self.validation_results)}")

        # Generate detailed report
        report = {
            "overall_ready": overall_ready,
            "readiness_score": f"{passed}/{total}",
            "readiness_percentage": round(passed/total*100, 1),
            "validation_start": self.start_time.isoformat(),
            "validation_end": end_time.isoformat(),
            "validation_duration": str(duration),
            "environment": self.environment,
            "target_host": self.target_host,
            "category_results": results,
            "detailed_results": self.validation_results
        }

        return report

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save validation report to file"""
        if filename is None:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"pre_production_validation_{timestamp}.json"

        report_path = project_root / "docs" / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved: {report_path}")
        return str(report_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Pre-production readiness validation")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host")
    parser.add_argument("--environment", default="production", help="Target environment")
    parser.add_argument("--save", help="Save report to specific filename")
    parser.add_argument("--fail-on-not-ready", action="store_true",
                       help="Exit with error code if not ready")

    args = parser.parse_args()

    # Run validation
    validator = PreProductionValidator(args.host, args.environment)
    report = validator.run_comprehensive_validation()

    # Save report
    if args.save:
        validator.save_report(report, args.save)
    else:
        validator.save_report(report)

    # Exit with appropriate code
    if args.fail_on_not_ready and not report["overall_ready"]:
        print("\n🚫 VALIDATION FAILED: System not ready for production")
        sys.exit(1)
    elif report["overall_ready"]:
        print("\n🎉 SUCCESS: System ready for production deployment!")
        sys.exit(0)
    else:
        print("\n⚠️ VALIDATION COMPLETE: Review results before proceeding")
        sys.exit(0)


if __name__ == "__main__":
    main()