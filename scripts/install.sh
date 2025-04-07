#!/bin/bash

# ============================================================
# MoonVPN Installation Script
# 
# این اسکریپت برای نصب و راه‌اندازی اولیه MoonVPN استفاده می‌شود
# پیش‌نیازها: Docker, Docker Compose, Git
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
echo -e "      Installation Script v1.0              "
echo -e "${NC}"

# تنظیم مسیر پروژه
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT" || { echo -e "${RED}خطا: مسیر پروژه یافت نشد!${NC}"; exit 1; }

echo -e "${YELLOW}مسیر نصب: ${CYAN}$PROJECT_ROOT${NC}"

# بررسی پیش‌نیازها
echo -e "\n${YELLOW}بررسی پیش‌نیازها...${NC}"

# بررسی Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker نصب نشده است. لطفا ابتدا Docker را نصب کنید.${NC}"
    echo -e "${YELLOW}برای نصب Docker، دستورات زیر را اجرا کنید:${NC}"
    echo -e "curl -fsSL https://get.docker.com -o get-docker.sh"
    echo -e "sudo sh get-docker.sh"
    exit 1
else
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker نصب شده است: $DOCKER_VERSION${NC}"
fi

# بررسی Docker Compose
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Docker Compose نصب نشده است. لطفا ابتدا Docker Compose را نصب کنید.${NC}"
        echo -e "${YELLOW}برای نصب Docker Compose، دستورات زیر را اجرا کنید:${NC}"
        echo -e "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo -e "sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
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
    echo -e "${RED}Git نصب نشده است. لطفا ابتدا Git را نصب کنید.${NC}"
    echo -e "${YELLOW}برای نصب Git، دستور زیر را اجرا کنید:${NC}"
    echo -e "sudo apt-get update && sudo apt-get install -y git"
    exit 1
else
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}✓ Git نصب شده است: $GIT_VERSION${NC}"
fi

# ساخت فایل محیطی از نمونه
echo -e "\n${YELLOW}در حال تنظیم فایل‌های محیطی...${NC}"
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✓ فایل .env از نمونه ساخته شد.${NC}"
        echo -e "${YELLOW}توجه: لطفا فایل .env را ویرایش کرده و مقادیر مناسب را وارد کنید.${NC}"
    else
        echo -e "${RED}خطا: فایل .env.example یافت نشد!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ فایل .env از قبل وجود دارد.${NC}"
fi

# بررسی و ساخت دایرکتوری‌های مورد نیاز
echo -e "\n${YELLOW}در حال ساخت دایرکتوری‌های مورد نیاز...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/backups"

echo -e "${GREEN}✓ دایرکتوری‌های مورد نیاز ساخته شدند.${NC}"

# تنظیم دسترسی‌های اسکریپت‌ها
echo -e "\n${YELLOW}در حال تنظیم دسترسی‌های اسکریپت‌ها...${NC}"
chmod +x "$PROJECT_ROOT/scripts/start.sh"
chmod +x "$PROJECT_ROOT/scripts/backup.sh"
chmod +x "$PROJECT_ROOT/scripts/healthcheck.py"
chmod +x "$PROJECT_ROOT/scripts/moonvpn.sh"

echo -e "${GREEN}✓ دسترسی‌های اسکریپت‌ها تنظیم شدند.${NC}"

# ساخت لینک سیمبولیک برای دستور moonvpn
echo -e "\n${YELLOW}در حال ساخت لینک سیمبولیک برای دستور moonvpn...${NC}"
if [ -f "/usr/local/bin/moonvpn" ]; then
    sudo rm -f /usr/local/bin/moonvpn
fi

sudo ln -sf "$PROJECT_ROOT/scripts/moonvpn.sh" /usr/local/bin/moonvpn
echo -e "${GREEN}✓ لینک سیمبولیک با موفقیت ساخته شد.${NC}"
echo -e "${CYAN}حالا می‌توانید از دستور 'moonvpn' در هر مسیری استفاده کنید.${NC}"

# نصب پکیج‌های Python مورد نیاز
echo -e "\n${YELLOW}در حال نصب پکیج‌های Python مورد نیاز...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "${GREEN}✓ پکیج‌های Python نصب شدند.${NC}"
else
    echo -e "${RED}پکیج pip3 یافت نشد. لطفا Python و pip را نصب کنید.${NC}"
    echo -e "${YELLOW}دستور نصب: ${NC}sudo apt-get update && sudo apt-get install -y python3-pip"
    exit 1
fi

# شروع سرویس‌ها
echo -e "\n${YELLOW}آیا مایل هستید سرویس‌ها را اکنون راه‌اندازی کنید؟ (y/n)${NC}"
read -r START_SERVICES

if [[ "$START_SERVICES" =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}در حال راه‌اندازی سرویس‌ها...${NC}"
    $PROJECT_ROOT/scripts/start.sh
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}============================================${NC}"
        echo -e "${GREEN}✓ نصب و راه‌اندازی MoonVPN با موفقیت انجام شد!${NC}"
        echo -e "${GREEN}============================================${NC}"
        echo -e "\n${CYAN}برای مدیریت سرویس‌ها، از دستورات زیر استفاده کنید:${NC}"
        echo -e "${YELLOW}moonvpn start${NC} - راه‌اندازی سرویس‌ها"
        echo -e "${YELLOW}moonvpn stop${NC} - توقف سرویس‌ها"
        echo -e "${YELLOW}moonvpn restart${NC} - راه‌اندازی مجدد سرویس‌ها"
        echo -e "${YELLOW}moonvpn status${NC} - نمایش وضعیت سرویس‌ها"
        echo -e "${YELLOW}moonvpn logs${NC} - نمایش لاگ‌ها"
        echo -e "${YELLOW}moonvpn backup${NC} - تهیه پشتیبان"
        echo -e "${YELLOW}moonvpn help${NC} - نمایش راهنما"
    else
        echo -e "\n${RED}خطا در راه‌اندازی سرویس‌ها. لطفا لاگ‌ها را بررسی کنید.${NC}"
    fi
else
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}✓ نصب MoonVPN با موفقیت انجام شد!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "\n${CYAN}برای راه‌اندازی سرویس‌ها، دستور زیر را اجرا کنید:${NC}"
    echo -e "${YELLOW}moonvpn start${NC}"
fi

exit 0
