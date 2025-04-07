#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "==============================================="
echo "          MoonVPN 🌙 Startup Script           "
echo "==============================================="
echo -e "${NC}"

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to check if container is running
check_container() {
    docker ps -q -f name=$1
}

# Stop existing containers if they're running
echo -e "${YELLOW}Checking for existing MoonVPN containers...${NC}"
if [ -n "$(check_container moonvpn)" ]; then
    echo -e "${YELLOW}Stopping existing MoonVPN containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Existing containers stopped.${NC}"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env file not found. Creating from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}.env file created from example. Please edit it with your settings.${NC}"
        exit 1
    else
        echo -e "${RED}.env.example file not found. Cannot continue.${NC}"
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo -e "${YELLOW}Creating logs directory...${NC}"
    mkdir -p logs
    echo -e "${GREEN}Logs directory created.${NC}"
fi

# Build and start containers
echo -e "${YELLOW}Starting MoonVPN services...${NC}"
docker-compose up -d --build

# Check if containers are running
if [ -z "$(check_container moonvpn_db)" ] || [ -z "$(check_container moonvpn_api)" ] || [ -z "$(check_container moonvpn_bot)" ]; then
    echo -e "${RED}Failed to start some containers. Check logs with 'docker-compose logs'.${NC}"
    exit 1
fi

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Run database setup script
echo -e "${YELLOW}Initializing database...${NC}"
docker exec moonvpn_api python /app/scripts/setup_db.py

# Show status
echo -e "${GREEN}"
echo "==============================================="
echo "         MoonVPN Started Successfully!         "
echo "==============================================="
echo "API: http://localhost:$(grep API_PORT .env | cut -d= -f2)"
echo "phpMyAdmin: http://localhost:$(grep PHPMYADMIN_PORT .env | cut -d= -f2)"
echo ""
echo "To check logs:"
echo "  API: docker logs moonvpn_api"
echo "  Bot: docker logs moonvpn_bot"
echo "  DB: docker logs moonvpn_db"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo "==============================================="
echo -e "${NC}"

exit 0 