"""
Locust load testing scenarios for performance baseline establishment
"""
import json
import time
import random
from typing import Dict, Any, Optional
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger(__name__)


class BaseHalcytoneUser(HttpUser):
    """Base class for Halcytone load testing users"""

    abstract = True
    host = "http://localhost:8000"

    # Test data for content generation
    test_content_data = [
        {
            "content_type": "newsletter",
            "template": "modern",
            "data": {
                "title": "Weekly Health Update",
                "sections": [
                    {"type": "text", "content": "This week's health insights and tips"},
                    {"type": "data", "content": "Patient engagement metrics"}
                ]
            }
        },
        {
            "content_type": "web_update",
            "template": "clean",
            "data": {
                "title": "Service Update",
                "content": "New features and improvements",
                "category": "announcement"
            }
        },
        {
            "content_type": "social_post",
            "template": "engaging",
            "data": {
                "platform": "twitter",
                "content": "Health tip of the day",
                "hashtags": ["#health", "#wellness"]
            }
        }
    ]

    def on_start(self):
        """Initialize user session"""
        self.client.verify = False

        # Set API key for authentication
        self.api_key = "test-api-key-performance-testing"
        self.client.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

        logger.info(f"Started user session: {self.__class__.__name__}")

    def get_random_content_data(self) -> Dict[str, Any]:
        """Get random test content data"""
        return random.choice(self.test_content_data)


class HealthCheckUser(BaseHalcytoneUser):
    """User that only performs health checks"""

    wait_time = between(1, 3)
    weight = 1

    @task(10)
    def health_check(self):
        """Basic health check"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def readiness_check(self):
        """Readiness check"""
        with self.client.get("/ready", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Readiness check unexpected status: {response.status_code}")

    @task(2)
    def liveness_check(self):
        """Liveness check"""
        with self.client.get("/live", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check failed: {response.status_code}")

    @task(1)
    def metrics_endpoint(self):
        """Metrics endpoint check"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics endpoint failed: {response.status_code}")


class ContentGenerationUser(BaseHalcytoneUser):
    """User focused on content generation operations"""

    wait_time = between(2, 8)
    weight = 3

    @task(15)
    def generate_content(self):
        """Generate individual content"""
        content_data = self.get_random_content_data()

        with self.client.post(
            "/api/v2/content/generate",
            json=content_data,
            catch_response=True,
            name="content_generation"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "content" in result:
                        response.success()
                    else:
                        response.failure("No content in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 422:
                response.failure("Validation error")
            else:
                response.failure(f"Content generation failed: {response.status_code}")

    @task(8)
    def generate_enhanced_content(self):
        """Generate enhanced content with AI features"""
        content_data = self.get_random_content_data()
        content_data["ai_enhancement"] = True
        content_data["quality_scoring"] = True

        with self.client.post(
            "/api/v2/content/generate/enhanced",
            json=content_data,
            catch_response=True,
            name="enhanced_content_generation"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "content" in result and "quality_score" in result:
                        response.success()
                    else:
                        response.failure("Missing enhanced content fields")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Enhanced content generation failed: {response.status_code}")

    @task(5)
    def batch_generate(self):
        """Generate batch content"""
        batch_data = {
            "items": [self.get_random_content_data() for _ in range(random.randint(2, 5))],
            "batch_settings": {
                "parallel": True,
                "max_concurrency": 3
            }
        }

        with self.client.post(
            "/api/v1/content/batch",
            json=batch_data,
            catch_response=True,
            name="batch_content_generation",
            timeout=30
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "results" in result:
                        response.success()
                    else:
                        response.failure("No batch results in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Batch generation failed: {response.status_code}")

    @task(3)
    def validate_content(self):
        """Validate content request"""
        content_data = self.get_random_content_data()

        with self.client.post(
            "/api/v2/content/validate",
            json=content_data,
            catch_response=True,
            name="content_validation"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 422:
                # Validation errors are expected for some test data
                response.success()
            else:
                response.failure(f"Content validation failed: {response.status_code}")


class APIExplorationUser(BaseHalcytoneUser):
    """User that explores various API endpoints"""

    wait_time = between(3, 10)
    weight = 2

    @task(8)
    def get_service_status(self):
        """Get service status"""
        with self.client.get("/api/v1/services/status", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Service status failed: {response.status_code}")

    @task(5)
    def get_database_status(self):
        """Get database status"""
        with self.client.get("/api/v1/database/status", catch_response=True) as response:
            if response.status_code in [200, 500]:  # 500 if DB not configured
                response.success()
            else:
                response.failure(f"Database status failed: {response.status_code}")

    @task(3)
    def validate_services(self):
        """Validate external services"""
        with self.client.post("/api/v1/services/validate", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Service validation failed: {response.status_code}")

    @task(6)
    def get_detailed_health(self):
        """Get detailed health check"""
        with self.client.get("/health/detailed", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Detailed health check failed: {response.status_code}")

    @task(2)
    def trigger_component_check(self):
        """Trigger individual component health check"""
        components = ["database", "cache", "external_services"]
        component = random.choice(components)

        with self.client.post(f"/health/check/{component}", catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 if component doesn't exist
                response.success()
            else:
                response.failure(f"Component check failed: {response.status_code}")


class HeavyWorkloadUser(BaseHalcytoneUser):
    """User that simulates heavy workload scenarios"""

    wait_time = between(1, 5)
    weight = 1

    @task(10)
    def concurrent_content_generation(self):
        """Generate multiple content pieces rapidly"""
        for _ in range(random.randint(3, 6)):
            content_data = self.get_random_content_data()

            with self.client.post(
                "/api/v2/content/generate",
                json=content_data,
                catch_response=True,
                name="concurrent_content_generation"
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Concurrent generation failed: {response.status_code}")
                    break

            # Small delay between requests
            time.sleep(0.1)

    @task(5)
    def large_batch_generation(self):
        """Generate large batches"""
        batch_data = {
            "items": [self.get_random_content_data() for _ in range(random.randint(8, 15))],
            "batch_settings": {
                "parallel": True,
                "max_concurrency": 5
            }
        }

        with self.client.post(
            "/api/v1/content/batch",
            json=batch_data,
            catch_response=True,
            name="large_batch_generation",
            timeout=60
        ) as response:
            if response.status_code != 200:
                response.failure(f"Large batch generation failed: {response.status_code}")

    @task(3)
    def sustained_load(self):
        """Sustained API calls"""
        for _ in range(10):
            endpoint = random.choice(["/health", "/ready", "/metrics"])

            with self.client.get(endpoint, catch_response=True) as response:
                if response.status_code not in [200, 503]:
                    response.failure(f"Sustained load call failed: {response.status_code}")

            time.sleep(0.05)  # 50ms between calls


class MixedWorkloadUser(BaseHalcytoneUser):
    """User with mixed realistic workload patterns"""

    wait_time = between(2, 15)
    weight = 4

    @task(20)
    def typical_content_workflow(self):
        """Typical user workflow: validate -> generate -> check status"""
        content_data = self.get_random_content_data()

        # Step 1: Validate content
        with self.client.post(
            "/api/v2/content/validate",
            json=content_data,
            catch_response=True
        ) as response:
            if response.status_code not in [200, 422]:
                response.failure("Validation step failed")
                return

        # Step 2: Generate content
        with self.client.post(
            "/api/v2/content/generate",
            json=content_data,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure("Generation step failed")
                return

        # Step 3: Check service status
        with self.client.get("/api/v1/services/status", catch_response=True) as response:
            if response.status_code != 200:
                response.failure("Status check step failed")

    @task(10)
    def periodic_health_monitoring(self):
        """Periodic health monitoring like a monitoring system would do"""
        endpoints = ["/health", "/ready", "/live", "/metrics"]

        for endpoint in endpoints:
            with self.client.get(endpoint, catch_response=True) as response:
                expected_codes = [200, 503] if endpoint in ["/health", "/ready"] else [200]
                if response.status_code not in expected_codes:
                    response.failure(f"Health monitoring failed for {endpoint}")

            time.sleep(0.1)

    @task(8)
    def realistic_batch_processing(self):
        """Realistic batch processing scenario"""
        # Small to medium batch sizes
        batch_size = random.choices([2, 3, 5, 8], weights=[40, 30, 20, 10])[0]

        batch_data = {
            "items": [self.get_random_content_data() for _ in range(batch_size)],
            "batch_settings": {
                "parallel": batch_size <= 5,
                "max_concurrency": min(3, batch_size)
            }
        }

        with self.client.post(
            "/api/v1/content/batch",
            json=batch_data,
            catch_response=True,
            timeout=45
        ) as response:
            if response.status_code != 200:
                response.failure(f"Realistic batch processing failed: {response.status_code}")

    @task(5)
    def error_handling_scenarios(self):
        """Test error handling with invalid requests"""
        scenarios = [
            # Invalid content type
            {"content_type": "invalid_type", "data": {}},
            # Missing required fields
            {"content_type": "newsletter"},
            # Invalid JSON structure
            {"invalid": "structure", "nested": {"deeply": {"invalid": True}}}
        ]

        scenario = random.choice(scenarios)

        with self.client.post(
            "/api/v2/content/generate",
            json=scenario,
            catch_response=True,
            name="error_handling_test"
        ) as response:
            if response.status_code == 422:
                response.success()  # Expected validation error
            elif response.status_code == 400:
                response.success()  # Expected bad request
            else:
                response.failure(f"Unexpected error handling response: {response.status_code}")


# Default user for general load testing
class HalcytoneUser(MixedWorkloadUser):
    """Default user class combining all patterns for general load testing"""
    wait_time = between(1, 10)


# Event listeners for performance metrics collection
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Collect custom metrics during load testing"""
    if exception:
        logger.error(f"Request failed: {request_type} {name} - {exception}")
    else:
        # Log successful requests for analysis
        logger.debug(f"Request completed: {request_type} {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize performance test"""
    logger.info("Performance test started")
    logger.info(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize performance test"""
    logger.info("Performance test completed")

    # Log final statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time}ms")
    logger.info(f"Requests per second: {stats.total.current_rps:.2f}")


if __name__ == "__main__":
    # Can be run directly with: python -m locust -f performance/load_tests.py
    print("Load testing scenarios available:")
    print("- HealthCheckUser: Health endpoint focused testing")
    print("- ContentGenerationUser: Content generation focused testing")
    print("- APIExplorationUser: API endpoint exploration")
    print("- HeavyWorkloadUser: High-intensity load testing")
    print("- MixedWorkloadUser: Realistic mixed workload")
    print("- HalcytoneUser: Default comprehensive testing")
    print("\nRun with: locust -f performance/load_tests.py --host http://localhost:8000")