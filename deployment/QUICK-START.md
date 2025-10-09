# 🚀 Quick Start - Deploy in 45 Minutes

Follow these steps in order. Each step should take 5-10 minutes.

---

## ⚡ Super Quick Overview

```
1. Create SSH key         (5 min)
2. Create DigitalOcean    (10 min)
3. Configure DNS          (5 min + 10 min wait)
4. Run deploy script      (10 min)
5. Setup SSL              (5 min)
6. Deploy app             (5 min)
7. Test & verify          (5 min)
```

---

## 📝 Copy-Paste Commands

### 1. Create SSH Key (Windows PowerShell)

```powershell
cd C:\Users\kmast\PycharmProjects\toombos-backend\deployment\scripts
.\setup-ssh-key.ps1
```
→ Copy the public key that appears

---

### 2. Create Server

1. Go to: https://www.digitalocean.com
2. Create Droplet → Ubuntu 22.04 → 4GB RAM → Paste SSH key
3. Copy the IP address you get

---

### 3. Set DNS

In your domain registrar:
```
Type: A Record
Name: api
Value: [Your IP from step 2]
```

Wait 10 minutes, then verify:
```powershell
nslookup api.toombos.com
```

---

### 4. Deploy to Server (Git Bash)

```bash
cd /c/Users/kmast/PycharmProjects/toombos-backend
export SERVER_IP="YOUR_IP_HERE"  # Replace with your IP
bash deployment/scripts/deploy-to-cloud.sh
```

---

### 5. Configure & Deploy (On Server)

```bash
# SSH to server
ssh -i ~/.ssh/toombos_rsa root@YOUR_IP_HERE

# Edit secrets
cd /opt/toombos/toombos-backend
nano .env.production
# Change POSTGRES_PASSWORD=REPLACE_WITH... to a strong password
# Save: Ctrl+X, Y, Enter

# Setup SSL
chmod +x deployment/scripts/setup-ssl.sh
./deployment/scripts/setup-ssl.sh api.toombos.com

# Deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Check status (wait 30 seconds first)
docker compose -f docker-compose.prod.yml ps
```

---

### 6. Test

```bash
# From anywhere:
curl https://api.toombos.com/health
```

Should return: `{"status":"healthy",...}`

---

## ✅ That's It!

Your backend is live at: **https://api.toombos.com**

CORS is configured for your Vercel frontend.

---

## 🆘 Quick Troubleshooting

**DNS not working?**
```bash
# Wait 15 more minutes, then:
ipconfig /flushdns  # Windows
nslookup api.toombos.com
```

**SSL failing?**
```bash
# On server:
docker compose -f docker-compose.prod.yml stop nginx
./deployment/scripts/setup-ssl.sh api.toombos.com
```

**Services not healthy?**
```bash
# On server:
docker compose -f docker-compose.prod.yml logs
docker compose -f docker-compose.prod.yml restart
```

---

## 📖 Full Guide

For detailed explanations: See `DEPLOYMENT.md`
