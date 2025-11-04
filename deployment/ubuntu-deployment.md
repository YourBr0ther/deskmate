# DeskMate Ubuntu Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying DeskMate in a production environment on Ubuntu 22.04 LTS. The deployment includes SSL/TLS encryption, firewall configuration, automated backups, and monitoring.

## Prerequisites

### System Requirements

**Minimum Hardware:**
- CPU: 2 cores (4 cores recommended)
- RAM: 4 GB (8 GB recommended)
- Storage: 20 GB available space (50 GB recommended)
- Network: Public IP address with domain name

**Software Requirements:**
- Ubuntu 22.04 LTS (fresh installation recommended)
- Root access (via sudo)
- Domain name pointing to your server's IP address

### Network Requirements

**Required Ports:**
- Port 22 (SSH) - For server administration
- Port 80 (HTTP) - For Let's Encrypt challenges and HTTP to HTTPS redirect
- Port 443 (HTTPS) - For secure web access to DeskMate

**Blocked Ports (for security):**
- Port 5432 (PostgreSQL) - Database should not be externally accessible
- Port 6333 (Qdrant) - Vector database should not be externally accessible
- Port 8000 (Backend API) - Only accessible through nginx reverse proxy

## Quick Installation

### Automated Installation

For a quick setup, use the automated installation script:

```bash
# 1. Connect to your Ubuntu server
ssh root@your-server-ip

# 2. Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/YourBr0ther/deskmate/main/deployment/production/install.sh | sudo bash
```

This script will:
- Install Docker and Docker Compose
- Create system user and directories
- Clone the DeskMate repository
- Configure environment variables
- Set up SSL certificates
- Configure firewall
- Start all services

### Manual Installation

If you prefer to install manually or want to understand each step:

## Step 1: System Preparation

### Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

### Install Required Packages

```bash
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    ufw \
    fail2ban \
    certbot \
    nginx
```

## Step 2: Docker Installation

### Install Docker

```bash
# Remove old Docker versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Verify Installation

```bash
docker --version
docker-compose --version
```

## Step 3: DeskMate Setup

### Create System User

```bash
sudo useradd --system --create-home --home-dir /opt/deskmate --shell /bin/bash deskmate
sudo usermod -aG docker deskmate
sudo mkdir -p /opt/deskmate/{data,logs,backups,config}
sudo mkdir -p /opt/deskmate/data/{postgres,qdrant}
sudo chown -R deskmate:deskmate /opt/deskmate
```

### Clone Repository

```bash
sudo -u deskmate git clone https://github.com/YourBr0ther/deskmate.git /opt/deskmate/deskmate
```

### Configure Environment

```bash
cd /opt/deskmate/deskmate/deployment/production

# Copy environment template
sudo cp .env.prod.example .env.prod

# Generate secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 48)
JWT_SECRET=$(openssl rand -base64 48)

# Update environment file
sudo sed -i "s/your_secure_postgres_password_here/$POSTGRES_PASSWORD/g" .env.prod
sudo sed -i "s/your_secret_key_here_minimum_32_characters_long/$SECRET_KEY/g" .env.prod
sudo sed -i "s/your_jwt_secret_here_minimum_32_characters/$JWT_SECRET/g" .env.prod

# Set your domain name
sudo sed -i "s/your-domain.com/yourdomain.com/g" .env.prod

# Set ownership and permissions
sudo chown deskmate:deskmate .env.prod
sudo chmod 600 .env.prod
```

**Important:** Edit `.env.prod` to add your specific configuration:
- Domain name
- Nano-GPT API key
- SMTP settings for alerts
- Any other custom settings

## Step 4: SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
cd /opt/deskmate/deskmate/deployment/production
sudo ./ssl-setup.sh letsencrypt
```

### Using Self-Signed Certificates (Testing Only)

```bash
cd /opt/deskmate/deskmate/deployment/production
sudo ./ssl-setup.sh self-signed
```

## Step 5: Firewall Configuration

```bash
cd /opt/deskmate/deskmate/deployment/production
sudo ./firewall-setup.sh setup
```

This will:
- Configure UFW (Uncomplicated Firewall)
- Allow SSH, HTTP, and HTTPS traffic
- Block database ports from external access
- Set up Fail2Ban for intrusion prevention
- Configure rate limiting

## Step 6: Systemd Service Setup

```bash
sudo tee /etc/systemd/system/deskmate.service > /dev/null << 'EOF'
[Unit]
Description=DeskMate AI Companion
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=deskmate
Group=deskmate
WorkingDirectory=/opt/deskmate/deskmate/deployment/production
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable deskmate
sudo systemctl start deskmate
```

## Step 7: Backup Configuration

### Create Backup Script

```bash
sudo tee /usr/local/bin/deskmate-backup.sh > /dev/null << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/deskmate/backups"
DATE=$(date +%Y%m%d-%H%M%S)
DESKMATE_HOME="/opt/deskmate"

mkdir -p "$BACKUP_DIR/$DATE"

# Backup PostgreSQL
docker exec deskmate-postgres pg_dump -U deskmate deskmate | gzip > "$BACKUP_DIR/$DATE/postgres-$DATE.sql.gz"

# Backup Qdrant data
docker exec deskmate-qdrant tar czf - /qdrant/storage > "$BACKUP_DIR/$DATE/qdrant-$DATE.tar.gz"

# Backup configuration
tar czf "$BACKUP_DIR/$DATE/config-$DATE.tar.gz" -C "$DESKMATE_HOME/deskmate" deployment/production/.env.prod data/

# Remove old backups
find "$BACKUP_DIR" -name "*-*-*" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
EOF

sudo chmod +x /usr/local/bin/deskmate-backup.sh
```

### Schedule Daily Backups

```bash
echo "0 2 * * * root /usr/local/bin/deskmate-backup.sh" | sudo tee /etc/cron.d/deskmate-backup
```

## Step 8: Monitoring Setup

### Create Status Script

```bash
sudo tee /usr/local/bin/deskmate-status.sh > /dev/null << 'EOF'
#!/bin/bash

echo "=== DeskMate System Status ==="
echo "Date: $(date)"
echo ""

echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== System Resources ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /opt/deskmate
echo ""

echo "=== Service Health ==="
systemctl is-active deskmate
systemctl is-active docker
echo ""

echo "=== Recent Logs ==="
journalctl -u deskmate --since "1 hour ago" --no-pager -n 5
EOF

sudo chmod +x /usr/local/bin/deskmate-status.sh
```

## Step 9: Verification

### Check Service Status

```bash
# Check if all containers are running
docker ps

# Check service status
sudo systemctl status deskmate

# Check logs
sudo journalctl -u deskmate -f
```

### Test Web Access

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://yourdomain.com

# Test HTTPS
curl -I https://yourdomain.com

# Test API health
curl https://yourdomain.com/api/health
```

### Verify SSL Certificate

```bash
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null | openssl x509 -noout -dates
```

## Management Commands

### Service Management

```bash
# Start DeskMate
sudo systemctl start deskmate

# Stop DeskMate
sudo systemctl stop deskmate

# Restart DeskMate
sudo systemctl restart deskmate

# Check status
sudo systemctl status deskmate

# View logs
sudo journalctl -u deskmate -f
```

### Docker Management

```bash
cd /opt/deskmate/deskmate/deployment/production

# View container logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# Update containers
sudo -u deskmate docker-compose -f docker-compose.prod.yml pull
sudo systemctl restart deskmate
```

### Backup and Restore

```bash
# Manual backup
sudo /usr/local/bin/deskmate-backup.sh

# List backups
ls -la /opt/deskmate/backups/

# Restore from backup (example)
# Stop services first
sudo systemctl stop deskmate

# Restore PostgreSQL
docker exec -i deskmate-postgres psql -U deskmate -d deskmate < backup.sql

# Restart services
sudo systemctl start deskmate
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker status
sudo systemctl status docker

# Check for port conflicts
sudo netstat -tlnp | grep -E ':(80|443|22|5432|6333)'

# Check logs
sudo journalctl -u deskmate --since "10 minutes ago"
```

#### SSL Certificate Issues

```bash
# Check certificate status
sudo /opt/deskmate/deskmate/deployment/production/ssl-setup.sh verify

# Renew certificates manually
sudo /opt/deskmate/deskmate/deployment/production/ssl-setup.sh renew
```

#### Database Connection Issues

```bash
# Check PostgreSQL logs
docker logs deskmate-postgres

# Check if database is accessible
docker exec -it deskmate-postgres psql -U deskmate -d deskmate -c '\l'
```

#### Performance Issues

```bash
# Check system resources
sudo /usr/local/bin/deskmate-status.sh

# Check container resource usage
docker stats

# Check disk space
df -h
du -sh /opt/deskmate/*
```

### Log Locations

- **System logs:** `sudo journalctl -u deskmate`
- **Container logs:** `docker-compose -f docker-compose.prod.yml logs`
- **Nginx logs:** `/var/log/nginx/`
- **Application logs:** `/opt/deskmate/logs/`

### Getting Help

If you encounter issues:

1. Check the logs first
2. Verify all services are running
3. Check firewall and network configuration
4. Review the environment configuration
5. Consult the GitHub repository for updates

## Security Best Practices

### Post-Installation Security

1. **Change default passwords** in `.env.prod`
2. **Configure SSH key authentication** and disable password login
3. **Set up regular security updates:**
   ```bash
   echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades
   sudo systemctl enable unattended-upgrades
   ```
4. **Monitor logs regularly** for suspicious activity
5. **Keep backups secure** and test restore procedures

### Firewall Management

```bash
# View firewall status
sudo ufw status verbose

# Allow specific IP for management
sudo ufw allow from YOUR_IP_ADDRESS to any port 22

# Block specific IP
sudo ufw deny from SUSPICIOUS_IP_ADDRESS
```

### Regular Maintenance

1. **Weekly:** Check system status and logs
2. **Monthly:** Update system packages and restart
3. **Quarterly:** Review and test backup/restore procedures
4. **Annually:** Review security configuration and access controls

## Updates and Upgrades

### Updating DeskMate

```bash
cd /opt/deskmate/deskmate
sudo -u deskmate git pull origin main
sudo systemctl restart deskmate
```

### System Updates

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
cd /opt/deskmate/deskmate/deployment/production
sudo -u deskmate docker-compose -f docker-compose.prod.yml pull
sudo systemctl restart deskmate
```

## Performance Optimization

### Resource Tuning

Edit `/opt/deskmate/deskmate/deployment/production/.env.prod`:

```bash
# For larger servers, increase worker count
MAX_WORKERS=4

# Adjust memory limits based on available RAM
MEMORY_LIMIT_BACKEND=2g
MEMORY_LIMIT_POSTGRES=1g
```

### Database Optimization

```bash
# PostgreSQL tuning (for servers with 8GB+ RAM)
docker exec -it deskmate-postgres psql -U deskmate -d deskmate -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
SELECT pg_reload_conf();
"
```

## Support and Community

- **GitHub Repository:** https://github.com/YourBr0ther/deskmate
- **Documentation:** Check the `/docs` directory in the repository
- **Issues:** Report bugs and feature requests on GitHub

---

**Congratulations!** You have successfully deployed DeskMate in production. Your virtual AI companion is now running securely with SSL encryption, automated backups, and monitoring.

For any issues or questions, please refer to the troubleshooting section or check the GitHub repository for the latest updates and community support.