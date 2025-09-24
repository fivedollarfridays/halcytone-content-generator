#!/bin/bash

# Halcytone Content Generator - Monitoring Stack Startup Script
# Sprint 4: Monitoring & Observability

set -e

echo "🚀 Starting Halcytone Monitoring Stack..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker and docker-compose are available
check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating log directories..."
    mkdir -p logs
    touch logs/.gitkeep
    print_success "Log directories created"
}

# Start the monitoring stack
start_monitoring() {
    print_status "Starting monitoring services..."

    # Pull latest images
    print_status "Pulling latest Docker images..."
    docker-compose -f docker-compose.monitoring.yml pull

    # Start services
    print_status "Starting services in detached mode..."
    docker-compose -f docker-compose.monitoring.yml up -d

    print_success "Monitoring services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to become healthy..."

    # Wait for Prometheus
    print_status "Checking Prometheus..."
    for i in {1..30}; do
        if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
            print_success "Prometheus is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Prometheus health check timeout"
        fi
        sleep 2
    done

    # Wait for Grafana
    print_status "Checking Grafana..."
    for i in {1..30}; do
        if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
            print_success "Grafana is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Grafana health check timeout"
        fi
        sleep 2
    done

    # Wait for Loki
    print_status "Checking Loki..."
    for i in {1..30}; do
        if curl -sf http://localhost:3100/ready > /dev/null 2>&1; then
            print_success "Loki is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Loki health check timeout"
        fi
        sleep 2
    done

    # Wait for AlertManager
    print_status "Checking AlertManager..."
    for i in {1..30}; do
        if curl -sf http://localhost:9093/-/healthy > /dev/null 2>&1; then
            print_success "AlertManager is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "AlertManager health check timeout"
        fi
        sleep 2
    done
}

# Display service status
show_status() {
    print_status "Service status:"
    docker-compose -f docker-compose.monitoring.yml ps

    echo ""
    print_status "Service URLs:"
    echo "  📊 Grafana:      http://localhost:3000 (admin/halcytone_monitor_2025)"
    echo "  📈 Prometheus:   http://localhost:9090"
    echo "  🔔 AlertManager: http://localhost:9093"
    echo "  📝 Loki:        http://localhost:3100"
    echo ""

    print_status "Available Dashboards:"
    echo "  🎯 Service Overview: http://localhost:3000/d/halcytone-overview"
    echo "  🤖 Mock Services:    http://localhost:3000/d/mock-services"
    echo ""
}

# Main execution
main() {
    echo "=================================================="
    echo "  Halcytone Content Generator"
    echo "  Sprint 4: Monitoring & Observability"
    echo "=================================================="
    echo ""

    check_prerequisites
    create_directories
    start_monitoring
    wait_for_services
    show_status

    print_success "🎉 Monitoring stack is ready!"
    echo ""
    print_status "💡 Quick commands:"
    echo "  View logs:    docker-compose -f docker-compose.monitoring.yml logs -f"
    echo "  Stop stack:   docker-compose -f docker-compose.monitoring.yml down"
    echo "  Restart:      docker-compose -f docker-compose.monitoring.yml restart [service]"
    echo ""
    print_status "📖 For troubleshooting, see: docs/monitoring-runbook.md"
}

# Handle script arguments
case "$1" in
    "stop")
        print_status "Stopping monitoring stack..."
        docker-compose -f docker-compose.monitoring.yml down
        print_success "Monitoring stack stopped"
        ;;
    "restart")
        print_status "Restarting monitoring stack..."
        docker-compose -f docker-compose.monitoring.yml restart
        print_success "Monitoring stack restarted"
        ;;
    "status")
        docker-compose -f docker-compose.monitoring.yml ps
        ;;
    "logs")
        docker-compose -f docker-compose.monitoring.yml logs -f
        ;;
    *)
        main
        ;;
esac