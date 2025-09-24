"""
Performance tests for tone switching system
Sprint 4: Ecosystem Integration - Performance testing for tone selection and switching
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any
import statistics

from src.halcytone_content_generator.services.tone_manager import (
    get_tone_manager, AdvancedTone
)


class TestToneSwitchingPerformance:
    """Performance tests for tone switching operations"""

    @pytest.fixture
    def tone_manager(self):
        """Get tone manager instance"""
        return get_tone_manager()

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing"""
        return {
            'breathscape': [
                {
                    'title': 'Advanced Breathing Technique',
                    'content': 'Learn about advanced breathing patterns for stress reduction and wellness enhancement.',
                    'tags': ['breathing', 'wellness', 'advanced']
                }
            ],
            'hardware': [
                {
                    'title': 'Sensor Update',
                    'content': 'Latest improvements to heart rate monitoring accuracy and battery life.',
                    'tags': ['hardware', 'sensors', 'update']
                }
            ]
        }

    def test_tone_selection_performance(self, tone_manager, sample_content):
        """Test performance of tone selection operations"""
        iterations = 1000
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            # Test tone selection for different channels
            tone = tone_manager.select_tone(
                content_type="newsletter",
                channel="email",
                context={"content_items": len(sample_content.get('breathscape', []))}
            )

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Performance assertions
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile

        print(f"\nTone Selection Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  Min time: {min_time*1000:.2f}ms")
        print(f"  Max time: {max_time*1000:.2f}ms")
        print(f"  95th percentile: {p95_time*1000:.2f}ms")
        print(f"  Iterations: {iterations}")

        # Performance requirements
        assert avg_time < 0.010, f"Average tone selection time {avg_time*1000:.2f}ms exceeds 10ms"
        assert p95_time < 0.050, f"95th percentile time {p95_time*1000:.2f}ms exceeds 50ms"
        assert max_time < 0.100, f"Maximum time {max_time*1000:.2f}ms exceeds 100ms"

    def test_tone_profile_retrieval_performance(self, tone_manager):
        """Test performance of tone profile retrieval"""
        iterations = 2000
        tones = [AdvancedTone.PROFESSIONAL, AdvancedTone.ENCOURAGING, AdvancedTone.MEDICAL_SCIENTIFIC]
        times = []

        for i in range(iterations):
            tone = tones[i % len(tones)]
            start_time = time.perf_counter()

            profile = tone_manager.get_tone_profile(tone.value)

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]

        print(f"\nTone Profile Retrieval Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  95th percentile: {p95_time*1000:.2f}ms")
        print(f"  Iterations: {iterations}")

        # Should be very fast for cached profiles
        assert avg_time < 0.001, f"Average profile retrieval time {avg_time*1000:.2f}ms exceeds 1ms"
        assert p95_time < 0.005, f"95th percentile time {p95_time*1000:.2f}ms exceeds 5ms"

    def test_multi_tone_blending_performance(self, tone_manager):
        """Test performance of multi-tone blending operations"""
        iterations = 500
        combinations = [
            "professional_encouraging",
            "encouraging_medical",
            "professional_medical"
        ]
        times = []

        for i in range(iterations):
            combination = combinations[i % len(combinations)]
            start_time = time.perf_counter()

            blended_tone = tone_manager.blend_tones(combination)

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]

        print(f"\nMulti-Tone Blending Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  95th percentile: {p95_time*1000:.2f}ms")
        print(f"  Iterations: {iterations}")

        # Blending should be reasonably fast
        assert avg_time < 0.020, f"Average blending time {avg_time*1000:.2f}ms exceeds 20ms"
        assert p95_time < 0.100, f"95th percentile time {p95_time*1000:.2f}ms exceeds 100ms"

    def test_concurrent_tone_selection_performance(self, tone_manager, sample_content):
        """Test performance under concurrent tone selection load"""

        async def select_tone_task():
            """Single tone selection task"""
            start_time = time.perf_counter()
            tone = tone_manager.select_tone(
                content_type="newsletter",
                channel="email",
                context={"content_items": len(sample_content.get('breathscape', []))}
            )
            end_time = time.perf_counter()
            return end_time - start_time

        async def run_concurrent_test():
            """Run concurrent tone selections"""
            concurrent_requests = 100
            tasks = [select_tone_task() for _ in range(concurrent_requests)]

            start_time = time.perf_counter()
            times = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start_time

            return times, total_time

        # Run the async test
        times, total_time = asyncio.run(run_concurrent_test())

        avg_time = statistics.mean(times)
        throughput = len(times) / total_time

        print(f"\nConcurrent Tone Selection Performance:")
        print(f"  Concurrent requests: 100")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average per-request time: {avg_time*1000:.2f}ms")
        print(f"  Throughput: {throughput:.1f} requests/second")

        # Performance requirements for concurrent access
        assert throughput > 500, f"Throughput {throughput:.1f} req/s is below minimum 500 req/s"
        assert avg_time < 0.050, f"Average concurrent time {avg_time*1000:.2f}ms exceeds 50ms"

    def test_brand_validation_performance(self, tone_manager):
        """Test performance of brand consistency validation"""
        iterations = 200
        test_content = "This is a test content piece for brand validation performance testing."
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            # Test brand validation
            score = tone_manager.validate_brand_consistency(
                content=test_content,
                selected_tone=AdvancedTone.PROFESSIONAL,
                channel="email"
            )

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]

        print(f"\nBrand Validation Performance:")
        print(f"  Average time: {avg_time*1000:.2f}ms")
        print(f"  95th percentile: {p95_time*1000:.2f}ms")
        print(f"  Iterations: {iterations}")

        # Brand validation should be reasonably fast
        assert avg_time < 0.050, f"Average validation time {avg_time*1000:.2f}ms exceeds 50ms"
        assert p95_time < 0.200, f"95th percentile time {p95_time*1000:.2f}ms exceeds 200ms"

    def test_tone_system_memory_usage(self, tone_manager):
        """Test memory efficiency of tone system"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many tone operations
        for i in range(1000):
            tone_manager.select_tone("newsletter", "email")
            tone_manager.get_tone_profile("professional")
            tone_manager.blend_tones("professional_encouraging")

            # Validate every 100 iterations
            if i % 100 == 0:
                tone_manager.validate_brand_consistency(
                    "Test content", AdvancedTone.PROFESSIONAL, "email"
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\nTone System Memory Usage:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")

        # Memory usage should not grow significantly
        assert memory_increase < 50, f"Memory increase {memory_increase:.1f}MB exceeds 50MB limit"

    @pytest.mark.parametrize("content_size", [10, 50, 100, 500])
    def test_tone_selection_scalability(self, tone_manager, content_size):
        """Test tone selection performance with varying content sizes"""
        # Generate content of different sizes
        large_content = {
            'breathscape': [
                {
                    'title': f'Article {i}',
                    'content': f'Content piece {i} with detailed information about breathing techniques.',
                    'tags': ['breathing', 'wellness']
                }
                for i in range(content_size)
            ]
        }

        iterations = 50
        times = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            tone = tone_manager.select_tone(
                content_type="newsletter",
                channel="email",
                context={"content_items": len(large_content.get('breathscape', []))}
            )

            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = statistics.mean(times)

        print(f"\nScalability Test (Content Size: {content_size}):")
        print(f"  Average time: {avg_time*1000:.2f}ms")

        # Performance should not degrade significantly with content size
        expected_max_time = 0.010 + (content_size * 0.0001)  # Linear scaling allowance
        assert avg_time < expected_max_time, f"Average time {avg_time*1000:.2f}ms exceeds expected {expected_max_time*1000:.2f}ms for content size {content_size}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])