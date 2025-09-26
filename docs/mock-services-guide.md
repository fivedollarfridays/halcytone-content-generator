# Mock Services Guide

## Overview

The Halcytone Content Generator includes comprehensive mock services for development and testing without external dependencies. This guide covers how to start, manage, and use mock services.

## Mock Services Available

### CRM Service (Port 8001)
- **Purpose**: Simulates CRM API for email sending and contact management
- **Health Check**: `http://localhost:8001/health`
- **API Documentation**: `http://localhost:8001/docs`
- **Key Endpoints**:
  - `GET /contacts` - Retrieve contacts
  - `POST /send-email` - Send email campaigns
  - `GET /campaigns` - Campaign management
  - `POST /analytics/track` - Email analytics tracking

### Platform Service (Port 8002)
- **Purpose**: Simulates Platform API for web publishing and social media
- **Health Check**: `http://localhost:8002/health`
- **API Documentation**: `http://localhost:8002/docs`
- **Key Endpoints**:
  - `GET /content` - Content management
  - `POST /content/publish` - Publish content
  - `GET /social-posts` - Social media posts
  - `GET /analytics` - Platform analytics

## Quick Start

### Method 1: Python Script (Recommended)
```bash
# Start mock services
python scripts/start_mock_services.py

# Force restart if already running
python scripts/start_mock_services.py --force

# Quiet mode (for automated testing)
python scripts/start_mock_services.py --quiet
```

### Method 2: Make Commands
```bash
# Start mock services
make mock-start

# Check status
make mock-status

# View logs
make mock-logs

# Stop services
make mock-stop

# Clean and rebuild
make mock-rebuild
```

### Method 3: Direct Docker Compose
```bash
# Build and start
docker-compose -f docker-compose.mocks.yml up -d

# Stop services
docker-compose -f docker-compose.mocks.yml down

# View logs
docker-compose -f docker-compose.mocks.yml logs -f
```

### Method 4: Platform-Specific Scripts

**Unix/Linux/macOS:**
```bash
./scripts/start-mock-services.sh
```

**Windows:**
```batch
scripts\start-mock-services.bat
```

## Testing Integration

### Automatic Startup for Tests

The mock services include pytest fixtures that automatically start services before tests run:

```python
# In your test file
import pytest

def test_content_generation(mock_services):
    """Test using both CRM and Platform services"""
    crm_url = mock_services["crm"]["base_url"]
    platform_url = mock_services["platform"]["base_url"]
    # Your test code here

def test_crm_only(mock_crm_service):
    """Test using only CRM service"""
    response = requests.get(f"{mock_crm_service['base_url']}/contacts")
    assert response.status_code == 200
```

### Running Contract Tests
```bash
# Run contract tests (will auto-start mock services)
make test-contracts

# Or directly with pytest
pytest tests/contracts/ -v
```

## Service Configuration

### Environment Variables

Mock services respect these environment variables:

```bash
# Service configuration
SERVICE_NAME=mock-crm|mock-platform
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
PYTHONPATH=/app

# Container configuration
MOCK_SERVICES_TIMEOUT=30        # Startup timeout in seconds
MOCK_SERVICES_HEALTH_INTERVAL=30s  # Health check interval
```

### Docker Configuration

The services are configured in `docker-compose.mocks.yml`:

```yaml
# Key configuration highlights:
services:
  mock-crm:
    ports: ["8001:8001"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]

  mock-platform:
    ports: ["8002:8002"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
```

## Development Workflow

### Starting Development Environment
```bash
# 1. Start mock services
make mock-start

# 2. Start main application
uvicorn src.halcytone_content_generator.main:app --reload --port 8000

# 3. Verify everything is working
make mock-status
curl http://localhost:8000/health
```

### Testing Workflow
```bash
# Run tests with mock services
make test-contracts

# Run specific contract test
pytest tests/contracts/test_content_api.py::TestContentAPIContract::test_dry_run_contract -v

# Check service logs if tests fail
make mock-logs
```

## Troubleshooting

### Common Issues

#### Services Won't Start
1. **Check Docker**: Ensure Docker Desktop is running
   ```bash
   docker info
   ```

2. **Port Conflicts**: Check if ports 8001/8002 are in use
   ```bash
   # Windows
   netstat -ano | findstr :8001
   netstat -ano | findstr :8002

   # Unix/Linux/macOS
   lsof -i :8001
   lsof -i :8002
   ```

3. **Force Restart**: Clean and restart services
   ```bash
   make mock-clean
   make mock-start
   ```

#### Services Appear Healthy but Tests Fail
1. **Check Service Endpoints**:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   curl http://localhost:8001/contacts
   curl http://localhost:8002/content
   ```

2. **Review Logs**:
   ```bash
   make mock-logs
   # Or
   docker-compose -f docker-compose.mocks.yml logs --tail=50
   ```

#### Memory/Resource Issues
1. **Increase Docker Resources**: Allocate more memory to Docker Desktop
2. **Clean Docker System**:
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or modify docker-compose.mocks.yml temporarily:
environment:
  - LOG_LEVEL=DEBUG
```

## API Reference

### CRM Service Endpoints

#### Email Management
- `POST /send-email` - Send email campaign
  ```json
  {
    "subject": "Newsletter Subject",
    "html_content": "<h1>Content</h1>",
    "recipients": ["user@example.com"],
    "campaign_id": "campaign_123"
  }
  ```

#### Contact Management
- `GET /contacts` - List all contacts
- `POST /contacts` - Add new contact
- `GET /contacts/{contact_id}` - Get contact details

#### Campaign Management
- `GET /campaigns` - List campaigns
- `POST /campaigns` - Create campaign
- `GET /campaigns/{campaign_id}/analytics` - Campaign analytics

### Platform Service Endpoints

#### Content Management
- `GET /content` - List published content
- `POST /content/publish` - Publish new content
  ```json
  {
    "title": "Content Title",
    "content": "Content body...",
    "content_type": "web_update",
    "tags": ["news", "update"]
  }
  ```

#### Social Media
- `GET /social-posts` - List social posts
- `POST /social-posts` - Create social post
  ```json
  {
    "platform": "twitter",
    "content": "Post content",
    "hashtags": ["#halcytone", "#wellness"]
  }
  ```

## Integration with Main Application

### Configuration

The main application detects mock services automatically when running in development mode:

```python
# In .env file
DRY_RUN_MODE=true
USE_MOCK_SERVICES=true
CRM_BASE_URL=http://localhost:8001
PLATFORM_BASE_URL=http://localhost:8002
```

### Service Discovery

The application includes health checks and service discovery:

```python
# Health check endpoint
GET /ready
# Returns service connectivity status
```

## Production Considerations

### Security

- Mock services are **NOT** intended for production use
- They contain no authentication or security measures
- All data is stored in memory and lost on restart

### Performance

- Mock services have minimal latency (< 10ms response time)
- No rate limiting is enforced
- Memory usage is minimal (~50MB per service)

### Limitations

- No persistent data storage
- No real external integrations
- Simplified business logic
- No rate limiting or quotas

## Support

### Getting Help

1. **Check Logs**: Always start with service logs
   ```bash
   make mock-logs
   ```

2. **Health Checks**: Verify service health
   ```bash
   make mock-status
   ```

3. **Clean Restart**: When in doubt, clean restart
   ```bash
   make mock-clean
   make mock-start
   ```

4. **Documentation**: Review API docs
   - CRM: http://localhost:8001/docs
   - Platform: http://localhost:8002/docs

### Filing Issues

When reporting issues, include:
- Operating system and Docker version
- Complete error messages
- Output from `make mock-status`
- Relevant log excerpts
- Steps to reproduce the issue

---

## Version History

- **v1.0** - Initial mock services implementation
- **v1.1** - Added automated startup scripts
- **v1.2** - Added pytest integration
- **v1.3** - Added cross-platform support
- **v1.4** - Enhanced error handling and logging