#!/bin/bash

# MoonVPN Domain Management
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

# Domains configuration file
DOMAINS_FILE="/etc/moonvpn/domains.conf"

# Function to check if domains file exists
check_domains_file() {
    if [ ! -f "$DOMAINS_FILE" ]; then
        mkdir -p "$(dirname "$DOMAINS_FILE")"
        touch "$DOMAINS_FILE"
    fi
}

# Function to validate domain
validate_domain() {
    local domain="$1"
    
    # Basic domain validation
    if [[ ! "$domain" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$ ]]; then
        print_error "فرمت دامنه نامعتبر است"
        return 1
    fi
    
    return 0
}

# Function to add domain
add_domain() {
    if [ -z "$1" ]; then
        print_error "لطفاً نام دامنه را مشخص کنید"
        exit 1
    fi
    
    local domain="$1"
    
    # Validate domain
    if ! validate_domain "$domain"; then
        exit 1
    fi
    
    # Check if domain already exists
    if grep -q "^$domain$" "$DOMAINS_FILE"; then
        print_error "دامنه قبلاً ثبت شده است"
        exit 1
    fi
    
    # Add domain to file
    echo "$domain" >> "$DOMAINS_FILE"
    
    print_success "دامنه با موفقیت اضافه شد"
    
    # Check if SSL certificate exists
    if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        print_success "گواهینامه SSL برای دامنه موجود است"
    else
        print_warning "گواهینامه SSL برای دامنه موجود نیست. می‌توانید با دستور 'moonvpn ssl install' نصب کنید"
    fi
}

# Function to remove domain
remove_domain() {
    if [ -z "$1" ]; then
        print_error "لطفاً نام دامنه را مشخص کنید"
        exit 1
    fi
    
    local domain="$1"
    
    # Check if domain exists
    if ! grep -q "^$domain$" "$DOMAINS_FILE"; then
        print_error "دامنه یافت نشد"
        exit 1
    fi
    
    # Remove domain from file
    sed -i "/^$domain$/d" "$DOMAINS_FILE"
    
    print_success "دامنه با موفقیت حذف شد"
}

# Function to list domains
list_domains() {
    print_persian "لیست دامنه‌ها:"
    echo
    
    if [ ! -s "$DOMAINS_FILE" ]; then
        print_warning "هیچ دامنه‌ای ثبت نشده است"
        exit 0
    fi
    
    while IFS= read -r domain; do
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            echo "$domain (SSL فعال)"
        else
            echo "$domain (بدون SSL)"
        fi
    done < "$DOMAINS_FILE"
}

# Main command handler
case "$1" in
    "add")
        check_domains_file
        add_domain "$2"
        ;;
    "remove")
        check_domains_file
        remove_domain "$2"
        ;;
    "list")
        check_domains_file
        list_domains
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {add|remove|list}"
        exit 1
        ;;
esac 