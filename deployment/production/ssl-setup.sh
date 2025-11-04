#!/bin/bash

# DeskMate SSL Setup Script
# This script sets up SSL certificates using Let's Encrypt for DeskMate production deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/ssl"
CERTBOT_DIR="/opt/certbot"

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

check_domain() {
    if [[ -z "${DOMAIN_NAME:-}" ]]; then
        log_error "DOMAIN_NAME environment variable is not set"
        log_info "Please set DOMAIN_NAME in your .env.prod file or export it"
        log_info "Example: export DOMAIN_NAME=your-domain.com"
        exit 1
    fi

    log_info "Checking domain DNS resolution for: $DOMAIN_NAME"
    if ! dig +short "$DOMAIN_NAME" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null; then
        log_warning "Domain $DOMAIN_NAME does not resolve to an IP address"
        log_warning "Make sure DNS is properly configured before proceeding"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

install_certbot() {
    log_info "Installing Certbot..."

    # Install snapd if not present
    if ! command -v snap &> /dev/null; then
        apt update
        apt install -y snapd
    fi

    # Install certbot via snap
    snap install core; snap refresh core
    snap install --classic certbot

    # Create symlink
    ln -sf /snap/bin/certbot /usr/local/bin/certbot

    log_success "Certbot installed successfully"
}

setup_directories() {
    log_info "Setting up SSL directories..."

    mkdir -p "$SSL_DIR"
    mkdir -p /var/www/certbot

    # Set proper permissions
    chmod 755 "$SSL_DIR"
    chmod 755 /var/www/certbot

    log_success "SSL directories created"
}

generate_self_signed_cert() {
    log_info "Generating self-signed certificate for initial setup..."

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN_NAME"

    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"

    log_success "Self-signed certificate generated"
}

obtain_letsencrypt_cert() {
    log_info "Obtaining Let's Encrypt certificate for $DOMAIN_NAME..."

    # Stop nginx if running
    if systemctl is-active --quiet nginx; then
        systemctl stop nginx
        NGINX_WAS_RUNNING=true
    fi

    # Obtain certificate using standalone mode
    certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email "admin@$DOMAIN_NAME" \
        --domains "$DOMAIN_NAME" \
        --keep-until-expiring

    if [[ $? -eq 0 ]]; then
        log_success "Let's Encrypt certificate obtained successfully"

        # Copy certificates to our SSL directory
        cp "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" "$SSL_DIR/cert.pem"
        cp "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" "$SSL_DIR/key.pem"

        # Set proper permissions
        chmod 600 "$SSL_DIR/key.pem"
        chmod 644 "$SSL_DIR/cert.pem"

        log_success "Certificates copied to $SSL_DIR"
    else
        log_error "Failed to obtain Let's Encrypt certificate"
        log_info "Using self-signed certificate as fallback"
        generate_self_signed_cert
    fi

    # Restart nginx if it was running
    if [[ "${NGINX_WAS_RUNNING:-false}" == "true" ]]; then
        systemctl start nginx
    fi
}

setup_renewal_cron() {
    log_info "Setting up automatic certificate renewal..."

    # Create renewal script
    cat > /usr/local/bin/deskmate-cert-renew.sh << 'EOF'
#!/bin/bash
/usr/local/bin/certbot renew --quiet --deploy-hook "docker-compose -f /opt/deskmate/deployment/production/docker-compose.prod.yml restart nginx"
EOF

    chmod +x /usr/local/bin/deskmate-cert-renew.sh

    # Add cron job for renewal (runs twice daily)
    echo "0 0,12 * * * root /usr/local/bin/deskmate-cert-renew.sh" > /etc/cron.d/deskmate-certbot-renewal
    chmod 644 /etc/cron.d/deskmate-certbot-renewal

    log_success "Automatic renewal configured"
}

verify_certificates() {
    log_info "Verifying SSL certificates..."

    if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
        # Check certificate validity
        if openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -q "Issuer.*Let's Encrypt"; then
            log_success "Valid Let's Encrypt certificate found"
        else
            log_warning "Self-signed certificate in use"
        fi

        # Check expiration
        EXPIRY=$(openssl x509 -in "$SSL_DIR/cert.pem" -noout -enddate | cut -d= -f2)
        log_info "Certificate expires: $EXPIRY"

        # Verify private key matches certificate
        CERT_HASH=$(openssl x509 -in "$SSL_DIR/cert.pem" -noout -modulus | openssl md5)
        KEY_HASH=$(openssl rsa -in "$SSL_DIR/key.pem" -noout -modulus | openssl md5)

        if [[ "$CERT_HASH" == "$KEY_HASH" ]]; then
            log_success "Certificate and private key match"
        else
            log_error "Certificate and private key do not match!"
            exit 1
        fi
    else
        log_error "SSL certificates not found!"
        exit 1
    fi
}

main() {
    log_info "DeskMate SSL Setup Starting..."

    # Load environment variables
    if [[ -f "${SCRIPT_DIR}/.env.prod" ]]; then
        source "${SCRIPT_DIR}/.env.prod"
        log_info "Loaded production environment variables"
    else
        log_warning "Production environment file not found: ${SCRIPT_DIR}/.env.prod"
        log_info "Make sure to create .env.prod with DOMAIN_NAME before running this script"
    fi

    check_root
    check_domain

    # Parse command line arguments
    case "${1:-}" in
        "self-signed")
            log_info "Generating self-signed certificates only..."
            setup_directories
            generate_self_signed_cert
            ;;
        "letsencrypt")
            log_info "Setting up Let's Encrypt certificates..."
            install_certbot
            setup_directories
            obtain_letsencrypt_cert
            setup_renewal_cron
            ;;
        "renew")
            log_info "Renewing certificates..."
            /usr/local/bin/deskmate-cert-renew.sh
            ;;
        "verify")
            log_info "Verifying existing certificates..."
            verify_certificates
            ;;
        *)
            log_info "Usage: $0 [self-signed|letsencrypt|renew|verify]"
            log_info ""
            log_info "Commands:"
            log_info "  self-signed  - Generate self-signed certificates for testing"
            log_info "  letsencrypt  - Obtain Let's Encrypt certificates (recommended)"
            log_info "  renew        - Manually renew certificates"
            log_info "  verify       - Verify existing certificates"
            log_info ""
            log_info "Environment variables required:"
            log_info "  DOMAIN_NAME  - Your domain name (e.g., deskmate.example.com)"
            exit 1
            ;;
    esac

    verify_certificates
    log_success "SSL setup completed successfully!"
    log_info "Certificates are located in: $SSL_DIR"
    log_info "You can now start the DeskMate production environment"
}

# Run main function with all arguments
main "$@"