"""
Pytest configuration for mock services
This module provides fixtures to ensure mock services are running during tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.start_mock_services import ensure_mock_services_running


@pytest.fixture(scope="session", autouse=True)
def ensure_mock_services():
    """
    Pytest fixture that ensures mock services are running before any tests execute.
    This fixture runs automatically for the entire test session.
    """
    print("\n🚀 Starting mock services for test session...")

    success = ensure_mock_services_running(force=False, quiet=False)

    if not success:
        pytest.fail("Failed to start mock services. Tests cannot proceed.")

    print("✅ Mock services are ready for testing")

    # Services will continue running after tests complete
    # They can be manually stopped with: docker-compose -f docker-compose.mocks.yml down
    yield

    print("🧹 Test session completed. Mock services left running for development.")


@pytest.fixture(scope="function")
def mock_crm_service():
    """
    Fixture providing CRM service connection information.
    Use this fixture in tests that need CRM service details.
    """
    return {
        "base_url": "http://localhost:8001",
        "health_url": "http://localhost:8001/health",
        "docs_url": "http://localhost:8001/docs",
        "contacts_endpoint": "http://localhost:8001/contacts",
        "email_endpoint": "http://localhost:8001/send-email",
        "campaigns_endpoint": "http://localhost:8001/campaigns"
    }


@pytest.fixture(scope="function")
def mock_platform_service():
    """
    Fixture providing Platform service connection information.
    Use this fixture in tests that need Platform service details.
    """
    return {
        "base_url": "http://localhost:8002",
        "health_url": "http://localhost:8002/health",
        "docs_url": "http://localhost:8002/docs",
        "content_endpoint": "http://localhost:8002/content",
        "social_endpoint": "http://localhost:8002/social-posts",
        "analytics_endpoint": "http://localhost:8002/analytics"
    }


@pytest.fixture(scope="function")
def mock_services():
    """
    Combined fixture providing both CRM and Platform service information.
    Use this fixture when tests need both services.
    """
    return {
        "crm": {
            "base_url": "http://localhost:8001",
            "health_url": "http://localhost:8001/health",
            "docs_url": "http://localhost:8001/docs",
            "contacts_endpoint": "http://localhost:8001/contacts",
            "email_endpoint": "http://localhost:8001/send-email",
            "campaigns_endpoint": "http://localhost:8001/campaigns"
        },
        "platform": {
            "base_url": "http://localhost:8002",
            "health_url": "http://localhost:8002/health",
            "docs_url": "http://localhost:8002/docs",
            "content_endpoint": "http://localhost:8002/content",
            "social_endpoint": "http://localhost:8002/social-posts",
            "analytics_endpoint": "http://localhost:8002/analytics"
        }
    }


# Hook to customize test collection
def pytest_configure(config):
    """Configure pytest with custom markers for mock service tests"""
    config.addinivalue_line(
        "markers",
        "mock_services: tests that require mock services to be running"
    )
    config.addinivalue_line(
        "markers",
        "crm_service: tests that specifically require the CRM mock service"
    )
    config.addinivalue_line(
        "markers",
        "platform_service: tests that specifically require the Platform mock service"
    )


def pytest_collection_modifyitems(config, items):
    """
    Add mock_services marker to tests that use mock service fixtures
    """
    mock_service_fixtures = {
        "mock_crm_service",
        "mock_platform_service",
        "mock_services"
    }

    mock_services_marker = pytest.mark.mock_services

    for item in items:
        if hasattr(item, "fixturenames"):
            if any(fixture in mock_service_fixtures for fixture in item.fixturenames):
                item.add_marker(mock_services_marker)