#!/bin/bash

# MoonVPN Backup Management
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

# Backup directory
BACKUP_DIR="/var/backups/moonvpn"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to create backup
create_backup() {
    print_persian "ایجاد پشتیبان..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Create backup filename
    BACKUP_FILE="$BACKUP_DIR/moonvpn_backup_$TIMESTAMP.tar.gz"
    
    # Stop services
    print_persian "توقف سرویس‌ها..."
    docker-compose down
    
    # Create backup
    print_persian "فشرده‌سازی فایل‌ها..."
    tar -czf "$BACKUP_FILE" \
        ./data \
        ./config \
        ./logs \
        .env \
        docker-compose.yml \
        moonvpn \
        install.sh \
        backup.sh
    
    # Start services
    print_persian "راه‌اندازی مجدد سرویس‌ها..."
    docker-compose up -d
    
    if [ -f "$BACKUP_FILE" ]; then
        print_success "پشتیبان با موفقیت ایجاد شد: $BACKUP_FILE"
    else
        print_error "خطا در ایجاد پشتیبان"
        exit 1
    fi
}

# Function to restore backup
restore_backup() {
    if [ -z "$1" ]; then
        print_error "لطفاً مسیر فایل پشتیبان را مشخص کنید"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "فایل پشتیبان یافت نشد: $BACKUP_FILE"
        exit 1
    fi
    
    print_persian "بازیابی از پشتیبان..."
    
    # Stop services
    print_persian "توقف سرویس‌ها..."
    docker-compose down
    
    # Restore backup
    print_persian "بازیابی فایل‌ها..."
    tar -xzf "$BACKUP_FILE" -C .
    
    # Start services
    print_persian "راه‌اندازی مجدد سرویس‌ها..."
    docker-compose up -d
    
    print_success "بازیابی با موفقیت انجام شد"
}

# Function to list backups
list_backups() {
    print_persian "لیست پشتیبان‌ها:"
    echo
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "دایرکتوری پشتیبان خالی است"
        exit 0
    fi
    
    ls -lh "$BACKUP_DIR" | grep "moonvpn_backup_" | awk '{print $9, "(" $5 ")"}'
}

# Function to delete backup
delete_backup() {
    if [ -z "$1" ]; then
        print_error "لطفاً نام فایل پشتیبان را مشخص کنید"
        exit 1
    fi
    
    BACKUP_FILE="$BACKUP_DIR/$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "فایل پشتیبان یافت نشد: $BACKUP_FILE"
        exit 1
    fi
    
    print_persian "حذف پشتیبان..."
    rm -f "$BACKUP_FILE"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_success "پشتیبان با موفقیت حذف شد"
    else
        print_error "خطا در حذف پشتیبان"
        exit 1
    fi
}

# Main command handler
case "$1" in
    "create")
        create_backup
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    "delete")
        delete_backup "$2"
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {create|restore|list|delete}"
        exit 1
        ;;
esac 