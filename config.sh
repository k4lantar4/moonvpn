#!/bin/bash

# MoonVPN Configuration Management
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

# Configuration files
ENV_FILE=".env"
DOCKER_COMPOSE_FILE="docker-compose.yml"
NGINX_CONFIG="/etc/nginx/conf.d/moonvpn.conf"

# Function to show configuration
show_config() {
    print_persian "نمایش تنظیمات:"
    echo
    
    # Show .env file
    if [ -f "$ENV_FILE" ]; then
        print_persian "تنظیمات محیطی (.env):"
        grep -v '^#' "$ENV_FILE" | grep -v '^$'
        echo
    else
        print_warning "فایل .env یافت نشد"
    fi
    
    # Show docker-compose.yml
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        print_persian "تنظیمات Docker:"
        cat "$DOCKER_COMPOSE_FILE"
        echo
    else
        print_warning "فایل docker-compose.yml یافت نشد"
    fi
    
    # Show nginx configuration
    if [ -f "$NGINX_CONFIG" ]; then
        print_persian "تنظیمات Nginx:"
        cat "$NGINX_CONFIG"
    else
        print_warning "فایل تنظیمات Nginx یافت نشد"
    fi
}

# Function to edit configuration
edit_config() {
    if [ -z "$1" ]; then
        print_error "لطفاً نام فایل تنظیمات را مشخص کنید"
        echo "گزینه‌های موجود: env, docker, nginx"
        exit 1
    fi
    
    case "$1" in
        "env")
            if [ -f "$ENV_FILE" ]; then
                nano "$ENV_FILE"
                print_success "تنظیمات محیطی ذخیره شد"
            else
                print_error "فایل .env یافت نشد"
                exit 1
            fi
            ;;
        "docker")
            if [ -f "$DOCKER_COMPOSE_FILE" ]; then
                nano "$DOCKER_COMPOSE_FILE"
                print_success "تنظیمات Docker ذخیره شد"
            else
                print_error "فایل docker-compose.yml یافت نشد"
                exit 1
            fi
            ;;
        "nginx")
            if [ -f "$NGINX_CONFIG" ]; then
                nano "$NGINX_CONFIG"
                print_success "تنظیمات Nginx ذخیره شد"
            else
                print_error "فایل تنظیمات Nginx یافت نشد"
                exit 1
            fi
            ;;
        *)
            print_error "فایل تنظیمات نامعتبر است"
            echo "گزینه‌های موجود: env, docker, nginx"
            exit 1
            ;;
    esac
    
    # Ask to restart services
    read -p "آیا می‌خواهید سرویس‌ها را راه‌اندازی مجدد کنید؟ (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_persian "راه‌اندازی مجدد سرویس‌ها..."
        docker-compose restart
        print_success "سرویس‌ها با موفقیت راه‌اندازی مجدد شدند"
    fi
}

# Function to reset configuration
reset_config() {
    if [ -z "$1" ]; then
        print_error "لطفاً نام فایل تنظیمات را مشخص کنید"
        echo "گزینه‌های موجود: env, docker, nginx"
        exit 1
    fi
    
    case "$1" in
        "env")
            if [ -f "$ENV_FILE" ]; then
                cp "$ENV_FILE" "${ENV_FILE}.backup"
                cat > "$ENV_FILE" << EOL
# MoonVPN Environment Configuration
# Version: 1.0.0

# Domain Configuration
DOMAIN=example.com

# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=moonvpn
DB_USER=moonvpn
DB_PASSWORD=change_me

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change_me

# VPN Configuration
VPN_PORT=1194
VPN_PROTOCOL=udp
VPN_NETWORK=10.8.0.0/24
VPN_DNS=8.8.8.8

# Security Configuration
JWT_SECRET=change_me
ENCRYPTION_KEY=change_me

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Backup Configuration
BACKUP_DIR=/var/backups/moonvpn
BACKUP_RETENTION=7
EOL
                print_success "تنظیمات محیطی به حالت پیش‌فرض بازگردانده شد"
            else
                print_error "فایل .env یافت نشد"
                exit 1
            fi
            ;;
        "docker")
            if [ -f "$DOCKER_COMPOSE_FILE" ]; then
                cp "$DOCKER_COMPOSE_FILE" "${DOCKER_COMPOSE_FILE}.backup"
                cat > "$DOCKER_COMPOSE_FILE" << EOL
version: '3.8'

services:
  app:
    build: .
    restart: always
    ports:
      - "80:80"
      - "443:443"
      - "1194:1194/udp"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
      - /etc/letsencrypt:/etc/letsencrypt
    environment:
      - DOMAIN=\${DOMAIN}
      - DB_HOST=\${DB_HOST}
      - DB_PORT=\${DB_PORT}
      - DB_NAME=\${DB_NAME}
      - DB_USER=\${DB_USER}
      - DB_PASSWORD=\${DB_PASSWORD}
      - REDIS_HOST=\${REDIS_HOST}
      - REDIS_PORT=\${REDIS_PORT}
      - REDIS_PASSWORD=\${REDIS_PASSWORD}
      - VPN_PORT=\${VPN_PORT}
      - VPN_PROTOCOL=\${VPN_PROTOCOL}
      - VPN_NETWORK=\${VPN_NETWORK}
      - VPN_DNS=\${VPN_DNS}
      - JWT_SECRET=\${JWT_SECRET}
      - ENCRYPTION_KEY=\${ENCRYPTION_KEY}
    depends_on:
      - db
      - redis

  db:
    image: postgres:13-alpine
    restart: always
    volumes:
      - ./data/db:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=\${DB_NAME}
      - POSTGRES_USER=\${DB_USER}
      - POSTGRES_PASSWORD=\${DB_PASSWORD}

  redis:
    image: redis:6-alpine
    restart: always
    volumes:
      - ./data/redis:/data
    command: redis-server --requirepass \${REDIS_PASSWORD}

  prometheus:
    image: prom/prometheus:latest
    restart: always
    ports:
      - "\${PROMETHEUS_PORT}:9090"
    volumes:
      - ./config/prometheus:/etc/prometheus
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    restart: always
    ports:
      - "\${GRAFANA_PORT}:3000"
    volumes:
      - ./data/grafana:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=change_me

volumes:
  prometheus_data:
EOL
                print_success "تنظیمات Docker به حالت پیش‌فرض بازگردانده شد"
            else
                print_error "فایل docker-compose.yml یافت نشد"
                exit 1
            fi
            ;;
        "nginx")
            if [ -f "$NGINX_CONFIG" ]; then
                cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup"
                cat > "$NGINX_CONFIG" << EOL
server {
    listen 80;
    server_name \${DOMAIN} www.\${DOMAIN};
    
    location / {
        proxy_pass http://app:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name \${DOMAIN} www.\${DOMAIN};
    
    ssl_certificate /etc/letsencrypt/live/\${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/\${DOMAIN}/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    location / {
        proxy_pass http://app:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
                print_success "تنظیمات Nginx به حالت پیش‌فرض بازگردانده شد"
            else
                print_error "فایل تنظیمات Nginx یافت نشد"
                exit 1
            fi
            ;;
        *)
            print_error "فایل تنظیمات نامعتبر است"
            echo "گزینه‌های موجود: env, docker, nginx"
            exit 1
            ;;
    esac
    
    # Ask to restart services
    read -p "آیا می‌خواهید سرویس‌ها را راه‌اندازی مجدد کنید؟ (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_persian "راه‌اندازی مجدد سرویس‌ها..."
        docker-compose restart
        print_success "سرویس‌ها با موفقیت راه‌اندازی مجدد شدند"
    fi
}

# Main command handler
case "$1" in
    "show")
        show_config
        ;;
    "edit")
        edit_config "$2"
        ;;
    "reset")
        reset_config "$2"
        ;;
    *)
        print_error "دستور نامعتبر است"
        echo "استفاده: $0 {show|edit|reset}"
        exit 1
        ;;
esac 