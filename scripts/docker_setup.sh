#!/bin/bash

# MoonVPN Docker Setup Script

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to print messages
print_message() {
    echo "--------------------------------------------------"
    echo " $1"
    echo "--------------------------------------------------"
}

# Navigate to project root (assuming script is in scripts/ directory)
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

print_message "Setting up MoonVPN using Docker Compose..."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_message "Error: docker-compose is not installed."
    echo "Please install Docker and Docker Compose before running this script."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_message "Error: .env file not found."
    echo "Please create a .env file in the project root with the required environment variables."
    exit 1
fi

# Build and start containers
print_message "Building and starting containers..."
docker-compose build
docker-compose up -d

# Wait for services to start
print_message "Waiting for services to start..."
sleep 10

# Run database migrations
print_message "Running database migrations..."
docker-compose exec core_api alembic upgrade head

print_message "MoonVPN Docker setup completed!"
echo "Core API is running at: http://localhost:8888"
echo "Telegram Bot is also running."
echo ""
echo "Use the following commands to manage your Docker setup:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
echo ""
echo "Happy testing! 🚀" 