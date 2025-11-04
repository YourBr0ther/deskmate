#!/bin/bash

# DeskMate Production Installation Script
# This script automates the complete deployment of DeskMate on Ubuntu 22.04 LTS

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DESKMATE_USER="deskmate"
DESKMATE_HOME="/opt/deskmate"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/deskmate-install.log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_ubuntu_version() {
    log_info "Checking Ubuntu version..."

    if ! grep -q "Ubuntu 22.04" /etc/os-release; then
        log_warning "This script is designed for Ubuntu 22.04 LTS"
        log_warning "Current OS: $(lsb_release -d | cut -f2)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Ubuntu 22.04 LTS detected"
    fi
}

update_system() {
    log_step "Updating system packages..."

    export DEBIAN_FRONTEND=noninteractive
    apt update
    apt upgrade -y
    apt autoremove -y

    log_success "System updated"
}

install_docker() {
    log_step "Installing Docker and Docker Compose..."

    # Remove old Docker versions
    apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Install prerequisites
    apt install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Enable and start Docker
    systemctl enable docker
    systemctl start docker

    # Install Docker Compose standalone (for compatibility)
    curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    log_success "Docker installed successfully"
}

create_deskmate_user() {
    log_step "Creating DeskMate system user..."

    # Create system user
    if ! id "$DESKMATE_USER" &>/dev/null; then
        useradd --system --create-home --home-dir "$DESKMATE_HOME" --shell /bin/bash "$DESKMATE_USER"
        usermod -aG docker "$DESKMATE_USER"
        log_success "DeskMate user created"
    else
        log_info "DeskMate user already exists"
    fi

    # Create necessary directories
    mkdir -p "$DESKMATE_HOME"/{data,logs,backups,config}
    mkdir -p "$DESKMATE_HOME"/data/{postgres,qdrant}
    chown -R "$DESKMATE_USER:$DESKMATE_USER" "$DESKMATE_HOME"

    log_success "DeskMate directories created"
}

clone_repository() {
    log_step "Cloning DeskMate repository..."

    if [[ ! -d "$DESKMATE_HOME/deskmate" ]]; then
        sudo -u "$DESKMATE_USER" git clone https://github.com/YourBr0ther/deskmate.git "$DESKMATE_HOME/deskmate"
        log_success "Repository cloned"
    else
        log_info "Repository already exists, pulling latest changes..."
        cd "$DESKMATE_HOME/deskmate"
        sudo -u "$DESKMATE_USER" git pull origin main
        log_success "Repository updated"
    fi

    chown -R "$DESKMATE_USER:$DESKMATE_USER" "$DESKMATE_HOME/deskmate"
}

setup_environment() {
    log_step "Setting up environment configuration..."

    local env_file="$DESKMATE_HOME/deskmate/deployment/production/.env.prod"

    if [[ ! -f "$env_file" ]]; then
        cp "$DESKMATE_HOME/deskmate/deployment/production/.env.prod.example" "$env_file"

        # Generate secure passwords and secrets
        local postgres_password=$(openssl rand -base64 32)
        local secret_key=$(openssl rand -base64 48)
        local jwt_secret=$(openssl rand -base64 48)

        # Update environment file with generated values
        sed -i "s/your_secure_postgres_password_here/$postgres_password/g" "$env_file"
        sed -i "s/your_secret_key_here_minimum_32_characters_long/$secret_key/g" "$env_file"
        sed -i "s/your_jwt_secret_here_minimum_32_characters/$jwt_secret/g" "$env_file"

        # Prompt for domain name
        read -p "Enter your domain name (e.g., deskmate.example.com): " domain_name
        if [[ -n "$domain_name" ]]; then
            sed -i "s/your-domain.com/$domain_name/g" "$env_file"
        fi

        # Prompt for API keys
        read -p "Enter your Nano-GPT API key (press Enter to skip): " nano_gpt_key
        if [[ -n "$nano_gpt_key" ]]; then
            sed -i "s/your_nano_gpt_api_key_here/$nano_gpt_key/g" "$env_file"
        fi

        chown "$DESKMATE_USER:$DESKMATE_USER" "$env_file"
        chmod 600 "$env_file"

        log_success "Environment configuration created"
        log_warning "Please review and update $env_file with your specific settings"
    else
        log_info "Environment file already exists"
    fi
}

setup_systemd_service() {
    log_step "Setting up systemd service..."

    cat > /etc/systemd/system/deskmate.service << EOF
[Unit]
Description=DeskMate AI Companion
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$DESKMATE_USER
Group=$DESKMATE_USER
WorkingDirectory=$DESKMATE_HOME/deskmate/deployment/production
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable deskmate

    log_success "Systemd service configured"
}

setup_backup_script() {
    log_step "Setting up backup automation..."

    cat > /usr/local/bin/deskmate-backup.sh << 'EOF'
#!/bin/bash

# DeskMate Backup Script
BACKUP_DIR="/opt/deskmate/backups"
DATE=$(date +%Y%m%d-%H%M%S)
DESKMATE_HOME="/opt/deskmate"

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup PostgreSQL
docker exec deskmate-postgres pg_dump -U deskmate deskmate | gzip > "$BACKUP_DIR/$DATE/postgres-$DATE.sql.gz"

# Backup Qdrant data
docker exec deskmate-qdrant tar czf - /qdrant/storage > "$BACKUP_DIR/$DATE/qdrant-$DATE.tar.gz"

# Backup configuration files
tar czf "$BACKUP_DIR/$DATE/config-$DATE.tar.gz" -C "$DESKMATE_HOME/deskmate" deployment/production/.env.prod data/

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*-*-*" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
EOF

    chmod +x /usr/local/bin/deskmate-backup.sh

    # Add cron job for daily backups
    echo "0 2 * * * root /usr/local/bin/deskmate-backup.sh" > /etc/cron.d/deskmate-backup
    chmod 644 /etc/cron.d/deskmate-backup

    log_success "Backup automation configured"
}

setup_log_rotation() {
    log_step "Setting up log rotation..."

    cat > /etc/logrotate.d/deskmate << 'EOF'
/var/log/deskmate/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 deskmate deskmate
    postrotate
        systemctl reload deskmate || true
    endscript
}

/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        docker exec deskmate-nginx nginx -s reload || true
    endscript
}
EOF

    log_success "Log rotation configured"
}

install_monitoring_tools() {
    log_step "Installing monitoring tools..."

    # Install basic monitoring tools
    apt install -y htop iotop nethogs ncdu tree

    # Install Docker monitoring script
    cat > /usr/local/bin/deskmate-status.sh << 'EOF'
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
systemctl is-active nginx
echo ""

echo "=== Recent Logs ==="
journalctl -u deskmate --since "1 hour ago" --no-pager -n 5
EOF

    chmod +x /usr/local/bin/deskmate-status.sh

    log_success "Monitoring tools installed"
}

configure_firewall() {
    log_step "Configuring firewall..."

    if [[ -f "$SCRIPT_DIR/firewall-setup.sh" ]]; then
        bash "$SCRIPT_DIR/firewall-setup.sh" setup
        log_success "Firewall configured"
    else
        log_warning "Firewall setup script not found, skipping firewall configuration"
        log_info "Please run firewall-setup.sh manually after installation"
    fi
}

setup_ssl() {
    log_step "Setting up SSL certificates..."

    if [[ -f "$SCRIPT_DIR/ssl-setup.sh" ]]; then
        # Source environment for domain name
        if [[ -f "$DESKMATE_HOME/deskmate/deployment/production/.env.prod" ]]; then
            source "$DESKMATE_HOME/deskmate/deployment/production/.env.prod"
        fi

        if [[ -n "${DOMAIN_NAME:-}" ]]; then
            bash "$SCRIPT_DIR/ssl-setup.sh" letsencrypt
            log_success "SSL certificates configured"
        else
            log_warning "No domain name configured, setting up self-signed certificates"
            bash "$SCRIPT_DIR/ssl-setup.sh" self-signed
        fi
    else
        log_warning "SSL setup script not found, skipping SSL configuration"
        log_info "Please run ssl-setup.sh manually after installation"
    fi
}

start_services() {
    log_step "Starting DeskMate services..."

    # Start the service
    systemctl start deskmate

    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30

    # Check if services are running
    if docker ps | grep -q deskmate; then
        log_success "DeskMate services started successfully"
    else
        log_error "Failed to start DeskMate services"
        log_info "Check logs with: journalctl -u deskmate -f"
        exit 1
    fi
}

show_completion_info() {
    log_success "DeskMate installation completed successfully!"
    echo ""
    echo "=================================================="
    echo "🎉 DeskMate Production Installation Complete! 🎉"
    echo "=================================================="
    echo ""
    echo "📁 Installation Directory: $DESKMATE_HOME"
    echo "👤 Service User: $DESKMATE_USER"
    echo "🔧 Configuration: $DESKMATE_HOME/deskmate/deployment/production/.env.prod"
    echo ""
    echo "🌐 Web Access:"
    if [[ -n "${DOMAIN_NAME:-}" ]]; then
        echo "   https://$DOMAIN_NAME"
    else
        echo "   https://$(hostname -I | awk '{print $1}')"
    fi
    echo ""
    echo "🔍 Useful Commands:"
    echo "   Status:     deskmate-status.sh"
    echo "   Logs:       journalctl -u deskmate -f"
    echo "   Restart:    systemctl restart deskmate"
    echo "   Backup:     deskmate-backup.sh"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Review configuration: $DESKMATE_HOME/deskmate/deployment/production/.env.prod"
    echo "2. Add your API keys (Nano-GPT, SMTP settings)"
    echo "3. Configure your domain's DNS to point to this server"
    echo "4. Test the application and SSL certificates"
    echo ""
    echo "📖 Documentation:"
    echo "   Deployment Guide: $DESKMATE_HOME/deskmate/deployment/ubuntu-deployment.md"
    echo ""
    echo "🚨 Security Reminders:"
    echo "   - Firewall is configured and active"
    echo "   - Change default passwords in .env.prod"
    echo "   - Enable SSH key authentication"
    echo "   - Review backup configuration"
    echo ""
    echo "=================================================="
}

main() {
    echo -e "${PURPLE}"
    echo "======================================="
    echo "🚀 DeskMate Production Installation 🚀"
    echo "======================================="
    echo -e "${NC}"

    # Initialize log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    log_info "Starting DeskMate production installation..."
    log_info "Installation log: $LOG_FILE"

    check_root
    check_ubuntu_version

    # Run installation steps
    update_system
    install_docker
    create_deskmate_user
    clone_repository
    setup_environment
    setup_systemd_service
    setup_backup_script
    setup_log_rotation
    install_monitoring_tools
    configure_firewall
    setup_ssl
    start_services

    show_completion_info
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"