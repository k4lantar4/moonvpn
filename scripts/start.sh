#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is installed
if ! command_exists docker; then
    print_message "$RED" "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command_exists docker-compose; then
    print_message "$RED" "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_message "$YELLOW" "🔧 Creating necessary directories..."
mkdir -p logs/dev logs/test logs/prod

# Stop any running containers
print_message "$YELLOW" "🛑 Stopping any running containers..."
docker-compose down

# Remove old containers, networks, and volumes
print_message "$YELLOW" "🧹 Cleaning up old containers and volumes..."
docker-compose rm -f
docker volume prune -f

# Build and start services
print_message "$YELLOW" "🚀 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_message "$YELLOW" "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
print_message "$YELLOW" "🔍 Checking service health..."

# Function to check container health
check_container() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)
    
    if [ "$status" = "healthy" ]; then
        print_message "$GREEN" "✅ $container is healthy"
        return 0
    else
        print_message "$RED" "❌ $container is not healthy (status: $status)"
        return 1
    fi
}

# Check each service
services=("moonvpn_db" "moonvpn_redis" "moonvpn_api" "moonvpn_bot" "moonvpn_phpmyadmin")
all_healthy=true

for service in "${services[@]}"; do
    if ! check_container "$service"; then
        all_healthy=false
    fi
done

# Show service status and URLs
if [ "$all_healthy" = true ]; then
    print_message "$GREEN" "\n🎉 All services are running!\n"
    echo -e "📌 Service URLs:"
    echo -e "   API: ${YELLOW}http://localhost:8000${NC}"
    echo -e "   phpMyAdmin: ${YELLOW}http://localhost:8080${NC}"
    echo -e "\n📋 To view logs:"
    echo -e "   API: ${YELLOW}docker logs -f moonvpn_api${NC}"
    echo -e "   Bot: ${YELLOW}docker logs -f moonvpn_bot${NC}"
    echo -e "   Database: ${YELLOW}docker logs -f moonvpn_db${NC}"
    echo -e "   Redis: ${YELLOW}docker logs -f moonvpn_redis${NC}"
else
    print_message "$RED" "\n⚠️ Some services are not healthy. Please check the logs for more information."
    exit 1
fi 