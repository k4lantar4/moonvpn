#!/bin/bash

# MoonVPN Monitoring Management
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

# Function to show metrics
show_metrics() {
    print_persian "نمایش متریک‌ها..."
    
    # Check if Prometheus is running
    if ! docker-compose ps prometheus | grep -q "Up"; then
        print_error "Prometheus در حال اجرا نیست"
        exit 1
    fi
    
    # Get Prometheus port from environment
    PROMETHEUS_PORT=$(grep "PROMETHEUS_PORT" .env | cut -d= -f2)
    if [ -z "$PROMETHEUS_PORT" ]; then
        PROMETHEUS_PORT=9090
    fi
    
    # Get system metrics
    print_persian "متریک‌های سیستم:"
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=node_cpu_seconds_total" | jq .
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=node_memory_MemTotal_bytes" | jq .
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=node_disk_read_bytes_total" | jq .
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=node_disk_written_bytes_total" | jq .
    
    # Get VPN metrics
    print_persian "متریک‌های VPN:"
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=openvpn_client_connected" | jq .
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=openvpn_client_bytes_received" | jq .
    curl -s "http://localhost:$PROMETHEUS_PORT/api/v1/query?query=openvpn_client_bytes_sent" | jq .
}

# Function to manage alerts
manage_alerts() {
    if [ -z "$1" ]; then
        print_error "لطفاً دستور را مشخص کنید"
        echo "دستورات موجود:"
        echo "  show                     نمایش هشدارها"
        echo "  add <name> <condition>   افزودن هشدار"
        echo "  remove <name>            حذف هشدار"
        exit 1
    fi
    
    case "$1" in
        "show")
            print_persian "لیست هشدارها:"
            if [ -f "config/prometheus/rules.yml" ]; then
                cat "config/prometheus/rules.yml"
            else
                print_warning "فایل قوانین هشدار یافت نشد"
            fi
            ;;
            
        "add")
            if [ -z "$2" ] || [ -z "$3" ]; then
                print_error "لطفاً نام و شرط هشدار را مشخص کنید"
                exit 1
            fi
            
            ALERT_NAME="$2"
            ALERT_CONDITION="$3"
            
            print_persian "افزودن هشدار $ALERT_NAME..."
            
            # Create rules file if it doesn't exist
            mkdir -p "config/prometheus"
            touch "config/prometheus/rules.yml"
            
            # Add alert rule
            cat >> "config/prometheus/rules.yml" << EOL
groups:
- name: moonvpn_alerts
  rules:
  - alert: $ALERT_NAME
    expr: $ALERT_CONDITION
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "هشدار $ALERT_NAME"
      description: "شرط هشدار: $ALERT_CONDITION"
EOL
            
            print_success "هشدار با موفقیت افزوده شد"
            
            # Reload Prometheus
            print_persian "بارگذاری مجدد Prometheus..."
            docker-compose restart prometheus
            ;;
            
        "remove")
            if [ -z "$2" ]; then
                print_error "لطفاً نام هشدار را مشخص کنید"
                exit 1
            fi
            
            ALERT_NAME="$2"
            
            print_persian "حذف هشدار $ALERT_NAME..."
            
            if [ -f "config/prometheus/rules.yml" ]; then
                # Remove alert rule
                sed -i "/alert: $ALERT_NAME/,/description:/d" "config/prometheus/rules.yml"
                sed -i '/^$/N;/^\n$/D' "config/prometheus/rules.yml"
                
                print_success "هشدار با موفقیت حذف شد"
                
                # Reload Prometheus
                print_persian "بارگذاری مجدد Prometheus..."
                docker-compose restart prometheus
            else
                print_warning "فایل قوانین هشدار یافت نشد"
            fi
            ;;
            
        *)
            print_error "دستور نامعتبر است"
            echo "دستورات موجود:"
            echo "  show                     نمایش هشدارها"
            echo "  add <name> <condition>   افزودن هشدار"
            echo "  remove <name>            حذف هشدار"
            exit 1
            ;;
    esac
}

# Function to open monitoring dashboard
open_dashboard() {
    print_persian "باز کردن داشبورد نظارتی..."
    
    # Check if Grafana is running
    if ! docker-compose ps grafana | grep -q "Up"; then
        print_error "Grafana در حال اجرا نیست"
        exit 1
    fi
    
    # Get Grafana port from environment
    GRAFANA_PORT=$(grep "GRAFANA_PORT" .env | cut -d= -f2)
    if [ -z "$GRAFANA_PORT" ]; then
        GRAFANA_PORT=3000
    fi
    
    # Get Grafana admin password
    GRAFANA_PASSWORD=$(grep "GF_SECURITY_ADMIN_PASSWORD" .env | cut -d= -f2)
    if [ -z "$GRAFANA_PASSWORD" ]; then
        GRAFANA_PASSWORD="admin"
    fi
    
    print_persian "داشبورد Grafana در دسترس است:"
    print_persian "آدرس: http://localhost:$GRAFANA_PORT"
    print_persian "نام کاربری: admin"
    print_persian "رمز عبور: $GRAFANA_PASSWORD"
    
    # Open browser if possible
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:$GRAFANA_PORT"
    elif command -v open &> /dev/null; then
        open "http://localhost:$GRAFANA_PORT"
    fi
}

# Main command handler
case "$1" in
    "metrics")
        show_metrics
        ;;
    "alerts")
        manage_alerts "$2" "$3" "$4"
        ;;
    "dashboard")
        open_dashboard
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {metrics|alerts|dashboard}"
        exit 1
        ;;
esac 