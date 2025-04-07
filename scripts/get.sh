#!/bin/bash

# ============================================================
# MoonVPN Quick Installation Script
# 
# این اسکریپت برای نصب سریع MoonVPN با یک خط دستور استفاده می‌شود
# curl -fsSL https://raw.githubusercontent.com/yourusername/moonvpn/main/scripts/get.sh | bash
# ============================================================

# رنگ‌های متن برای نمایش بهتر خروجی
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# نمایش بنر
echo -e "${BLUE}"
echo -e "  __  __  ___   ___  _  _  _   _ ____  _  _ "
echo -e " |  \/  |/ _ \ / _ \| \| || | | |  _ \| \| |"
echo -e " | |\/| | (_) | (_) | .  || |_| | |_) | .  |"
echo -e " |_|  |_|\___/ \___/|_|\_| \___/|____/|_|\_|"
echo -e "                                            "
echo -e "      Quick Installation Script v1.0        "
echo -e "${NC}"

echo -e "${YELLOW}در حال شروع نصب سریع MoonVPN...${NC}"

# بررسی پیش‌نیازها
echo -e "\n${YELLOW}بررسی پیش‌نیازها...${NC}"

# بررسی Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker نصب نشده است. در حال نصب...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker نصب شده است: $DOCKER_VERSION${NC}"
fi

# بررسی Docker Compose
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Docker Compose نصب نشده است. در حال نصب...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        DOCKER_COMPOSE_VERSION=$(docker compose version)
        echo -e "${GREEN}✓ Docker Compose نصب شده است: $DOCKER_COMPOSE_VERSION${NC}"
    fi
else
    DOCKER_COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose نصب شده است: $DOCKER_COMPOSE_VERSION${NC}"
fi

# بررسی Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git نصب نشده است. در حال نصب...${NC}"
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y git
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        sudo yum install -y git
    else
        echo -e "${RED}سیستم عامل شما پشتیبانی نمی‌شود. لطفا Git را به صورت دستی نصب کنید.${NC}"
        exit 1
    fi
else
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}✓ Git نصب شده است: $GIT_VERSION${NC}"
fi

# تنظیم مسیر نصب
INSTALL_DIR="${HOME}/moonvpn"
echo -e "${YELLOW}مسیر نصب: ${CYAN}$INSTALL_DIR${NC}"

# کلون کردن مخزن
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}پوشه moonvpn از قبل وجود دارد. آیا می‌خواهید آن را حذف کرده و دوباره نصب کنید؟ (y/n)${NC}"
    read -r REMOVE_DIR
    if [[ "$REMOVE_DIR" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}در حال حذف پوشه قبلی...${NC}"
        rm -rf "$INSTALL_DIR"
    else
        echo -e "${RED}نصب لغو شد.${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}در حال کلون کردن مخزن MoonVPN...${NC}"
git clone https://github.com/yourusername/moonvpn.git "$INSTALL_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}خطا در کلون کردن مخزن.${NC}"
    exit 1
fi

# رفتن به مسیر نصب
cd "$INSTALL_DIR" || { echo -e "${RED}خطا: رفتن به مسیر نصب ناموفق بود!${NC}"; exit 1; }

# اجرای اسکریپت نصب
echo -e "${YELLOW}در حال اجرای اسکریپت نصب...${NC}"
chmod +x scripts/install.sh
./scripts/install.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}نصب با خطا مواجه شد. لطفا لاگ‌ها را بررسی کنید.${NC}"
    exit 1
fi

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}✓ نصب سریع MoonVPN با موفقیت انجام شد!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\n${CYAN}برای راه‌اندازی سرویس‌ها، دستور زیر را اجرا کنید:${NC}"
echo -e "${YELLOW}moonvpn start${NC}"

exit 0 