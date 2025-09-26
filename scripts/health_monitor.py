#!/usr/bin/env python
"""
Health monitoring script for production deployments
Continuously monitors application health and performance metrics
"""
import argparse
import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass, asdict
from enum import Enum


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    endpoint: str
    status: HealthStatus
    response_time_ms: float
    status_code: Optional[int]
    error: Optional[str]
    timestamp: datetime
    details: Dict


class HealthMonitor:
    """Monitor application health across environments"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_health(self) -> HealthCheckResult:
        """Check basic health endpoint"""
        return await self._check_endpoint("/health", "Health Check")

    async def check_readiness(self) -> HealthCheckResult:
        """Check readiness endpoint"""
        return await self._check_endpoint("/ready", "Readiness Check")

    async def check_api_endpoint(self, endpoint: str) -> HealthCheckResult:
        """Check specific API endpoint"""
        return await self._check_endpoint(f"/api/v1{endpoint}", f"API: {endpoint}")

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        return await self._check_endpoint("/api/v1/database/status", "Database")

    async def check_external_services(self) -> HealthCheckResult:
        """Check external service connectivity"""
        return await self._check_endpoint("/api/v1/services/status", "External Services")

    async def _check_endpoint(self, path: str, name: str) -> HealthCheckResult:
        """Check a specific endpoint"""
        url = f"{self.base_url}{path}"
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        start_time = time.time()
        try:
            async with self.session.get(url, headers=headers, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000
                body = await response.text()

                try:
                    details = json.loads(body)
                except json.JSONDecodeError:
                    details = {"response": body[:500]}

                if response.status == 200:
                    # Check response content for health status
                    if "status" in details:
                        if details["status"] in ["healthy", "success", "operational"]:
                            status = HealthStatus.HEALTHY
                        elif details["status"] in ["degraded", "partial"]:
                            status = HealthStatus.DEGRADED
                        else:
                            status = HealthStatus.UNHEALTHY
                    else:
                        status = HealthStatus.HEALTHY
                elif response.status == 503:
                    status = HealthStatus.UNHEALTHY
                elif 400 <= response.status < 500:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY

                return HealthCheckResult(
                    endpoint=name,
                    status=status,
                    response_time_ms=response_time,
                    status_code=response.status,
                    error=None,
                    timestamp=datetime.utcnow(),
                    details=details
                )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                endpoint=name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=10000,
                status_code=None,
                error="Timeout",
                timestamp=datetime.utcnow(),
                details={"error": "Request timeout after 10 seconds"}
            )
        except Exception as e:
            return HealthCheckResult(
                endpoint=name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                status_code=None,
                error=str(e),
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )

    async def run_full_check(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        checks = {
            "health": self.check_health(),
            "readiness": self.check_readiness(),
            "database": self.check_database(),
            "services": self.check_external_services(),
        }

        results = {}
        for name, check_coro in checks.items():
            try:
                results[name] = await check_coro
            except Exception as e:
                results[name] = HealthCheckResult(
                    endpoint=name,
                    status=HealthStatus.UNKNOWN,
                    response_time_ms=0,
                    status_code=None,
                    error=str(e),
                    timestamp=datetime.utcnow(),
                    details={"error": str(e)}
                )

        return results


class PerformanceMonitor:
    """Monitor application performance metrics"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.metrics_history: List[Dict] = []

    async def measure_response_times(self, endpoints: List[str], iterations: int = 10) -> Dict:
        """Measure average response times for endpoints"""
        async with aiohttp.ClientSession() as session:
            results = {}

            for endpoint in endpoints:
                times = []
                errors = 0

                for _ in range(iterations):
                    start = time.time()
                    try:
                        url = f"{self.base_url}{endpoint}"
                        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

                        async with session.get(url, headers=headers, timeout=30) as response:
                            await response.text()
                            if response.status == 200:
                                times.append((time.time() - start) * 1000)
                            else:
                                errors += 1
                    except:
                        errors += 1

                    # Small delay between requests
                    await asyncio.sleep(0.1)

                if times:
                    results[endpoint] = {
                        "avg_response_time_ms": sum(times) / len(times),
                        "min_response_time_ms": min(times),
                        "max_response_time_ms": max(times),
                        "success_rate": len(times) / iterations,
                        "error_count": errors
                    }
                else:
                    results[endpoint] = {
                        "avg_response_time_ms": None,
                        "success_rate": 0,
                        "error_count": errors
                    }

            return results

    async def load_test(self, endpoint: str, concurrent_requests: int = 10, duration_seconds: int = 60) -> Dict:
        """Run a simple load test"""
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            end_time = start_time + duration_seconds
            request_count = 0
            error_count = 0
            response_times = []

            async def make_request():
                nonlocal request_count, error_count
                url = f"{self.base_url}{endpoint}"
                headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

                try:
                    req_start = time.time()
                    async with session.get(url, headers=headers, timeout=30) as response:
                        await response.text()
                        response_time = (time.time() - req_start) * 1000
                        response_times.append(response_time)
                        request_count += 1

                        if response.status != 200:
                            error_count += 1
                except:
                    error_count += 1
                    request_count += 1

            # Run concurrent requests for the specified duration
            while time.time() < end_time:
                tasks = [make_request() for _ in range(concurrent_requests)]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(1)  # Wait 1 second between batches

            # Calculate metrics
            total_time = time.time() - start_time
            if response_times:
                return {
                    "total_requests": request_count,
                    "total_errors": error_count,
                    "duration_seconds": total_time,
                    "requests_per_second": request_count / total_time,
                    "success_rate": (request_count - error_count) / request_count if request_count > 0 else 0,
                    "avg_response_time_ms": sum(response_times) / len(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "p50_response_time_ms": sorted(response_times)[len(response_times) // 2],
                    "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)],
                    "p99_response_time_ms": sorted(response_times)[int(len(response_times) * 0.99)]
                }
            else:
                return {
                    "total_requests": request_count,
                    "total_errors": error_count,
                    "duration_seconds": total_time,
                    "success_rate": 0,
                    "error": "No successful requests"
                }


class ContinuousMonitor:
    """Continuously monitor application health"""

    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 check_interval: int = 30, alert_threshold: int = 3):
        self.base_url = base_url
        self.api_key = api_key
        self.check_interval = check_interval
        self.alert_threshold = alert_threshold
        self.failure_count = 0
        self.notification_script = "scripts/deployment_notifications.py"

    async def monitor(self, duration_minutes: int = 60):
        """Monitor application for specified duration"""
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)

        async with HealthMonitor(self.base_url, self.api_key) as monitor:
            while datetime.utcnow() < end_time:
                results = await monitor.run_full_check()

                # Analyze results
                unhealthy_checks = [
                    name for name, result in results.items()
                    if result.status in [HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]
                ]

                degraded_checks = [
                    name for name, result in results.items()
                    if result.status == HealthStatus.DEGRADED
                ]

                # Print status
                print(f"\n[{datetime.utcnow().isoformat()}] Health Check Results:")
                for name, result in results.items():
                    status_emoji = {
                        HealthStatus.HEALTHY: "✅",
                        HealthStatus.DEGRADED: "⚠️",
                        HealthStatus.UNHEALTHY: "❌",
                        HealthStatus.UNKNOWN: "❓"
                    }.get(result.status, "")

                    print(f"  {status_emoji} {name}: {result.status.value} "
                         f"({result.response_time_ms:.0f}ms)")

                # Check if we need to send alerts
                if unhealthy_checks:
                    self.failure_count += 1
                    if self.failure_count >= self.alert_threshold:
                        await self._send_alert(unhealthy_checks, results)
                        self.failure_count = 0  # Reset after alert
                else:
                    self.failure_count = 0

                # Wait for next check
                await asyncio.sleep(self.check_interval)

        print(f"\nMonitoring completed after {duration_minutes} minutes")

    async def _send_alert(self, unhealthy_checks: List[str], results: Dict):
        """Send alert for unhealthy services"""
        details = {
            check: {
                "status": results[check].status.value,
                "error": results[check].error,
                "response_time_ms": results[check].response_time_ms
            }
            for check in unhealthy_checks
        }

        # Call notification script
        cmd = [
            sys.executable,
            self.notification_script,
            "--status", "warning",
            "--environment", "production",
            "--version", "current",
            "--message", f"Health check failures detected: {', '.join(unhealthy_checks)}",
            "--details", json.dumps(details),
            "--channels", "slack", "pagerduty"
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Health monitoring for deployments")
    parser.add_argument("--url", type=str, required=True,
                       help="Base URL of the application")
    parser.add_argument("--api-key", type=str,
                       help="API key for authentication")
    parser.add_argument("--mode", choices=["quick", "full", "continuous", "performance", "load"],
                       default="quick",
                       help="Monitoring mode")
    parser.add_argument("--duration", type=int, default=60,
                       help="Duration in minutes (for continuous mode)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds (for continuous mode)")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Concurrent requests (for load test)")
    parser.add_argument("--output", type=str,
                       help="Output file for results (JSON)")

    args = parser.parse_args()

    if args.mode == "quick":
        # Quick health check
        async with HealthMonitor(args.url, args.api_key) as monitor:
            result = await monitor.check_health()
            print(f"Health Status: {result.status.value}")
            print(f"Response Time: {result.response_time_ms:.0f}ms")
            if result.error:
                print(f"Error: {result.error}")
                sys.exit(1)

    elif args.mode == "full":
        # Full health check
        async with HealthMonitor(args.url, args.api_key) as monitor:
            results = await monitor.run_full_check()

            all_healthy = all(r.status == HealthStatus.HEALTHY for r in results.values())

            print("\nFull Health Check Results:")
            print("=" * 50)
            for name, result in results.items():
                print(f"\n{name}:")
                print(f"  Status: {result.status.value}")
                print(f"  Response Time: {result.response_time_ms:.0f}ms")
                if result.error:
                    print(f"  Error: {result.error}")

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(
                        {k: asdict(v) for k, v in results.items()},
                        f,
                        indent=2,
                        default=str
                    )

            sys.exit(0 if all_healthy else 1)

    elif args.mode == "continuous":
        # Continuous monitoring
        monitor = ContinuousMonitor(
            args.url,
            args.api_key,
            check_interval=args.interval
        )
        await monitor.monitor(duration_minutes=args.duration)

    elif args.mode == "performance":
        # Performance testing
        perf_monitor = PerformanceMonitor(args.url, args.api_key)
        endpoints = ["/health", "/api/v1/content/generate"]
        results = await perf_monitor.measure_response_times(endpoints)

        print("\nPerformance Test Results:")
        print("=" * 50)
        for endpoint, metrics in results.items():
            print(f"\n{endpoint}:")
            for key, value in metrics.items():
                if value is not None:
                    print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

    elif args.mode == "load":
        # Load testing
        perf_monitor = PerformanceMonitor(args.url, args.api_key)
        result = await perf_monitor.load_test(
            "/health",
            concurrent_requests=args.concurrent,
            duration_seconds=args.duration * 60
        )

        print("\nLoad Test Results:")
        print("=" * 50)
        for key, value in result.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())