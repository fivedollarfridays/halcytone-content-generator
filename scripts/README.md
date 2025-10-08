# Production Scripts

This directory contains scripts for production deployment, secrets management, and operational tasks.

## Table of Contents

- [Secrets Management](#secrets-management)
- [Service Validation](#service-validation)
- [Database Operations](#database-operations)
- [Deployment Automation](#deployment-automation)

---

## Secrets Management

### AWS Secrets Manager Setup

**Script**: `setup_aws_secrets.sh`

Sets up all production secrets in AWS Secrets Manager.

#### Prerequisites

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

#### Usage

```bash
# Interactive setup (will prompt for secrets)
chmod +x scripts/setup_aws_secrets.sh
./scripts/setup_aws_secrets.sh

# Specify region and profile
./scripts/setup_aws_secrets.sh --region us-west-2 --profile production

# Non-interactive (requires environment variables)
export CRM_API_KEY="your-key"
export PLATFORM_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_CREDENTIALS_FILE="./google-creds.json"
./scripts/setup_aws_secrets.sh
```

#### What it does

1. Creates or updates secrets in AWS Secrets Manager
2. Generates secure random values for JWT and encryption keys
3. Stores Google service account credentials
4. Configures database connection strings
5. Sets up alerting webhooks

#### Secrets Created

| Secret Name | Description |
|------------|-------------|
| `halcytone/production/crm-api-key` | CRM Service API Key |
| `halcytone/production/platform-api-key` | Platform Service API Key |
| `halcytone/production/google-credentials` | Google Cloud service account JSON |
| `halcytone/production/notion-api-key` | Notion API Key (optional) |
| `halcytone/production/openai-api-key` | OpenAI API Key |
| `halcytone/production/jwt-secret-key` | JWT signing secret |
| `halcytone/production/api-key-encryption-key` | API key encryption key |
| `halcytone/production/database-url` | PostgreSQL connection string |
| `halcytone/production/redis-url` | Redis connection string |
| `halcytone/production/cdn-api-key` | CDN API key |
| `halcytone/production/slack-webhook-url` | Slack webhook for alerts |

---

## Service Validation

### External Service Connectivity Validation

**Script**: `validate_external_services.py`

Validates connectivity and authentication with all external services.

#### Prerequisites

```bash
# Install required packages
pip install httpx psycopg2-binary redis google-auth google-api-python-client python-dotenv
```

#### Usage

```bash
# Validate all services
python scripts/validate_external_services.py --all

# Validate specific services
python scripts/validate_external_services.py --service google_docs
python scripts/validate_external_services.py --service openai --service crm

# Load from specific .env file
python scripts/validate_external_services.py --all --env-file .env.production

# JSON output (for automation)
python scripts/validate_external_services.py --all --json
```

#### Services Validated

| Service | Checks |
|---------|--------|
| **Google Docs** | Credentials valid, document accessible |
| **Notion** | API key valid, database accessible |
| **OpenAI** | API key valid, models available |
| **CRM** | Service reachable, authentication works |
| **Platform** | Service reachable, authentication works |
| **Database** | Connection successful, database accessible |
| **Redis** | Connection successful, ping works |

#### Example Output

```
============================================================
         External Service Connectivity Validation
============================================================

ℹ Environment: production
ℹ Timestamp: 2025-09-30T10:30:00

Testing Google Docs API...
✓ Successfully connected to document: Breathscape Living Document
  document_id: 1abc123...
  document_title: Breathscape Living Document
  response_time_ms: 456

Testing OpenAI API...
✓ Successfully connected. 15 GPT models available
  available_models: 58
  gpt_models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
  response_time_ms: 234

============================================================
                  Validation Summary
============================================================
Total Services Validated: 7
✓ Successful: 7
Failed: 0

✓ All services validated successfully!
```

#### Exit Codes

- `0`: All services validated successfully
- `1`: One or more services failed validation

#### Integration with CI/CD

```yaml
# .github/workflows/deploy.yml
- name: Validate External Services
  run: |
    python scripts/validate_external_services.py --all --json > validation.json
    if [ $? -ne 0 ]; then
      echo "Service validation failed!"
      exit 1
    fi
```

---

## Database Operations

### Database Backup

**Script**: `backup-database.sh`

Creates compressed PostgreSQL backups and uploads to S3.

#### Usage

```bash
# Manual backup
chmod +x scripts/backup-database.sh
./scripts/backup-database.sh

# Automated via cron
# Add to crontab: 0 2 * * * /path/to/scripts/backup-database.sh
```

#### Features

- Creates compressed `.sql.gz` backup
- Uploads to S3 with timestamp
- Keeps last 30 days locally
- Logs all operations

### Database Migration

Run database migrations:

```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Rollback
alembic downgrade -1
```

---

## Deployment Automation

### Docker Compose Deployment

**Script**: `deployment/scripts/deploy-docker-compose.sh`

Deploys application using Docker Compose with rolling updates.

#### Usage

```bash
# Production deployment
./deployment/scripts/deploy-docker-compose.sh production

# Staging deployment
./deployment/scripts/deploy-docker-compose.sh staging
```

#### Features

- Pre-deployment validation
- Rolling update with zero downtime
- Health check verification
- Automatic rollback on failure

### Kubernetes Deployment

**Script**: `deployment/scripts/deploy-kubernetes.sh`

Deploys application to Kubernetes cluster.

#### Usage

```bash
# Deploy to production namespace
./deployment/scripts/deploy-kubernetes.sh production halcytone

# Deploy to staging
./deployment/scripts/deploy-kubernetes.sh staging halcytone-staging
```

#### Features

- Cluster connectivity checks
- Secret validation
- Sequential manifest application
- Pod health verification
- Endpoint testing

---

## Additional Scripts

### Generate Random Secrets

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate encryption key
openssl rand -hex 32

# Generate API key
openssl rand -base64 24 | tr -d "=+/" | cut -c1-32
```

### Test Database Connection

```bash
# PostgreSQL
psql "$DATABASE_URL" -c "SELECT version();"

# With SSL
psql "$DATABASE_URL?sslmode=require" -c "SELECT 1;"
```

### Test Redis Connection

```bash
# Using redis-cli
redis-cli -h redis-host -p 6379 ping

# Using Python
python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
```

### Check Secret in AWS

```bash
# List all secrets
aws secretsmanager list-secrets \
  --filters Key=name,Values=halcytone/production

# Get specific secret
aws secretsmanager get-secret-value \
  --secret-id halcytone/production/openai-api-key \
  --query SecretString \
  --output text

# Update secret
aws secretsmanager update-secret \
  --secret-id halcytone/production/openai-api-key \
  --secret-string "new-api-key"
```

---

## Troubleshooting

### Script Permissions

```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x deployment/scripts/*.sh
```

### AWS Authentication

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Test Secrets Manager access
aws secretsmanager list-secrets --max-results 1
```

### Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install optional dependencies
pip install psycopg2-binary redis google-auth google-api-python-client
```

### Environment Variables

```bash
# Verify environment variables are set
env | grep -E "(CRM|PLATFORM|OPENAI|GOOGLE|DATABASE)" | sort

# Load from .env file
set -a
source .env.production
set +a
```

---

## Best Practices

### Secret Rotation

1. **Never rotate all secrets at once** - Do one service at a time
2. **Test in staging first** - Always validate new credentials
3. **Keep old credentials active** - For 24-48 hours during transition
4. **Monitor for errors** - Watch logs and metrics after rotation
5. **Document rotation dates** - Maintain rotation tracking spreadsheet

### Backup Procedures

1. **Test restores regularly** - Verify backups are recoverable
2. **Store in multiple locations** - S3 + local or multi-region
3. **Encrypt backups** - Use encryption at rest and in transit
4. **Monitor backup success** - Alert on backup failures
5. **Document recovery procedures** - Keep runbook up to date

### Deployment Safety

1. **Use rolling updates** - Zero-downtime deployments
2. **Health check before traffic** - Verify pods are healthy
3. **Have rollback plan** - Test rollback procedures
4. **Monitor during deployment** - Watch error rates and latency
5. **Communicate changes** - Notify stakeholders of deployments

---

## Getting Help

For issues with scripts:

1. Check script output for specific error messages
2. Verify prerequisites are installed
3. Confirm environment variables are set correctly
4. Review relevant documentation in `docs/`
5. Check logs for detailed error information

For production issues:

1. Run service validation: `python scripts/validate_external_services.py --all`
2. Check health endpoints: `curl https://api.halcytone.com/health`
3. Review application logs: `kubectl logs -f deployment/content-generator`
4. Check monitoring dashboards in Grafana
5. Consult `docs/monitoring-runbook.md` for common issues

---

## PairCoder CLI

This project also uses the **PairCoder CLI** (Python) for development workflows:

```bash
bpsai-pair-init
bpsai-pair feature <name> --type feature|fix|refactor --primary "..." --phase "..."
bpsai-pair pack --out agent_pack.tgz
bpsai-pair context-sync --last "..." --next "..." --blockers "..."
```
