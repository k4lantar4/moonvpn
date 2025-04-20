#!/bin/bash
#
# MoonVPN CLI - ابزار خط فرمان برای مدیریت سرویس MoonVPN
#

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# تنظیم متغیر محیطی MOONVPN_ROOT
MOONVPN_ROOT=${MOONVPN_ROOT:-"/root/moonvpn"}

# تشخیص مسیر پروژه
find_project_root() {
    # اگر متغیر محیطی تنظیم شده باشد
    if [[ -n "$MOONVPN_ROOT" && -d "$MOONVPN_ROOT" && -f "$MOONVPN_ROOT/docker-compose.yml" ]]; then
        echo "$MOONVPN_ROOT"
        return 0
    fi
    
    # بررسی اینکه آیا اسکریپت در مسیر scripts/ پروژه است
    local script_path="$(readlink -f "${BASH_SOURCE[0]}")"
    local script_dir="$(dirname "$script_path")"
    
    if [[ "$(basename "$script_dir")" == "scripts" && -f "$(dirname "$script_dir")/docker-compose.yml" ]]; then
        echo "$(dirname "$script_dir")"
        return 0
    fi
    
    # بررسی اینکه آیا در مسیر پروژه هستیم
    if [[ -f "./docker-compose.yml" ]]; then
        echo "$(pwd)"
        return 0
    fi
    
    # جستجو در مسیرهای بالاتر
    local current_dir="$(pwd)"
    while [[ "$current_dir" != "/" ]]; do
        if [[ -f "$current_dir/docker-compose.yml" ]]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    # استفاده از مسیر پیش فرض
    if [[ -f "/root/moonvpn/docker-compose.yml" ]]; then
        echo "/root/moonvpn"
        return 0
    fi
    
    echo "❌ خطا: پوشه پروژه MoonVPN پیدا نشد!" >&2
    echo "لطفاً مسیر پروژه را با متغیر MOONVPN_ROOT مشخص کنید. مثال:" >&2
    echo "MOONVPN_ROOT=/path/to/moonvpn moonvpn COMMAND" >&2
    return 1
}

# مسیر اصلی پروژه
PROJECT_ROOT=$(find_project_root)
if [[ $? -ne 0 ]]; then
    exit 1
fi

# Display help message
show_help() {
    echo -e "${BLUE}MoonVPN CLI Management Tool${NC}"
    echo ""
    echo "Usage: moonvpn [command]"
    echo ""
    echo "Commands:"
    echo "  up              Start all services"
    echo "  down            Stop all services"
    echo "  restart         Restart all services"
    echo "  restart-bot     Restart only the bot service"
    echo "  update-bot      Pull changes and restart bot"
    echo "  reload          Send reload signal to bot"
    echo "  logs [service]  View last 50 lines of logs (app, db, redis, phpmyadmin)"
    echo "  logs-follow [s] Follow logs continuously (app, db, redis, phpmyadmin)"
    echo "  bot-logs        View last 50 lines of bot logs"
    echo "  migrate         Run database migrations"
    echo "  migrate-create  Create a new migration with message"
    echo "  shell [service] List available containers or open shell in specified service"
    echo "  status          Check status of all services"
    echo "  build           Build the app container"
    echo "  ps              List all running containers"
    echo "  exec-bot        Run bot directly and see output"
    echo "  install         Install moonvpn command system-wide"
    echo "  help            Show this help message"
    echo ""
}

# Install moonvpn command system-wide
install_command() {
    local script_path="$(readlink -f "${BASH_SOURCE[0]}")"
    local bin_path="/usr/local/bin/moonvpn"

    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}Error: This command requires root privileges${NC}"
        echo -e "Please run: ${YELLOW}sudo moonvpn install${NC}"
        exit 1
    fi

    echo -e "${BLUE}Installing MoonVPN CLI system-wide...${NC}"
    
    # Make sure the script is executable
    chmod +x "$script_path"
    
    # Create symbolic link to the script
    ln -sf "$script_path" "$bin_path"
    chmod +x "$bin_path"
    
    echo -e "${GREEN}✓ MoonVPN CLI has been installed!${NC}"
    echo -e "You can now run ${YELLOW}moonvpn${NC} from anywhere."
}

# Check if Docker and Docker Compose are installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
}

# List available containers and show information
list_containers() {
    echo -e "${BLUE}Available containers:${NC}"
    docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}"
    echo ""
    echo -e "${YELLOW}To open a shell in a specific container, use:${NC}"
    echo -e "moonvpn shell [service_name]"
    echo ""
    echo -e "${YELLOW}Available services:${NC}"
    docker compose config --services | awk '{print "  - " $0}'
    echo ""
}

# Ensure we're in the project directory
cd "$PROJECT_ROOT" || { echo -e "${RED}Error: Could not change to project directory${NC}"; exit 1; }

# Main command handler
case "$1" in
    up)
        check_docker
        echo -e "${BLUE}Starting MoonVPN services...${NC}"
        docker compose up -d
        echo -e "${GREEN}Services started successfully${NC}"
        ;;
    
    down)
        check_docker
        echo -e "${BLUE}Stopping MoonVPN services...${NC}"
        docker compose down
        echo -e "${GREEN}Services stopped successfully${NC}"
        ;;
    
    restart)
        check_docker
        echo -e "${BLUE}Restarting MoonVPN services...${NC}"
        docker compose restart
        echo -e "${GREEN}Services restarted successfully${NC}"
        ;;

    restart-bot)
        check_docker
        echo -e "${BLUE}Restarting only the bot service...${NC}"
        docker compose restart app
        echo -e "${GREEN}Bot service restarted successfully${NC}"
        ;;

    update-bot)
        check_docker
        echo -e "${BLUE}Updating and restarting the bot...${NC}"
        git pull
        docker compose restart app
        echo -e "${GREEN}Bot updated and restarted successfully${NC}"
        ;;

    reload)
        check_docker
        echo -e "${BLUE}Sending reload signal to bot...${NC}"
        # ایجاد یک فایل خالی در مسیر bot/ برای فعال‌سازی سیستم بارگذاری مجدد
        docker exec moonvpn_app touch /app/bot/.reload_trigger
        echo -e "${GREEN}Reload signal sent! Bot will reload momentarily.${NC}"
        ;;
    
    logs)
        check_docker
        echo -e "${BLUE}Showing last 50 lines of logs...${NC}"
        if [ -z "$2" ]; then
            docker compose logs --tail=50
        else
            docker compose logs --tail=50 "$2"
        fi
        ;;

    logs-follow)
        check_docker
        echo -e "${BLUE}Following logs continuously (Ctrl+C to stop)...${NC}"
        if [ -z "$2" ]; then
            docker compose logs -f
        else
            docker compose logs -f "$2"
        fi
        ;;

    bot-logs)
        check_docker
        echo -e "${BLUE}Showing last 50 lines of bot logs...${NC}"
        docker compose logs --tail=50 app
        ;;
    
    migrate)
        check_docker
        echo -e "${BLUE}Running database migrations...${NC}"
        docker compose exec app alembic upgrade head
        echo -e "${GREEN}Migrations completed${NC}"
        ;;

    migrate-create)
        check_docker
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Migration message is required${NC}"
            echo -e "Usage: moonvpn migrate-create \"your migration message\""
            exit 1
        fi
        echo -e "${BLUE}Creating new migration with message: $2${NC}"
        docker compose exec app alembic revision --autogenerate -m "$2"
        echo -e "${GREEN}Migration created. Run 'moonvpn migrate' to apply it.${NC}"
        ;;
    
    shell)
        check_docker
        if [ -z "$2" ]; then
            # List available containers if no service specified
            list_containers
        else
            # Check if service exists
            if docker compose ps --services | grep -q "^$2$"; then
                echo -e "${BLUE}Opening shell in $2 container...${NC}"
                docker compose exec "$2" bash || {
                    echo -e "${YELLOW}Bash not available in this container, trying sh...${NC}"
                    docker compose exec "$2" sh
                }
            else
                echo -e "${RED}Error: Service '$2' not found${NC}"
                list_containers
            fi
        fi
        ;;
    
    status)
        check_docker
        echo -e "${BLUE}MoonVPN services status:${NC}"
        docker compose ps
        ;;
    
    build)
        check_docker
        echo -e "${BLUE}Building MoonVPN services...${NC}"
        docker compose build
        echo -e "${GREEN}Build completed${NC}"
        ;;
    
    ps)
        check_docker
        docker compose ps
        ;;

    exec-bot)
        check_docker
        echo -e "${BLUE}Running bot directly (Ctrl+C to stop)...${NC}"
        docker compose exec app python -m bot.main
        ;;
    
    install)
        install_command
        ;;
    
    help|*)
        show_help
        ;;
esac

exit 0
