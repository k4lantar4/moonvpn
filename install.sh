#!/bin/bash

# MoonVPN Installation Script
# Version: 1.0.0
# Author: MoonVPN Team
# License: Proprietary

# Color definitions for Persian text
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Unicode support for Persian text
export LANG=fa_IR.UTF-8
export LC_ALL=fa_IR.UTF-8

# Function to print Persian text
print_persian() {
    echo -e "${BLUE}$1${NC}"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Function to check system requirements
check_system_requirements() {
    print_persian "بررسی نیازمندی‌های سیستم..."
    
    # Check OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        print_error "سیستم عامل پشتیبانی نمی‌شود"
        exit 1
    fi
    
    # Check Python version
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
            print_error "نیاز به Python 3.8 یا بالاتر"
            exit 1
        fi
    else
        print_error "Python 3.8 یا بالاتر یافت نشد"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &>/dev/null; then
        print_error "Docker یافت نشد"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &>/dev/null; then
        print_error "Docker Compose یافت نشد"
        exit 1
    fi
    
    print_success "بررسی نیازمندی‌های سیستم با موفقیت انجام شد"
}

# Function to check network connectivity
check_network() {
    print_persian "بررسی اتصال به شبکه..."
    
    if ! ping -c 1 google.com &>/dev/null; then
        print_error "اتصال به اینترنت برقرار نیست"
        exit 1
    fi
    
    print_success "اتصال به شبکه برقرار است"
}

# Function to install dependencies
install_dependencies() {
    print_persian "نصب وابستگی‌ها..."
    
    # Update system packages
    apt-get update
    
    # Install required packages
    apt-get install -y \
        python3-pip \
        python3-venv \
        git \
        curl \
        wget \
        nginx \
        certbot \
        python3-certbot-nginx
    
    # Install Python packages
    pip3 install -r requirements.txt
    
    print_success "نصب وابستگی‌ها با موفقیت انجام شد"
}

# Function to configure environment
configure_environment() {
    print_persian "پیکربندی محیط..."
    
    # Create .env file if not exists
    if [ ! -f .env ]; then
        cp .env.example .env
        print_warning "فایل .env ایجاد شد. لطفاً تنظیمات را بررسی کنید"
    fi
    
    # Create necessary directories
    mkdir -p logs data/backups
    
    print_success "پیکربندی محیط با موفقیت انجام شد"
}

# Function to setup Docker
setup_docker() {
    print_persian "راه‌اندازی Docker..."
    
    # Start Docker service
    systemctl start docker
    systemctl enable docker
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    print_success "راه‌اندازی Docker با موفقیت انجام شد"
}

# Function to setup SSL
setup_ssl() {
    print_persian "راه‌اندازی SSL..."
    
    # Get domain from .env file
    DOMAIN=$(grep DOMAIN .env | cut -d '=' -f2)
    
    if [ -n "$DOMAIN" ]; then
        # Install SSL certificate
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
        print_success "گواهینامه SSL با موفقیت نصب شد"
    else
        print_warning "دامنه تنظیم نشده است. SSL نصب نشد"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    print_persian "راه‌اندازی سیستم نظارت..."
    
    # Start monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d
    
    print_success "سیستم نظارت با موفقیت راه‌اندازی شد"
}

# Function to setup backup
setup_backup() {
    print_persian "راه‌اندازی سیستم پشتیبان‌گیری..."
    
    # Create backup directory
    mkdir -p /var/backups/moonvpn
    
    # Add backup cron job
    (crontab -l 2>/dev/null; echo "0 0 * * * /usr/local/bin/moonvpn backup create") | crontab -
    
    print_success "سیستم پشتیبان‌گیری با موفقیت راه‌اندازی شد"
}

# Main installation function
main() {
    print_persian "شروع نصب MoonVPN..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "لطفاً با دسترسی root اجرا کنید"
        exit 1
    fi
    
    # Run installation steps
    check_system_requirements
    check_network
    install_dependencies
    configure_environment
    setup_docker
    setup_ssl
    setup_monitoring
    setup_backup
    
    print_success "نصب MoonVPN با موفقیت به پایان رسید"
    print_persian "برای شروع استفاده، لطفاً دستور 'moonvpn status' را اجرا کنید"
}

# Run main function
main 