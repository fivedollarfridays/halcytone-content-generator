# Secrets Management & API Key Rotation Guide

## Table of Contents

1. [Overview](#overview)
2. [Secrets Management Systems](#secrets-management-systems)
3. [API Key Rotation Procedures](#api-key-rotation-procedures)
4. [Emergency Procedures](#emergency-procedures)
5. [Audit & Compliance](#audit--compliance)

---

## Overview

This guide provides comprehensive procedures for managing secrets, rotating API keys, and maintaining security compliance for the Halcytone Content Generator production environment.

### Critical Secrets Inventory

| Secret Type | Service | Rotation Frequency | Priority |
|------------|---------|-------------------|----------|
| Google Service Account | Google Docs API | 90 days | Critical |
| Notion API Key | Notion API | 90 days | Critical |
| OpenAI API Key | OpenAI GPT-4 | 60 days | Critical |
| CRM API Key | CRM Service | 90 days | Critical |
| Platform API Key | Platform Service | 90 days | Critical |
| Database Password | PostgreSQL | 90 days | Critical |
| Redis Password | Redis Cache | 90 days | High |
| JWT Secret | Authentication | 180 days | Critical |
| Encryption Keys | Data Encryption | 365 days | Critical |
| CDN API Key | Cloudflare/CDN | 90 days | Medium |
| Webhook Secrets | Cache Invalidation | 90 days | Medium |
| Slack Webhook | Alerting | 180 days | Low |

---

## Secrets Management Systems

### Option 1: AWS Secrets Manager (Recommended for AWS)

#### Initial Setup

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create secret
aws secretsmanager create-secret \
  --name halcytone/production/openai-api-key \
  --description "OpenAI API key for production" \
  --secret-string "sk-prod-xxxxx"
```

#### Store All Production Secrets

```bash
#!/bin/bash
# Script: scripts/setup-aws-secrets.sh

# CRM API Key
aws secretsmanager create-secret \
  --name halcytone/production/crm-api-key \
  --secret-string "$CRM_API_KEY"

# Platform API Key
aws secretsmanager create-secret \
  --name halcytone/production/platform-api-key \
  --secret-string "$PLATFORM_API_KEY"

# Google Credentials (JSON)
aws secretsmanager create-secret \
  --name halcytone/production/google-credentials \
  --secret-string file://google-service-account.json

# Notion API Key
aws secretsmanager create-secret \
  --name halcytone/production/notion-api-key \
  --secret-string "$NOTION_API_KEY"

# OpenAI API Key
aws secretsmanager create-secret \
  --name halcytone/production/openai-api-key \
  --secret-string "$OPENAI_API_KEY"

# Database Password
aws secretsmanager create-secret \
  --name halcytone/production/database-password \
  --secret-string "$DATABASE_PASSWORD"

# JWT Secret
aws secretsmanager create-secret \
  --name halcytone/production/jwt-secret-key \
  --secret-string "$(openssl rand -base64 32)"

# API Key Encryption Key
aws secretsmanager create-secret \
  --name halcytone/production/api-key-encryption-key \
  --secret-string "$(openssl rand -base64 32)"
```

#### Retrieve Secrets at Runtime

```python
# src/halcytone_content_generator/core/secrets.py
import boto3
import json
from functools import lru_cache

class SecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region_name)

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret {secret_name}: {e}")

    def get_json_secret(self, secret_name: str) -> dict:
        """Retrieve JSON secret"""
        secret_string = self.get_secret(secret_name)
        return json.loads(secret_string)

# Usage in application
secrets = SecretsManager()
openai_key = secrets.get_secret('halcytone/production/openai-api-key')
google_creds = secrets.get_json_secret('halcytone/production/google-credentials')
```

#### Enable Automatic Rotation

```bash
# Enable automatic rotation for database password
aws secretsmanager rotate-secret \
  --secret-id halcytone/production/database-password \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789:function:SecretsManagerRotation \
  --rotation-rules AutomaticallyAfterDays=90
```

---

### Option 2: Azure Key Vault

#### Initial Setup

```bash
# Install Azure CLI
pip install azure-cli

# Login to Azure
az login

# Create Key Vault
az keyvault create \
  --name halcytone-prod-vault \
  --resource-group halcytone-production \
  --location eastus

# Grant access to application
az keyvault set-policy \
  --name halcytone-prod-vault \
  --spn YOUR-APP-ID \
  --secret-permissions get list
```

#### Store Secrets

```bash
# Store API keys
az keyvault secret set \
  --vault-name halcytone-prod-vault \
  --name crm-api-key \
  --value "$CRM_API_KEY"

az keyvault secret set \
  --vault-name halcytone-prod-vault \
  --name openai-api-key \
  --value "$OPENAI_API_KEY"

az keyvault secret set \
  --vault-name halcytone-prod-vault \
  --name google-credentials \
  --file google-service-account.json
```

#### Retrieve Secrets

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class AzureSecretsManager:
    def __init__(self, vault_url: str):
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret from Azure Key Vault"""
        secret = self.client.get_secret(secret_name)
        return secret.value

# Usage
vault_url = "https://halcytone-prod-vault.vault.azure.net/"
secrets = AzureSecretsManager(vault_url)
openai_key = secrets.get_secret('openai-api-key')
```

---

### Option 3: HashiCorp Vault

#### Initial Setup

```bash
# Start Vault server (production mode)
vault server -config=vault-config.hcl

# Initialize Vault
vault operator init

# Unseal Vault (requires threshold of unseal keys)
vault operator unseal <KEY1>
vault operator unseal <KEY2>
vault operator unseal <KEY3>

# Login
vault login <ROOT_TOKEN>

# Enable KV secrets engine
vault secrets enable -path=halcytone kv-v2
```

#### Store Secrets

```bash
# Store API keys
vault kv put halcytone/production/crm api_key="$CRM_API_KEY"
vault kv put halcytone/production/platform api_key="$PLATFORM_API_KEY"
vault kv put halcytone/production/openai api_key="$OPENAI_API_KEY"
vault kv put halcytone/production/notion api_key="$NOTION_API_KEY"

# Store Google credentials
vault kv put halcytone/production/google credentials=@google-service-account.json

# Store database credentials
vault kv put halcytone/production/database \
  username="dbuser" \
  password="$DB_PASSWORD" \
  url="postgresql://dbuser:pass@db:5432/halcytone_prod"
```

#### Retrieve Secrets

```python
import hvac

class VaultSecretsManager:
    def __init__(self, vault_url: str, token: str):
        self.client = hvac.Client(url=vault_url, token=token)

    def get_secret(self, path: str, key: str) -> str:
        """Retrieve secret from Vault"""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data'][key]

# Usage
vault = VaultSecretsManager('http://vault:8200', token='hvs.xxx')
openai_key = vault.get_secret('halcytone/production/openai', 'api_key')
```

---

## API Key Rotation Procedures

### Pre-Rotation Checklist

- [ ] Schedule maintenance window (if required)
- [ ] Notify stakeholders of rotation schedule
- [ ] Backup current configuration
- [ ] Verify new keys are generated and tested in staging
- [ ] Prepare rollback plan
- [ ] Document rotation date and new key metadata

---

### 1. Google Service Account Rotation

**Frequency**: 90 days
**Impact**: High - Affects content retrieval from Google Docs
**Downtime**: None (with proper procedure)

#### Procedure

```bash
# 1. Create new service account
gcloud iam service-accounts create halcytone-prod-v2 \
  --display-name="Halcytone Content Generator Production v2"

# 2. Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:halcytone-prod-v2@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/drive.readonly"

# 3. Create and download new key
gcloud iam service-accounts keys create google-creds-v2.json \
  --iam-account=halcytone-prod-v2@PROJECT_ID.iam.gserviceaccount.com

# 4. Share Google Doc with new service account
# Via Google Drive UI or API:
gcloud drive files share DOC_ID \
  --email=halcytone-prod-v2@PROJECT_ID.iam.gserviceaccount.com \
  --role=reader

# 5. Update secret in secrets manager
aws secretsmanager update-secret \
  --secret-id halcytone/production/google-credentials \
  --secret-string file://google-creds-v2.json

# 6. Rolling restart of application pods
kubectl rollout restart deployment/content-generator -n halcytone

# 7. Verify connectivity
kubectl exec -it deployment/content-generator -n halcytone -- \
  python scripts/validate_external_services.py --service google_docs

# 8. After verification (24-48 hours), disable old service account
gcloud iam service-accounts disable halcytone-prod-v1@PROJECT_ID.iam.gserviceaccount.com

# 9. After 30 days, delete old service account
gcloud iam service-accounts delete halcytone-prod-v1@PROJECT_ID.iam.gserviceaccount.com
```

---

### 2. Notion API Key Rotation

**Frequency**: 90 days
**Impact**: High - Affects content retrieval from Notion
**Downtime**: None

#### Procedure

```bash
# 1. Generate new integration in Notion workspace
# Navigate to: https://www.notion.so/my-integrations
# Create new internal integration
# Copy new API key

# 2. Test new key in staging
export NOTION_API_KEY="secret_NEW_KEY"
python scripts/validate_external_services.py --service notion

# 3. Update secret in secrets manager
aws secretsmanager update-secret \
  --secret-id halcytone/production/notion-api-key \
  --secret-string "secret_NEW_KEY"

# 4. Rolling restart
kubectl rollout restart deployment/content-generator -n halcytone

# 5. Verify in production
kubectl logs -f deployment/content-generator -n halcytone | grep "Notion"

# 6. Revoke old integration after verification (24 hours)
# In Notion: Settings → Integrations → Revoke old integration
```

---

### 3. OpenAI API Key Rotation

**Frequency**: 60 days
**Impact**: Critical - Affects all content generation
**Downtime**: None

#### Procedure

```bash
# 1. Create new API key in OpenAI dashboard
# https://platform.openai.com/api-keys
# Click "Create new secret key"
# Name: "halcytone-prod-YYYY-MM-DD"
# Copy key immediately (shown only once)

# 2. Test new key in staging
export OPENAI_API_KEY="sk-proj-NEW_KEY"
python scripts/validate_external_services.py --service openai

# 3. Update usage limits on new key
# Set monthly budget cap
# Configure rate limits

# 4. Update secret
aws secretsmanager update-secret \
  --secret-id halcytone/production/openai-api-key \
  --secret-string "sk-proj-NEW_KEY"

# 5. Rolling restart with health checks
kubectl rollout restart deployment/content-generator -n halcytone
kubectl rollout status deployment/content-generator -n halcytone

# 6. Monitor for errors
kubectl logs -f deployment/content-generator -n halcytone | grep -i "openai\|error"

# 7. Verify content generation works
curl -X POST https://api.halcytone.com/api/v1/content/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# 8. After 24 hours verification, revoke old key in OpenAI dashboard
```

---

### 4. CRM & Platform API Keys Rotation

**Frequency**: 90 days
**Impact**: High - Affects email distribution and platform integration
**Downtime**: None

#### Procedure

```bash
# 1. Contact CRM/Platform provider to generate new API keys
# Or use provider's dashboard/API to rotate keys

# 2. Test new keys in staging environment
export CRM_API_KEY="NEW_CRM_KEY"
export PLATFORM_API_KEY="NEW_PLATFORM_KEY"
python scripts/validate_external_services.py --service crm --service platform

# 3. Update secrets
aws secretsmanager update-secret \
  --secret-id halcytone/production/crm-api-key \
  --secret-string "NEW_CRM_KEY"

aws secretsmanager update-secret \
  --secret-id halcytone/production/platform-api-key \
  --secret-string "NEW_PLATFORM_KEY"

# 4. Rolling restart
kubectl rollout restart deployment/content-generator -n halcytone

# 5. Verify connectivity
python scripts/validate_external_services.py --all

# 6. Monitor error rates
# Check Grafana dashboard for error spikes
# Review logs for authentication failures

# 7. Revoke old keys after 48-hour verification period
```

---

### 5. Database Password Rotation

**Frequency**: 90 days
**Impact**: Critical - Service unavailable if misconfigured
**Downtime**: None (with proper procedure)

#### Procedure

```bash
# 1. Create new database user with same permissions (dual-user method)
psql -h production-db.example.com -U admin -d halcytone_prod << EOF
CREATE USER halcytone_app_v2 WITH PASSWORD 'NEW_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE halcytone_prod TO halcytone_app_v2;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO halcytone_app_v2;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO halcytone_app_v2;
EOF

# 2. Update connection string with new user
NEW_DB_URL="postgresql://halcytone_app_v2:NEW_SECURE_PASSWORD@prod-db:5432/halcytone_prod"

# 3. Test new connection
psql "$NEW_DB_URL" -c "SELECT 1;"

# 4. Update secret
aws secretsmanager update-secret \
  --secret-id halcytone/production/database-url \
  --secret-string "$NEW_DB_URL"

# 5. Rolling restart (one pod at a time to ensure no downtime)
kubectl rollout restart deployment/content-generator -n halcytone
kubectl rollout status deployment/content-generator -n halcytone --timeout=5m

# 6. Monitor database connections
psql -h prod-db -U admin -d halcytone_prod -c \
  "SELECT usename, COUNT(*) FROM pg_stat_activity GROUP BY usename;"

# 7. After 48 hours, verify all pods use new user
# Then revoke old user
psql -h prod-db -U admin -d halcytone_prod << EOF
REVOKE ALL PRIVILEGES ON DATABASE halcytone_prod FROM halcytone_app_v1;
DROP USER halcytone_app_v1;
EOF
```

---

### 6. JWT Secret & Encryption Keys Rotation

**Frequency**: 180 days (JWT), 365 days (Encryption)
**Impact**: High - May invalidate existing sessions
**Downtime**: None

#### Procedure

```bash
# 1. Generate new secrets
NEW_JWT_SECRET=$(openssl rand -base64 32)
NEW_ENCRYPTION_KEY=$(openssl rand -base64 32)

# 2. For JWT: Implement dual-key verification (old + new)
# Update application to accept both old and new JWT secrets temporarily

# 3. Update secrets
aws secretsmanager update-secret \
  --secret-id halcytone/production/jwt-secret-key \
  --secret-string "$NEW_JWT_SECRET"

aws secretsmanager update-secret \
  --secret-id halcytone/production/api-key-encryption-key \
  --secret-string "$NEW_ENCRYPTION_KEY"

# 4. Rolling restart
kubectl rollout restart deployment/content-generator -n halcytone

# 5. Monitor for authentication errors
# Users may need to re-authenticate

# 6. After grace period (7 days), remove old JWT secret support
```

---

## Emergency Procedures

### Secret Compromise Response

If a secret is compromised, follow these steps immediately:

#### 1. Immediate Containment (Within 15 minutes)

```bash
# 1. Rotate the compromised secret immediately
aws secretsmanager update-secret \
  --secret-id halcytone/production/COMPROMISED_SECRET \
  --secret-string "NEW_EMERGENCY_VALUE"

# 2. Force immediate pod restart (no rolling update)
kubectl delete pods -n halcytone -l app=content-generator

# 3. Block old credentials at provider level
# - Revoke in Google Cloud Console
# - Revoke in OpenAI dashboard
# - Revoke in service provider dashboards
```

#### 2. Investigation (Within 1 hour)

```bash
# Review audit logs for unauthorized access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=COMPROMISED_SECRET \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 100

# Check application logs for suspicious activity
kubectl logs -n halcytone -l app=content-generator --since=7d | grep "COMPROMISED"

# Review access patterns
python scripts/analyze_secret_access.py --secret COMPROMISED_SECRET --days 7
```

#### 3. Notification (Within 2 hours)

- Notify security team
- Notify affected service providers
- Document incident in security log
- Update incident response tracker

#### 4. Post-Incident Actions

- Complete full security audit
- Review access controls
- Update rotation procedures if needed
- Conduct post-mortem meeting

---

## Audit & Compliance

### Secrets Audit Checklist

Run monthly:

```bash
# 1. List all secrets and last rotation dates
aws secretsmanager list-secrets \
  --filters Key=name,Values=halcytone/production \
  --query 'SecretList[*].[Name,LastRotatedDate]' \
  --output table

# 2. Check for secrets older than rotation policy
python scripts/audit_secret_age.py --threshold 90

# 3. Verify all secrets have proper access controls
aws secretsmanager describe-secret --secret-id halcytone/production/* \
  | jq '.RotationRules'

# 4. Review access logs
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S)
```

### Compliance Requirements

- **SOC 2**: All secrets rotated every 90 days
- **ISO 27001**: Access to secrets logged and reviewed monthly
- **HIPAA**: Encryption keys rotated annually
- **PCI DSS**: API keys rotated every 90 days, logged access

### Secret Rotation Tracking

| Secret | Last Rotated | Next Rotation | Owner | Status |
|--------|-------------|---------------|-------|--------|
| Google Service Account | 2025-09-15 | 2025-12-15 | DevOps | ✅ Current |
| Notion API Key | 2025-09-01 | 2025-12-01 | DevOps | ✅ Current |
| OpenAI API Key | 2025-09-10 | 2025-11-10 | DevOps | ✅ Current |
| CRM API Key | 2025-08-20 | 2025-11-20 | DevOps | ⚠️ Due Soon |
| Platform API Key | 2025-08-20 | 2025-11-20 | DevOps | ⚠️ Due Soon |
| Database Password | 2025-07-01 | 2025-10-01 | DBA | 🔴 Overdue |
| JWT Secret | 2025-06-01 | 2026-06-01 | Security | ✅ Current |

---

## Automation Scripts

All rotation procedures can be automated using the provided scripts in `scripts/`:

- `scripts/rotate_all_secrets.py` - Automated rotation with notifications
- `scripts/validate_external_services.py` - Post-rotation validation
- `scripts/audit_secret_age.py` - Compliance reporting
- `scripts/emergency_secret_revoke.py` - Emergency compromise response

See `scripts/README.md` for detailed usage instructions.
