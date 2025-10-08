#!/bin/bash
# Kubernetes deployment script for Toombos
# Usage: ./deploy-kubernetes.sh [environment] [namespace]

set -e

ENVIRONMENT=${1:-production}
NAMESPACE=${2:-halcytone}
DEPLOYMENT_DIR="deployment/kubernetes"

echo "==================================="
echo "Toombos"
echo "Kubernetes Deployment"
echo "Environment: ${ENVIRONMENT}"
echo "Namespace: ${NAMESPACE}"
echo "==================================="

# Check kubectl installation
echo ""
echo "Pre-deployment checks..."
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check cluster connection
echo "- Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

# Create namespace if it doesn't exist
echo "- Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Label namespace
kubectl label namespace ${NAMESPACE} environment=${ENVIRONMENT} --overwrite

# Apply ConfigMaps
echo ""
echo "Applying ConfigMaps..."
kubectl apply -f ${DEPLOYMENT_DIR}/configmap.yaml -n ${NAMESPACE}

# Apply Secrets
echo ""
echo "Applying Secrets..."
echo "WARNING: Make sure secrets are properly configured!"
read -p "Have you configured secrets properly? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Please configure secrets first"
    echo "You can use: kubectl create secret generic content-generator-secrets --from-env-file=.env.${ENVIRONMENT} -n ${NAMESPACE}"
    exit 1
fi

# Check if secrets exist
if ! kubectl get secret content-generator-secrets -n ${NAMESPACE} &> /dev/null; then
    echo "Error: Secret 'content-generator-secrets' not found in namespace ${NAMESPACE}"
    echo "Create it with: kubectl create secret generic content-generator-secrets --from-env-file=.env.${ENVIRONMENT} -n ${NAMESPACE}"
    exit 1
fi

# Apply Services
echo ""
echo "Applying Services..."
kubectl apply -f ${DEPLOYMENT_DIR}/service.yaml -n ${NAMESPACE}

# Apply Deployment
echo ""
echo "Applying Deployment..."
kubectl apply -f ${DEPLOYMENT_DIR}/deployment.yaml -n ${NAMESPACE}

# Wait for deployment to be ready
echo ""
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/content-generator -n ${NAMESPACE}

# Apply Autoscaling
echo ""
echo "Applying Autoscaling policies..."
kubectl apply -f ${DEPLOYMENT_DIR}/autoscaling.yaml -n ${NAMESPACE}

# Apply Ingress
echo ""
echo "Applying Ingress..."
kubectl apply -f ${DEPLOYMENT_DIR}/ingress.yaml -n ${NAMESPACE}

# Check deployment status
echo ""
echo "Checking deployment status..."
kubectl get all -n ${NAMESPACE} -l app=content-generator

# Check pod health
echo ""
echo "Checking pod health..."
pods=$(kubectl get pods -n ${NAMESPACE} -l app=content-generator -o jsonpath='{.items[*].metadata.name}')

all_healthy=true
for pod in $pods; do
    echo -n "Checking ${pod}... "
    if kubectl get pod ${pod} -n ${NAMESPACE} | grep -q "Running"; then
        echo "✓ Running"
    else
        echo "✗ Not Running"
        all_healthy=false
    fi
done

if [ "$all_healthy" = false ]; then
    echo ""
    echo "Warning: Some pods are not running"
    echo "Check logs with: kubectl logs -n ${NAMESPACE} -l app=content-generator"
    exit 1
fi

# Test endpoints through service
echo ""
echo "Testing endpoints..."
echo "Port-forwarding to test..."
kubectl port-forward -n ${NAMESPACE} svc/content-generator-service 8000:8000 &
PORT_FORWARD_PID=$!
sleep 5

echo -n "Testing health endpoint... "
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ Failed"
fi

# Stop port-forward
kill $PORT_FORWARD_PID 2>/dev/null || true

# Show deployment info
echo ""
echo "Deployment Information:"
echo "-----------------------"
kubectl get deployment content-generator -n ${NAMESPACE}
echo ""
kubectl get hpa -n ${NAMESPACE}
echo ""
kubectl get ingress -n ${NAMESPACE}

# Get endpoint URL
echo ""
echo "Endpoints:"
INGRESS_HOST=$(kubectl get ingress content-generator-ingress -n ${NAMESPACE} -o jsonpath='{.spec.rules[0].host}')
if [ -n "$INGRESS_HOST" ]; then
    echo "  - API: https://${INGRESS_HOST}"
    echo "  - Health: https://${INGRESS_HOST}/health"
    echo "  - Docs: https://${INGRESS_HOST}/docs"
else
    echo "  - Ingress not configured yet"
fi

echo ""
echo "==================================="
echo "Deployment completed successfully!"
echo "==================================="
echo ""
echo "Useful commands:"
echo "  - View pods: kubectl get pods -n ${NAMESPACE} -l app=content-generator"
echo "  - View logs: kubectl logs -n ${NAMESPACE} -l app=content-generator -f"
echo "  - Describe deployment: kubectl describe deployment content-generator -n ${NAMESPACE}"
echo "  - Scale deployment: kubectl scale deployment content-generator --replicas=5 -n ${NAMESPACE}"
echo "  - Rollback: kubectl rollout undo deployment/content-generator -n ${NAMESPACE}"
echo "  - Status: kubectl rollout status deployment/content-generator -n ${NAMESPACE}"
echo ""
