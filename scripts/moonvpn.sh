#!/bin/bash

# MoonVPN CLI Tool
# This script is used to manage the MoonVPN project
# through command line interface

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root path
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT" || exit 1

# Show banner
show_banner() {
    echo -e "${BLUE}"
    echo "  ╭──────────────────────────────────────╮"
    echo "  │                                      │"
    echo "  │       🌙 MoonVPN CLI Tool 🌙         │"
    echo "  │                                      │"
    echo "  ╰──────────────────────────────────────╯"
    echo -e "${NC}"
}

# Show help
show_help() {
    echo -e "${CYAN}Usage:${NC} moonvpn [command]"
    echo
    echo -e "${CYAN}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}        Start MoonVPN services"
    echo -e "  ${GREEN}stop${NC}         Stop MoonVPN services"
    echo -e "  ${GREEN}restart${NC}      Restart MoonVPN services"
    echo -e "  ${GREEN}status${NC}       Show MoonVPN services status"
    echo -e "  ${GREEN}logs${NC} [service] Show service logs (api, bot, db)"
    echo -e "  ${GREEN}backup${NC}       Create database backup"
    echo -e "  ${GREEN}restore${NC} [file] Restore database from backup"
    echo -e "  ${GREEN}update${NC}       Update to latest version"
    echo -e "  ${GREEN}shell${NC} [service] Enter service shell"
    echo -e "  ${GREEN}install${NC}      Install MoonVPN"
    echo -e "  ${GREEN}uninstall${NC}    Uninstall MoonVPN"
    echo -e "  ${GREEN}help${NC}         Show this help"
    echo
    echo -e "${CYAN}Example:${NC}"
    echo -e "  moonvpn start"
    echo -e "  moonvpn logs api"
    echo
}

# Check Docker installation
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

# Check container status
check_containers() {
    local container_name="$1"
    docker ps -q -f name="$container_name"
}

# Start services
start_services() {
    echo -e "${YELLOW}Checking existing services...${NC}"
    
    if [ -n "$(check_containers moonvpn)" ]; then
        echo -e "${YELLOW}MoonVPN services are already running. Use 'moonvpn restart' to restart.${NC}"
        return 0
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}.env file created. Please edit it with your settings.${NC}"
            exit 1
        else
            echo -e "${RED}Error: .env.example file not found. Cannot continue.${NC}"
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
    docker-compose down &> /dev/null  # Stop any existing containers
    docker-compose up -d --build
    
    # Check if containers are running
    if [ -z "$(check_containers moonvpn_db)" ] || [ -z "$(check_containers moonvpn_api)" ] || [ -z "$(check_containers moonvpn_bot)" ]; then
        echo -e "${RED}Error: Failed to start some containers. Check logs with 'moonvpn logs'${NC}"
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
    echo "      MoonVPN Started Successfully!            "
    echo "==============================================="
    echo "API: http://localhost:$(grep API_PORT .env | cut -d= -f2)"
    echo "phpMyAdmin: http://localhost:$(grep PHPMYADMIN_PORT .env | cut -d= -f2)"
    echo ""
    echo "To view logs:"
    echo "  API: moonvpn logs api"
    echo "  Bot: moonvpn logs bot"
    echo "  DB: moonvpn logs db"
    echo ""
    echo "To stop services:"
    echo "  moonvpn stop"
    echo "==============================================="
    echo -e "${NC}"
}

# Stop services
stop_services() {
    echo -e "${YELLOW}Stopping MoonVPN services...${NC}"
    docker-compose down
    echo -e "${GREEN}MoonVPN services stopped successfully.${NC}"
}

# Restart services
restart_services() {
    echo -e "${YELLOW}Restarting MoonVPN services...${NC}"
    docker-compose down
    docker-compose up -d --build
    echo -e "${GREEN}MoonVPN services restarted successfully.${NC}"
}

# Show services status
show_status() {
    echo -e "${YELLOW}MoonVPN Services Status:${NC}"
    docker-compose ps
}

# Show logs
show_logs() {
    local service="$1"
    
    case "$service" in
        api)
            docker logs moonvpn_api --tail 100 -f
            ;;
        bot)
            docker logs moonvpn_bot --tail 100 -f
            ;;
        db)
            docker logs moonvpn_db --tail 100 -f
            ;;
        redis)
            docker logs moonvpn_redis --tail 100 -f
            ;;
        phpmyadmin)
            docker logs moonvpn_phpmyadmin --tail 100 -f
            ;;
        *)
            echo -e "${YELLOW}Showing all services logs:${NC}"
            docker-compose logs --tail 50
            ;;
    esac
}

# Create backup
create_backup() {
    local backup_dir="$PROJECT_ROOT/backups"
    local date_str=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/moonvpn_backup_$date_str.sql"
    
    # Create backups directory if it doesn't exist
    if [ ! -d "$backup_dir" ]; then
        echo -e "${YELLOW}Creating backups directory...${NC}"
        mkdir -p "$backup_dir"
        echo -e "${GREEN}Backups directory created.${NC}"
    fi
    
    echo -e "${YELLOW}Creating database backup...${NC}"
    docker exec moonvpn_db mysqldump -u root --password="$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)" moonvpn > "$backup_file"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup saved successfully to $backup_file${NC}"
        
        # Compress backup file
        gzip "$backup_file"
        echo -e "${GREEN}Backup file compressed: ${backup_file}.gz${NC}"
        
        # Keep only last 5 backups
        echo -e "${YELLOW}Cleaning old backups...${NC}"
        ls -t "$backup_dir"/moonvpn_backup_*.gz | tail -n +6 | xargs -r rm
        echo -e "${GREEN}Old backups cleaned.${NC}"
    else
        echo -e "${RED}Error: Backup failed!${NC}"
        exit 1
    fi
}

# Restore backup
restore_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Error: Backup file $backup_file not found!${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Warning: This will overwrite all current data!${NC}"
    echo -e "${YELLOW}Are you sure you want to continue? (y/n)${NC}"
    read -r confirm
    
    if [ "$confirm" != "y" ]; then
        echo -e "${YELLOW}Restore operation cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}Restoring database from $backup_file...${NC}"
    
    # Handle compressed files
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | docker exec -i moonvpn_db mysql -u root --password="$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)" moonvpn
    else
        cat "$backup_file" | docker exec -i moonvpn_db mysql -u root --password="$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)" moonvpn
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database restored successfully.${NC}"
    else
        echo -e "${RED}Error: Database restore failed!${NC}"
        exit 1
    fi
}

# Update MoonVPN
update_moonvpn() {
    echo -e "${YELLOW}Updating MoonVPN...${NC}"
    
    # Check for Git repository
    if [ -d ".git" ]; then
        git fetch
        local_rev=$(git rev-parse HEAD)
        remote_rev=$(git rev-parse @{upstream})
        
        if [ "$local_rev" = "$remote_rev" ]; then
            echo -e "${GREEN}MoonVPN is already up to date.${NC}"
            exit 0
        fi
        
        echo -e "${YELLOW}New version available. Updating...${NC}"
        
        # Create backup before update
        create_backup
        
        # Update code
        git pull
        
        # Restart services
        restart_services
        
        echo -e "${GREEN}MoonVPN updated successfully.${NC}"
    else
        echo -e "${RED}Error: This is not a Git installation. Update not supported.${NC}"
        exit 1
    fi
}

# Enter service shell
enter_shell() {
    local service="$1"
    
    case "$service" in
        api)
            docker exec -it moonvpn_api /bin/bash
            ;;
        bot)
            docker exec -it moonvpn_bot /bin/bash
            ;;
        db)
            docker exec -it moonvpn_db /bin/bash
            ;;
        redis)
            docker exec -it moonvpn_redis /bin/sh
            ;;
        *)
            echo -e "${RED}Error: Invalid service. Choose from: api, bot, db, redis${NC}"
            exit 1
            ;;
    esac
}

# Install MoonVPN
install_moonvpn() {
    echo -e "${YELLOW}Installing MoonVPN...${NC}"
    
    # Check Docker
    check_docker
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}.env file created. Please edit it with your settings.${NC}"
        else
            echo -e "${RED}Error: .env.example file not found. Cannot continue.${NC}"
            exit 1
        fi
    fi
    
    # Create required directories
    echo -e "${YELLOW}Creating required directories...${NC}"
    mkdir -p logs
    mkdir -p backups
    mkdir -p data
    echo -e "${GREEN}Directories created.${NC}"
    
    # Build and start containers
    echo -e "${YELLOW}Starting MoonVPN services...${NC}"
    docker-compose up -d --build
    
    # Check if containers are running
    if [ -z "$(check_containers moonvpn_db)" ] || [ -z "$(check_containers moonvpn_api)" ] || [ -z "$(check_containers moonvpn_bot)" ]; then
        echo -e "${RED}Error: Installation failed. Check logs with 'docker-compose logs'${NC}"
        exit 1
    fi
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10
    
    # Run database setup script
    echo -e "${YELLOW}Initializing database...${NC}"
    docker exec moonvpn_api python /app/scripts/setup_db.py
    
    # Create symlink for moonvpn command
    sudo ln -sf "$PROJECT_ROOT/scripts/moonvpn.sh" /usr/local/bin/moonvpn
    sudo chmod +x "$PROJECT_ROOT/scripts/moonvpn.sh"
    
    echo -e "${GREEN}"
    echo "==============================================="
    echo "      MoonVPN Installed Successfully!          "
    echo "==============================================="
    echo "You can now use the 'moonvpn' command from anywhere."
    echo ""
    echo "API: http://localhost:$(grep API_PORT .env | cut -d= -f2)"
    echo "phpMyAdmin: http://localhost:$(grep PHPMYADMIN_PORT .env | cut -d= -f2)"
    echo ""
    echo "To see available commands:"
    echo "  moonvpn help"
    echo "==============================================="
    echo -e "${NC}"
}

# Uninstall MoonVPN
uninstall_moonvpn() {
    echo -e "${YELLOW}Warning: This will remove all MoonVPN data!${NC}"
    echo -e "${YELLOW}Are you sure you want to continue? (y/n)${NC}"
    read -r confirm
    
    if [ "$confirm" != "y" ]; then
        echo -e "${YELLOW}Uninstall cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}Uninstalling MoonVPN...${NC}"
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove symlink
    if [ -L "/usr/local/bin/moonvpn" ]; then
        sudo rm -f /usr/local/bin/moonvpn
    fi
    
    echo -e "${GREEN}MoonVPN uninstalled successfully.${NC}"
}

# Process arguments
main() {
    show_banner
    
    # Check Docker
    check_docker
    
    local command="$1"
    shift
    
    case "$command" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$1"
            ;;
        backup)
            create_backup
            ;;
        restore)
            restore_backup "$1"
            ;;
        update)
            update_moonvpn
            ;;
        shell)
            enter_shell "$1"
            ;;
        install)
            install_moonvpn
            ;;
        uninstall)
            uninstall_moonvpn
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            echo -e "${RED}Error: Invalid command: $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Main execution
main "$@" 