# Toombos Backend - Production Deployment Guide

Complete step-by-step guide to deploy your backend to `api.toombos.com`

## 📋 Prerequisites Checklist

- [ ] DigitalOcean account (or other cloud provider)
- [ ] Domain name `toombos.com` (with access to DNS settings)
- [ ] Credit card for cloud provider
- [ ] SSH client (Windows Terminal or PowerShell)

---

## 🎯 Deployment Steps

### Step 1: Create SSH Key (5 minutes)

**On your Windows machine:**

```powershell
# Open PowerShell and run:
cd C:\Users\kmast\PycharmProjects\toombos-backend\deployment\scripts
.\setup-ssh-key.ps1
```

**This will:**
- Generate SSH key pair
- Copy public key to your clipboard

**Keep the terminal open** - you'll need the public key in the next step.

---

### Step 2: Create Cloud Server (10 minutes)

#### Option A: DigitalOcean (Recommended)

1. **Sign up:** https://www.digitalocean.com
2. **Create Droplet:**
   - Click **"Create"** → **"Droplets"**

3. **Choose Region:**
   - Select closest to your users (e.g., New York for US East)

4. **Choose Image:**
   - **Ubuntu 22.04 LTS**

5. **Choose Size:**
   - **Basic Plan**
   - **$24/month** - 4GB RAM / 2 vCPUs / 80GB SSD
   - (This can handle moderate traffic, scale up later if needed)

6. **Authentication:**
   - Select **"SSH Key"**
   - Click **"New SSH Key"**
   - Paste the public key from Step 1
   - Name it: `toombos-deployment`

7. **Hostname:**
   - Enter: `toombos-api`

8. **Create Droplet**

9. **Wait 1-2 minutes** for the droplet to be created

10. **Copy the IP address** shown on the droplet page

---

### Step 3: Configure DNS (5 minutes)

**In your domain registrar (GoDaddy, Namecheap, etc.):**

1. Go to DNS Management
2. Add **A Record:**
   ```
   Type: A
   Name: api
   Value: [Your Droplet IP from Step 2]
   TTL: 600 (or default)
   ```
3. Save changes
4. **Wait 5-15 minutes** for DNS propagation

**Verify DNS:**
```bash
# On your Windows machine:
nslookup api.toombos.com
# Should return your server IP
```

---

### Step 4: Deploy to Server (10 minutes)

**Open Git Bash (or WSL):**

```bash
cd /c/Users/kmast/PycharmProjects/toombos-backend

# Set your server IP (from Step 2)
export SERVER_IP="YOUR_DROPLET_IP_HERE"

# Run deployment script
bash deployment/scripts/deploy-to-cloud.sh
```

**This script will:**
- ✅ Test SSH connection
- ✅ Install Docker on server
- ✅ Transfer your backend code
- ✅ Configure firewall
- ✅ Set up the environment

**Expected time:** 5-10 minutes

---

### Step 5: Configure Production Secrets (5 minutes)

**SSH into your server:**

```bash
# Use the SSH key you created
ssh -i ~/.ssh/toombos_rsa root@YOUR_SERVER_IP

# Navigate to project
cd /opt/toombos/toombos-backend
```

**Edit production environment file:**

```bash
nano .env.production
```

**Required Changes:**

```bash
# Change this:
POSTGRES_PASSWORD=REPLACE_WITH_PRODUCTION_PASSWORD

# To (generate a strong password):
POSTGRES_PASSWORD=your_strong_password_here_123!

# Optionally update these for full functionality:
API_KEY=your_secure_api_key_here
OPENAI_API_KEY=sk-your-openai-key-if-needed
GOOGLE_CREDENTIALS_JSON=your-google-creds-if-needed
GRAFANA_ADMIN_PASSWORD=grafana_admin_password
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

### Step 6: Set Up SSL Certificates (5 minutes)

**Still on the server (via SSH):**

```bash
cd /opt/toombos/toombos-backend

# Make script executable
chmod +x deployment/scripts/setup-ssl.sh

# Run SSL setup (use your domain)
./deployment/scripts/setup-ssl.sh api.toombos.com
```

**This will:**
- ✅ Verify DNS points to server
- ✅ Get Let's Encrypt SSL certificate
- ✅ Set up auto-renewal

**If DNS isn't ready:**
- Wait 5-15 minutes
- Run the script again

---

### Step 7: Deploy the Application (5 minutes)

**On the server:**

```bash
cd /opt/toombos/toombos-backend

# Build and start all services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Wait 30 seconds for services to start
sleep 30

# Check status
docker compose -f docker-compose.prod.yml ps
```

**You should see:**
```
NAME                   STATUS
content-generator-1    Up (healthy)
content-generator-2    Up (healthy)
content-generator-3    Up (healthy)
halcytone-nginx        Up (healthy)
halcytone-redis        Up (healthy)
halcytone-postgres     Up (healthy)
...
```

---

### Step 8: Verify Deployment (5 minutes)

**Test the endpoints:**

```bash
# Health check
curl https://api.toombos.com/health

# Should return:
# {"status":"healthy","timestamp":"..."}

# API root
curl https://api.toombos.com/

# Should return:
# {"service":"Halcytone Content Generator","version":"0.1.0","status":"operational"}
```

**From your browser:**
- Visit: https://api.toombos.com
- Should see JSON response (not an error)
- Check for 🔒 padlock icon (SSL working)

---

### Step 9: Test CORS from Frontend (2 minutes)

**Update your Vercel frontend to use:**

```javascript
// In your frontend config:
const API_URL = "https://api.toombos.com";

// Test API call:
fetch(`${API_URL}/health`)
  .then(r => r.json())
  .then(data => console.log("Backend connected:", data));
```

**CORS is already configured for:**
- ✅ `https://toombos-frontend-1dvdoaozf-kevin-mastersons-projects.vercel.app`
- ✅ `https://api.toombos.com`

---

## 🎉 Deployment Complete!

Your backend is now live at: **https://api.toombos.com**

### 📊 Monitoring & Management

**View logs:**
```bash
# SSH into server
ssh -i ~/.ssh/toombos_rsa root@YOUR_SERVER_IP

# View all logs
cd /opt/toombos/toombos-backend
docker compose -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.prod.yml logs -f content-generator-1
```

**Restart services:**
```bash
docker compose -f docker-compose.prod.yml restart
```

**Update deployment:**
```bash
# On your local machine, after making changes:
cd /c/Users/kmast/PycharmProjects/toombos-backend
git add .
git commit -m "Update backend"

# Re-run deployment
export SERVER_IP="YOUR_SERVER_IP"
bash deployment/scripts/deploy-to-cloud.sh

# SSH into server and rebuild
ssh -i ~/.ssh/toombos_rsa root@YOUR_SERVER_IP
cd /opt/toombos/toombos-backend
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

---

## 🔍 Troubleshooting

### Issue: Cannot connect to server
```bash
# Check if server is running
ping YOUR_SERVER_IP

# Check SSH
ssh -i ~/.ssh/toombos_rsa root@YOUR_SERVER_IP

# If SSH fails, check DigitalOcean console
```

### Issue: DNS not resolving
```bash
# Check DNS propagation
nslookup api.toombos.com

# Wait 15 minutes and try again
# Clear local DNS cache (Windows):
ipconfig /flushdns
```

### Issue: SSL certificate fails
```bash
# On server, check if port 80 is free:
netstat -tlnp | grep :80

# Stop nginx temporarily:
docker compose -f docker-compose.prod.yml stop nginx

# Try SSL setup again:
./deployment/scripts/setup-ssl.sh api.toombos.com
```

### Issue: Services not healthy
```bash
# On server, check logs:
docker compose -f docker-compose.prod.yml logs

# Check specific service:
docker compose -f docker-compose.prod.yml logs content-generator-1

# Restart services:
docker compose -f docker-compose.prod.yml restart
```

### Issue: CORS errors
```bash
# Verify CORS config on server:
cat /opt/toombos/toombos-backend/.env.production | grep CORS

# Should show:
# CORS_ORIGINS=https://toombos-frontend-1dvdoaozf-kevin-mastersons-projects.vercel.app,https://api.toombos.com

# If wrong, edit and restart:
nano .env.production
docker compose -f docker-compose.prod.yml restart
```

---

## 💰 Cost Estimate

**Monthly Costs:**
- DigitalOcean Droplet (4GB): **$24/month**
- SSL Certificate: **Free** (Let's Encrypt)
- Domain: **~$10-15/year** (already owned)

**Total: ~$24/month**

---

## 🚀 Next Steps

1. **Set up monitoring:** Configure Grafana dashboards
2. **Set up backups:** Schedule PostgreSQL backups
3. **Set up alerts:** Configure error notifications
4. **Scale if needed:** Add more backend instances

---

## 📞 Support

If you encounter issues:
1. Check troubleshooting section above
2. Review server logs
3. Check DigitalOcean status page

---

## ✅ Quick Checklist

- [ ] Step 1: SSH key created
- [ ] Step 2: DigitalOcean droplet created
- [ ] Step 3: DNS configured (api.toombos.com → server IP)
- [ ] Step 4: Code deployed to server
- [ ] Step 5: Production secrets configured
- [ ] Step 6: SSL certificates installed
- [ ] Step 7: Application deployed
- [ ] Step 8: Endpoints verified
- [ ] Step 9: CORS tested from frontend

**When all checked:** 🎉 Your backend is live!
