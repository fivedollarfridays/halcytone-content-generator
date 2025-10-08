#!/bin/bash
# AWS Secrets Manager Setup Script
# Sets up all production secrets in AWS Secrets Manager
#
# Usage: ./setup_aws_secrets.sh [--region us-east-1] [--profile default]
#
# Prerequisites:
# - AWS CLI installed and configured
# - Appropriate IAM permissions for Secrets Manager
# - All secret values available (from .env.production or manual input)

set -e

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
NAMESPACE="halcytone/production"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      REGION="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--region REGION] [--profile PROFILE]"
      echo ""
      echo "Options:"
      echo "  --region   AWS region (default: us-east-1)"
      echo "  --profile  AWS CLI profile (default: default)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "==========================================="
echo "AWS Secrets Manager Setup"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Namespace: $NAMESPACE"
echo "==========================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Verify AWS credentials
echo "Verifying AWS credentials..."
if ! aws sts get-caller-identity --profile "$PROFILE" --region "$REGION" &> /dev/null; then
    echo "Error: AWS credentials not configured correctly"
    exit 1
fi
echo "✓ AWS credentials verified"
echo ""

# Helper function to create or update secret
create_or_update_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local description="$3"

    echo -n "Creating/updating secret: $secret_name... "

    # Check if secret exists
    if aws secretsmanager describe-secret \
        --secret-id "$secret_name" \
        --profile "$PROFILE" \
        --region "$REGION" &> /dev/null; then
        # Update existing secret
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --profile "$PROFILE" \
            --region "$REGION" > /dev/null
        echo "✓ Updated"
    else
        # Create new secret
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$secret_value" \
            --profile "$PROFILE" \
            --region "$REGION" > /dev/null
        echo "✓ Created"
    fi
}

# Helper function to create secret from file
create_secret_from_file() {
    local secret_name="$1"
    local file_path="$2"
    local description="$3"

    if [ ! -f "$file_path" ]; then
        echo "✗ File not found: $file_path"
        return 1
    fi

    echo -n "Creating/updating secret from file: $secret_name... "

    # Read file content
    local file_content=$(cat "$file_path")

    # Check if secret exists
    if aws secretsmanager describe-secret \
        --secret-id "$secret_name" \
        --profile "$PROFILE" \
        --region "$REGION" &> /dev/null; then
        # Update existing secret
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$file_content" \
            --profile "$PROFILE" \
            --region "$REGION" > /dev/null
        echo "✓ Updated"
    else
        # Create new secret
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$file_content" \
            --profile "$PROFILE" \
            --region "$REGION" > /dev/null
        echo "✓ Created"
    fi
}

# Prompt for secret if not in environment
prompt_secret() {
    local var_name="$1"
    local prompt_text="$2"
    local is_sensitive="${3:-true}"

    if [ -z "${!var_name}" ]; then
        if [ "$is_sensitive" = "true" ]; then
            read -sp "$prompt_text: " value
            echo ""
        else
            read -p "$prompt_text: " value
        fi
        eval "$var_name='$value'"
    fi
}

echo "=== External Service API Keys ==="
echo ""

# CRM API Key
prompt_secret "CRM_API_KEY" "Enter CRM API Key"
create_or_update_secret \
    "$NAMESPACE/crm-api-key" \
    "$CRM_API_KEY" \
    "CRM Service API Key for production"

# Platform API Key
prompt_secret "PLATFORM_API_KEY" "Enter Platform API Key"
create_or_update_secret \
    "$NAMESPACE/platform-api-key" \
    "$PLATFORM_API_KEY" \
    "Platform Service API Key for production"

echo ""
echo "=== Content Source Credentials ==="
echo ""

# Google Credentials
if [ -z "$GOOGLE_CREDENTIALS_FILE" ]; then
    read -p "Enter path to Google service account JSON file: " GOOGLE_CREDENTIALS_FILE
fi

if [ -f "$GOOGLE_CREDENTIALS_FILE" ]; then
    create_secret_from_file \
        "$NAMESPACE/google-credentials" \
        "$GOOGLE_CREDENTIALS_FILE" \
        "Google Cloud service account credentials for production"
else
    echo "✗ Google credentials file not found, skipping"
fi

# Notion API Key (optional)
read -p "Do you use Notion? (y/n): " use_notion
if [[ "$use_notion" =~ ^[Yy]$ ]]; then
    prompt_secret "NOTION_API_KEY" "Enter Notion API Key"
    prompt_secret "NOTION_DATABASE_ID" "Enter Notion Database ID" false

    create_or_update_secret \
        "$NAMESPACE/notion-api-key" \
        "$NOTION_API_KEY" \
        "Notion API Key for production"

    create_or_update_secret \
        "$NAMESPACE/notion-database-id" \
        "$NOTION_DATABASE_ID" \
        "Notion Database ID for production"
fi

echo ""
echo "=== AI Service Credentials ==="
echo ""

# OpenAI API Key
prompt_secret "OPENAI_API_KEY" "Enter OpenAI API Key"
create_or_update_secret \
    "$NAMESPACE/openai-api-key" \
    "$OPENAI_API_KEY" \
    "OpenAI API Key for production"

echo ""
echo "=== Security Secrets ==="
echo ""

# Generate or prompt for JWT secret
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "Generating JWT secret key..."
    JWT_SECRET_KEY=$(openssl rand -base64 32)
fi
create_or_update_secret \
    "$NAMESPACE/jwt-secret-key" \
    "$JWT_SECRET_KEY" \
    "JWT signing secret for production"

# Generate or prompt for API key encryption key
if [ -z "$API_KEY_ENCRYPTION_KEY" ]; then
    echo "Generating API key encryption key..."
    API_KEY_ENCRYPTION_KEY=$(openssl rand -base64 32)
fi
create_or_update_secret \
    "$NAMESPACE/api-key-encryption-key" \
    "$API_KEY_ENCRYPTION_KEY" \
    "API key encryption key for production"

# Content Generator API Key
if [ -z "$CONTENT_GENERATOR_API_KEY" ]; then
    echo "Generating Content Generator API key..."
    CONTENT_GENERATOR_API_KEY=$(openssl rand -base64 32)
fi
create_or_update_secret \
    "$NAMESPACE/content-generator-api-key" \
    "$CONTENT_GENERATOR_API_KEY" \
    "Content Generator service API key"

echo ""
echo "=== Database Credentials ==="
echo ""

# Database Password
prompt_secret "DATABASE_PASSWORD" "Enter Database Password"
prompt_secret "DATABASE_USER" "Enter Database User" false
prompt_secret "DATABASE_HOST" "Enter Database Host" false
prompt_secret "DATABASE_NAME" "Enter Database Name" false

# Construct database URL
DATABASE_URL="postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:5432/${DATABASE_NAME}"

create_or_update_secret \
    "$NAMESPACE/database-password" \
    "$DATABASE_PASSWORD" \
    "PostgreSQL database password"

create_or_update_secret \
    "$NAMESPACE/database-url" \
    "$DATABASE_URL" \
    "PostgreSQL connection string"

echo ""
echo "=== Cache & CDN Credentials ==="
echo ""

# Redis URL (optional)
read -p "Do you use Redis? (y/n): " use_redis
if [[ "$use_redis" =~ ^[Yy]$ ]]; then
    prompt_secret "REDIS_URL" "Enter Redis URL (e.g., redis://host:6379)" false
    create_or_update_secret \
        "$NAMESPACE/redis-url" \
        "$REDIS_URL" \
        "Redis connection URL for production"
fi

# CDN API Key (optional)
read -p "Do you use CDN (Cloudflare/CloudFront)? (y/n): " use_cdn
if [[ "$use_cdn" =~ ^[Yy]$ ]]; then
    prompt_secret "CDN_API_KEY" "Enter CDN API Key"
    prompt_secret "CDN_ZONE_ID" "Enter CDN Zone ID" false

    create_or_update_secret \
        "$NAMESPACE/cdn-api-key" \
        "$CDN_API_KEY" \
        "CDN API Key for cache invalidation"

    create_or_update_secret \
        "$NAMESPACE/cdn-zone-id" \
        "$CDN_ZONE_ID" \
        "CDN Zone ID"
fi

echo ""
echo "=== Alerting Credentials ==="
echo ""

# Slack Webhook (optional)
read -p "Configure Slack alerts? (y/n): " use_slack
if [[ "$use_slack" =~ ^[Yy]$ ]]; then
    prompt_secret "SLACK_WEBHOOK_URL" "Enter Slack Webhook URL"
    create_or_update_secret \
        "$NAMESPACE/slack-webhook-url" \
        "$SLACK_WEBHOOK_URL" \
        "Slack webhook for production alerts"
fi

echo ""
echo "==========================================="
echo "Setup Complete!"
echo "==========================================="
echo ""
echo "All secrets have been stored in AWS Secrets Manager."
echo ""
echo "Next steps:"
echo "1. Configure IAM permissions for application to read secrets"
echo "2. Update application configuration to use SecretsManager"
echo "3. Test secret retrieval from application"
echo "4. Set up automatic rotation for applicable secrets"
echo ""
echo "List all secrets:"
echo "  aws secretsmanager list-secrets --profile $PROFILE --region $REGION --filters Key=name,Values=$NAMESPACE"
echo ""
echo "Retrieve a secret:"
echo "  aws secretsmanager get-secret-value --secret-id $NAMESPACE/SECRET_NAME --profile $PROFILE --region $REGION"
echo ""
