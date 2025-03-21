#!/bin/bash

# MoonVPN Maintenance Management
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

# Function to perform system cleanup
perform_cleanup() {
    print_persian "انجام پاکسازی سیستم..."
    
    # Clean Docker resources
    print_persian "پاکسازی منابع Docker..."
    docker system prune -f
    
    # Clean old logs
    print_persian "پاکسازی لاگ‌های قدیمی..."
    find /var/log -type f -name "*.log" -mtime +30 -delete
    
    # Clean old backups
    print_persian "پاکسازی پشتیبان‌های قدیمی..."
    find /var/backups/moonvpn -type f -mtime +30 -delete
    
    # Clean temporary files
    print_persian "پاکسازی فایل‌های موقت..."
    rm -rf /tmp/moonvpn_*
    
    print_success "پاکسازی سیستم با موفقیت انجام شد"
}

# Function to optimize system
optimize_system() {
    print_persian "بهینه‌سازی سیستم..."
    
    # Optimize Docker
    print_persian "بهینه‌سازی Docker..."
    docker system prune -f
    docker volume prune -f
    
    # Optimize system resources
    print_persian "بهینه‌سازی منابع سیستم..."
    sync; echo 3 > /proc/sys/vm/drop_caches
    
    # Optimize database
    print_persian "بهینه‌سازی پایگاه داده..."
    docker-compose exec db psql -U postgres -c "VACUUM ANALYZE;"
    
    # Optimize Nginx
    print_persian "بهینه‌سازی Nginx..."
    docker-compose exec nginx nginx -t
    docker-compose exec nginx nginx -s reload
    
    print_success "بهینه‌سازی سیستم با موفقیت انجام شد"
}

# Function to check system health
check_health() {
    print_persian "بررسی سلامت سیستم..."
    
    # Check system resources
    print_persian "بررسی منابع سیستم..."
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | awk '{print $2}'
    echo "Memory Usage:"
    free -h
    echo "Disk Usage:"
    df -h
    
    # Check Docker services
    print_persian "بررسی سرویس‌های Docker..."
    docker-compose ps
    
    # Check service logs
    print_persian "بررسی لاگ‌های سرویس‌ها..."
    docker-compose logs --tail=100
    
    # Check network connectivity
    print_persian "بررسی اتصال شبکه..."
    ping -c 4 google.com
    
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
    
    # Check firewall status
    print_persian "بررسی وضعیت فایروال..."
    if command -v ufw &> /dev/null; then
        ufw status
    else
        print_warning "فایروال UFW نصب نشده است"
    fi
}

# Function to generate maintenance report
generate_report() {
    print_persian "تولید گزارش نگهداری..."
    
    # Create report directory
    REPORT_DIR="reports/maintenance"
    mkdir -p "$REPORT_DIR"
    
    # Generate report filename
    REPORT_FILE="$REPORT_DIR/maintenance_report_$(date +%Y%m%d_%H%M%S).txt"
    
    # Generate report
    {
        echo "گزارش نگهداری MoonVPN"
        echo "تاریخ: $(date)"
        echo "----------------------------------------"
        echo
        
        echo "1. وضعیت سیستم"
        echo "----------------------------------------"
        uname -a
        echo
        
        echo "2. منابع سیستم"
        echo "----------------------------------------"
        echo "CPU Usage:"
        top -bn1 | grep "Cpu(s)" | awk '{print $2}'
        echo "Memory Usage:"
        free -h
        echo "Disk Usage:"
        df -h
        echo
        
        echo "3. وضعیت Docker"
        echo "----------------------------------------"
        docker info
        echo
        
        echo "4. سرویس‌های در حال اجرا"
        echo "----------------------------------------"
        docker-compose ps
        echo
        
        echo "5. لاگ‌های سرویس‌ها"
        echo "----------------------------------------"
        docker-compose logs --tail=100
        echo
        
        echo "6. وضعیت شبکه"
        echo "----------------------------------------"
        ping -c 4 google.com
        echo
        
        echo "7. وضعیت SSL"
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
        
        echo "8. وضعیت فایروال"
        echo "----------------------------------------"
        if command -v ufw &> /dev/null; then
            ufw status
        else
            echo "فایروال UFW نصب نشده است"
        fi
        
    } > "$REPORT_FILE"
    
    print_success "گزارش نگهداری با موفقیت تولید شد: $REPORT_FILE"
}

# Main command handler
case "$1" in
    "cleanup")
        perform_cleanup
        ;;
    "optimize")
        optimize_system
        ;;
    "health")
        check_health
        ;;
    "report")
        generate_report
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {cleanup|optimize|health|report}"
        exit 1
        ;;
esac 