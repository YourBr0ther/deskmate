#!/bin/bash

# Phase 12A: Production Infrastructure & Deployment Test Script
# This script tests all Phase 12A components and deployment configurations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_RESULTS=()
DEPLOYMENT_DIR="$SCRIPT_DIR/deployment"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TEST_RESULTS+=("PASS: $1")
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    TEST_RESULTS+=("WARN: $1")
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    TEST_RESULTS+=("FAIL: $1")
}

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

# Test functions
test_directory_structure() {
    log_test "Testing deployment directory structure..."

    local required_dirs=(
        "deployment/production"
        "deployment/monitoring"
    )

    local required_files=(
        "deployment/production/docker-compose.prod.yml"
        "deployment/production/nginx.prod.conf"
        "deployment/production/.env.prod.example"
        "deployment/production/ssl-setup.sh"
        "deployment/production/firewall-setup.sh"
        "deployment/production/install.sh"
        "deployment/ubuntu-deployment.md"
        "deployment/monitoring/Dockerfile"
        "deployment/monitoring/monitor.py"
        "deployment/monitoring/simple_alerting.py"
        "deployment/monitoring/docker-compose.monitoring.yml"
        "deployment/monitoring/prometheus.yml"
        "deployment/monitoring/alertmanager.yml"
        "deployment/monitoring/alert_rules.yml"
        "backend/Dockerfile.prod"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "$SCRIPT_DIR/$dir" ]]; then
            log_success "Directory exists: $dir"
        else
            log_error "Missing directory: $dir"
        fi
    done

    for file in "${required_files[@]}"; do
        if [[ -f "$SCRIPT_DIR/$file" ]]; then
            log_success "File exists: $file"
        else
            log_error "Missing file: $file"
        fi
    done
}

test_docker_compose_syntax() {
    log_test "Testing Docker Compose file syntax..."

    local compose_files=(
        "deployment/production/docker-compose.prod.yml"
        "deployment/monitoring/docker-compose.monitoring.yml"
        "docker-compose.yml"
    )

    for file in "${compose_files[@]}"; do
        if [[ -f "$SCRIPT_DIR/$file" ]]; then
            # Basic syntax check - look for required elements
            if grep -q "^version:" "$SCRIPT_DIR/$file" && grep -q "^services:" "$SCRIPT_DIR/$file"; then
                log_success "Basic Docker Compose syntax OK: $file"
            else
                log_error "Invalid Docker Compose structure: $file"
            fi
        else
            log_warning "Compose file not found: $file"
        fi
    done
}

test_dockerfile_syntax() {
    log_test "Testing Dockerfile syntax..."

    local dockerfiles=(
        "backend/Dockerfile"
        "backend/Dockerfile.prod"
        "frontend/Dockerfile"
        "deployment/monitoring/Dockerfile"
    )

    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$SCRIPT_DIR/$dockerfile" ]]; then
            # Simple syntax check using docker build --dry-run (if available)
            if docker build --help | grep -q "dry-run" 2>/dev/null; then
                if docker build --dry-run -f "$SCRIPT_DIR/$dockerfile" "$SCRIPT_DIR/$(dirname $dockerfile)" > /dev/null 2>&1; then
                    log_success "Valid Dockerfile syntax: $dockerfile"
                else
                    log_error "Invalid Dockerfile syntax: $dockerfile"
                fi
            else
                # Basic syntax validation
                if grep -q "FROM" "$SCRIPT_DIR/$dockerfile" && ! grep -q "^#.*syntax error" "$SCRIPT_DIR/$dockerfile"; then
                    log_success "Basic Dockerfile syntax OK: $dockerfile"
                else
                    log_error "Dockerfile syntax issues: $dockerfile"
                fi
            fi
        else
            log_warning "Dockerfile not found: $dockerfile"
        fi
    done
}

test_script_permissions() {
    log_test "Testing script permissions..."

    local scripts=(
        "deployment/production/ssl-setup.sh"
        "deployment/production/firewall-setup.sh"
        "deployment/production/install.sh"
        "deployment/monitoring/simple_alerting.py"
    )

    for script in "${scripts[@]}"; do
        if [[ -f "$SCRIPT_DIR/$script" ]]; then
            if [[ -x "$SCRIPT_DIR/$script" ]]; then
                log_success "Script is executable: $script"
            else
                log_error "Script not executable: $script"
            fi
        else
            log_warning "Script not found: $script"
        fi
    done
}

test_environment_template() {
    log_test "Testing environment template..."

    local env_file="$SCRIPT_DIR/deployment/production/.env.prod.example"

    if [[ -f "$env_file" ]]; then
        # Check for required variables
        local required_vars=(
            "DOMAIN_NAME"
            "POSTGRES_PASSWORD"
            "NANO_GPT_API_KEY"
            "SMTP_HOST"
            "ALERT_EMAIL"
            "ENVIRONMENT"
        )

        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" "$env_file"; then
                log_success "Environment variable present: $var"
            else
                log_error "Missing environment variable: $var"
            fi
        done

        # Check for placeholder values that need to be replaced
        local placeholders=(
            "your-domain.com"
            "your_nano_gpt_api_key_here"
            "your_secure_postgres_password_here"
        )

        for placeholder in "${placeholders[@]}"; do
            if grep -q "$placeholder" "$env_file"; then
                log_success "Placeholder present (needs replacement): $placeholder"
            else
                log_warning "Placeholder not found: $placeholder"
            fi
        done
    else
        log_error "Environment template not found"
    fi
}

test_nginx_configuration() {
    log_test "Testing nginx configuration..."

    local nginx_config="$SCRIPT_DIR/deployment/production/nginx.prod.conf"

    if [[ -f "$nginx_config" ]]; then
        # Check for required nginx directives
        local required_directives=(
            "listen 443 ssl"
            "ssl_certificate"
            "proxy_pass.*backend"
            "location /api/"
            "location /ws"
        )

        for directive in "${required_directives[@]}"; do
            if grep -q "$directive" "$nginx_config"; then
                log_success "Nginx directive present: $directive"
            else
                log_error "Missing nginx directive: $directive"
            fi
        done

        # Check for security headers
        local security_headers=(
            "X-Frame-Options"
            "X-Content-Type-Options"
            "X-XSS-Protection"
            "Strict-Transport-Security"
        )

        for header in "${security_headers[@]}"; do
            if grep -q "$header" "$nginx_config"; then
                log_success "Security header configured: $header"
            else
                log_warning "Security header missing: $header"
            fi
        done
    else
        log_error "Nginx production config not found"
    fi
}

test_ssl_setup_script() {
    log_test "Testing SSL setup script functionality..."

    local ssl_script="$SCRIPT_DIR/deployment/production/ssl-setup.sh"

    if [[ -f "$ssl_script" ]]; then
        # Test script help/usage
        if "$ssl_script" 2>&1 | grep -q "Usage:"; then
            log_success "SSL setup script shows usage information"
        else
            log_warning "SSL setup script usage information unclear"
        fi

        # Check for required functions
        local required_functions=(
            "check_domain"
            "install_certbot"
            "generate_self_signed_cert"
            "obtain_letsencrypt_cert"
        )

        for func in "${required_functions[@]}"; do
            if grep -q "^$func()" "$ssl_script"; then
                log_success "SSL script function present: $func"
            else
                log_error "SSL script function missing: $func"
            fi
        done
    else
        log_error "SSL setup script not found"
    fi
}

test_firewall_setup_script() {
    log_test "Testing firewall setup script functionality..."

    local fw_script="$SCRIPT_DIR/deployment/production/firewall-setup.sh"

    if [[ -f "$fw_script" ]]; then
        # Check for required functions
        local required_functions=(
            "install_ufw"
            "configure_ssh_access"
            "configure_web_access"
            "configure_fail2ban_integration"
        )

        for func in "${required_functions[@]}"; do
            if grep -q "^$func()" "$fw_script"; then
                log_success "Firewall script function present: $func"
            else
                log_error "Firewall script function missing: $func"
            fi
        done

        # Check for important security configurations
        if grep -q "ufw allow.*SSH_PORT" "$fw_script" || grep -q "ufw allow.*ssh" "$fw_script"; then
            log_success "SSH access configuration found"
        else
            log_error "SSH access configuration missing"
        fi

        if grep -q "ufw allow 80" "$fw_script" && grep -q "ufw allow 443" "$fw_script"; then
            log_success "Web access configuration found"
        else
            log_error "Web access configuration missing"
        fi
    else
        log_error "Firewall setup script not found"
    fi
}

test_installation_script() {
    log_test "Testing installation script functionality..."

    local install_script="$SCRIPT_DIR/deployment/production/install.sh"

    if [[ -f "$install_script" ]]; then
        # Check for required functions
        local required_functions=(
            "install_docker"
            "create_deskmate_user"
            "clone_repository"
            "setup_systemd_service"
            "setup_backup_script"
        )

        for func in "${required_functions[@]}"; do
            if grep -q "^$func()" "$install_script"; then
                log_success "Install script function present: $func"
            else
                log_error "Install script function missing: $func"
            fi
        done

        # Check for safety measures
        if grep -q "check_root" "$install_script"; then
            log_success "Root check present in install script"
        else
            log_error "Root check missing in install script"
        fi

        if grep -q "check_ubuntu_version" "$install_script"; then
            log_success "Ubuntu version check present"
        else
            log_warning "Ubuntu version check missing"
        fi
    else
        log_error "Installation script not found"
    fi
}

test_monitoring_infrastructure() {
    log_test "Testing monitoring infrastructure..."

    # Check monitoring Docker Compose
    local monitoring_compose="$SCRIPT_DIR/deployment/monitoring/docker-compose.monitoring.yml"
    if [[ -f "$monitoring_compose" ]]; then
        local monitoring_services=(
            "prometheus"
            "grafana"
            "node-exporter"
            "cadvisor"
            "alertmanager"
        )

        for service in "${monitoring_services[@]}"; do
            if grep -q "^  $service:" "$monitoring_compose"; then
                log_success "Monitoring service defined: $service"
            else
                log_error "Monitoring service missing: $service"
            fi
        done
    else
        log_error "Monitoring Docker Compose not found"
    fi

    # Check Prometheus configuration
    local prometheus_config="$SCRIPT_DIR/deployment/monitoring/prometheus.yml"
    if [[ -f "$prometheus_config" ]]; then
        if grep -q "job_name.*deskmate" "$prometheus_config"; then
            log_success "DeskMate jobs configured in Prometheus"
        else
            log_error "DeskMate jobs missing from Prometheus config"
        fi
    else
        log_error "Prometheus configuration not found"
    fi

    # Check alert rules
    local alert_rules="$SCRIPT_DIR/deployment/monitoring/alert_rules.yml"
    if [[ -f "$alert_rules" ]]; then
        local required_alerts=(
            "HighCPUUsage"
            "HighMemoryUsage"
            "LowDiskSpace"
            "ServiceDown"
        )

        for alert in "${required_alerts[@]}"; do
            if grep -q "alert: $alert" "$alert_rules"; then
                log_success "Alert rule defined: $alert"
            else
                log_error "Alert rule missing: $alert"
            fi
        done
    else
        log_error "Alert rules not found"
    fi
}

test_backend_health_endpoints() {
    log_test "Testing enhanced health check system..."

    local health_file="$SCRIPT_DIR/backend/app/api/health.py"
    if [[ -f "$health_file" ]]; then
        # Check for enhanced endpoints
        local health_endpoints=(
            "/health"
            "/health/detailed"
            "/health/live"
            "/health/ready"
        )

        for endpoint in "${health_endpoints[@]}"; do
            if grep -q "\"$endpoint\"" "$health_file"; then
                log_success "Health endpoint defined: $endpoint"
            else
                log_error "Health endpoint missing: $endpoint"
            fi
        done

        # Check for system metrics
        if grep -q "psutil" "$health_file"; then
            log_success "System metrics collection implemented"
        else
            log_error "System metrics collection missing"
        fi

        # Check requirements.txt for psutil
        local requirements="$SCRIPT_DIR/backend/requirements.txt"
        if [[ -f "$requirements" ]] && grep -q "psutil" "$requirements"; then
            log_success "psutil dependency added to requirements"
        else
            log_error "psutil dependency missing from requirements"
        fi
    else
        log_error "Health check module not found"
    fi
}

test_production_optimizations() {
    log_test "Testing production optimizations..."

    # Check production Dockerfile optimizations
    local prod_dockerfile="$SCRIPT_DIR/backend/Dockerfile.prod"
    if [[ -f "$prod_dockerfile" ]]; then
        if grep -q "multi-stage" "$prod_dockerfile" || grep -q "FROM.*as builder" "$prod_dockerfile"; then
            log_success "Multi-stage build configured"
        else
            log_error "Multi-stage build not configured"
        fi

        if grep -q "useradd.*deskmate" "$prod_dockerfile"; then
            log_success "Non-root user configured in production Dockerfile"
        else
            log_error "Non-root user not configured"
        fi

        if grep -q "HEALTHCHECK" "$prod_dockerfile"; then
            log_success "Health check configured in Dockerfile"
        else
            log_warning "Health check missing from Dockerfile"
        fi
    else
        log_error "Production Dockerfile not found"
    fi

    # Check production Docker Compose optimizations
    local prod_compose="$SCRIPT_DIR/deployment/production/docker-compose.prod.yml"
    if [[ -f "$prod_compose" ]]; then
        if grep -q "restart: unless-stopped" "$prod_compose"; then
            log_success "Restart policy configured"
        else
            log_error "Restart policy not configured"
        fi

        if grep -q "deploy:" "$prod_compose" && grep -q "limits:" "$prod_compose"; then
            log_success "Resource limits configured"
        else
            log_warning "Resource limits not configured"
        fi

        if grep -q "healthcheck:" "$prod_compose"; then
            log_success "Health checks configured in compose"
        else
            log_warning "Health checks missing from compose"
        fi
    else
        log_error "Production Docker Compose not found"
    fi
}

test_security_configurations() {
    log_test "Testing security configurations..."

    # Check environment template for security settings
    local env_template="$SCRIPT_DIR/deployment/production/.env.prod.example"
    if [[ -f "$env_template" ]]; then
        if grep -q "SECRET_KEY" "$env_template"; then
            log_success "Secret key configuration present"
        else
            log_error "Secret key configuration missing"
        fi

        if grep -q "DEBUG=false" "$env_template"; then
            log_success "Debug mode disabled in production"
        else
            log_error "Debug mode not properly configured"
        fi

        if grep -q "ENVIRONMENT=production" "$env_template"; then
            log_success "Production environment specified"
        else
            log_error "Production environment not specified"
        fi
    fi

    # Check nginx security configurations
    local nginx_config="$SCRIPT_DIR/deployment/production/nginx.prod.conf"
    if [[ -f "$nginx_config" ]]; then
        if grep -q "limit_req_zone" "$nginx_config"; then
            log_success "Rate limiting configured"
        else
            log_warning "Rate limiting not configured"
        fi

        if grep -q "ssl_protocols.*TLSv1.3" "$nginx_config"; then
            log_success "Modern TLS protocols configured"
        else
            log_warning "TLS configuration should be reviewed"
        fi
    fi
}

test_documentation_completeness() {
    log_test "Testing documentation completeness..."

    local deployment_guide="$SCRIPT_DIR/deployment/ubuntu-deployment.md"
    if [[ -f "$deployment_guide" ]]; then
        # Check for required sections
        local required_sections=(
            "System Requirements"
            "Docker Installation"
            "SSL Certificate Setup"
            "Firewall Configuration"
            "Troubleshooting"
            "Security Best Practices"
        )

        for section in "${required_sections[@]}"; do
            if grep -q "$section" "$deployment_guide"; then
                log_success "Documentation section present: $section"
            else
                log_error "Documentation section missing: $section"
            fi
        done

        # Check for command examples
        if grep -q '```bash' "$deployment_guide"; then
            log_success "Command examples present in documentation"
        else
            log_warning "Command examples missing from documentation"
        fi
    else
        log_error "Deployment guide not found"
    fi
}

generate_test_report() {
    log_info "Generating test report..."

    echo ""
    echo "======================================="
    echo "Phase 12A Deployment Test Report"
    echo "======================================="
    echo "Date: $(date)"
    echo "Total Tests: ${#TEST_RESULTS[@]}"
    echo ""

    local pass_count=0
    local fail_count=0
    local warn_count=0

    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == PASS:* ]]; then
            ((pass_count++))
            echo -e "${GREEN}✓${NC} ${result#PASS: }"
        elif [[ $result == FAIL:* ]]; then
            ((fail_count++))
            echo -e "${RED}✗${NC} ${result#FAIL: }"
        elif [[ $result == WARN:* ]]; then
            ((warn_count++))
            echo -e "${YELLOW}⚠${NC} ${result#WARN: }"
        fi
    done

    echo ""
    echo "======================================="
    echo -e "Results: ${GREEN}$pass_count passed${NC}, ${RED}$fail_count failed${NC}, ${YELLOW}$warn_count warnings${NC}"
    echo "======================================="

    if [[ $fail_count -eq 0 ]]; then
        echo -e "${GREEN}🎉 All critical tests passed! Phase 12A is ready for deployment.${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Please review the issues above before deploying.${NC}"
        return 1
    fi
}

main() {
    echo -e "${PURPLE}"
    echo "======================================="
    echo "🚀 Phase 12A Deployment Test Suite 🚀"
    echo "======================================="
    echo -e "${NC}"

    log_info "Testing Phase 12A: Production Infrastructure & Deployment"
    echo ""

    # Run all tests
    test_directory_structure
    test_docker_compose_syntax
    test_dockerfile_syntax
    test_script_permissions
    test_environment_template
    test_nginx_configuration
    test_ssl_setup_script
    test_firewall_setup_script
    test_installation_script
    test_monitoring_infrastructure
    test_backend_health_endpoints
    test_production_optimizations
    test_security_configurations
    test_documentation_completeness

    echo ""
    generate_test_report
}

# Run main function
main "$@"