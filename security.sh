#!/bin/bash

# MoonVPN Security Management
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

# Function to perform security audit
perform_audit() {
    print_persian "انجام بررسی امنیتی..."
    
    # Check system updates
    print_persian "بررسی بروزرسانی‌های سیستم..."
    apt-get update
    apt-get upgrade -s | grep -i "security"
    
    # Check Docker security
    print_persian "بررسی امنیت Docker..."
    docker info | grep -i "security"
    
    # Check SSL certificates
    print_persian "بررسی گواهینامه‌های SSL..."
    if [ -f "/etc/letsencrypt/live/*/fullchain.pem" ]; then
        for cert in /etc/letsencrypt/live/*/fullchain.pem; do
            echo "گواهینامه: $cert"
            openssl x509 -in "$cert" -noout -dates
        done
    else
        print_warning "هیچ گواهینامه SSL یافت نشد"
    fi
    
    # Check firewall rules
    print_persian "بررسی قوانین فایروال..."
    if command -v ufw &> /dev/null; then
        ufw status
    else
        print_warning "فایروال UFW نصب نشده است"
    fi
    
    # Check file permissions
    print_persian "بررسی مجوزهای فایل‌ها..."
    find . -type f -perm -o+w -ls
    find . -type d -perm -o+w -ls
    
    # Check environment variables
    print_persian "بررسی متغیرهای محیطی..."
    if [ -f ".env" ]; then
        grep -v '^#' .env | grep -v '^$'
    else
        print_warning "فایل .env یافت نشد"
    fi
    
    # Check running services
    print_persian "بررسی سرویس‌های در حال اجرا..."
    docker-compose ps
    
    # Check logs for security issues
    print_persian "بررسی لاگ‌ها برای مشکلات امنیتی..."
    docker-compose logs | grep -i "error\|warning\|fail\|security"
}

# Function to update security
update_security() {
    print_persian "بروزرسانی امنیتی..."
    
    # Update system packages
    print_persian "بروزرسانی بسته‌های سیستم..."
    apt-get update
    apt-get upgrade -y
    
    # Update Docker images
    print_persian "بروزرسانی تصاویر Docker..."
    docker-compose pull
    
    # Update application dependencies
    print_persian "بروزرسانی وابستگی‌های برنامه..."
    docker-compose run --rm app pip install -r requirements.txt --upgrade
    
    # Restart services
    print_persian "راه‌اندازی مجدد سرویس‌ها..."
    docker-compose restart
    
    print_success "بروزرسانی امنیتی با موفقیت انجام شد"
}

# Function to generate security report
generate_report() {
    print_persian "تولید گزارش امنیتی..."
    
    # Create report directory
    REPORT_DIR="reports/security"
    mkdir -p "$REPORT_DIR"
    
    # Generate report filename
    REPORT_FILE="$REPORT_DIR/security_report_$(date +%Y%m%d_%H%M%S).txt"
    
    # Generate report
    {
        echo "گزارش امنیتی MoonVPN"
        echo "تاریخ: $(date)"
        echo "----------------------------------------"
        echo
        
        echo "1. وضعیت سیستم"
        echo "----------------------------------------"
        uname -a
        echo
        
        echo "2. بروزرسانی‌های سیستم"
        echo "----------------------------------------"
        apt-get update
        apt-get upgrade -s | grep -i "security"
        echo
        
        echo "3. وضعیت Docker"
        echo "----------------------------------------"
        docker info | grep -i "security"
        echo
        
        echo "4. وضعیت SSL"
        echo "----------------------------------------"
        if [ -f "/etc/letsencrypt/live/*/fullchain.pem" ]; then
            for cert in /etc/letsencrypt/live/*/fullchain.pem; do
                echo "گواهینامه: $cert"
                openssl x509 -in "$cert" -noout -dates
            done
        else
            echo "هیچ گواهینامه SSL یافت نشد"
        fi
        echo
        
        echo "5. وضعیت فایروال"
        echo "----------------------------------------"
        if command -v ufw &> /dev/null; then
            ufw status
        else
            echo "فایروال UFW نصب نشده است"
        fi
        echo
        
        echo "6. مجوزهای فایل‌ها"
        echo "----------------------------------------"
        find . -type f -perm -o+w -ls
        find . -type d -perm -o+w -ls
        echo
        
        echo "7. متغیرهای محیطی"
        echo "----------------------------------------"
        if [ -f ".env" ]; then
            grep -v '^#' .env | grep -v '^$'
        else
            echo "فایل .env یافت نشد"
        fi
        echo
        
        echo "8. سرویس‌های در حال اجرا"
        echo "----------------------------------------"
        docker-compose ps
        echo
        
        echo "9. لاگ‌های امنیتی"
        echo "----------------------------------------"
        docker-compose logs | grep -i "error\|warning\|fail\|security"
        
    } > "$REPORT_FILE"
    
    print_success "گزارش امنیتی با موفقیت تولید شد: $REPORT_FILE"
}

# Main command handler
case "$1" in
    "audit")
        perform_audit
        ;;
    "update")
        update_security
        ;;
    "report")
        generate_report
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {audit|update|report}"
        exit 1
        ;;
esac 