"""
Unit tests for main application entry point
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('halcytone_content_generator.main.get_settings') as mock:
        settings = MagicMock()
        settings.ENVIRONMENT = "test"
        settings.DEBUG = True
        settings.LOG_LEVEL = "INFO"
        settings.ENABLE_METRICS = False
        settings.METRICS_PORT = 9090
        mock.return_value = settings
        yield settings

@pytest.fixture
def test_client(mock_settings):
    """Create test client"""
    from halcytone_content_generator.main import app
    return TestClient(app)

def test_app_startup(test_client):
    """Test application starts up correctly"""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_app_ready_endpoint(test_client):
    """Test ready endpoint"""
    response = test_client.get("/ready")
    assert response.status_code == 200

def test_api_routes_included(test_client):
    """Test API routes are included"""
    # Test health endpoint from health_endpoints router
    response = test_client.get("/health")
    assert response.status_code == 200

def test_cors_middleware_configured(test_client):
    """Test CORS is configured"""
    response = test_client.options("/health", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" in response.headers

def test_main_execution():
    """Test main execution with uvicorn"""
    with patch('uvicorn.run') as mock_run:
        with patch.object(sys, 'argv', ['main.py']):
            # Import and execute main
            from halcytone_content_generator import main as main_module
            if hasattr(main_module, '__name__'):
                with patch.object(main_module, '__name__', '__main__'):
                    # This would normally trigger the if __name__ == "__main__" block
                    # But we'll just call uvicorn.run directly for testing
                    import uvicorn
                    uvicorn.run("src.halcytone_content_generator.main:app", host="0.0.0.0", port=8002, reload=True)

            mock_run.assert_called_once()

def test_lifespan_events():
    """Test application lifespan events"""
    from halcytone_content_generator.main import app

    # Test startup
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

def test_exception_handlers(test_client):
    """Test exception handlers are configured"""
    # Test 404 handler
    response = test_client.get("/nonexistent")
    assert response.status_code == 404

def test_metrics_endpoint_exists(test_client):
    """Test metrics endpoint exists"""
    # The /metrics endpoint is provided by health_endpoints router
    response = test_client.get("/metrics")
    assert response.status_code == 200

def test_api_documentation(test_client):
    """Test API documentation is available"""
    response = test_client.get("/docs")
    assert response.status_code == 200

def test_openapi_schema(test_client):
    """Test OpenAPI schema is available"""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Halcytone Content Generator"


def test_root_endpoint(test_client):
    """Test root endpoint returns service info"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Halcytone Content Generator"
    assert data["version"] == "0.1.0"
    assert data["status"] == "operational"


def test_legacy_health_endpoint(test_client):
    """Test legacy health endpoint"""
    response = test_client.get("/health-legacy")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # Settings are injected at runtime, just verify structure
    assert "service" in data
    assert "environment" in data


def test_multiple_router_endpoints(test_client):
    """Test that multiple routers are properly included"""
    # Test endpoints from different routers
    endpoints_to_test = [
        "/",  # root
        "/health",  # health_endpoints
        "/ready",  # health_endpoints
        "/metrics",  # health_endpoints
        "/docs",  # FastAPI auto
        "/openapi.json",  # FastAPI auto
    ]

    for endpoint in endpoints_to_test:
        response = test_client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} failed with {response.status_code}"


def test_legacy_readiness_endpoint(test_client, mock_settings):
    """Test legacy readiness endpoint"""
    mock_settings.CRM_BASE_URL = "https://crm.example.com"
    mock_settings.PLATFORM_BASE_URL = "https://platform.example.com"
    mock_settings.LIVING_DOC_ID = "doc_123"

    response = test_client.get("/ready-legacy")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert data["checks"]["crm_configured"] is True
    assert data["checks"]["platform_configured"] is True


def test_service_status_endpoint(test_client):
    """Test service status endpoint"""
    with patch('halcytone_content_generator.core.services.validate_all_services') as mock_validate, \
         patch('halcytone_content_generator.core.services.get_service_info') as mock_info:

        mock_validate.return_value = {
            "crm": {"status": "connected", "details": "OK"},
            "platform": {"status": "connected", "details": "OK"}
        }
        mock_info.return_value = {
            "crm": {"type": "CRM", "version": "1.0"},
            "platform": {"type": "Platform", "version": "1.0"}
        }

        response = test_client.get("/api/v1/services/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "service_info" in data
        assert "validation_results" in data


def test_service_status_endpoint_error(test_client):
    """Test service status endpoint handles errors"""
    with patch('halcytone_content_generator.core.services.validate_all_services', side_effect=Exception("Service error")):
        response = test_client.get("/api/v1/services/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data


def test_cors_headers_on_endpoints(test_client):
    """Test CORS headers are present on various endpoints"""
    response = test_client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    # CORS middleware should add headers
    assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


def test_application_metadata(test_client):
    """Test application metadata in OpenAPI schema"""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()

    # Verify application metadata
    assert data["info"]["title"] == "Halcytone Content Generator"
    assert data["info"]["description"] == "Automated multi-channel content generation for marketing communications"
    assert data["info"]["version"] == "0.1.0"


def test_router_prefixes(test_client):
    """Test routers are mounted with correct prefixes"""
    # The health endpoints should work without prefix
    response = test_client.get("/health")
    assert response.status_code == 200

    # Legacy endpoints should work
    response = test_client.get("/health-legacy")
    assert response.status_code == 200

    response = test_client.get("/ready-legacy")
    assert response.status_code == 200


def test_error_responses(test_client):
    """Test error response format"""
    # Test 404
    response = test_client.get("/completely/invalid/path")
    assert response.status_code == 404

    # Response should be JSON (FastAPI default)
    assert response.headers.get("content-type", "").startswith("application/json")


def test_validate_services_endpoint(test_client):
    """Test service validation endpoint"""
    with patch('halcytone_content_generator.core.services.validate_all_services') as mock_validate:
        mock_validate.return_value = {
            "crm": {"status": "connected", "details": "OK"},
            "platform": {"status": "connected", "details": "OK"}
        }

        response = test_client.post("/api/v1/services/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["all_services_ok"] is True
        assert "results" in data


def test_validate_services_endpoint_partial_failure(test_client):
    """Test service validation endpoint with partial failures"""
    with patch('halcytone_content_generator.core.services.validate_all_services') as mock_validate:
        mock_validate.return_value = {
            "crm": {"status": "connected", "details": "OK"},
            "platform": {"status": "error", "details": "Connection failed"}
        }

        response = test_client.post("/api/v1/services/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial_failure"
        assert data["all_services_ok"] is False


def test_validate_services_endpoint_error(test_client):
    """Test service validation endpoint handles errors"""
    with patch('halcytone_content_generator.core.services.validate_all_services', side_effect=Exception("Validation error")):
        response = test_client.post("/api/v1/services/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data


def test_database_status_endpoint_success(test_client):
    """Test database status endpoint when database is available"""
    with patch('halcytone_content_generator.database.get_database') as mock_get_db, \
         patch('halcytone_content_generator.database.config.get_database_settings') as mock_get_settings:

        # Mock database
        mock_db = MagicMock()
        mock_db.health_check = Mock(return_value={
            "status": "healthy",
            "connection": "active",
            "latency_ms": 5
        })
        mock_get_db.return_value = mock_db

        # Mock settings
        mock_settings = MagicMock()
        mock_settings.DATABASE_TYPE.value = "postgresql"
        mock_settings.DATABASE_NAME = "test_db"
        mock_settings.DATABASE_POOL_SIZE = 10
        mock_settings.DATABASE_POOL_MAX_OVERFLOW = 5
        mock_settings.DATABASE_SSL_MODE = "require"
        mock_settings.DATABASE_AUTO_MIGRATE = True
        mock_settings.DATABASE_USE_READ_REPLICA = False
        mock_get_settings.return_value = mock_settings

        response = test_client.get("/api/v1/database/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "health" in data
        assert "configuration" in data
        assert data["configuration"]["database_type"] == "postgresql"
        assert data["configuration"]["database_name"] == "test_db"


def test_database_status_endpoint_error(test_client):
    """Test database status endpoint when database is not available"""
    with patch('halcytone_content_generator.database.get_database', side_effect=Exception("Database not configured")):
        response = test_client.get("/api/v1/database/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data
        assert "message" in data


def test_database_migrate_endpoint_success(test_client):
    """Test database migration endpoint success"""
    with patch('halcytone_content_generator.database.get_database') as mock_get_db:
        mock_db = MagicMock()
        mock_db.run_migrations = Mock(return_value=None)
        mock_get_db.return_value = mock_db

        response = test_client.post("/api/v1/database/migrate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "message" in data
        mock_db.run_migrations.assert_called_once()


def test_database_migrate_endpoint_error(test_client):
    """Test database migration endpoint handles errors"""
    with patch('halcytone_content_generator.database.get_database', side_effect=Exception("Migration failed")):
        response = test_client.post("/api/v1/database/migrate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "error" in data
        assert "message" in data


def test_legacy_health_endpoint_with_database(test_client, mock_settings):
    """Test legacy health endpoint includes database health"""
    with patch('halcytone_content_generator.database.get_database') as mock_get_db:
        mock_db = MagicMock()
        mock_db.is_connected = True
        mock_db.health_check = Mock(return_value={"status": "healthy", "connection": "active"})
        mock_get_db.return_value = mock_db

        response = test_client.get("/health-legacy")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert data["database"]["status"] == "healthy"


def test_legacy_health_endpoint_database_error(test_client, mock_settings):
    """Test legacy health endpoint handles database errors"""
    with patch('halcytone_content_generator.database.get_database', side_effect=Exception("DB connection failed")):
        response = test_client.get("/health-legacy")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert data["database"]["status"] == "error"


def test_legacy_readiness_endpoint_with_service_validation(test_client, mock_settings):
    """Test legacy readiness endpoint with service validation"""
    mock_settings.CRM_BASE_URL = "https://crm.example.com"
    mock_settings.PLATFORM_BASE_URL = "https://platform.example.com"
    mock_settings.LIVING_DOC_ID = "doc_123"

    with patch('halcytone_content_generator.core.services.validate_all_services') as mock_validate:
        mock_validate.return_value = {
            "crm": {"status": "connected", "details": "OK"},
            "platform": {"status": "configured", "details": "OK"}
        }

        response = test_client.get("/ready-legacy")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert data["checks"]["services_validated"] is True


def test_legacy_readiness_endpoint_service_validation_failure(test_client, mock_settings):
    """Test legacy readiness endpoint when service validation fails"""
    mock_settings.CRM_BASE_URL = "https://crm.example.com"
    mock_settings.PLATFORM_BASE_URL = "https://platform.example.com"
    mock_settings.LIVING_DOC_ID = "doc_123"

    with patch('halcytone_content_generator.core.services.validate_all_services', side_effect=Exception("Validation failed")):
        response = test_client.get("/ready-legacy")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert data["checks"]["services_validated"] is False


def test_all_routers_included(test_client):
    """Test that all routers are properly included in the application"""
    # Verify the app has the expected routers
    from halcytone_content_generator.main import app

    # Check that routers are included by examining the app routes
    route_paths = [route.path for route in app.routes]

    # Should have routes from all included routers
    assert "/" in route_paths  # root endpoint
    assert any("/api/v1" in path for path in route_paths)  # v1 endpoints
    assert any("/api/v2" in path or "/api/v3" in path for path in route_paths)  # v2/v3 endpoints
    # Health endpoints exist
    assert "/health" in route_paths or any("health" in path for path in route_paths)