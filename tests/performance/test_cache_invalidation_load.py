"""
Load tests for cache invalidation system
Sprint 4: Ecosystem Integration - Load testing for cache invalidation operations
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any
import statistics
from unittest.mock import AsyncMock, patch

from src.halcytone_content_generator.services.cache_manager import (
    get_cache_manager, CacheManager, InvalidationRequest, CacheTarget, initialize_cache_manager
)
from src.halcytone_content_generator.config import get_settings


class TestCacheInvalidationLoad:
    """Load tests for cache invalidation operations"""

    @pytest.fixture
    def cache_manager(self):
        """Get cache manager instance"""
        # Initialize cache manager first with test config
        config = {
            'cdn_api_key': 'test_api_key',
            'cdn_zone_id': 'test_zone_id',
            'api_base_url': 'http://localhost:8000',
            'redis_url': 'redis://localhost:6379',
            'webhook_secret': 'test_webhook_secret',
            'enable_cdn': False,  # Disable for testing
            'enable_redis': False  # Disable for testing
        }
        initialize_cache_manager(config)
        return get_cache_manager()

    @pytest.fixture
    def sample_invalidation_request(self):
        """Sample cache invalidation request"""
        return InvalidationRequest(
            targets=[CacheTarget.LOCAL, CacheTarget.API],
            keys=["test_key_1", "test_key_2", "test_key_3"],
            patterns=["api/v1/*", "content/*"],
            force=False,
            reason="Performance test invalidation"
        )

    @pytest.mark.asyncio
    async def test_single_invalidation_performance(self, cache_manager, sample_invalidation_request):
        """Test performance of single cache invalidation operations"""
        iterations = 100
        times = []

        for i in range(iterations):
            # Modify request to make it unique
            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL],
                keys=[f"test_key_{i}"],
                patterns=[f"test_pattern_{i}/*"],
                force=False,
                reason=f"Test invalidation {i}"
            )

            start_time = time.perf_counter()
            result = await cache_manager.invalidate_cache(request)
            end_time = time.perf_counter()

            times.append(end_time - start_time)
            assert result is not None

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        max_time = max(times)

        print(f"\nSingle Invalidation Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  95th percentile: {p95_time*1000:.2f}ms")
        print(f"  Max time: {max_time*1000:.2f}ms")
        print(f"  Iterations: {iterations}")

        # Performance requirements
        assert avg_time < 0.100, f"Average invalidation time {avg_time*1000:.2f}ms exceeds 100ms"
        assert p95_time < 0.500, f"95th percentile time {p95_time*1000:.2f}ms exceeds 500ms"

    @pytest.mark.asyncio
    async def test_concurrent_invalidation_load(self, cache_manager):
        """Test cache invalidation under concurrent load"""

        async def invalidation_task(task_id: int):
            """Single invalidation task"""
            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL],
                keys=[f"concurrent_key_{task_id}"],
                patterns=[f"concurrent/*/{task_id}"],
                force=False,
                reason=f"Concurrent test {task_id}",
                initiated_by=f"load_test_{task_id}"
            )

            start_time = time.perf_counter()
            result = await cache_manager.invalidate_cache(request)
            end_time = time.perf_counter()

            return {
                'task_id': task_id,
                'duration': end_time - start_time,
                'success': result.status.value in ['success', 'partial']
            }

        # Test with different concurrency levels
        concurrency_levels = [10, 25, 50, 100]

        for concurrency in concurrency_levels:
            print(f"\nTesting concurrency level: {concurrency}")

            start_time = time.perf_counter()
            tasks = [invalidation_task(i) for i in range(concurrency)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.perf_counter() - start_time

            # Filter out exceptions and get successful results
            successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]

            if successful_results:
                durations = [r['duration'] for r in successful_results]
                avg_duration = statistics.mean(durations)
                throughput = len(successful_results) / total_time
                success_rate = len(successful_results) / len(results) * 100

                print(f"  Total time: {total_time:.2f}s")
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Throughput: {throughput:.1f} invalidations/second")
                print(f"  Average per-request time: {avg_duration*1000:.2f}ms")

                # Performance assertions based on concurrency level
                min_throughput = max(20, 100 - concurrency)  # Lower expectations at high concurrency
                assert success_rate >= 95, f"Success rate {success_rate:.1f}% below 95%"
                assert throughput >= min_throughput, f"Throughput {throughput:.1f} below minimum {min_throughput}"

    @pytest.mark.asyncio
    async def test_bulk_invalidation_performance(self, cache_manager):
        """Test performance of bulk invalidation operations"""
        bulk_sizes = [10, 50, 100, 500]

        for size in bulk_sizes:
            keys = [f"bulk_key_{i}" for i in range(size)]
            patterns = [f"bulk_pattern_{i}/*" for i in range(min(size // 10, 50))]  # Reasonable pattern count

            request = InvalidationRequest(
                targets=[CacheTarget.LOCAL, CacheTarget.API],
                keys=keys,
                patterns=patterns,
                force=False,
                reason=f"Bulk test with {size} keys",
                initiated_by=f"bulk_load_test_{size}"
            )

            start_time = time.perf_counter()
            result = await cache_manager.invalidate_cache(request)
            end_time = time.perf_counter()

            duration = end_time - start_time
            keys_per_second = size / duration if duration > 0 else 0

            print(f"\nBulk Invalidation (Size: {size}):")
            print(f"  Duration: {duration*1000:.2f}ms")
            print(f"  Keys/second: {keys_per_second:.1f}")
            print(f"  Status: {result.status.value}")

            # Performance scaling expectations
            max_expected_time = 0.050 + (size * 0.001)  # Base time + linear scaling
            assert duration < max_expected_time, f"Bulk invalidation time {duration*1000:.2f}ms exceeds expected {max_expected_time*1000:.2f}ms"

    @pytest.mark.asyncio
    async def test_cache_target_performance_comparison(self, cache_manager):
        """Compare performance across different cache targets"""
        targets_to_test = [
            [CacheTarget.LOCAL],
            [CacheTarget.API],
            [CacheTarget.LOCAL, CacheTarget.API]
        ]

        results = {}

        for targets in targets_to_test:
            target_names = [t.value for t in targets]
            target_key = "_".join(target_names)

            times = []
            iterations = 50

            for i in range(iterations):
                request = InvalidationRequest(
                    targets=targets,
                    keys=[f"target_test_{target_key}_{i}"],
                    patterns=[f"target_test/{target_key}/*"],
                    force=False,
                    reason=f"Target performance test: {target_key}"
                )

                start_time = time.perf_counter()
                result = await cache_manager.invalidate_cache(request)
                end_time = time.perf_counter()

                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            results[target_key] = avg_time

            print(f"\nTarget Performance: {target_names}")
            print(f"  Average time: {avg_time*1000:.2f}ms")
            print(f"  Iterations: {iterations}")

        # Multi-target operations should not be significantly slower than single-target
        single_local_time = results.get('local', 0)
        multi_target_time = results.get('local_api', 0)

        if single_local_time > 0 and multi_target_time > 0:
            overhead_ratio = multi_target_time / single_local_time
            print(f"\nMulti-target overhead: {overhead_ratio:.2f}x")
            assert overhead_ratio < 3.0, f"Multi-target overhead {overhead_ratio:.2f}x is too high"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, cache_manager):
        """Test memory usage during sustained cache invalidation load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run sustained load test
        total_operations = 500
        batch_size = 25

        for batch in range(0, total_operations, batch_size):
            tasks = []
            for i in range(batch, min(batch + batch_size, total_operations)):
                request = InvalidationRequest(
                    targets=[CacheTarget.LOCAL],
                    keys=[f"memory_test_key_{i}"],
                    patterns=[f"memory_test/{i}/*"],
                    force=False,
                    reason=f"Memory test batch {batch//batch_size}"
                )
                tasks.append(cache_manager.invalidate_cache(request))

            await asyncio.gather(*tasks)

            # Check memory every 5 batches
            if batch % (batch_size * 5) == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"  Operations completed: {batch + batch_size}, Memory: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory

        print(f"\nMemory Usage Test:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Total increase: {total_memory_increase:.1f}MB")
        print(f"  Operations: {total_operations}")

        # Memory usage should not grow excessively
        assert total_memory_increase < 100, f"Memory increase {total_memory_increase:.1f}MB exceeds 100MB limit"

    @pytest.mark.asyncio
    async def test_error_handling_under_load(self, cache_manager):
        """Test error handling and recovery under load conditions"""

        # Simulate some failing invalidation requests
        async def mixed_invalidation_task(task_id: int, should_fail: bool = False):
            """Task that may succeed or fail based on parameters"""
            if should_fail:
                # Create an invalid request that should fail
                request = InvalidationRequest(
                    targets=[],  # Empty targets should cause failure
                    keys=[f"fail_key_{task_id}"],
                    patterns=[],
                    force=False,
                    reason=f"Intentional failure test {task_id}"
                )
            else:
                request = InvalidationRequest(
                    targets=[CacheTarget.LOCAL],
                    keys=[f"success_key_{task_id}"],
                    patterns=[f"success/*/{task_id}"],
                    force=False,
                    reason=f"Success test {task_id}"
                )

            try:
                start_time = time.perf_counter()
                result = await cache_manager.invalidate_cache(request)
                duration = time.perf_counter() - start_time

                return {
                    'task_id': task_id,
                    'success': True,
                    'duration': duration,
                    'status': result.status.value
                }
            except Exception as e:
                return {
                    'task_id': task_id,
                    'success': False,
                    'error': str(e),
                    'duration': 0
                }

        # Create mixed workload: 80% success, 20% failure
        total_tasks = 100
        tasks = []

        for i in range(total_tasks):
            should_fail = (i % 5 == 0)  # Every 5th task fails
            tasks.append(mixed_invalidation_task(i, should_fail))

        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start_time

        # Analyze results
        successful_tasks = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed_tasks = [r for r in results if isinstance(r, dict) and not r.get('success')]
        exceptions = [r for r in results if isinstance(r, Exception)]

        success_rate = len(successful_tasks) / total_tasks * 100
        error_rate = (len(failed_tasks) + len(exceptions)) / total_tasks * 100

        print(f"\nError Handling Under Load:")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Successful: {len(successful_tasks)}")
        print(f"  Failed: {len(failed_tasks)}")
        print(f"  Exceptions: {len(exceptions)}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Error rate: {error_rate:.1f}%")
        print(f"  Total time: {total_time:.2f}s")

        # System should handle errors gracefully
        assert len(exceptions) == 0, "No unhandled exceptions should occur"
        assert success_rate >= 75, f"Success rate {success_rate:.1f}% below acceptable 75%"

    @pytest.mark.asyncio
    async def test_webhook_processing_load(self, cache_manager):
        """Test webhook processing under load conditions"""

        webhook_payloads = []
        for i in range(50):
            payload = {
                'event': 'content_updated' if i % 2 == 0 else 'deployment',
                'targets': ['local', 'api'],
                'patterns': [f'webhook_test/{i}/*'],
                'reason': f'Webhook load test {i}'
            }
            webhook_payloads.append(payload)

        async def process_webhook_task(payload_id: int, payload: dict):
            """Single webhook processing task"""
            start_time = time.perf_counter()

            try:
                result = await cache_manager.process_webhook_invalidation(payload)
                duration = time.perf_counter() - start_time

                return {
                    'payload_id': payload_id,
                    'success': True,
                    'duration': duration,
                    'status': result.status.value if hasattr(result, 'status') else 'unknown'
                }
            except Exception as e:
                duration = time.perf_counter() - start_time
                return {
                    'payload_id': payload_id,
                    'success': False,
                    'duration': duration,
                    'error': str(e)
                }

        # Process webhooks concurrently
        start_time = time.perf_counter()
        tasks = [process_webhook_task(i, payload) for i, payload in enumerate(webhook_payloads)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.perf_counter() - start_time

        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        throughput = len(successful_results) / total_time

        if successful_results:
            avg_duration = statistics.mean([r['duration'] for r in successful_results])
            print(f"\nWebhook Processing Load Test:")
            print(f"  Webhooks processed: {len(successful_results)}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.1f} webhooks/second")
            print(f"  Average processing time: {avg_duration*1000:.2f}ms")

            # Performance requirements for webhook processing
            assert throughput >= 25, f"Webhook throughput {throughput:.1f}/s below minimum 25/s"
            assert avg_duration < 0.200, f"Average webhook processing {avg_duration*1000:.2f}ms exceeds 200ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])