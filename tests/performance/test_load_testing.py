"""
Load testing suite for batch content generation
Sprint 5: Stress testing and load simulation
"""
import pytest
import time
import asyncio
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, AsyncMock, patch
import psutil
import gc
import json
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from src.halcytone_content_generator.main import app
from src.halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler


class TestLoadSimulation:
    """Simulate realistic load patterns"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def user_profiles(self):
        """Different user behavior profiles"""
        return {
            "heavy": {
                "request_rate": 10,  # requests per minute
                "batch_size": 20,
                "complexity": "high"
            },
            "normal": {
                "request_rate": 5,
                "batch_size": 10,
                "complexity": "medium"
            },
            "light": {
                "request_rate": 2,
                "batch_size": 5,
                "complexity": "low"
            }
        }

    def generate_content_payload(self, complexity="medium", batch_size=1):
        """Generate content payload based on complexity"""
        base_content = {
            "low": "Simple content " * 10,
            "medium": "Medium complexity content with more details " * 20,
            "high": "Complex content with extensive details and multiple sections " * 50
        }

        if batch_size == 1:
            return {
                "content": {
                    "type": "update",
                    "title": f"Load Test {datetime.now().timestamp()}",
                    "content": base_content[complexity]
                },
                "publish_web": True,
                "generate_social": complexity in ["medium", "high"],
                "send_email": complexity == "high"
            }
        else:
            return {
                "items": [
                    {
                        "content": {
                            "type": "update",
                            "title": f"Batch Item {i}",
                            "content": base_content[complexity]
                        },
                        "publish_web": True
                    }
                    for i in range(batch_size)
                ],
                "batch_size": min(10, batch_size),
                "parallel_processing": True
            }

    def test_sustained_load_10_minutes(self, client):
        """Test system under sustained load for 10 minutes"""
        duration_seconds = 600  # 10 minutes
        requests_per_second = 2
        start_time = time.time()

        results = {
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "error_types": {}
        }

        print(f"\n=== Starting 10-minute load test ===")
        print(f"Target: {requests_per_second} requests/second")

        while time.time() - start_time < duration_seconds:
            request_start = time.perf_counter()

            # Generate varying complexity payloads
            complexity = random.choice(["low", "medium", "high"])
            payload = self.generate_content_payload(complexity)

            try:
                response = client.post(
                    "/api/v2/generate-content",
                    json=payload,
                    headers={"Authorization": "Bearer test-token"},
                    timeout=10
                )

                response_time = time.perf_counter() - request_start
                results["response_times"].append(response_time)

                if response.status_code == 200:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    error_type = f"HTTP_{response.status_code}"
                    results["error_types"][error_type] = results["error_types"].get(error_type, 0) + 1

            except Exception as e:
                results["failed"] += 1
                error_type = type(e).__name__
                results["error_types"][error_type] = results["error_types"].get(error_type, 0) + 1

            # Progress report every minute
            elapsed = time.time() - start_time
            if int(elapsed) % 60 == 0 and int(elapsed) > 0:
                self._print_progress(results, elapsed)

            # Sleep to maintain request rate
            sleep_time = max(0, (1 / requests_per_second) - response_time)
            time.sleep(sleep_time)

        # Final report
        self._print_final_report(results, duration_seconds)

        # Assertions
        success_rate = results["successful"] / (results["successful"] + results["failed"])
        assert success_rate > 0.95, f"Success rate {success_rate:.2%} below 95%"

        avg_response = statistics.mean(results["response_times"])
        assert avg_response < 2.0, f"Average response time {avg_response:.2f}s exceeds 2s"

    def test_spike_load_handling(self, client):
        """Test system response to sudden load spikes"""
        normal_load = 2  # requests/second
        spike_load = 20  # requests/second

        results = {
            "normal": {"times": [], "errors": 0},
            "spike": {"times": [], "errors": 0},
            "recovery": {"times": [], "errors": 0}
        }

        print("\n=== Spike Load Test ===")

        # Phase 1: Normal load (30 seconds)
        print("Phase 1: Normal load...")
        self._execute_load_phase(client, normal_load, 30, results["normal"])

        # Phase 2: Spike load (60 seconds)
        print("Phase 2: Spike load...")
        self._execute_load_phase(client, spike_load, 60, results["spike"])

        # Phase 3: Recovery (30 seconds)
        print("Phase 3: Recovery phase...")
        self._execute_load_phase(client, normal_load, 30, results["recovery"])

        # Analysis
        normal_avg = statistics.mean(results["normal"]["times"])
        spike_avg = statistics.mean(results["spike"]["times"])
        recovery_avg = statistics.mean(results["recovery"]["times"])

        print(f"\nResults:")
        print(f"  Normal avg: {normal_avg:.3f}s")
        print(f"  Spike avg: {spike_avg:.3f}s")
        print(f"  Recovery avg: {recovery_avg:.3f}s")

        # System should recover after spike
        assert recovery_avg < spike_avg * 1.5, "System not recovering from spike"
        assert results["spike"]["errors"] < 10, "Too many errors during spike"

    def test_concurrent_user_simulation(self, client, user_profiles):
        """Simulate multiple concurrent users with different profiles"""
        num_users = {
            "heavy": 2,
            "normal": 5,
            "light": 10
        }

        test_duration = 120  # 2 minutes

        def simulate_user(user_type, user_id):
            profile = user_profiles[user_type]
            results = []
            start_time = time.time()

            while time.time() - start_time < test_duration:
                payload = self.generate_content_payload(
                    complexity=profile["complexity"],
                    batch_size=random.randint(1, profile["batch_size"])
                )

                req_start = time.perf_counter()
                try:
                    response = client.post(
                        "/api/v2/generate-content" if payload.get("content") else "/api/batch/generate",
                        json=payload,
                        headers={"Authorization": f"Bearer user-{user_type}-{user_id}"}
                    )

                    results.append({
                        "user": f"{user_type}-{user_id}",
                        "status": response.status_code,
                        "time": time.perf_counter() - req_start
                    })
                except Exception as e:
                    results.append({
                        "user": f"{user_type}-{user_id}",
                        "status": "error",
                        "time": time.perf_counter() - req_start,
                        "error": str(e)
                    })

                # Wait based on request rate
                time.sleep(60 / profile["request_rate"])

            return results

        print(f"\n=== Concurrent User Simulation ===")
        print(f"Users: {sum(num_users.values())} total")

        all_results = []
        with ThreadPoolExecutor(max_workers=sum(num_users.values())) as executor:
            futures = []

            for user_type, count in num_users.items():
                for i in range(count):
                    futures.append(executor.submit(simulate_user, user_type, i))

            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analysis
        successful = [r for r in all_results if r.get("status") == 200]
        failed = [r for r in all_results if r.get("status") != 200]

        success_rate = len(successful) / len(all_results) if all_results else 0
        avg_response = statistics.mean([r["time"] for r in successful]) if successful else 0

        print(f"\nResults:")
        print(f"  Total requests: {len(all_results)}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Average response: {avg_response:.3f}s")
        print(f"  Failed requests: {len(failed)}")

        # Assertions
        assert success_rate > 0.90, f"Success rate {success_rate:.2%} below 90%"
        assert avg_response < 3.0, f"Average response {avg_response:.3f}s exceeds 3s"

    def _execute_load_phase(self, client, rps, duration, results):
        """Execute a load phase with specific RPS"""
        start = time.time()

        while time.time() - start < duration:
            req_start = time.perf_counter()

            payload = self.generate_content_payload(
                complexity=random.choice(["low", "medium", "high"])
            )

            try:
                response = client.post(
                    "/api/v2/generate-content",
                    json=payload,
                    headers={"Authorization": "Bearer test-token"}
                )

                response_time = time.perf_counter() - req_start
                results["times"].append(response_time)

                if response.status_code != 200:
                    results["errors"] += 1

            except Exception:
                results["errors"] += 1
                results["times"].append(time.perf_counter() - req_start)

            # Maintain RPS
            sleep_time = max(0, (1 / rps) - response_time)
            time.sleep(sleep_time)

    def _print_progress(self, results, elapsed):
        """Print progress report during load test"""
        total = results["successful"] + results["failed"]
        success_rate = results["successful"] / total if total > 0 else 0
        avg_response = statistics.mean(results["response_times"]) if results["response_times"] else 0

        print(f"\n[{int(elapsed)}s] Requests: {total}, Success: {success_rate:.1%}, Avg: {avg_response:.3f}s")

    def _print_final_report(self, results, duration):
        """Print final load test report"""
        total = results["successful"] + results["failed"]
        success_rate = results["successful"] / total if total > 0 else 0

        print(f"\n=== Load Test Complete ({duration}s) ===")
        print(f"Total Requests: {total}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {success_rate:.2%}")

        if results["response_times"]:
            print(f"\nResponse Times:")
            print(f"  Min: {min(results['response_times']):.3f}s")
            print(f"  Max: {max(results['response_times']):.3f}s")
            print(f"  Avg: {statistics.mean(results['response_times']):.3f}s")
            print(f"  P50: {statistics.median(results['response_times']):.3f}s")

            sorted_times = sorted(results['response_times'])
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            print(f"  P95: {sorted_times[p95_index]:.3f}s")
            print(f"  P99: {sorted_times[p99_index]:.3f}s")

        if results["error_types"]:
            print(f"\nError Types:")
            for error_type, count in results["error_types"].items():
                print(f"  {error_type}: {count}")


class TestBatchLoadTesting:
    """Load testing specifically for batch operations"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_large_batch_processing(self, client):
        """Test processing of large batches"""
        batch_sizes = [10, 25, 50, 100]
        results = []

        print("\n=== Large Batch Processing Test ===")

        for size in batch_sizes:
            payload = {
                "items": [
                    {
                        "content": {
                            "type": "update",
                            "title": f"Batch Item {i}",
                            "content": f"Content for batch item {i} with sufficient text."
                        },
                        "publish_web": True
                    }
                    for i in range(size)
                ],
                "batch_size": 10,  # Process in chunks of 10
                "parallel_processing": True,
                "continue_on_error": True
            }

            start = time.perf_counter()
            response = client.post(
                "/api/batch/generate",
                json=payload,
                headers={"Authorization": "Bearer test-token"},
                timeout=30
            )
            elapsed = time.perf_counter() - start

            result = {
                "batch_size": size,
                "status_code": response.status_code,
                "response_time": elapsed,
                "items_per_second": size / elapsed if elapsed > 0 else 0
            }
            results.append(result)

            print(f"Batch {size}: {elapsed:.2f}s ({result['items_per_second']:.1f} items/s)")

            # Check status if batch endpoint returns batch ID
            if response.status_code == 202:
                data = response.json()
                if "batch_id" in data:
                    # Poll for completion (simplified)
                    time.sleep(2)

        # Performance assertions
        for result in results:
            if result["batch_size"] == 10:
                # Critical benchmark: 10 items < 2 seconds
                assert result["response_time"] < 2.0, \
                       f"Batch of 10 took {result['response_time']:.2f}s (target: <2s)"

            # Items per second should remain relatively constant
            assert result["items_per_second"] > 3, \
                   f"Processing too slow: {result['items_per_second']:.1f} items/s"

    def test_parallel_batch_requests(self, client):
        """Test multiple batch requests in parallel"""
        num_batches = 5
        items_per_batch = 10

        def process_batch(batch_id):
            payload = {
                "items": [
                    {
                        "content": {
                            "type": "update",
                            "title": f"Batch {batch_id} Item {i}",
                            "content": f"Content for parallel batch testing."
                        },
                        "publish_web": True
                    }
                    for i in range(items_per_batch)
                ],
                "batch_size": 5,
                "parallel_processing": True
            }

            start = time.perf_counter()
            response = client.post(
                "/api/batch/generate",
                json=payload,
                headers={"Authorization": f"Bearer batch-{batch_id}"}
            )

            return {
                "batch_id": batch_id,
                "status": response.status_code,
                "time": time.perf_counter() - start
            }

        print(f"\n=== Parallel Batch Requests ({num_batches} batches) ===")

        start_all = time.perf_counter()
        with ThreadPoolExecutor(max_workers=num_batches) as executor:
            futures = [executor.submit(process_batch, i) for i in range(num_batches)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.perf_counter() - start_all

        successful = [r for r in results if r["status"] in [200, 202]]
        avg_time = statistics.mean([r["time"] for r in results])

        print(f"Total time: {total_time:.2f}s")
        print(f"Average per batch: {avg_time:.2f}s")
        print(f"Success rate: {len(successful)}/{num_batches}")

        # All batches should complete successfully
        assert len(successful) >= num_batches * 0.8, "Too many batch failures"

        # Total time should show parallelization benefit
        sequential_estimate = avg_time * num_batches
        parallelization_factor = sequential_estimate / total_time
        print(f"Parallelization factor: {parallelization_factor:.2f}x")

        assert parallelization_factor > 1.5, "Insufficient parallelization"


class TestResourceUtilization:
    """Monitor resource utilization under load"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_memory_under_load(self, client):
        """Monitor memory usage under sustained load"""
        process = psutil.Process()
        duration = 60  # 1 minute

        memory_samples = []
        cpu_samples = []

        start = time.time()
        request_count = 0

        print("\n=== Resource Utilization Test ===")

        while time.time() - start < duration:
            # Make request
            payload = self.generate_content_payload("medium")

            response = client.post(
                "/api/v2/generate-content",
                json=payload,
                headers={"Authorization": "Bearer test-token"}
            )
            request_count += 1

            # Sample resources
            memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
            cpu_samples.append(process.cpu_percent())

            # Report every 10 requests
            if request_count % 10 == 0:
                current_memory = memory_samples[-1]
                current_cpu = cpu_samples[-1]
                print(f"[{request_count}] Memory: {current_memory:.1f}MB, CPU: {current_cpu:.1f}%")

            time.sleep(0.5)  # 2 requests per second

        # Analysis
        initial_memory = memory_samples[0]
        peak_memory = max(memory_samples)
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        avg_cpu = statistics.mean(cpu_samples)

        print(f"\nResource Summary:")
        print(f"  Initial Memory: {initial_memory:.1f}MB")
        print(f"  Peak Memory: {peak_memory:.1f}MB")
        print(f"  Final Memory: {final_memory:.1f}MB")
        print(f"  Memory Growth: {memory_growth:.1f}MB")
        print(f"  Average CPU: {avg_cpu:.1f}%")

        # Assertions
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"
        assert avg_cpu < 80, f"CPU usage too high: {avg_cpu:.1f}%"

    def generate_content_payload(self, complexity="medium"):
        """Helper to generate content payload"""
        base_content = {
            "low": "Simple content " * 10,
            "medium": "Medium complexity content " * 20,
            "high": "Complex content with details " * 50
        }

        return {
            "content": {
                "type": "update",
                "title": f"Load Test {time.time()}",
                "content": base_content[complexity]
            },
            "publish_web": True
        }


class TestPerformanceBenchmarkValidation:
    """Validate that performance benchmarks are met"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def assembler(self):
        return EnhancedContentAssembler()

    @pytest.mark.critical
    def test_batch_10_items_under_2_seconds(self, assembler):
        """CRITICAL: Validate batch of 10 items completes in <2 seconds"""
        batch_content = [
            {
                "breathscape": [{
                    "title": f"Item {i}",
                    "content": f"Content for item {i} with standard length.",
                    "author": "Test"
                }],
                "hardware": [{
                    "title": f"Hardware {i}",
                    "content": f"Hardware update {i}."
                }]
            }
            for i in range(10)
        ]

        # Warm up
        assembler.generate_newsletter(batch_content[0])

        # Actual test
        start = time.perf_counter()

        for content in batch_content:
            newsletter = assembler.generate_newsletter(content)
            web_update = assembler.generate_web_update(content)
            social_posts = assembler.generate_social_posts(content)

            assert newsletter is not None
            assert web_update is not None
            assert social_posts is not None

        elapsed = time.perf_counter() - start

        print(f"\n✅ CRITICAL BENCHMARK: Batch of 10 items in {elapsed:.3f}s")

        # CRITICAL ASSERTION
        assert elapsed < 2.0, f"❌ FAILED: Batch of 10 items took {elapsed:.3f}s (target: <2s)"

        # Calculate metrics
        items_per_second = 10 / elapsed
        ms_per_item = (elapsed * 1000) / 10

        print(f"   Performance: {items_per_second:.1f} items/s ({ms_per_item:.0f}ms/item)")

        return elapsed

    def test_api_response_time_benchmarks(self, client):
        """Validate API response time benchmarks"""
        benchmarks = {
            "simple_content": 200,  # ms
            "complex_content": 500,  # ms
            "batch_5_items": 1000,  # ms
            "with_cache": 50  # ms
        }

        results = {}

        # Simple content
        simple_payload = {
            "content": {
                "type": "update",
                "title": "Simple",
                "content": "Simple content test."
            },
            "preview_only": True
        }

        start = time.perf_counter()
        response = client.post("/api/v2/generate-content", json=simple_payload,
                              headers={"Authorization": "Bearer test"})
        results["simple_content"] = (time.perf_counter() - start) * 1000

        # Complex content
        complex_payload = {
            "content": {
                "type": "blog",
                "title": "Complex Blog Post",
                "content": "Complex content " * 100,
                "target_keywords": ["keyword1", "keyword2", "keyword3"]
            },
            "publish_web": True,
            "generate_social": True,
            "seo_optimize": True
        }

        start = time.perf_counter()
        response = client.post("/api/v2/generate-content", json=complex_payload,
                              headers={"Authorization": "Bearer test"})
        results["complex_content"] = (time.perf_counter() - start) * 1000

        # Print results
        print("\n=== API Response Time Benchmarks ===")
        for test_name, actual_time in results.items():
            target = benchmarks.get(test_name, 1000)
            status = "✅" if actual_time < target else "❌"
            print(f"{status} {test_name}: {actual_time:.0f}ms (target: <{target}ms)")

        # Validate benchmarks
        for test_name, actual_time in results.items():
            target = benchmarks.get(test_name, 1000)
            assert actual_time < target * 1.2, \
                   f"{test_name} exceeded benchmark: {actual_time:.0f}ms > {target}ms"