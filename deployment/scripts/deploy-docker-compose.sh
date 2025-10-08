#!/bin/bash
# Production deployment script for Docker Compose
# Usage: ./deploy-docker-compose.sh [environment]

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.${ENVIRONMENT}"

echo "==================================="
echo "Toombos"
echo "Docker Compose Deployment"
echo "Environment: ${ENVIRONMENT}"
echo "==================================="

# Check if .env file exists
if [ ! -f "${ENV_FILE}" ]; then
    echo "Error: Environment file ${ENV_FILE} not found"
    echo "Please create it from .env.production.template"
    exit 1
fi

# Load environment variables
export $(cat ${ENV_FILE} | grep -v '^#' | xargs)

# Check required environment variables
required_vars=(
    "CRM_API_KEY"
    "PLATFORM_API_KEY"
    "OPENAI_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable ${var} is not set"
        exit 1
    fi
done

# Pre-deployment checks
echo ""
echo "Pre-deployment checks..."
echo "- Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

echo "- Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "- Creating required directories..."
mkdir -p logs data cache deployment/nginx/ssl

# Build images
echo ""
echo "Building Docker images..."
${DOCKER_COMPOSE} -f ${COMPOSE_FILE} build --no-cache

# Run health checks on current deployment (if exists)
echo ""
echo "Checking current deployment status..."
if ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} ps | grep -q "Up"; then
    echo "Current deployment is running. Performing rolling update..."

    # Rolling update strategy
    echo "Starting new instances..."
    ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} up -d --no-deps --scale content-generator-1=0 --scale content-generator-2=0 content-generator-3
    sleep 10

    # Wait for health check
    echo "Waiting for health check..."
    for i in {1..30}; do
        if ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} exec -T content-generator-3 curl -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "Health check passed!"
            break
        fi
        echo "Waiting for service to be healthy... ($i/30)"
        sleep 2
    done

    # Update other instances
    echo "Updating remaining instances..."
    ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} up -d --no-deps content-generator-1 content-generator-2
    sleep 10
else
    echo "No existing deployment found. Performing fresh deployment..."
    ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} up -d
fi

# Wait for all services to be healthy
echo ""
echo "Waiting for all services to be healthy..."
sleep 15

# Verify deployment
echo ""
echo "Verifying deployment..."
services=("content-generator-1" "content-generator-2" "content-generator-3" "nginx" "redis")

all_healthy=true
for service in "${services[@]}"; do
    echo -n "Checking ${service}... "
    if ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} ps ${service} | grep -q "Up (healthy)"; then
        echo "✓ Healthy"
    else
        echo "✗ Unhealthy"
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    echo ""
    echo "Warning: Some services are not healthy"
    echo "Check logs with: ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} logs"
    exit 1
fi

# Test endpoints
echo ""
echo "Testing endpoints..."
echo -n "Testing health endpoint... "
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ Failed"
    exit 1
fi

echo -n "Testing API endpoint... "
if curl -f http://localhost/api/v1/health > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ Failed"
    exit 1
fi

# Show service status
echo ""
echo "Deployment Status:"
${DOCKER_COMPOSE} -f ${COMPOSE_FILE} ps

# Show logs from last minute
echo ""
echo "Recent logs:"
${DOCKER_COMPOSE} -f ${COMPOSE_FILE} logs --tail=50 content-generator-1

echo ""
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
echo ""
echo "Services:"
echo "  - API: http://localhost:80"
echo "  - Metrics: http://localhost:9090/metrics"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "Useful commands:"
echo "  - View logs: ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} logs -f"
echo "  - Restart service: ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} restart content-generator-1"
echo "  - Scale service: ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} up -d --scale content-generator-1=2"
echo "  - Stop all: ${DOCKER_COMPOSE} -f ${COMPOSE_FILE} down"
echo ""
