#!/bin/bash
# SSL Certificate Setup Script using Let's Encrypt
# Run this on the server after DNS is configured

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get domain from argument or prompt
DOMAIN=${1:-}
if [ -z "$DOMAIN" ]; then
    echo -e "${YELLOW}Enter your domain (e.g., api.toombos.com):${NC}"
    read DOMAIN
fi

EMAIL="admin@toombos.com"  # Update this to your email

echo -e "${GREEN}🔐 Setting up SSL certificates for $DOMAIN${NC}"
echo "=============================================="
echo ""

# Check if DNS is configured
echo -e "${YELLOW}Checking DNS configuration...${NC}"
if host $DOMAIN > /dev/null 2>&1; then
    IP=$(host $DOMAIN | awk '/has address/ { print $4 }' | head -1)
    SERVER_IP=$(curl -s ifconfig.me)

    echo "Domain $DOMAIN points to: $IP"
    echo "Server IP is: $SERVER_IP"

    if [ "$IP" != "$SERVER_IP" ]; then
        echo -e "${RED}⚠️  WARNING: DNS doesn't point to this server!${NC}"
        echo "Domain resolves to: $IP"
        echo "This server is: $SERVER_IP"
        echo ""
        echo "Please update your DNS A record and wait for propagation."
        echo "This may take 5-15 minutes."
        exit 1
    else
        echo -e "${GREEN}✅ DNS is correctly configured${NC}"
    fi
else
    echo -e "${RED}❌ Cannot resolve domain $DOMAIN${NC}"
    echo "Please configure your DNS A record first."
    exit 1
fi

# Install certbot
echo ""
echo -e "${YELLOW}Installing Certbot...${NC}"
apt-get update -y
apt-get install -y certbot

# Stop nginx if running (to free port 80)
echo ""
echo -e "${YELLOW}Stopping nginx temporarily...${NC}"
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true

# Get certificate
echo ""
echo -e "${YELLOW}Obtaining SSL certificate from Let's Encrypt...${NC}"
certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN" \
    --keep-until-expiring

# Create ssl directory for nginx
mkdir -p deployment/nginx/ssl

# Copy certificates to nginx ssl directory
echo ""
echo -e "${YELLOW}Copying certificates...${NC}"
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem deployment/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem deployment/nginx/ssl/

# Set permissions
chmod 644 deployment/nginx/ssl/fullchain.pem
chmod 600 deployment/nginx/ssl/privkey.pem

echo ""
echo -e "${GREEN}✅ SSL certificates installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Setting up auto-renewal...${NC}"

# Create renewal cron job
cat > /etc/cron.d/certbot-renew <<EOF
# Renew Let's Encrypt certificates twice daily
0 0,12 * * * root certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/toombos/toombos-backend/deployment/nginx/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/toombos/toombos-backend/deployment/nginx/ssl/ && cd /opt/toombos/toombos-backend && docker compose -f docker-compose.prod.yml restart nginx"
EOF

echo -e "${GREEN}✅ Auto-renewal configured${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Certificates are valid for 90 days and will auto-renew."
echo ""
echo "Next step: Deploy your application"
echo "  docker compose -f docker-compose.prod.yml --env-file .env.production up -d"
echo ""
