#!/bin/bash

# MoonVPN SSL Management
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

# Function to check if certbot is installed
check_certbot() {
    if ! command -v certbot &> /dev/null; then
        print_persian "نصب Certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi
}

# Function to install SSL certificate
install_ssl() {
    print_persian "نصب گواهینامه SSL..."
    
    # Check if domain is set
    if [ -z "$DOMAIN" ]; then
        print_error "دامنه تنظیم نشده است. لطفاً در فایل .env تنظیم کنید"
        exit 1
    fi
    
    # Check if certbot is installed
    check_certbot
    
    # Stop nginx
    print_persian "توقف Nginx..."
    docker-compose stop nginx
    
    # Install certificate
    print_persian "درخواست گواهینامه..."
    certbot certonly --standalone \
        --preferred-challenges http \
        --agree-tos \
        --email admin@$DOMAIN \
        -d $DOMAIN \
        -d www.$DOMAIN
    
    # Start nginx
    print_persian "راه‌اندازی مجدد Nginx..."
    docker-compose start nginx
    
    # Check if certificate was installed
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        print_success "گواهینامه با موفقیت نصب شد"
    else
        print_error "خطا در نصب گواهینامه"
        exit 1
    fi
}

# Function to renew SSL certificate
renew_ssl() {
    print_persian "تمدید گواهینامه SSL..."
    
    # Check if certbot is installed
    check_certbot
    
    # Stop nginx
    print_persian "توقف Nginx..."
    docker-compose stop nginx
    
    # Renew certificate
    print_persian "تمدید گواهینامه..."
    certbot renew
    
    # Start nginx
    print_persian "راه‌اندازی مجدد Nginx..."
    docker-compose start nginx
    
    print_success "گواهینامه با موفقیت تمدید شد"
}

# Function to check SSL certificate status
check_ssl_status() {
    print_persian "وضعیت گواهینامه SSL..."
    
    # Check if domain is set
    if [ -z "$DOMAIN" ]; then
        print_error "دامنه تنظیم نشده است. لطفاً در فایل .env تنظیم کنید"
        exit 1
    fi
    
    # Check if certificate exists
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        print_success "گواهینامه نصب شده است"
        
        # Get certificate expiration date
        EXPIRY=$(openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -noout -dates | grep "notAfter" | cut -d= -f2)
        print_persian "تاریخ انقضا: $EXPIRY"
        
        # Check if certificate is valid
        if openssl x509 -checkend 2592000 -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem"; then
            print_success "گواهینامه معتبر است"
        else
            print_warning "گواهینامه کمتر از 30 روز تا انقضا دارد"
        fi
    else
        print_warning "گواهینامه نصب نشده است"
    fi
}

# Main command handler
case "$1" in
    "install")
        install_ssl
        ;;
    "renew")
        renew_ssl
        ;;
    "status")
        check_ssl_status
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {install|renew|status}"
        exit 1
        ;;
esac 