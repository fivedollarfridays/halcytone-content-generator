# Production Configuration Guide

## Overview

This guide covers the comprehensive production configuration management system for the Toombos, including secure secrets management, environment-specific settings, and deployment validation.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Architecture](#configuration-architecture)
- [Secrets Management](#secrets-management)
- [Environment Templates](#environment-templates)
- [Validation and Security](#validation-and-security)
- [Deployment Procedures](#deployment-procedures)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Generate Production Template
```bash
# Generate production configuration template
python scripts/config_manager.py generate-template --output .env.production

# Review and customize the template
vi .env.production
```

### 2. Configure Secrets Management
```bash
# For Azure Key Vault
export AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
export AZURE_CLIENT_ID=your-client-id
export AZURE_TENANT_ID=your-tenant-id

# For AWS Secrets Manager
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
```

### 3. Validate Configuration
```bash
# Validate production configuration
python scripts/config_manager.py validate production

# Test production readiness
python scripts/config_manager.py test-production
```

### 4. Deploy with Validated Configuration
```bash
# Final validation before deployment
python scripts/config_manager.py validate production --config-file .env.production

# Deploy if validation passes
docker-compose -f docker-compose.production.yml up -d
```

## Configuration Architecture

### Hierarchical Configuration Loading

The system loads configuration in the following priority order:

1. **Secrets Manager** (Azure Key Vault, AWS Secrets Manager)
2. **Environment-specific files** (`.env.production`, `.env.staging`)
3. **Environment variables**
4. **Default values**

### Configuration Structure

```
src/halcytone_content_generator/config/
├── __init__.py                 # Package exports
├── enhanced_config.py          # Main configuration classes
├── secrets_manager.py          # Secrets management
└── validation.py              # Configuration validation

Environment Templates:
├── .env.example               # Development template
├── .env.production.template   # Production template
├── .env.staging.template      # Staging template
└── .env.production           # Your production config (not in git)
```

### Configuration Classes

#### ProductionSettings
Main configuration class with nested structures:
- `security`: Security-related settings
- `external_services`: External API configuration
- `database`: Database settings (if applicable)
- `cache`: Caching configuration
- `monitoring`: Observability settings
- `alerts`: Alerting configuration

#### Environment-Specific Validation
- **Development**: Relaxed validation, warnings for best practices
- **Staging**: Production-like validation with test data
- **Production**: Strict validation, security requirements enforced

## Secrets Management

### Supported Providers

#### 1. Azure Key Vault (Recommended for Azure)
```bash
# Setup
pip install azure-keyvault-secrets azure-identity

# Configuration
export AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/
export SECRETS_PROVIDER=azure_key_vault

# Store secrets in Azure Key Vault
az keyvault secret set --vault-name your-vault --name API-KEY-ENCRYPTION-KEY --value "your-secret"
```

#### 2. AWS Secrets Manager (Recommended for AWS)
```bash
# Setup
pip install boto3

# Configuration
export AWS_REGION=us-east-1
export SECRETS_PROVIDER=aws_secrets_manager

# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret --name halcytone/api-key-encryption-key --secret-string "your-secret"
```

#### 3. Environment Variables (Simple deployments)
```bash
export SECRETS_PROVIDER=environment
export API_KEY_ENCRYPTION_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
```

#### 4. Local File (Development only)
```json
# secrets.json (DO NOT COMMIT)
{
  "API_KEY_ENCRYPTION_KEY": "dev-encryption-key",
  "JWT_SECRET_KEY": "dev-jwt-secret",
  "CRM_API_KEY": "dev-crm-key"
}
```

### Secret References

Define secrets in configuration:
```python
from src.halcytone_content_generator.config import SecretReference, SecretsProvider

secrets = [
    SecretReference(
        key="API_KEY_ENCRYPTION_KEY",
        provider=SecretsProvider.AZURE_KEY_VAULT,
        vault_name="production-vault",
        required=True
    ),
    SecretReference(
        key="OPENAI_API_KEY",
        provider=SecretsProvider.AWS_SECRETS_MANAGER,
        region="us-east-1",
        required=False,
        default_value="not-configured"
    )
]
```

## Environment Templates

### Production Template (.env.production.template)
```bash
# Copy and customize
cp .env.production.template .env.production

# Key sections to configure:
# 1. Replace all ${VARIABLE} placeholders
# 2. Set strong encryption keys (32+ characters)
# 3. Configure production URLs (HTTPS only)
# 4. Enable production features
# 5. Configure monitoring and alerting
```

### Critical Production Settings
```bash
# Security (REQUIRED)
API_KEY_ENCRYPTION_KEY=<32+ character random string>
JWT_SECRET_KEY=<32+ character random string>
API_KEY=<16+ character API key>

# Environment (REQUIRED)
ENVIRONMENT=production
DEBUG=false
DRY_RUN_MODE=false
USE_MOCK_SERVICES=false

# Database Configuration (REQUIRED)
DATABASE_URL=postgresql://user:password@db.yourcompany.com:5432/halcytone_prod
DATABASE_POOL_SIZE=20
DATABASE_POOL_MAX_OVERFLOW=10
DATABASE_SSL_MODE=require
DATABASE_AUTO_MIGRATE=false

# External Services (REQUIRED)
CRM_BASE_URL=https://production-crm.yourcompany.com
CRM_API_KEY=<production CRM key>
PLATFORM_BASE_URL=https://production-platform.yourcompany.com
PLATFORM_API_KEY=<production platform key>

# Monitoring (RECOMMENDED)
ENABLE_METRICS=true
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_RECIPIENTS=["ops@yourcompany.com"]
```

### Staging Template (.env.staging.template)
Similar to production but with:
- Staging service endpoints
- Relaxed validation settings
- Enhanced debugging features
- Test data configurations

## Validation and Security

### Configuration Manager CLI

#### Validate Configuration
```bash
# Validate specific environment
python scripts/config_manager.py validate production

# Validate from specific file
python scripts/config_manager.py validate production --config-file .env.production

# Check secrets availability
python scripts/config_manager.py check-secrets --provider azure_key_vault
```

#### Production Readiness Test
```bash
# Comprehensive production readiness check
python scripts/config_manager.py test-production

# Output includes:
# - Configuration validation
# - Security checks
# - Service connectivity tests
# - Performance considerations
```

### Validation Levels

#### 🚨 CRITICAL Issues
- Must be fixed before production deployment
- Examples: Weak secrets, HTTP URLs in production, debug mode enabled

#### ⚠️ HIGH Priority Issues
- Should be fixed before production deployment
- Examples: Missing required configurations, insecure settings

#### ⚡ MEDIUM Priority Issues
- Should be addressed for optimal operation
- Examples: Suboptimal timeouts, missing monitoring

#### 💡 LOW Priority Issues
- Nice to have improvements
- Examples: Performance optimizations, additional features

### Security Validation

#### Secret Strength Checks
- Minimum length requirements (32 chars for encryption keys)
- Pattern detection for development placeholders
- Entropy analysis for randomness

#### URL Security Validation
- HTTPS enforcement in production
- Localhost detection in production
- Valid URL format verification

#### Environment Security
- Production flag consistency
- Debug mode detection
- Mock service usage in production

## Deployment Procedures

### Pre-Deployment Checklist

1. **Configuration Validation**
   ```bash
   python scripts/config_manager.py validate production
   ```

2. **Secrets Verification**
   ```bash
   python scripts/config_manager.py check-secrets
   ```

3. **Production Readiness**
   ```bash
   python scripts/config_manager.py test-production
   ```

4. **Service Connectivity**
   ```bash
   # Test external service endpoints
   curl -H "Authorization: Bearer $CRM_API_KEY" $CRM_BASE_URL/health
   curl -H "Authorization: Bearer $PLATFORM_API_KEY" $PLATFORM_BASE_URL/health
   ```

### Deployment Steps

#### 1. Environment Preparation
```bash
# Set environment
export ENVIRONMENT=production

# Load configuration
source .env.production

# Validate final configuration
python scripts/config_manager.py validate production
```

#### 2. Secrets Deployment
```bash
# For Azure Key Vault
az keyvault secret set --vault-name prod-vault --name api-key --value "$API_KEY"

# For AWS Secrets Manager
aws secretsmanager put-secret-value --secret-id prod/api-key --secret-string "$API_KEY"
```

#### 3. Application Deployment
```bash
# Using Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Using Kubernetes
kubectl apply -f k8s/production/

# Verify deployment
python scripts/config_manager.py test-production
```

#### 4. Post-Deployment Validation
```bash
# Health checks
curl https://your-production-url/health
curl https://your-production-url/ready

# Configuration verification
curl https://your-production-url/api/v1/config/status
```

### Rolling Back Configuration Changes

#### 1. Emergency Rollback
```bash
# Restore previous configuration
cp .env.production.backup .env.production

# Restart services
docker-compose -f docker-compose.production.yml restart

# Validate rollback
python scripts/config_manager.py validate production
```

#### 2. Planned Configuration Updates
```bash
# Create backup
cp .env.production .env.production.backup.$(date +%Y%m%d-%H%M%S)

# Update configuration
vi .env.production

# Validate changes
python scripts/config_manager.py validate production

# Apply changes
docker-compose -f docker-compose.production.yml up -d --force-recreate
```

## Troubleshooting

### Common Issues

#### Configuration Validation Failures

**Issue**: "Secret contains development placeholder"
```bash
# Check for development patterns in secrets
grep -i "dev\|test\|example" .env.production

# Generate strong secrets
openssl rand -base64 32  # For encryption keys
openssl rand -hex 16     # For API keys
```

**Issue**: "URL must use HTTPS in production"
```bash
# Update URLs to use HTTPS
sed -i 's/http:/https:/g' .env.production
```

#### Secrets Management Issues

**Issue**: "Failed to retrieve secret from Azure Key Vault"
```bash
# Check Azure authentication
az account show
az keyvault secret list --vault-name your-vault

# Test secret access
az keyvault secret show --vault-name your-vault --name api-key
```

**Issue**: "AWS Secrets Manager connection failed"
```bash
# Check AWS credentials
aws sts get-caller-identity
aws secretsmanager list-secrets

# Test secret access
aws secretsmanager get-secret-value --secret-id your-secret
```

#### Application Startup Issues

**Issue**: "Configuration validation failed during startup"
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check configuration loading
python -c "
from src.halcytone_content_generator.config import get_production_settings
import asyncio
settings = asyncio.run(get_production_settings())
print('Configuration loaded successfully')
"
```

### Debugging Configuration Loading

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
export DEBUG_CONFIG_LOADING=true

# Run configuration validation with verbose output
python scripts/config_manager.py validate production
```

#### Check Configuration Sources
```python
from src.halcytone_content_generator.config import ConfigurationManager

manager = ConfigurationManager('production')
config_data = manager._load_base_config()
print(f"Loaded {len(config_data)} configuration items")

# Check specific values
for key in ['ENVIRONMENT', 'CRM_BASE_URL', 'API_KEY']:
    print(f"{key}: {config_data.get(key, 'NOT SET')}")
```

#### Validate Individual Components
```bash
# Test secrets manager
python scripts/config_manager.py check-secrets

# Test external service connectivity
curl -I $CRM_BASE_URL/health
curl -I $PLATFORM_BASE_URL/health

# Test database connectivity (if applicable)
python -c "import asyncio; from src.db import test_connection; asyncio.run(test_connection())"
```

### Performance Considerations

#### Configuration Loading Performance
- Secrets are cached after first load
- Environment files are parsed once at startup
- Validation runs only during initialization

#### Monitoring Configuration Changes
- Enable configuration change auditing
- Set up alerts for configuration validation failures
- Monitor secrets rotation and expiration

### Security Best Practices

1. **Never commit production secrets to version control**
2. **Use different secrets for each environment**
3. **Rotate secrets regularly**
4. **Monitor secret access and usage**
5. **Use least-privilege access for secrets**
6. **Enable audit logging for configuration changes**
7. **Validate configuration before deployment**
8. **Use HTTPS for all production endpoints**
9. **Enable security headers and CORS restrictions**
10. **Monitor for configuration drift**

## Integration Examples

### Docker Compose Integration
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  content-generator:
    image: toombos-backend:latest
    environment:
      - ENVIRONMENT=production
      - SECRETS_PROVIDER=azure_key_vault
      - AZURE_KEY_VAULT_URL=${AZURE_KEY_VAULT_URL}
    env_file:
      - .env.production
    command: ["python", "-m", "uvicorn", "src.halcytone_content_generator.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Integration
```yaml
# k8s/production/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-generator
spec:
  template:
    spec:
      containers:
      - name: content-generator
        image: toombos-backend:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SECRETS_PROVIDER
          value: "azure_key_vault"
        envFrom:
        - secretRef:
            name: content-generator-secrets
        - configMapRef:
            name: content-generator-config
```

### CI/CD Pipeline Integration
```yaml
# .github/workflows/deploy.yml
- name: Validate Configuration
  run: |
    python scripts/config_manager.py validate production --config-file .env.production

- name: Test Production Readiness
  run: |
    python scripts/config_manager.py test-production

- name: Deploy if Configuration Valid
  run: |
    if python scripts/config_manager.py validate production; then
      docker-compose -f docker-compose.production.yml up -d
    else
      echo "Configuration validation failed - deployment aborted"
      exit 1
    fi
```

---

## Support and Documentation

For additional help:
- Review the [Deployment Procedures](deployment-procedures.md)
- Check the [Troubleshooting Guide](troubleshooting.md)
- See [API Configuration Reference](api-configuration.md)
- Contact the development team for configuration assistance

**Last Updated**: $(date)
**Version**: 1.0