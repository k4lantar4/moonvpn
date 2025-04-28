#!/bin/bash

echo "Starting admin module refactoring deployment..."

# Run migrations
echo "Running database migrations..."
moonvpn migrate

# Restart the service
echo "Restarting MoonVPN service..."
moonvpn restart

# Display logs
echo "Displaying application logs..."
moonvpn logs app

echo "Deployment completed!" 