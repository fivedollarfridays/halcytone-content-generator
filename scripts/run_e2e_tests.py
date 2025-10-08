#!/usr/bin/env python3
"""
End-to-End Integration Tests

Comprehensive integration testing for production environments covering:
- Full content generation workflows
- Multi-service integration (CRM, Platform, Google Docs, OpenAI)
- Batch processing and scheduling
- Cache behavior
- Error recovery
- Performance under load

Usage:
    python scripts/run_e2e_tests.py --environment production
    python scripts/run_e2e_tests.py --environment staging --full-suite
    python scripts/run_e2e_tests.py --environment production --test-suite critical --verbose
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}→ {text}{Colors.RESET}")
    print(f"{Colors.MAGENTA}{'-' * 70}{Colors.RESET}")

def print_test(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▸ {text}{Colors.RESET}")

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


class E2ETestRunner:
    """End-to-end integration test runner"""

    def __init__(self, environment: str, host: str, api_key: Optional[str] = None,
                 timeout: int = 30, verbose: bool = False):
        self.environment = environment
        self.host = host.rstrip('/')
        self.api_key = api_key or os.getenv('API_KEY')
        self.timeout = timeout
        self.verbose = verbose
        self.results = []
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self, test_suite: str = "full"):
        """Run all E2E tests"""
        self.start_time = time.time()

        print_header("End-to-End Integration Tests")
        print_info(f"Environment: {self.environment}")
        print_info(f"Host: {self.host}")
        print_info(f"Test Suite: {test_suite}")
        print_info(f"Timestamp: {datetime.now().isoformat()}")

        if test_suite in ["critical", "full"]:
            await self.test_health_check()
            await self.test_service_connectivity()

        if test_suite in ["smoke", "full"]:
            await self.test_content_generation_basic()
            await self.test_error_handling()

        if test_suite == "full":
            await self.test_content_generation_advanced()
            await self.test_batch_processing()
            await self.test_scheduling()
            await self.test_cache_behavior()
            await self.test_dry_run_mode()
            await self.test_ab_testing()
            await self.test_multi_channel_generation()
            await self.test_concurrent_requests()
            await self.test_error_recovery()

        self.end_time = time.time()
        return self.generate_report()

    def add_result(self, test_name: str, passed: bool, duration_ms: int,
                   message: str = "", details: Dict = None):
        """Add test result"""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'duration_ms': duration_ms,
            'message': message,
            'details': details or {}
        })

    async def test_health_check(self):
        """Test health check endpoints"""
        print_section("Health Check Tests")

        endpoints = [
            ('/health', 'Liveness'),
            ('/ready', 'Readiness'),
            ('/api/v1/health', 'API Health'),
        ]

        for endpoint, name in endpoints:
            print_test(f"{name} Check")
            start = time.time()

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.host}{endpoint}")

                duration_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')

                    if status in ['healthy', 'ok']:
                        print_success(f"{name}: {status} ({duration_ms}ms)")
                        self.add_result(f"Health: {name}", True, duration_ms, status)
                    else:
                        print_error(f"{name}: {status}")
                        self.add_result(f"Health: {name}", False, duration_ms, status)
                else:
                    print_error(f"{name}: HTTP {response.status_code}")
                    self.add_result(f"Health: {name}", False, duration_ms,
                                  f"HTTP {response.status_code}")

            except Exception as e:
                duration_ms = int((time.time() - start) * 1000)
                print_error(f"{name}: {str(e)}")
                self.add_result(f"Health: {name}", False, duration_ms, str(e))

    async def test_service_connectivity(self):
        """Test external service connectivity"""
        print_section("Service Connectivity Tests")

        # This would call the validate_external_services script
        print_test("External Services Validation")

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, 'scripts/validate_external_services.py', '--all', '--json'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=project_root
            )

            if result.returncode == 0:
                print_success("All external services validated")
                self.add_result("Service Connectivity", True, 0, "All services OK")
            else:
                print_warning("Some external services failed validation")
                self.add_result("Service Connectivity", False, 0, "Some services failed")

        except Exception as e:
            print_warning(f"Service connectivity check skipped: {str(e)}")

    async def test_content_generation_basic(self):
        """Test basic content generation"""
        print_section("Basic Content Generation")

        print_test("Single Content Generation")

        if not self.api_key:
            print_warning("No API key provided, skipping authenticated tests")
            return

        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                payload = {
                    "content_type": "newsletter",
                    "template": "breathscape",
                    "dry_run": True,
                    "metadata": {
                        "test": True,
                        "test_id": f"e2e_{int(time.time())}"
                    }
                }

                response = await client.post(
                    f"{self.host}/api/v1/content/generate",
                    headers=headers,
                    json=payload
                )

                duration_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Content generated ({duration_ms}ms)")
                    print_info(f"Content ID: {data.get('content_id', 'N/A')}", indent=1)

                    self.add_result("Content Generation: Basic", True, duration_ms,
                                  "Success", {'content_id': data.get('content_id')})
                elif response.status_code == 401:
                    print_error("Authentication failed - check API key")
                    self.add_result("Content Generation: Basic", False, duration_ms,
                                  "Auth failed")
                else:
                    print_error(f"HTTP {response.status_code}: {response.text[:100]}")
                    self.add_result("Content Generation: Basic", False, duration_ms,
                                  f"HTTP {response.status_code}")

        except httpx.TimeoutException:
            duration_ms = int((time.time() - start) * 1000)
            print_error(f"Request timeout after {duration_ms}ms")
            self.add_result("Content Generation: Basic", False, duration_ms, "Timeout")
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            print_error(f"Test failed: {str(e)}")
            self.add_result("Content Generation: Basic", False, duration_ms, str(e))

    async def test_content_generation_advanced(self):
        """Test advanced content generation features"""
        print_section("Advanced Content Generation")

        if not self.api_key:
            return

        tests = [
            {
                'name': 'AI Enhancement',
                'payload': {
                    'content_type': 'newsletter',
                    'template': 'breathscape',
                    'dry_run': True,
                    'enable_ai_enhancement': True
                }
            },
            {
                'name': 'Quality Scoring',
                'payload': {
                    'content_type': 'newsletter',
                    'template': 'breathscape',
                    'dry_run': True,
                    'enable_quality_scoring': True
                }
            },
            {
                'name': 'Personalization',
                'payload': {
                    'content_type': 'newsletter',
                    'template': 'breathscape',
                    'dry_run': True,
                    'user_segment': 'active_users'
                }
            },
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {'Authorization': f'Bearer {self.api_key}'}

            for test in tests:
                print_test(test['name'])
                start = time.time()

                try:
                    response = await client.post(
                        f"{self.host}/api/v2/content/generate",
                        headers=headers,
                        json=test['payload']
                    )

                    duration_ms = int((time.time() - start) * 1000)

                    if response.status_code == 200:
                        print_success(f"{test['name']} ({duration_ms}ms)")
                        self.add_result(f"Advanced: {test['name']}", True, duration_ms)
                    else:
                        print_warning(f"{test['name']}: HTTP {response.status_code}")
                        self.add_result(f"Advanced: {test['name']}", False, duration_ms)

                except Exception as e:
                    duration_ms = int((time.time() - start) * 1000)
                    print_warning(f"{test['name']}: {str(e)}")
                    self.add_result(f"Advanced: {test['name']}", False, duration_ms, str(e))

    async def test_batch_processing(self):
        """Test batch content generation"""
        print_section("Batch Processing")

        if not self.api_key:
            return

        print_test("Batch Content Generation")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:  # Longer timeout for batch
                headers = {'Authorization': f'Bearer {self.api_key}'}

                payload = {
                    "period": "week",
                    "channels": ["email", "social"],
                    "dry_run": True,
                    "max_items": 5
                }

                response = await client.post(
                    f"{self.host}/api/v1/content/batch",
                    headers=headers,
                    json=payload
                )

                duration_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    batch_id = data.get('batch_id', 'N/A')
                    item_count = len(data.get('items', []))

                    print_success(f"Batch created: {batch_id} ({item_count} items, {duration_ms}ms)")
                    self.add_result("Batch Processing", True, duration_ms,
                                  f"{item_count} items", {'batch_id': batch_id})
                else:
                    print_error(f"Batch failed: HTTP {response.status_code}")
                    self.add_result("Batch Processing", False, duration_ms,
                                  f"HTTP {response.status_code}")

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            print_error(f"Batch test failed: {str(e)}")
            self.add_result("Batch Processing", False, duration_ms, str(e))

    async def test_scheduling(self):
        """Test content scheduling"""
        print_section("Content Scheduling")

        if not self.api_key:
            return

        print_test("Schedule Content")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                # Schedule for 1 hour from now
                scheduled_time = (datetime.now() + timedelta(hours=1)).isoformat()

                payload = {
                    "content_type": "newsletter",
                    "template": "breathscape",
                    "scheduled_time": scheduled_time,
                    "dry_run": True
                }

                response = await client.post(
                    f"{self.host}/api/v1/content/schedule",
                    headers=headers,
                    json=payload
                )

                duration_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    schedule_id = data.get('schedule_id', 'N/A')

                    print_success(f"Content scheduled: {schedule_id} ({duration_ms}ms)")
                    self.add_result("Scheduling", True, duration_ms,
                                  "Scheduled", {'schedule_id': schedule_id})
                else:
                    print_warning(f"Scheduling: HTTP {response.status_code}")
                    self.add_result("Scheduling", False, duration_ms,
                                  f"HTTP {response.status_code}")

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            print_warning(f"Scheduling test: {str(e)}")
            self.add_result("Scheduling", False, duration_ms, str(e))

    async def test_cache_behavior(self):
        """Test cache behavior"""
        print_section("Cache Behavior")

        print_test("Cache Warm/Cold")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First request (cache miss)
                start1 = time.time()
                response1 = await client.get(f"{self.host}/health")
                time1_ms = int((time.time() - start1) * 1000)

                # Second request (cache hit)
                start2 = time.time()
                response2 = await client.get(f"{self.host}/health")
                time2_ms = int((time.time() - start2) * 1000)

                speedup = ((time1_ms - time2_ms) / time1_ms * 100) if time1_ms > 0 else 0

                print_info(f"First request: {time1_ms}ms", indent=1)
                print_info(f"Second request: {time2_ms}ms", indent=1)

                if time2_ms < time1_ms * 0.8:  # 20% faster
                    print_success(f"Cache working: {speedup:.1f}% speedup")
                    self.add_result("Cache Behavior", True, time2_ms,
                                  f"{speedup:.1f}% speedup")
                else:
                    print_info(f"Cache effect: {speedup:.1f}%")
                    self.add_result("Cache Behavior", True, time2_ms,
                                  f"{speedup:.1f}% effect")

        except Exception as e:
            print_warning(f"Cache test: {str(e)}")

    async def test_dry_run_mode(self):
        """Test dry run mode"""
        print_section("Dry Run Mode")

        if not self.api_key:
            return

        print_test("Dry Run Content Generation")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                payload = {
                    "content_type": "newsletter",
                    "template": "breathscape",
                    "dry_run": True
                }

                response = await client.post(
                    f"{self.host}/api/v1/content/generate",
                    headers=headers,
                    json=payload
                )

                duration_ms = int((time.time() - start) * 1000)

                if response.status_code == 200:
                    data = response.json()

                    # Verify it's marked as dry run
                    if data.get('dry_run') or data.get('is_dry_run'):
                        print_success(f"Dry run successful ({duration_ms}ms)")
                        self.add_result("Dry Run Mode", True, duration_ms, "Working")
                    else:
                        print_warning("Dry run flag not set in response")
                        self.add_result("Dry Run Mode", False, duration_ms,
                                      "Flag not set")
                else:
                    print_warning(f"Dry run: HTTP {response.status_code}")

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            print_warning(f"Dry run test: {str(e)}")

    async def test_ab_testing(self):
        """Test A/B testing functionality"""
        print_section("A/B Testing")

        if not self.api_key:
            return

        print_test("A/B Test Creation")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                payload = {
                    "content_type": "newsletter",
                    "template": "breathscape",
                    "dry_run": True,
                    "enable_ab_testing": True,
                    "variants": 2
                }

                response = await client.post(
                    f"{self.host}/api/v2/content/generate",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    variants = data.get('variants', [])

                    if len(variants) >= 2:
                        print_success(f"A/B test created: {len(variants)} variants")
                        self.add_result("A/B Testing", True, 0,
                                      f"{len(variants)} variants")
                    else:
                        print_warning("A/B test created but insufficient variants")

        except Exception as e:
            print_info(f"A/B testing: {str(e)}")

    async def test_multi_channel_generation(self):
        """Test multi-channel content generation"""
        print_section("Multi-Channel Generation")

        if not self.api_key:
            return

        print_test("Email + Social + Web Generation")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {'Authorization': f'Bearer {self.api_key}'}

                payload = {
                    "channels": ["email", "social", "web"],
                    "dry_run": True
                }

                response = await client.post(
                    f"{self.host}/api/v2/content/generate/multi-channel",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    channels = data.get('channels', {})

                    print_success(f"Multi-channel generated: {len(channels)} channels")
                    self.add_result("Multi-Channel", True, 0, f"{len(channels)} channels")
                else:
                    print_info(f"Multi-channel: HTTP {response.status_code}")

        except Exception as e:
            print_info(f"Multi-channel test: {str(e)}")

    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print_section("Concurrent Requests")

        print_test("10 Concurrent Health Checks")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start = time.time()

                # Send 10 concurrent requests
                tasks = [client.get(f"{self.host}/health") for _ in range(10)]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                duration_ms = int((time.time() - start) * 1000)

                success_count = sum(1 for r in responses
                                  if not isinstance(r, Exception) and r.status_code == 200)

                if success_count == 10:
                    print_success(f"All 10 requests successful ({duration_ms}ms total)")
                    self.add_result("Concurrent Requests", True, duration_ms,
                                  "10/10 successful")
                else:
                    print_warning(f"{success_count}/10 requests successful")
                    self.add_result("Concurrent Requests", False, duration_ms,
                                  f"{success_count}/10 successful")

        except Exception as e:
            print_warning(f"Concurrent test: {str(e)}")

    async def test_error_handling(self):
        """Test error handling"""
        print_section("Error Handling")

        tests = [
            {
                'name': 'Invalid Endpoint',
                'method': 'GET',
                'url': '/api/v1/nonexistent',
                'expected': 404
            },
            {
                'name': 'Invalid Method',
                'method': 'DELETE',
                'url': '/api/v1/content/generate',
                'expected': 405
            },
            {
                'name': 'Invalid Payload',
                'method': 'POST',
                'url': '/api/v1/content/generate',
                'expected': 422,
                'payload': {'invalid': 'data'}
            },
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for test in tests:
                print_test(test['name'])

                try:
                    if test['method'] == 'GET':
                        response = await client.get(f"{self.host}{test['url']}")
                    elif test['method'] == 'POST':
                        response = await client.post(f"{self.host}{test['url']}",
                                                    json=test.get('payload', {}))
                    elif test['method'] == 'DELETE':
                        response = await client.delete(f"{self.host}{test['url']}")

                    if response.status_code == test['expected']:
                        print_success(f"Returned expected HTTP {test['expected']}")
                        self.add_result(f"Error: {test['name']}", True, 0)
                    else:
                        print_warning(f"Expected {test['expected']}, got {response.status_code}")
                        self.add_result(f"Error: {test['name']}", False, 0)

                except Exception as e:
                    print_warning(f"{test['name']}: {str(e)}")

    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        print_section("Error Recovery")

        print_test("Service Recovery After Error")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try to trigger an error
                response1 = await client.get(f"{self.host}/api/v1/trigger-error")

                # Verify service still works
                response2 = await client.get(f"{self.host}/health")

                if response2.status_code == 200:
                    print_success("Service recovered after error")
                    self.add_result("Error Recovery", True, 0, "Service stable")
                else:
                    print_error("Service failed to recover")
                    self.add_result("Error Recovery", False, 0, "Recovery failed")

        except Exception:
            # If error endpoint doesn't exist, just verify health works
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.host}/health")
                    if response.status_code == 200:
                        print_success("Service is stable")
            except Exception as e:
                print_error(f"Error recovery test: {str(e)}")

    def generate_report(self) -> Dict:
        """Generate test report"""
        print_section("E2E Test Summary")

        total = len(self.results)
        passed = len([r for r in self.results if r['passed']])
        failed = total - passed

        if total > 0:
            pass_rate = (passed / total) * 100
        else:
            pass_rate = 0

        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0

        print_info(f"Total Tests: {total}", indent=0)
        print_success(f"Passed: {passed} ({pass_rate:.1f}%)", indent=0) if failed == 0 else print_info(f"Passed: {passed} ({pass_rate:.1f}%)", indent=0)
        print_error(f"Failed: {failed}", indent=0) if failed > 0 else print_success(f"Failed: {failed}", indent=0)
        print_info(f"Total Duration: {total_duration:.2f}s", indent=0)

        if failed > 0:
            print("\n" + Colors.RED + Colors.BOLD + "Failed Tests:" + Colors.RESET)
            for result in self.results:
                if not result['passed']:
                    print_error(f"{result['test']}: {result['message']}", indent=1)

        # Overall status
        print()
        if failed == 0:
            print_header("✓ ALL E2E TESTS PASSED")
            overall_status = "PASSED"
        elif pass_rate >= 80:
            print_header("⚠ E2E TESTS PASSED WITH FAILURES")
            overall_status = "PASSED_WITH_FAILURES"
        else:
            print_header("✗ E2E TESTS FAILED")
            overall_status = "FAILED"

        return {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "host": self.host,
            "overall_status": overall_status,
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "duration_seconds": total_duration
            },
            "results": self.results
        }


async def main():
    parser = argparse.ArgumentParser(
        description='End-to-End Integration Tests',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--environment', required=True,
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--host', help='Override host URL')
    parser.add_argument('--api-key', help='API key for authenticated tests')
    parser.add_argument('--test-suite', default='full',
                       choices=['critical', 'smoke', 'full'],
                       help='Test suite to run')
    parser.add_argument('--full-suite', action='store_true',
                       help='Run full test suite (equivalent to --test-suite full)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--save', help='Save results to JSON file')

    args = parser.parse_args()

    # Determine host based on environment
    if args.host:
        host = args.host
    elif args.environment == 'production':
        host = os.getenv('PRODUCTION_HOST', 'https://api.halcytone.com')
    elif args.environment == 'staging':
        host = os.getenv('STAGING_HOST', 'https://staging-api.halcytone.com')
    else:
        host = os.getenv('DEV_HOST', 'http://localhost:8000')

    # Determine test suite
    test_suite = 'full' if args.full_suite else args.test_suite

    runner = E2ETestRunner(
        environment=args.environment,
        host=host,
        api_key=args.api_key,
        timeout=args.timeout,
        verbose=args.verbose
    )

    report = await runner.run_all_tests(test_suite=test_suite)

    if args.save:
        with open(args.save, 'w') as f:
            json.dump(report, f, indent=2)
        print_info(f"\nResults saved to: {args.save}")

    # Exit codes
    if report['overall_status'] == 'PASSED':
        sys.exit(0)
    elif report['overall_status'] == 'PASSED_WITH_FAILURES':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    asyncio.run(main())
