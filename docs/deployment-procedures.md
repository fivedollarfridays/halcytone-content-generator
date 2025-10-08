# Toombos - Deployment Procedures

## Overview

This document provides comprehensive deployment procedures for the Toombos dry run system across different environments: local development, staging, and production simulation.

**Version:** Sprint 5 - Documentation & Production Readiness
**Last Updated:** 2025-01-24

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development Deployment](#local-development-deployment)
4. [Staging Deployment](#staging-deployment)
5. [Production Simulation Deployment](#production-simulation-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Rollback Procedures](#rollback-procedures)
8. [Health Checks](#health-checks)
9. [Post-Deployment Validation](#post-deployment-validation)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

#### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **RAM**: 4GB available memory
- **CPU**: 2+ cores
- **Storage**: 10GB available disk space
- **Network**: Internet access for initial setup

#### Recommended Requirements
- **OS**: Linux (Ubuntu 22.04 LTS)
- **RAM**: 8GB available memory
- **CPU**: 4+ cores
- **Storage**: 20GB SSD storage
- **Network**: Stable broadband connection

### Software Dependencies

#### Required Software
```bash
# Python 3.11 or higher
python3 --version  # Should be 3.11+

# pip package manager
pip3 --version

# Git version control
git --version

# curl for API testing
curl --version

# Optional: Docker and Docker Compose
docker --version
docker-compose --version
```

#### Installation Commands

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-pip git curl
sudo apt install -y docker.io docker-compose  # Optional

# Add user to docker group (if using Docker)
sudo usermod -aG docker $USER
newgrp docker
```

**macOS:**
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git curl
brew install docker docker-compose  # Optional
```

**Windows:**
```powershell
# Install Python 3.11+ from python.org
# Install Git from git-scm.com
# Install Docker Desktop (optional)

# Verify installations
python --version
git --version
curl --version
```

### Access Requirements

#### Repository Access
- **Git Repository**: Access to Toombos repository
- **Credentials**: SSH key or HTTPS authentication configured
- **Permissions**: Read access minimum, write access for contributors

#### Network Access
- **Ports**: 8000, 8001, 8002 available for services
- **Monitoring**: 3000, 9090, 9093, 3100 available for monitoring stack
- **Firewall**: Inbound/outbound rules configured appropriately

---

## Environment Setup

### Environment Variables

#### Core Configuration File (`.env`)
```ini
# === HALCYTONE CONTENT GENERATOR CONFIGURATION ===
# Sprint 5 - Production Ready Configuration

# === SERVICE IDENTIFICATION ===
SERVICE_NAME=toombos-backend
SERVICE_VERSION=1.0.0
ENVIRONMENT=production-simulation

# === DRY RUN SETTINGS ===
DRY_RUN_MODE=true
USE_MOCK_SERVICES=true
BATCH_DRY_RUN=true

# === SERVICE ENDPOINTS ===
# Main application
API_HOST=0.0.0.0
API_PORT=8000

# Mock services
MOCK_CRM_BASE_URL=http://localhost:8001
MOCK_PLATFORM_BASE_URL=http://localhost:8002

# === SECURITY CONFIGURATION ===
# IMPORTANT: Replace these with secure values in production
API_KEY_ENCRYPTION_KEY=production-encryption-key-replace-with-secure-value-2025
JWT_SECRET_KEY=production-jwt-secret-replace-with-secure-value-2025

# === PERFORMANCE SETTINGS ===
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
RATE_LIMIT_PER_MINUTE=1000
WORKER_PROCESSES=4

# === DATABASE CONFIGURATION ===
# For dry run mode, these can be minimal
DATABASE_URL=sqlite:///./data/halcytone.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# === LOGGING CONFIGURATION ===
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/halcytone.log
LOG_ROTATION=daily

# === MONITORING CONFIGURATION ===
MONITORING_ENABLED=true
METRICS_PORT=8080
HEALTH_CHECK_INTERVAL=30

# === CONTENT CONFIGURATION ===
CONTENT_CACHE_TTL=300
CONTENT_MAX_LENGTH=100000
CONTENT_BATCH_SIZE=10

# === EXTERNAL SERVICES (Disabled in Dry Run) ===
# These are included for completeness but ignored in dry run mode
GOOGLE_DOCS_API_KEY=disabled-in-dry-run
NOTION_API_TOKEN=disabled-in-dry-run
SLACK_WEBHOOK_URL=disabled-in-dry-run

# === FEATURE FLAGS ===
ENABLE_SOCIAL_PUBLISHING=true
ENABLE_EMAIL_PUBLISHING=true
ENABLE_WEB_PUBLISHING=true
ENABLE_BATCH_PROCESSING=true
ENABLE_WEBHOOKS=false

# === DEVELOPMENT SETTINGS (Remove in production) ===
DEBUG=false
RELOAD=false
ACCESS_LOG=true
```

#### Environment-Specific Overrides

**Local Development (`.env.local`):**
```ini
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
WORKER_PROCESSES=1
```

**Staging (`.env.staging`):**
```ini
ENVIRONMENT=staging
LOG_LEVEL=INFO
WORKER_PROCESSES=2
MONITORING_ENABLED=true
```

**Production Simulation (`.env.production`):**
```ini
ENVIRONMENT=production-simulation
LOG_LEVEL=WARNING
WORKER_PROCESSES=4
MONITORING_ENABLED=true
RATE_LIMIT_PER_MINUTE=500
```

### Security Configuration

#### API Key Generation
```bash
# Generate secure API keys
python3 -c "
import secrets
print('API_KEY_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))
print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))
"
```

#### File Permissions
```bash
# Set secure permissions
chmod 600 .env*
chmod 700 logs/
chmod 755 scripts/*.sh
```

#### SSL/TLS Setup (Production)
```bash
# Generate self-signed certificates for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
chmod 600 key.pem
chmod 644 cert.pem
```

---

## Local Development Deployment

### Quick Start Development Setup

#### 1. Repository Setup
```bash
# Clone repository
git clone https://github.com/company/toombos-backend.git
cd toombos-backend

# Switch to development branch
git checkout develop

# Create local environment
cp .env.example .env.local
```

#### 2. Python Environment Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

#### 3. Environment Configuration
```bash
# Edit local configuration
nano .env.local

# Key settings for local development:
# DRY_RUN_MODE=true
# USE_MOCK_SERVICES=true
# DEBUG=true
# LOG_LEVEL=DEBUG
```

#### 4. Database Setup
```bash
# Create data directory
mkdir -p data logs

# Initialize database (if needed)
python -c "
from src.halcytone_content_generator.database import init_db
init_db()
print('Database initialized')
"
```

#### 5. Start Services
```bash
# Terminal 1: Start Mock CRM Service
python mocks/crm_service.py

# Terminal 2: Start Mock Platform Service
python mocks/platform_service.py

# Terminal 3: Start Main Application
source venv/bin/activate
export $(cat .env.local | xargs)
python -m uvicorn src.halcytone_content_generator.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 4: Start Monitoring (Optional)
./scripts/start-monitoring.sh
```

#### 6. Verify Installation
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Test content generation
curl -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}'
```

### Development Tools Setup

#### IDE Configuration

**VS Code (`.vscode/settings.json`):**
```json
{
  "python.pythonPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests/"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true
  }
}
```

**PyCharm Configuration:**
1. Open project in PyCharm
2. Configure Python interpreter: `venv/bin/python`
3. Set working directory to project root
4. Configure run configurations for each service

#### Testing Setup
```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run contract tests
python -m pytest tests/contracts/ -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

---

## Staging Deployment

### Staging Environment Setup

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-pip git curl nginx
sudo apt install -y supervisor  # Process management

# Create application user
sudo useradd -m -s /bin/bash halcytone
sudo usermod -aG sudo halcytone
```

#### 2. Application Deployment
```bash
# Switch to application user
sudo su - halcytone

# Clone repository
git clone https://github.com/company/toombos-backend.git
cd toombos-backend

# Checkout staging branch
git checkout staging

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configuration Setup
```bash
# Copy staging configuration
cp .env.example .env.staging

# Edit configuration for staging
nano .env.staging

# Key staging settings:
# ENVIRONMENT=staging
# DRY_RUN_MODE=true
# USE_MOCK_SERVICES=true
# LOG_LEVEL=INFO
# WORKER_PROCESSES=2
```

#### 4. Service Configuration

**Supervisor Configuration (`/etc/supervisor/conf.d/halcytone.conf`):**
```ini
[group:halcytone]
programs=halcytone-main,halcytone-crm-mock,halcytone-platform-mock

[program:halcytone-main]
command=/home/halcytone/toombos-backend/venv/bin/python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000 --workers 2
directory=/home/halcytone/toombos-backend
user=halcytone
autostart=true
autorestart=true
stdout_logfile=/home/halcytone/toombos-backend/logs/main.log
stderr_logfile=/home/halcytone/toombos-backend/logs/main-error.log
environment=PATH="/home/halcytone/toombos-backend/venv/bin"

[program:halcytone-crm-mock]
command=/home/halcytone/toombos-backend/venv/bin/python mocks/crm_service.py
directory=/home/halcytone/toombos-backend
user=halcytone
autostart=true
autorestart=true
stdout_logfile=/home/halcytone/toombos-backend/logs/crm-mock.log
stderr_logfile=/home/halcytone/toombos-backend/logs/crm-mock-error.log

[program:halcytone-platform-mock]
command=/home/halcytone/toombos-backend/venv/bin/python mocks/platform_service.py
directory=/home/halcytone/toombos-backend
user=halcytone
autostart=true
autorestart=true
stdout_logfile=/home/halcytone/toombos-backend/logs/platform-mock.log
stderr_logfile=/home/halcytone/toombos-backend/logs/platform-mock-error.log
```

**Nginx Configuration (`/etc/nginx/sites-available/halcytone`):**
```nginx
server {
    listen 80;
    server_name staging.halcytone.local;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Mock services
    location /mock/crm/ {
        rewrite ^/mock/crm/(.*) /$1 break;
        proxy_pass http://localhost:8001;
    }

    location /mock/platform/ {
        rewrite ^/mock/platform/(.*) /$1 break;
        proxy_pass http://localhost:8002;
    }
}
```

#### 5. Start Services
```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start services
sudo supervisorctl start halcytone:*

# Enable and start nginx
sudo ln -s /etc/nginx/sites-available/halcytone /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 6. Verify Staging Deployment
```bash
# Check service status
sudo supervisorctl status halcytone:*

# Test endpoints
curl http://staging.halcytone.local/health
curl http://staging.halcytone.local/mock/crm/health
curl http://staging.halcytone.local/mock/platform/health

# Test content generation
curl -X POST http://staging.halcytone.local/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}'
```

---

## Production Simulation Deployment

### Production-Like Environment Setup

#### 1. Infrastructure Preparation
```bash
# Prepare production-like server
sudo apt update && sudo apt upgrade -y

# Install production dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-pip git curl nginx
sudo apt install -y supervisor redis-server postgresql-client
sudo apt install -y logrotate fail2ban ufw  # Security tools

# Configure firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable
```

#### 2. Security Hardening
```bash
# Create dedicated user with limited privileges
sudo useradd -m -s /bin/bash -G sudo halcytone-prod
sudo passwd halcytone-prod

# SSH key-based authentication setup
sudo mkdir /home/halcytone-prod/.ssh
sudo cp ~/.ssh/authorized_keys /home/halcytone-prod/.ssh/
sudo chown -R halcytone-prod:halcytone-prod /home/halcytone-prod/.ssh
sudo chmod 700 /home/halcytone-prod/.ssh
sudo chmod 600 /home/halcytone-prod/.ssh/authorized_keys

# Disable password authentication (optional)
# Edit /etc/ssh/sshd_config: PasswordAuthentication no
```

#### 3. Application Deployment
```bash
# Switch to production user
sudo su - halcytone-prod

# Deploy application
git clone https://github.com/company/toombos-backend.git
cd toombos-backend
git checkout main  # Production branch

# Setup environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Production configuration
cp .env.example .env.production
```

#### 4. Production Configuration

**Security Configuration (`.env.production`):**
```ini
# Generate secure keys
API_KEY_ENCRYPTION_KEY=prod-secure-key-32-chars-minimum-length-2025
JWT_SECRET_KEY=prod-jwt-secret-32-chars-minimum-length-2025

# Production settings
ENVIRONMENT=production-simulation
LOG_LEVEL=WARNING
DEBUG=false
RELOAD=false

# Performance optimization
WORKER_PROCESSES=4
MAX_CONCURRENT_REQUESTS=200
REQUEST_TIMEOUT=60

# Security headers
SECURE_HEADERS=true
CORS_ALLOWED_ORIGINS=["https://halcytone.com"]
```

**Logging Configuration:**
```bash
# Create log rotation configuration
sudo tee /etc/logrotate.d/halcytone << EOF
/home/halcytone-prod/toombos-backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    create 644 halcytone-prod halcytone-prod
}
EOF
```

#### 5. SSL/TLS Configuration
```bash
# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d prod.halcytone.com

# Test auto-renewal
sudo certbot renew --dry-run
```

**Production Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name prod.halcytone.com;

    ssl_certificate /etc/letsencrypt/live/prod.halcytone.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/prod.halcytone.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Monitoring endpoints (restricted access)
    location /metrics {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://localhost:8000/metrics;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name prod.halcytone.com;
    return 301 https://$server_name$request_uri;
}
```

#### 6. Monitoring Deployment
```bash
# Deploy monitoring stack
./scripts/start-monitoring.sh

# Configure monitoring for production
cp monitoring/grafana/provisioning/datasources/datasources.yml.prod monitoring/grafana/provisioning/datasources/datasources.yml

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d
```

#### 7. Production Validation
```bash
# Comprehensive health check
./scripts/production-health-check.sh

# Load testing
./scripts/load-test.sh 50 1000

# Security scan
./scripts/security-audit.sh

# Performance benchmarks
./scripts/benchmark-test.sh
```

---

## Docker Deployment

### Containerized Deployment

#### 1. Docker Build

**Main Application Dockerfile:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY mocks/ mocks/
COPY scripts/ scripts/

# Create non-root user
RUN useradd -m -u 1000 halcytone
RUN chown -R halcytone:halcytone /app
USER halcytone

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "uvicorn", "src.halcytone_content_generator.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose Configuration:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main Application
  halcytone-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DRY_RUN_MODE=true
      - USE_MOCK_SERVICES=true
      - LOG_LEVEL=INFO
    depends_on:
      - mock-crm
      - mock-platform
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - halcytone

  # Mock CRM Service
  mock-crm:
    build:
      context: .
      dockerfile: mocks/Dockerfile.crm
    ports:
      - "8001:8001"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - halcytone

  # Mock Platform Service
  mock-platform:
    build:
      context: .
      dockerfile: mocks/Dockerfile.platform
    ports:
      - "8002:8002"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - halcytone

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - halcytone-app
    restart: unless-stopped
    networks:
      - halcytone

volumes:
  logs:
  data:

networks:
  halcytone:
    driver: bridge
```

#### 2. Build and Deploy
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs -f halcytone-app

# Health checks
curl http://localhost/health
```

#### 3. Production Docker Deployment

**Production Docker Compose (`docker-compose.prod.yml`):**
```yaml
version: '3.8'

services:
  halcytone-app:
    build: .
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - ENVIRONMENT=production
      - DRY_RUN_MODE=true
      - USE_MOCK_SERVICES=true
      - LOG_LEVEL=WARNING
      - WORKER_PROCESSES=2
    secrets:
      - api_encryption_key
      - jwt_secret_key
    networks:
      - halcytone
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

secrets:
  api_encryption_key:
    file: ./secrets/api_encryption_key.txt
  jwt_secret_key:
    file: ./secrets/jwt_secret_key.txt

networks:
  halcytone:
    driver: overlay
    attachable: true
```

---

## Rollback Procedures

### Automated Rollback

#### 1. Version Management
```bash
# Tag current deployment
git tag -a v1.0.1 -m "Production deployment v1.0.1"
git push origin v1.0.1

# Create deployment record
echo "$(date): Deployed v1.0.1 to production" >> deployments.log
```

#### 2. Rollback Script

**Rollback Script (`scripts/rollback.sh`):**
```bash
#!/bin/bash

set -e

ROLLBACK_VERSION=${1:-}
ENVIRONMENT=${2:-staging}

if [ -z "$ROLLBACK_VERSION" ]; then
    echo "Usage: $0 <version> [environment]"
    echo "Available versions:"
    git tag -l | tail -10
    exit 1
fi

echo "Rolling back to version $ROLLBACK_VERSION in $ENVIRONMENT environment"

# Backup current version
BACKUP_DIR="backups/rollback-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

# Stop services
if [ "$ENVIRONMENT" = "production" ]; then
    sudo supervisorctl stop halcytone:*
else
    docker-compose down
fi

# Backup current deployment
cp -r src/ $BACKUP_DIR/
cp .env* $BACKUP_DIR/
cp -r logs/ $BACKUP_DIR/

# Checkout rollback version
git fetch --tags
git checkout $ROLLBACK_VERSION

# Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart services
if [ "$ENVIRONMENT" = "production" ]; then
    sudo supervisorctl start halcytone:*
else
    docker-compose up -d
fi

# Health check
sleep 30
curl -f http://localhost:8000/health || {
    echo "Rollback failed - service not healthy"
    exit 1
}

echo "Rollback to $ROLLBACK_VERSION completed successfully"
echo "$(date): Rolled back to $ROLLBACK_VERSION" >> deployments.log
```

#### 3. Database Rollback (if applicable)
```bash
# Database migration rollback
python -c "
from src.halcytone_content_generator.database import rollback_migration
rollback_migration('$ROLLBACK_VERSION')
"

# Or manual database restore
cp backups/db-backup-pre-deployment.sql data/
```

### Manual Rollback Procedures

#### 1. Service Restoration
```bash
# Stop current services
sudo supervisorctl stop halcytone:*

# Restore previous version
cp -r backups/last-known-good/* ./

# Restart services
sudo supervisorctl start halcytone:*

# Verify health
./scripts/health-check-all.sh
```

#### 2. Configuration Rollback
```bash
# Restore configuration
cp backups/config/.env.production .env.production

# Reload configuration
sudo supervisorctl restart halcytone:*

# Verify configuration
python -c "
from src.halcytone_content_generator.config import get_settings
s = get_settings()
print('Configuration loaded successfully')
print(f'Environment: {s.ENVIRONMENT}')
print(f'Dry run mode: {s.DRY_RUN_MODE}')
"
```

---

## Health Checks

### Comprehensive Health Check Script

**Health Check Script (`scripts/health-check-all.sh`):**
```bash
#!/bin/bash

set -e

echo "=== Toombos Health Check ==="
echo "Timestamp: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Checking $name... "

    if response=$(curl -s -w "%{http_code}" -o /tmp/health_response "$url" 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}OK${NC}"
            return 0
        else
            echo -e "${RED}FAIL${NC} (HTTP $response)"
            return 1
        fi
    else
        echo -e "${RED}UNREACHABLE${NC}"
        return 1
    fi
}

# Main application health check
check_service "Main Application" "http://localhost:8000/health"

# Mock services health check
check_service "Mock CRM Service" "http://localhost:8001/health"
check_service "Mock Platform Service" "http://localhost:8002/health"

# Monitoring services (optional)
if curl -s http://localhost:3000/api/health >/dev/null 2>&1; then
    check_service "Grafana" "http://localhost:3000/api/health"
fi

if curl -s http://localhost:9090/-/healthy >/dev/null 2>&1; then
    check_service "Prometheus" "http://localhost:9090/-/healthy"
fi

echo
echo "=== Functional Tests ==="

# Test content generation
echo -n "Testing content generation... "
if curl -s -X POST http://localhost:8000/api/v2/generate-content \
  -H "Content-Type: application/json" \
  -d '{"preview_only": true}' | jq -e '.status == "preview"' >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

# Test mock services
echo -n "Testing mock CRM... "
if curl -s -X POST http://localhost:8001/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject": "health check", "html_content": "test"}' | jq -e '.status == "sent"' >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

echo -n "Testing mock Platform... "
if curl -s -X POST http://localhost:8002/api/v1/content/publish \
  -H "Content-Type: application/json" \
  -d '{"title": "health check", "content": "test"}' | jq -e '.status == "published"' >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

echo
echo "=== Resource Usage ==="

# Memory usage
MEMORY_USAGE=$(ps aux --sort=-%mem | grep -E "(python|uvicorn)" | head -3 | awk '{print $4}' | paste -sd+ | bc)
echo "Memory usage: ${MEMORY_USAGE}%"

# Disk usage
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
echo "Disk usage: $DISK_USAGE"

# Load average
LOAD_AVG=$(uptime | awk '{print $10 $11 $12}')
echo "Load average: $LOAD_AVG"

echo
echo -e "${GREEN}All health checks passed!${NC}"
echo "Health check completed at $(date)"
```

### Continuous Health Monitoring

#### 1. Cron-based Health Checks
```bash
# Add to crontab
echo "*/5 * * * * /home/halcytone/toombos-backend/scripts/health-check-all.sh >> /var/log/halcytone-health.log 2>&1" | crontab -
```

#### 2. Systemd Health Check Service
```ini
# /etc/systemd/system/halcytone-health.service
[Unit]
Description=Halcytone Health Check
After=network.target

[Service]
Type=oneshot
User=halcytone
ExecStart=/home/halcytone/toombos-backend/scripts/health-check-all.sh
StandardOutput=journal
StandardError=journal

# /etc/systemd/system/halcytone-health.timer
[Unit]
Description=Run Halcytone Health Check every 5 minutes
Requires=halcytone-health.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Post-Deployment Validation

### Validation Checklist

#### 1. Service Validation
- [ ] All services respond to health checks
- [ ] Main application accepts API requests
- [ ] Mock services return expected responses
- [ ] Monitoring dashboards display metrics

#### 2. Functional Validation
- [ ] Content generation workflow complete
- [ ] Email publishing via mock CRM works
- [ ] Web publishing via mock Platform works
- [ ] Social media posting works
- [ ] Dry run mode properly enabled

#### 3. Performance Validation
- [ ] Response times within acceptable limits (<2s)
- [ ] Concurrent request handling works (100+ concurrent)
- [ ] Memory usage stable (<1GB per service)
- [ ] CPU usage reasonable (<50% under load)

#### 4. Security Validation
- [ ] SSL/TLS certificates valid and secure
- [ ] API authentication working
- [ ] No sensitive data in logs
- [ ] Firewall rules properly configured

#### 5. Monitoring Validation
- [ ] Grafana dashboards accessible and populated
- [ ] Prometheus collecting metrics from all services
- [ ] Alert rules configured and tested
- [ ] Log aggregation working

### Validation Scripts

**Post-Deployment Validation Script (`scripts/validate-deployment.sh`):**
```bash
#!/bin/bash

set -e

echo "=== Post-Deployment Validation ==="
echo "Timestamp: $(date)"
echo

# Run comprehensive health check
./scripts/health-check-all.sh

echo "=== Load Testing ==="

# Basic load test
echo "Running basic load test..."
ab -n 100 -c 10 -p test-payload.json -T application/json \
  http://localhost:8000/api/v2/generate-content > load-test-results.txt

# Check load test results
FAILED_REQUESTS=$(grep "Failed requests" load-test-results.txt | awk '{print $3}')
if [ "$FAILED_REQUESTS" -gt 0 ]; then
    echo "Load test failed: $FAILED_REQUESTS failed requests"
    exit 1
fi

echo "Load test passed: All requests successful"

echo "=== Security Check ==="

# Basic security checks
echo "Checking for exposed sensitive information..."

# Check for hardcoded secrets
if grep -r "password\|secret\|key" --exclude-dir=venv --exclude-dir=.git --exclude="*.log" . | grep -v "example\|sample\|template" | grep -v "\.md:"; then
    echo "Warning: Potential hardcoded secrets found"
fi

# Check SSL configuration (if HTTPS enabled)
if command -v nmap >/dev/null 2>&1; then
    echo "Checking SSL configuration..."
    nmap --script ssl-cert,ssl-enum-ciphers -p 443 localhost || echo "HTTPS not configured"
fi

echo "=== Monitoring Validation ==="

# Check if monitoring is collecting metrics
echo "Validating monitoring stack..."

if curl -s http://localhost:9090/api/v1/targets | jq -e '.data.activeTargets | length > 0' >/dev/null 2>&1; then
    echo "Prometheus targets active"
else
    echo "Warning: Prometheus not collecting metrics"
fi

if curl -s http://localhost:3000/api/health | jq -e '.database == "ok"' >/dev/null 2>&1; then
    echo "Grafana healthy"
else
    echo "Warning: Grafana not accessible"
fi

echo
echo "=== Deployment Validation Complete ==="
echo "$(date): Deployment validated successfully" >> deployments.log
```

---

## Troubleshooting

### Common Deployment Issues

#### 1. Permission Errors
```bash
# Fix file permissions
chmod +x scripts/*.sh
chmod 600 .env*
chown -R halcytone:halcytone /home/halcytone/toombos-backend

# Fix log directory permissions
mkdir -p logs
chmod 755 logs
```

#### 2. Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep -E ":800[0-2]"

# Kill conflicting processes
sudo lsof -ti:8000 | xargs sudo kill -9
sudo lsof -ti:8001 | xargs sudo kill -9
sudo lsof -ti:8002 | xargs sudo kill -9
```

#### 3. Dependency Issues
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Reinstall Python dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Check Python version
python3 --version  # Should be 3.11+
```

#### 4. Configuration Issues
```bash
# Validate configuration
python -c "
from src.halcytone_content_generator.config import get_settings
try:
    s = get_settings()
    print('Configuration valid')
    print(f'DRY_RUN_MODE: {s.DRY_RUN_MODE}')
    print(f'USE_MOCK_SERVICES: {s.USE_MOCK_SERVICES}')
except Exception as e:
    print(f'Configuration error: {e}')
"

# Check environment variables
env | grep -E "(DRY_RUN|MOCK|HALCYTONE)" | sort
```

### Recovery Procedures

#### 1. Complete Service Recovery
```bash
# Stop all services
sudo supervisorctl stop halcytone:*
docker-compose down

# Clear temporary files
rm -rf /tmp/halcytone-*
rm -rf __pycache__

# Restart from clean state
source venv/bin/activate
python mocks/crm_service.py &
python mocks/platform_service.py &
python -m uvicorn src.halcytone_content_generator.main:app --host 0.0.0.0 --port 8000 &

# Wait for services to start
sleep 10

# Verify recovery
./scripts/health-check-all.sh
```

#### 2. Database Recovery
```bash
# Reset database (if applicable)
rm -f data/halcytone.db

# Reinitialize
python -c "
from src.halcytone_content_generator.database import init_db
init_db()
print('Database reinitialized')
"
```

### Support Contacts

#### Escalation Levels
| Level | Contact | Response Time | Scope |
|-------|---------|---------------|-------|
| L1 | Development Team | 15 minutes | Application issues |
| L2 | Operations Team | 30 minutes | Infrastructure issues |
| L3 | System Administrator | 1 hour | System-level issues |
| L4 | On-call Manager | 2 hours | Critical escalation |

#### Contact Information
- **Email**: deployment-support@halcytone.local
- **Slack**: #halcytone-deployment
- **Emergency**: +1-555-HALCYTONE

---

*Last Updated: Sprint 5 - Documentation & Production Readiness*
*Contact: Development Team*