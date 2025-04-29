#!/bin/bash
# MoonVPN Control Script

# Exit immediately if a command exits with a non-zero status.
set -e

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
    echo "  logs-follow [s] Follow logs continuously (defaults to app service if none specified)"
    echo "  bot-logs        View last 200 lines of bot logs"
    echo "  migrate         Run database migrations (alias for migrate upgrade)"
    echo "  migrate upgrade Run all pending migrations"
    echo "  migrate show    Show current migration state"
    echo "  migrate history Show migration history"
    echo "  migrate generate Create a new migration with message"
    echo "  migrate stamp   Set current migration version without running migrations"
    echo "  db [subcmd]     Database tools: shell, info, phpmyadmin, <SQL>"
    echo "  shell [service] List available containers or open shell in specified service"
    echo "  status          Check status of all services"
    echo "  build           Build the app container"
    echo "  ps              List all running containers"
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

# Check if we're in production environment
is_production() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        grep -q "^ENVIRONMENT=production" "$PROJECT_ROOT/.env"
        return $?
    fi
    return 1
}

# Function to check and potentially create .env file
check_env() {
  echo "Checking environment..."
  if [ ! -f .env ]; then
    echo "INFO: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "WARNING: .env file created from .env.example. Please review and update it with your actual credentials, especially BOT_TOKEN and ADMIN_ID."
  fi

  # Load .env variables into the script's environment
  # Temporarily disable nounset (-u) if set, as it interferes with checking unbound variables
  local options_before
  options_before=$(set +o | grep nounset)
  set +u
  # Source .env file safely
  set -a
  # Check if .env exists before sourcing
  if [ -f .env ]; then
    source .env
  else
    echo "ERROR: .env file does not exist even after attempting to copy. Cannot proceed."
    exit 1
  fi
  set +a
  # Restore nounset option if it was originally set
  eval "$options_before"


  # Validate required variables
  local missing_vars=0
  if [ -z "${BOT_TOKEN:-}" ]; then # Use parameter expansion for safe check
    echo "ERROR: BOT_TOKEN is not set in the .env file."
    missing_vars=1
  fi
  if [ -z "${ADMIN_ID:-}" ]; then
    echo "ERROR: ADMIN_ID is not set in the .env file."
    missing_vars=1
  fi
  if [ -z "${MYSQL_DATABASE:-}" ] || [ -z "${MYSQL_USER:-}" ] || [ -z "${MYSQL_PASSWORD:-}" ] || [ -z "${MYSQL_HOST:-}" ] || [ -z "${MYSQL_ROOT_PASSWORD:-}" ]; then
     echo "ERROR: One or more MySQL environment variables (MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_ROOT_PASSWORD) are not set in .env."
     missing_vars=1
  fi

  if [ "$missing_vars" -eq 1 ]; then
    echo "Please ensure all required variables are set in the .env file."
    exit 1
  fi
  echo "Environment variables checked successfully."
}

# Function to check database readiness using docker-compose healthcheck status
# Waits up to ~60 seconds by default (adjust attempts and sleep duration if needed)
check_db_health() {
  echo "Checking database readiness..."
  local attempts=12 # Number of attempts
  local sleep_duration=5 # Seconds between attempts

  for (( i=1; i<=attempts; i++ )); do
    # Get health status; suppress "no such service" error if db isn't up yet
    local health_status
    health_status=$(docker-compose ps db 2>/dev/null | grep ' Up (healthy)' || echo "not healthy")

    if [[ "$health_status" == *"Up (healthy)"* ]]; then
      echo "Database is healthy and ready."
      return 0 # Success
    fi

    echo "Database not ready yet (attempt $i/$attempts). Waiting ${sleep_duration}s..."
    sleep $sleep_duration
  done

  echo "ERROR: Database did not become healthy after $(($attempts * $sleep_duration)) seconds."
  # Provide more context if possible
  echo "Current 'db' service status:"
  docker-compose ps db || echo "Could not get status for 'db' service."
  exit 1
}

# Function to run database migrations
run_migrations() {
  echo "Running database migrations..."
  # Use 'run --rm' to execute the command in a temporary container based on the 'app' service image
  # Ensures dependencies and environment variables are correctly set for alembic
  docker-compose run --rm app alembic upgrade head
  echo "Migrations applied successfully."
}

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
        echo -e "${BLUE}Showing last 100 lines of logs...${NC}"
        if [ -z "$2" ]; then
            docker compose logs --tail=100
        else
            docker compose logs --tail=100 "$2"
        fi
        ;;

    logs-follow)
        check_docker
        echo -e "${BLUE}Following logs continuously (Ctrl+C to stop)...${NC}"
        if [ -z "$2" ]; then
            # Default to 'app' service if no service is specified
            echo -e "${YELLOW}No service specified, following 'app' logs...${NC}"
            docker compose logs -f app
        else
            docker compose logs -f "$2"
        fi
        ;;

    bot-logs)
        check_docker
        echo -e "${BLUE}Showing last 200 lines of bot logs...${NC}"
        docker compose logs --tail=200 app
        ;;
    
    migrate)
        check_docker
        case "$2" in
            ""|"upgrade")
                echo -e "${BLUE}Running database migrations...${NC}"
                docker compose exec app alembic upgrade head
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✓ Migrations completed successfully${NC}"
                else
                    echo -e "${RED}❌ Migration failed${NC}"
                    exit 1
                fi
                ;;
            
            "generate")
                if [ -z "$3" ]; then
                    echo -e "${RED}Error: Migration message is required${NC}"
                    echo -e "Usage: moonvpn migrate generate \"your migration message\""
                    echo -e "Example: moonvpn migrate generate \"add users table\""
                    exit 1
                fi

                if is_production; then
                    echo -e "${RED}⚠️ Warning: You are in PRODUCTION environment!${NC}"
                    echo -e "Are you sure you want to generate a new migration? (y/N)"
                    read -r response
                    if [[ ! "$response" =~ ^[Yy]$ ]]; then
                        echo -e "${YELLOW}Migration cancelled${NC}"
                        exit 0
                    fi
                fi

                # Validate migration message format
                if [[ ! "$3" =~ ^[a-zA-Z0-9_]+[a-zA-Z0-9_\ \-]*$ ]]; then
                    echo -e "${RED}Error: Invalid migration message format${NC}"
                    echo -e "Migration message should:"
                    echo -e "- Start with a letter, number, or underscore"
                    echo -e "- Contain only letters, numbers, spaces, underscores, or hyphens"
                    echo -e "Example: moonvpn migrate generate \"add_users_table\""
                    exit 1
                fi

                echo -e "${BLUE}Generating new migration...${NC}"
                echo -e "${YELLOW}Message: ${NC}$3"
                
                # Try to create the migration
                if ! output=$(docker compose exec app alembic revision --autogenerate -m "$3" 2>&1); then
                    echo -e "${RED}Error generating migration:${NC}"
                    echo "$output"
                    echo -e "\n${YELLOW}Troubleshooting:${NC}"
                    echo "1. Check if the database is running and accessible"
                    echo "2. Ensure your SQLAlchemy models have the required changes"
                    echo "3. Verify that alembic.ini is properly configured"
                    echo "4. Check if there are pending migrations to apply first"
                    exit 1
                fi

                # Extract the migration file name from the output
                migration_file=$(echo "$output" | grep -o "migrations/versions/[a-zA-Z0-9_]*.py")
                
                if [ -n "$migration_file" ]; then
                    echo -e "${GREEN}✓ Migration generated successfully!${NC}"
                    echo -e "${YELLOW}Migration file: ${NC}$migration_file"
                    echo -e "\n${BLUE}Next steps:${NC}"
                    echo "1. Review the migration file to ensure changes are correct"
                    echo "2. Run 'moonvpn migrate upgrade' to apply the migration"
                    echo "3. Test the changes in your development environment"
                    echo -e "4. Commit the migration file to version control\n"
                else
                    echo -e "${RED}Warning: Migration was generated but couldn't locate the file${NC}"
                    echo -e "Please check the migrations/versions directory manually"
                fi
                ;;

            "show")
                echo -e "${BLUE}Current migration state:${NC}"
                docker compose exec app alembic current
                ;;

            "history")
                echo -e "${BLUE}Migration history:${NC}"
                docker compose exec app alembic history --verbose
                ;;

            "stamp")
                if [ -z "$3" ]; then
                    echo -e "${RED}Error: Version is required for stamp command${NC}"
                    echo -e "Usage: moonvpn migrate stamp <version>"
                    echo -e "Example: moonvpn migrate stamp head"
                    exit 1
                fi

                if is_production; then
                    echo -e "${RED}⚠️ WARNING: You are in PRODUCTION environment!${NC}"
                    echo -e "Stamping migrations can be dangerous in production."
                    echo -e "Are you absolutely sure you want to proceed? (yes/N)"
                    read -r response
                    if [[ ! "$response" == "yes" ]]; then
                        echo -e "${YELLOW}Operation cancelled${NC}"
                        exit 0
                    fi
                fi

                echo -e "${BLUE}Stamping database with version $3...${NC}"
                docker compose exec app alembic stamp "$3"
                ;;

            *)
                echo -e "${RED}Error: Unknown migrate subcommand: $2${NC}"
                echo -e "Available subcommands:"
                echo -e "  moonvpn migrate          # Run all pending migrations"
                echo -e "  moonvpn migrate upgrade  # Run all pending migrations"
                echo -e "  moonvpn migrate generate # Create a new migration"
                echo -e "  moonvpn migrate show     # Show current migration state"
                echo -e "  moonvpn migrate history  # Show migration history"
                echo -e "  moonvpn migrate stamp    # Set current migration version"
                exit 1
                ;;
        esac
        ;;

    migrate-create)
        echo -e "${YELLOW}⚠️ Warning: 'migrate-create' is deprecated${NC}"
        echo -e "Please use 'moonvpn migrate generate' instead"
        echo -e "Example: moonvpn migrate generate \"your migration message\""
        exit 1
        ;;
    
    db)
        check_docker
        check_env
        case "$2" in
            shell)
                # چک مقدار متغیرهای دیتابیس
                if [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ] || [ -z "$MYSQL_DATABASE" ]; then
                  echo "❌ خطا: متغیرهای MYSQL_USER یا MYSQL_PASSWORD یا MYSQL_DATABASE مقدار ندارند!"
                  echo "MYSQL_USER: $MYSQL_USER"
                  echo "MYSQL_PASSWORD: $MYSQL_PASSWORD"
                  echo "MYSQL_DATABASE: $MYSQL_DATABASE"
                  exit 1
                fi
                echo "[DEBUG] MYSQL_USER: $MYSQL_USER, MYSQL_DATABASE: $MYSQL_DATABASE"
                echo -e "${BLUE}باز کردن mysql shell در کانتینر db...${NC}"
                docker compose exec db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
                ;;
            info)
                echo -e "${BLUE}اطلاعات اتصال دیتابیس:${NC}"
                echo -e "  هاست: ${YELLOW}$MYSQL_HOST${NC}"
                echo -e "  دیتابیس: ${YELLOW}$MYSQL_DATABASE${NC}"
                echo -e "  کاربر: ${YELLOW}$MYSQL_USER${NC}"
                echo -e "  رمز عبور: ${YELLOW}(مخفی)${NC}"
                ;;
            phpmyadmin)
                echo -e "${BLUE}phpMyAdmin معمولاً روی پورت 8080 در دسترس است.${NC}"
                echo -e "${YELLOW}آدرس: http://localhost:8080${NC}"
                if command -v xdg-open &> /dev/null; then
                    xdg-open "http://localhost:8080" &
                fi
                ;;
            "")
                echo -e "${YELLOW}دستور را وارد کنید. مثال:${NC}"
                echo -e "  moonvpn db shell            # باز کردن mysql shell"
                echo -e "  moonvpn db info             # نمایش اطلاعات اتصال"
                echo -e "  moonvpn db phpmyadmin       # باز کردن phpmyadmin"
                echo -e "  moonvpn db \"SHOW TABLES;\"   # اجرای دستور SQL"
                ;;
            *)
                echo -e "${BLUE}اجرای دستور SQL در دیتابیس...${NC}"
                docker compose exec db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "$2"
                ;;
        esac
        ;;
    
    shell)
        check_env
        check_docker
        if [ -z "$2" ]; then
            list_containers
        else
            service="$2"
            shift 2
            if ! docker compose ps --services | grep -q "^${service}$"; then
                echo -e "${RED}Error: Service '${service}' not found${NC}"
                list_containers
                exit 1
            fi
            if [ "$service" = "db" ] && [ $# -gt 0 ]; then
                # چک مقدار متغیرهای دیتابیس
                if [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ] || [ -z "$MYSQL_DATABASE" ]; then
                  echo "❌ خطا: متغیرهای MYSQL_USER یا MYSQL_PASSWORD یا MYSQL_DATABASE مقدار ندارند!"
                  echo "MYSQL_USER: $MYSQL_USER"
                  echo "MYSQL_PASSWORD: $MYSQL_PASSWORD"
                  echo "MYSQL_DATABASE: $MYSQL_DATABASE"
                  exit 1
                fi
                echo "[DEBUG] MYSQL_USER: $MYSQL_USER, MYSQL_DATABASE: $MYSQL_DATABASE"
                # اجرای دستور mysql
                if [ $# -eq 1 ]; then
                    docker compose exec db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "$1"
                else
                    sql_command="$*"
                    docker compose exec db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "$sql_command"
                fi
            elif [ $# -eq 0 ]; then
                echo -e "${BLUE}Opening shell in ${service} container...${NC}"
                docker compose exec "${service}" bash || {
                    echo -e "${YELLOW}Bash not available in this container, trying sh...${NC}"
                    docker compose exec "${service}" sh
                }
            else
                echo -e "${BLUE}Executing command in ${service} container...${NC}"
                docker compose exec "${service}" "$@"
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

    exec-app)
        check_docker
        echo -e "${BLUE}Executing command in app container...${NC}"
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: No command specified for exec-app${NC}"
            echo "Usage: moonvpn exec-app <command>"
            exit 1
        fi
        shift
        docker compose exec app "$@"
        ;;
    
    install)
        install_command
        ;;
    
    help|*)
        show_help
        ;;
esac

exit 0
