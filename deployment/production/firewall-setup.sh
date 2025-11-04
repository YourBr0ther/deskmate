#!/bin/bash

# DeskMate Firewall Setup Script
# This script configures UFW (Uncomplicated Firewall) for DeskMate production deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

install_ufw() {
    log_info "Installing UFW (Uncomplicated Firewall)..."

    apt update
    apt install -y ufw

    log_success "UFW installed successfully"
}

configure_default_policies() {
    log_info "Configuring default firewall policies..."

    # Set default policies
    ufw --force default deny incoming
    ufw --force default allow outgoing
    ufw --force default deny forward

    log_success "Default policies configured (deny incoming, allow outgoing)"
}

configure_ssh_access() {
    log_info "Configuring SSH access..."

    # Get current SSH port (default is 22)
    SSH_PORT=$(grep -E '^#?Port ' /etc/ssh/sshd_config | awk '{print $2}' || echo "22")

    # Allow SSH access
    ufw allow "${SSH_PORT}/tcp" comment "SSH access"

    log_success "SSH access allowed on port $SSH_PORT"
    log_warning "Make sure you have SSH key authentication configured!"
}

configure_web_access() {
    log_info "Configuring web server access..."

    # Allow HTTP and HTTPS
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"

    log_success "Web server access configured (HTTP: 80, HTTPS: 443)"
}

configure_database_access() {
    log_info "Configuring database access restrictions..."

    # Deny external access to PostgreSQL
    ufw deny 5432/tcp comment "PostgreSQL - blocked externally"

    # Deny external access to Qdrant
    ufw deny 6333/tcp comment "Qdrant - blocked externally"

    log_success "Database ports secured (blocked from external access)"
}

configure_docker_integration() {
    log_info "Configuring UFW for Docker integration..."

    # Create UFW Docker integration rules
    cat > /etc/ufw/after.rules << 'EOF'
# Docker Integration Rules
*filter
:ufw-user-forward - [0:0]
:DOCKER-USER - [0:0]
-A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A DOCKER-USER -m conntrack --ctstate INVALID -j DROP
-A DOCKER-USER -i deskmate0 -o deskmate0 -j ACCEPT
-A DOCKER-USER -i deskmate0 ! -o deskmate0 -j ufw-user-forward
-A DOCKER-USER -i deskmate0 -o deskmate0 -j DROP
COMMIT
EOF

    log_success "Docker integration configured"
}

configure_rate_limiting() {
    log_info "Configuring rate limiting rules..."

    # Limit SSH connections
    ufw limit ssh comment "SSH rate limiting"

    # Custom rate limiting for HTTP/HTTPS (handled by nginx)
    log_info "HTTP/HTTPS rate limiting will be handled by nginx"

    log_success "Rate limiting configured"
}

configure_monitoring_ports() {
    log_info "Configuring monitoring access..."

    # Block external access to monitoring ports
    ufw deny 9090/tcp comment "Prometheus - blocked externally"
    ufw deny 3000/tcp comment "Grafana - blocked externally"

    # Allow specific IPs for monitoring if configured
    if [[ -n "${MONITORING_ALLOWED_IPS:-}" ]]; then
        IFS=',' read -ra IPS <<< "$MONITORING_ALLOWED_IPS"
        for ip in "${IPS[@]}"; do
            ufw allow from "$ip" to any port 9090 comment "Prometheus access from $ip"
            ufw allow from "$ip" to any port 3000 comment "Grafana access from $ip"
        done
        log_success "Monitoring access allowed for specified IPs"
    else
        log_info "No monitoring IPs specified, all external monitoring access blocked"
    fi
}

configure_fail2ban_integration() {
    log_info "Installing and configuring Fail2Ban..."

    apt install -y fail2ban

    # Create custom Fail2Ban configuration
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
EOF

    # Create nginx filter for Fail2Ban
    cat > /etc/fail2ban/filter.d/nginx-limit-req.conf << 'EOF'
[Definition]
failregex = limiting requests, excess: .* by zone .*, client: <HOST>
ignoreregex =
EOF

    systemctl enable fail2ban
    systemctl restart fail2ban

    log_success "Fail2Ban configured and started"
}

show_firewall_status() {
    log_info "Current firewall status:"
    echo "========================="
    ufw status verbose
    echo "========================="

    log_info "Active fail2ban jails:"
    fail2ban-client status 2>/dev/null || log_warning "Fail2Ban not running"
}

backup_existing_rules() {
    log_info "Backing up existing firewall rules..."

    mkdir -p /opt/deskmate/backups/firewall
    iptables-save > "/opt/deskmate/backups/firewall/iptables-backup-$(date +%Y%m%d-%H%M%S).rules"

    if command -v ufw &> /dev/null; then
        cp -r /etc/ufw "/opt/deskmate/backups/firewall/ufw-backup-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
    fi

    log_success "Firewall rules backed up"
}

enable_firewall() {
    log_info "Enabling UFW firewall..."

    # Enable UFW
    ufw --force enable

    # Enable on boot
    systemctl enable ufw

    log_success "UFW firewall enabled and will start on boot"
}

main() {
    log_info "DeskMate Firewall Setup Starting..."

    # Load environment variables if available
    if [[ -f "$(dirname "$0")/.env.prod" ]]; then
        source "$(dirname "$0")/.env.prod"
        log_info "Loaded production environment variables"
    fi

    check_root

    case "${1:-setup}" in
        "setup")
            log_info "Setting up complete firewall configuration..."
            backup_existing_rules
            install_ufw
            configure_default_policies
            configure_ssh_access
            configure_web_access
            configure_database_access
            configure_docker_integration
            configure_rate_limiting
            configure_monitoring_ports
            configure_fail2ban_integration
            enable_firewall
            show_firewall_status
            ;;
        "status")
            show_firewall_status
            ;;
        "reset")
            log_warning "Resetting firewall to defaults..."
            read -p "Are you sure? This will remove all custom rules (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ufw --force reset
                log_success "Firewall reset to defaults"
            else
                log_info "Reset cancelled"
            fi
            ;;
        "backup")
            backup_existing_rules
            ;;
        *)
            log_info "Usage: $0 [setup|status|reset|backup]"
            log_info ""
            log_info "Commands:"
            log_info "  setup   - Configure complete firewall (default)"
            log_info "  status  - Show current firewall status"
            log_info "  reset   - Reset firewall to defaults (DANGEROUS)"
            log_info "  backup  - Backup current firewall rules"
            log_info ""
            log_info "Environment variables (optional):"
            log_info "  MONITORING_ALLOWED_IPS - Comma-separated IPs for monitoring access"
            exit 1
            ;;
    esac

    log_success "Firewall configuration completed!"
    log_info "Important: Test SSH access before closing this session!"
    log_info "If locked out, use server console to run: ufw disable"
}

# Run main function with all arguments
main "$@"