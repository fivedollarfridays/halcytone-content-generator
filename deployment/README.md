# Production Deployment Guide

Comprehensive deployment configuration for Halcytone Content Generator with support for Docker Compose and Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Docker**: 20.10+
- **Docker Compose**: 2.0+ or Docker with Compose V2
- **Kubernetes**: 1.24+ (for K8s deployment)
- **kubectl**: Latest version
- **Helm**: 3.0+ (optional, for chart deployment)

### Required Credentials

Before deployment, ensure you have:

1. CRM API credentials
2. Platform API credentials
3. Google Cloud service account JSON
4. Notion API key and database ID
5. OpenAI API key
6. SSL certificates (for production)

## Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd halcytone-content-generator

# Copy environment template
cp .env.production.template .env.production

# Edit configuration
nano .env.production
```

### 2. Choose Deployment Method

**Option A: Docker Compose (Recommended for single-server deployment)**
```bash
chmod +x deployment/scripts/deploy-docker-compose.sh
./deployment/scripts/deploy-docker-compose.sh production
```

**Option B: Kubernetes (Recommended for cloud deployment)**
```bash
chmod +x deployment/scripts/deploy-kubernetes.sh
./deployment/scripts/deploy-kubernetes.sh production halcytone
```

## Docker Compose Deployment

### Architecture

The Docker Compose deployment includes:

- **3x Application Instances**: Load-balanced FastAPI applications
- **Nginx**: Reverse proxy and load balancer
- **Redis**: Caching layer
- **PostgreSQL**: Persistent storage (optional)
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Jaeger**: Distributed tracing
- **Certbot**: SSL certificate management

### Deployment Steps

1. **Configure Environment**

```bash
# Create production environment file
cat > .env.production << EOF
# Service URLs
CRM_BASE_URL=https://crm.halcytone.com
PLATFORM_BASE_URL=https://platform.halcytone.com

# API Keys
CRM_API_KEY=your-crm-api-key
PLATFORM_API_KEY=your-platform-api-key
OPENAI_API_KEY=your-openai-api-key
NOTION_API_KEY=your-notion-api-key
NOTION_DATABASE_ID=your-notion-database-id

# Google Credentials (base64 encoded)
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# Database (optional)
POSTGRES_PASSWORD=secure-password

# Monitoring
GRAFANA_ADMIN_PASSWORD=secure-grafana-password
EOF
```

2. **Configure SSL Certificates**

```bash
# For Let's Encrypt (recommended)
# Initial setup
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d api.halcytone.com \
  --email admin@halcytone.com \
  --agree-tos

# Or copy existing certificates
cp fullchain.pem deployment/nginx/ssl/
cp privkey.pem deployment/nginx/ssl/
```

3. **Deploy**

```bash
# Deploy all services
./deployment/scripts/deploy-docker-compose.sh production

# Or manually
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

4. **Verify Deployment**

```bash
# Test health endpoint
curl https://api.halcytone.com/health

# Test API endpoint
curl https://api.halcytone.com/api/v1/health

# Check logs
docker-compose -f docker-compose.prod.yml logs -f content-generator-1
```

### Scaling with Docker Compose

```bash
# Scale application instances
docker-compose -f docker-compose.prod.yml up -d --scale content-generator-1=5

# Update nginx configuration to include new instances
# Edit deployment/nginx/nginx.conf and add new upstream servers

# Reload nginx without downtime
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## Kubernetes Deployment

### Architecture

The Kubernetes deployment includes:

- **Deployment**: 3-10 replicas with rolling updates
- **HorizontalPodAutoscaler**: CPU, memory, and custom metric-based scaling
- **Service**: ClusterIP service with session affinity
- **Ingress**: nginx-ingress with SSL termination and rate limiting
- **ConfigMap**: Application configuration
- **Secrets**: Sensitive credentials
- **PodDisruptionBudget**: High availability guarantees

### Deployment Steps

1. **Create Namespace**

```bash
kubectl create namespace halcytone
kubectl label namespace halcytone environment=production
```

2. **Create Secrets**

```bash
# Create from file
kubectl create secret generic content-generator-secrets \
  --from-env-file=.env.production \
  --namespace=halcytone

# Or create from literals
kubectl create secret generic content-generator-secrets \
  --from-literal=crm-api-key=YOUR_KEY \
  --from-literal=platform-api-key=YOUR_KEY \
  --from-file=google-credentials=./google-creds.json \
  --namespace=halcytone

# Verify secrets
kubectl get secrets -n halcytone
```

3. **Apply Kubernetes Manifests**

```bash
# Apply in order
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/service.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/autoscaling.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml

# Or use the deployment script
./deployment/scripts/deploy-kubernetes.sh production halcytone
```

4. **Verify Deployment**

```bash
# Check all resources
kubectl get all -n halcytone -l app=content-generator

# Check pod status
kubectl get pods -n halcytone -l app=content-generator

# Check HPA
kubectl get hpa -n halcytone

# Check ingress
kubectl get ingress -n halcytone
```

5. **Test Endpoints**

```bash
# Port-forward for testing
kubectl port-forward -n halcytone svc/content-generator-service 8000:8000

# Test in another terminal
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

### Scaling with Kubernetes

#### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment content-generator --replicas=5 -n halcytone

# Verify scaling
kubectl get pods -n halcytone -l app=content-generator
```

#### Auto-scaling

Auto-scaling is automatically configured via HPA:

- **Min Replicas**: 3
- **Max Replicas**: 10
- **Triggers**:
  - CPU > 70%
  - Memory > 80%
  - Custom metrics (if configured)

```bash
# Check HPA status
kubectl get hpa content-generator-hpa -n halcytone --watch

# Describe HPA for details
kubectl describe hpa content-generator-hpa -n halcytone
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/content-generator \
  content-generator=halcytone/content-generator:v1.1.0 \
  -n halcytone

# Watch rollout status
kubectl rollout status deployment/content-generator -n halcytone

# Rollback if needed
kubectl rollout undo deployment/content-generator -n halcytone
```

## Configuration

### Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `production` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WORKERS` | Number of worker processes | `4` |
| `PORT` | Application port | `8000` |
| `CRM_BASE_URL` | CRM service URL | Required |
| `PLATFORM_BASE_URL` | Platform API URL | Required |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent requests | `100` |

### Load Balancer Configuration

#### Nginx (Docker Compose)

- **Algorithm**: Least connections
- **Health Checks**: Every 30s
- **Timeouts**: 120s
- **Rate Limiting**: 100 req/s per IP
- **Caching**: 5-minute TTL for GET requests

#### Kubernetes Ingress

- **Class**: nginx-ingress
- **Algorithm**: EWMA
- **SSL**: Automatic via cert-manager
- **Rate Limiting**: 100 req/s per IP
- **Headers**: Security headers enabled

### Resource Limits

#### Docker Compose

Each application instance:
- **CPU Limit**: 2 cores
- **Memory Limit**: 2GB
- **CPU Reservation**: 1 core
- **Memory Reservation**: 1GB

#### Kubernetes

Each pod:
- **CPU Request**: 500m
- **CPU Limit**: 2000m
- **Memory Request**: 1Gi
- **Memory Limit**: 2Gi

## Monitoring

### Endpoints

- **Health**: `/health` - Liveness check
- **Readiness**: `/ready` - Readiness check
- **Metrics**: `/metrics` - Prometheus metrics

### Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active connections
sum(http_connections_active)
```

### Grafana Dashboards

Pre-configured dashboards available in `monitoring/grafana/dashboards/`:

1. **Application Overview**: Key metrics and health status
2. **Performance**: Response times, throughput, errors
3. **Infrastructure**: Resource usage, scaling events
4. **Business Metrics**: Content generation stats

## Troubleshooting

### Common Issues

#### 1. Service Unhealthy

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs content-generator-1

# Kubernetes
kubectl logs -n halcytone -l app=content-generator --tail=100
```

#### 2. High Memory Usage

```bash
# Docker Compose
docker stats

# Kubernetes
kubectl top pods -n halcytone -l app=content-generator
```

#### 3. Connection Timeouts

Check nginx/ingress logs:

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml logs nginx

# Kubernetes
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

#### 4. SSL Certificate Issues

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml exec certbot certbot certificates

# Kubernetes
kubectl describe certificate halcytone-tls-secret -n halcytone
```

### Debug Commands

```bash
# Docker Compose - Enter container
docker-compose -f docker-compose.prod.yml exec content-generator-1 bash

# Kubernetes - Enter pod
kubectl exec -it -n halcytone <pod-name> -- bash

# Check DNS resolution
nslookup redis-service
curl http://redis-service:6379

# Test internal endpoints
curl http://localhost:8000/health
```

## Security Considerations

1. **Secrets Management**: Use external secrets manager (AWS Secrets Manager, HashiCorp Vault)
2. **Network Policies**: Implement Kubernetes NetworkPolicies
3. **RBAC**: Configure appropriate role-based access
4. **SSL/TLS**: Always use HTTPS in production
5. **Rate Limiting**: Configure appropriate limits
6. **Security Headers**: Enabled by default in nginx/ingress
7. **Container Scanning**: Scan images for vulnerabilities
8. **Regular Updates**: Keep base images and dependencies updated

## Performance Tuning

### Application Level

- **Worker Processes**: Match CPU cores
- **Worker Connections**: 1000-2000 per worker
- **Keepalive**: Enable HTTP keepalive
- **Caching**: Enable Redis caching

### Infrastructure Level

- **Connection Pooling**: Configure in nginx/ingress
- **Resource Limits**: Set appropriate CPU/memory limits
- **Auto-scaling**: Tune HPA thresholds
- **Database**: Configure connection pooling

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U contentuser content_db > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U contentuser content_db < backup.sql
```

### Redis Backups

Redis is configured with AOF persistence. Backups are in the volume.

## Support

For issues and questions:
- Documentation: `docs/`
- Issues: GitHub Issues
- Runbooks: `docs/monitoring-runbook.md`
