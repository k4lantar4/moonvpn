#!/bin/bash

# MoonVPN Firewall Management
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

# Function to check if ufw is installed
check_ufw() {
    if ! command -v ufw &> /dev/null; then
        print_persian "نصب UFW..."
        apt-get update
        apt-get install -y ufw
    fi
}

# Function to enable firewall
enable_firewall() {
    print_persian "فعال‌سازی فایروال..."
    
    # Check if ufw is installed
    check_ufw
    
    # Enable UFW
    ufw --force enable
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP
    ufw allow http
    
    # Allow HTTPS
    ufw allow https
    
    # Allow VPN port
    ufw allow 1194/udp
    
    # Allow monitoring ports
    ufw allow 9090/tcp  # Prometheus
    ufw allow 3000/tcp  # Grafana
    
    print_success "فایروال با موفقیت فعال شد"
}

# Function to disable firewall
disable_firewall() {
    print_persian "غیرفعال‌سازی فایروال..."
    
    # Check if ufw is installed
    check_ufw
    
    # Disable UFW
    ufw --force disable
    
    print_success "فایروال با موفقیت غیرفعال شد"
}

# Function to manage firewall rules
manage_rules() {
    if [ -z "$1" ]; then
        print_error "لطفاً دستور را مشخص کنید"
        echo "دستورات موجود:"
        echo "  add <port> [protocol]    افزودن قانون"
        echo "  remove <port> [protocol] حذف قانون"
        echo "  list                     نمایش قوانین"
        exit 1
    fi
    
    case "$1" in
        "add")
            if [ -z "$2" ]; then
                print_error "لطفاً پورت را مشخص کنید"
                exit 1
            fi
            
            PORT="$2"
            PROTOCOL="${3:-tcp}"
            
            print_persian "افزودن قانون برای پورت $PORT/$PROTOCOL..."
            ufw allow "$PORT/$PROTOCOL"
            print_success "قانون با موفقیت افزوده شد"
            ;;
            
        "remove")
            if [ -z "$2" ]; then
                print_error "لطفاً پورت را مشخص کنید"
                exit 1
            fi
            
            PORT="$2"
            PROTOCOL="${3:-tcp}"
            
            print_persian "حذف قانون برای پورت $PORT/$PROTOCOL..."
            ufw delete allow "$PORT/$PROTOCOL"
            print_success "قانون با موفقیت حذف شد"
            ;;
            
        "list")
            print_persian "لیست قوانین فایروال:"
            ufw status numbered
            ;;
            
        *)
            print_error "دستور نامعتبر است"
            echo "دستورات موجود:"
            echo "  add <port> [protocol]    افزودن قانون"
            echo "  remove <port> [protocol] حذف قانون"
            echo "  list                     نمایش قوانین"
            exit 1
            ;;
    esac
}

# Function to check firewall status
check_status() {
    print_persian "وضعیت فایروال:"
    
    # Check if ufw is installed
    if ! command -v ufw &> /dev/null; then
        print_warning "UFW نصب نشده است"
        exit 0
    fi
    
    # Get UFW status
    UFW_STATUS=$(ufw status)
    
    # Check if UFW is active
    if echo "$UFW_STATUS" | grep -q "Status: active"; then
        print_success "فایروال فعال است"
    else
        print_warning "فایروال غیرفعال است"
    fi
    
    # Show rules
    echo
    print_persian "قوانین فعال:"
    echo "$UFW_STATUS" | grep -v "Status:"
}

# Main command handler
case "$1" in
    "enable")
        enable_firewall
        ;;
    "disable")
        disable_firewall
        ;;
    "rules")
        manage_rules "$2" "$3" "$4"
        ;;
    "status")
        check_status
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {enable|disable|rules|status}"
        exit 1
        ;;
esac 