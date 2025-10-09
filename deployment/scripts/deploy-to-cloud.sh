#!/bin/bash
# Toombos Backend - Cloud Server Deployment Script
# This script automates the deployment process to a cloud server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_USER="root"
PROJECT_NAME="toombos-backend"
DEPLOY_DIR="/opt/toombos"

echo -e "${GREEN}🚀 Toombos Backend - Cloud Deployment${NC}"
echo "========================================"
echo ""

# Step 1: Get server IP
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}Enter your server IP address:${NC}"
    read SERVER_IP
fi

# Step 2: Get SSH key path
if [ -z "$SSH_KEY" ]; then
    echo -e "${YELLOW}Enter path to your SSH private key (e.g., ~/.ssh/toombos_rsa):${NC}"
    read SSH_KEY
else
    SSH_KEY="$HOME/.ssh/toombos_rsa"
fi

# Step 3: Test SSH connection
echo ""
echo -e "${BLUE}Testing SSH connection to $SERVER_IP...${NC}"
if ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no $DEPLOY_USER@$SERVER_IP "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to server. Please check:${NC}"
    echo "   - Server IP address is correct"
    echo "   - SSH key is correct"
    echo "   - Server is running"
    echo "   - Firewall allows SSH (port 22)"
    exit 1
fi

# Step 4: Install Docker on server
echo ""
echo -e "${BLUE}📦 Installing Docker on server...${NC}"
ssh -i "$SSH_KEY" $DEPLOY_USER@$SERVER_IP 'bash -s' <<'ENDSSH'
    # Update system
    apt-get update -y
    apt-get upgrade -y

    # Install prerequisites
    apt-get install -y ca-certificates curl gnupg lsb-release git

    # Add Docker GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start Docker
    systemctl start docker
    systemctl enable docker

    echo "✅ Docker installed successfully"
    docker --version
    docker compose version
ENDSSH

echo -e "${GREEN}✅ Docker installation complete${NC}"

# Step 5: Create deployment directory
echo ""
echo -e "${BLUE}📁 Creating deployment directory...${NC}"
ssh -i "$SSH_KEY" $DEPLOY_USER@$SERVER_IP "mkdir -p $DEPLOY_DIR"

# Step 6: Transfer files to server
echo ""
echo -e "${BLUE}📤 Transferring files to server...${NC}"
echo "This may take a few minutes..."

# Create a tarball of the project (excluding node_modules, .git, etc.)
tar -czf /tmp/toombos-backend-deploy.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    --exclude='.env.local' \
    -C "$(dirname "$(pwd)")" toombos-backend

# Transfer tarball
scp -i "$SSH_KEY" /tmp/toombos-backend-deploy.tar.gz $DEPLOY_USER@$SERVER_IP:$DEPLOY_DIR/

# Extract on server
ssh -i "$SSH_KEY" $DEPLOY_USER@$SERVER_IP "cd $DEPLOY_DIR && tar -xzf toombos-backend-deploy.tar.gz && rm toombos-backend-deploy.tar.gz"

# Clean up local tarball
rm /tmp/toombos-backend-deploy.tar.gz

echo -e "${GREEN}✅ Files transferred successfully${NC}"

# Step 7: Configure firewall
echo ""
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ssh -i "$SSH_KEY" $DEPLOY_USER@$SERVER_IP 'bash -s' <<'ENDSSH'
    # Install UFW if not present
    apt-get install -y ufw

    # Allow SSH
    ufw allow 22/tcp

    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp

    # Enable firewall
    ufw --force enable

    echo "✅ Firewall configured"
    ufw status
ENDSSH

echo -e "${GREEN}✅ Firewall configured${NC}"

# Step 8: Display next steps
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Server Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. Configure DNS:"
echo "   - Go to your domain registrar"
echo "   - Add A record: api.toombos.com → $SERVER_IP"
echo "   - Wait 5-15 minutes for DNS propagation"
echo ""
echo "2. Update production environment:"
echo "   - Edit .env.production on the server"
echo "   - Add required secrets (POSTGRES_PASSWORD, API keys, etc.)"
echo ""
echo "3. Get SSL certificates:"
echo "   - After DNS is configured, run:"
echo "   ssh -i $SSH_KEY $DEPLOY_USER@$SERVER_IP"
echo "   cd $DEPLOY_DIR/toombos-backend"
echo "   ./deployment/scripts/setup-ssl.sh api.toombos.com"
echo ""
echo "4. Deploy the application:"
echo "   docker compose -f docker-compose.prod.yml --env-file .env.production up -d"
echo ""
echo -e "${BLUE}🔗 SSH into your server:${NC}"
echo "   ssh -i $SSH_KEY $DEPLOY_USER@$SERVER_IP"
echo ""
