#!/bin/bash
# Start Mock Services for Halcytone Content Generator
# This script ensures mock services are running for development and testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.mocks.yml"
TIMEOUT=30

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    log "Docker is running ✓"
}

# Check if docker-compose is available
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            error "Neither 'docker-compose' nor 'docker compose' is available."
            error "Please install Docker Compose and try again."
            exit 1
        fi
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    log "Docker Compose available: $COMPOSE_CMD ✓"
}

# Check if mock services are already running
check_running_services() {
    local crm_running=false
    local platform_running=false

    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        crm_running=true
    fi

    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        platform_running=true
    fi

    if $crm_running && $platform_running; then
        success "Mock services are already running!"
        log "CRM Service: http://localhost:8001/docs"
        log "Platform Service: http://localhost:8002/docs"
        return 0
    elif $crm_running || $platform_running; then
        warning "Some mock services are running but not all. Restarting all services..."
        return 1
    else
        log "No mock services detected. Starting fresh..."
        return 1
    fi
}

# Stop existing services if any
stop_services() {
    log "Stopping any existing mock services..."
    cd "$PROJECT_ROOT"

    # Stop containers gracefully
    $COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans > /dev/null 2>&1 || true

    # Clean up any stray processes on the ports
    if lsof -ti:8001 > /dev/null 2>&1; then
        warning "Killing process on port 8001..."
        kill -9 $(lsof -ti:8001) > /dev/null 2>&1 || true
    fi

    if lsof -ti:8002 > /dev/null 2>&1; then
        warning "Killing process on port 8002..."
        kill -9 $(lsof -ti:8002) > /dev/null 2>&1 || true
    fi

    sleep 2
    log "Cleanup completed"
}

# Build and start services
start_services() {
    log "Building and starting mock services..."
    cd "$PROJECT_ROOT"

    # Build the images
    log "Building Docker images..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache

    # Start services in detached mode
    log "Starting services..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d

    log "Services started in background"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to become healthy..."

    local count=0
    local max_attempts=$((TIMEOUT / 2))

    while [ $count -lt $max_attempts ]; do
        local crm_healthy=false
        local platform_healthy=false

        # Check CRM service health
        if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
            crm_healthy=true
        fi

        # Check Platform service health
        if curl -s -f http://localhost:8002/health > /dev/null 2>&1; then
            platform_healthy=true
        fi

        if $crm_healthy && $platform_healthy; then
            success "All services are healthy!"
            return 0
        fi

        printf "."
        sleep 2
        count=$((count + 1))
    done

    echo ""
    error "Services failed to become healthy within $TIMEOUT seconds"

    # Show logs for debugging
    log "Service logs:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=20

    return 1
}

# Show service information
show_service_info() {
    log "Mock Services Information:"
    echo ""
    echo "🔧 CRM Service:"
    echo "   - Health: http://localhost:8001/health"
    echo "   - API Docs: http://localhost:8001/docs"
    echo "   - OpenAPI: http://localhost:8001/openapi.json"
    echo ""
    echo "🌐 Platform Service:"
    echo "   - Health: http://localhost:8002/health"
    echo "   - API Docs: http://localhost:8002/docs"
    echo "   - OpenAPI: http://localhost:8002/openapi.json"
    echo ""
    echo "📊 Service Status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo ""
    echo "📝 View logs: docker-compose -f docker-compose.mocks.yml logs -f"
    echo "🛑 Stop services: docker-compose -f docker-compose.mocks.yml down"
}

# Test services with sample requests
test_services() {
    log "Testing services with sample requests..."

    # Test CRM service
    log "Testing CRM service..."
    if curl -s -X GET "http://localhost:8001/contacts" > /dev/null; then
        success "CRM service responding ✓"
    else
        error "CRM service test failed ✗"
        return 1
    fi

    # Test Platform service
    log "Testing Platform service..."
    if curl -s -X GET "http://localhost:8002/content" > /dev/null; then
        success "Platform service responding ✓"
    else
        error "Platform service test failed ✗"
        return 1
    fi

    success "All services tested successfully!"
}

# Main function
main() {
    log "Starting Halcytone Mock Services..."

    # Pre-flight checks
    check_docker
    check_compose

    # Check if services are already running
    if check_running_services; then
        if [[ "${1:-}" == "--force" ]] || [[ "${1:-}" == "-f" ]]; then
            log "Force restart requested..."
        else
            exit 0
        fi
    fi

    # Stop existing services
    stop_services

    # Start services
    start_services

    # Wait for health
    if ! wait_for_services; then
        error "Failed to start mock services"
        exit 1
    fi

    # Test services
    if ! test_services; then
        error "Service tests failed"
        exit 1
    fi

    # Show service information
    show_service_info

    success "Mock services are ready! 🚀"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Start Halcytone Mock Services for development and testing"
        echo ""
        echo "OPTIONS:"
        echo "  --force, -f    Force restart even if services are running"
        echo "  --help, -h     Show this help message"
        echo ""
        echo "The script will:"
        echo "  1. Check Docker availability"
        echo "  2. Stop any existing services"
        echo "  3. Build and start mock services"
        echo "  4. Wait for services to be healthy"
        echo "  5. Test service endpoints"
        echo "  6. Display service information"
        ;;
    *)
        main "$@"
        ;;
esac