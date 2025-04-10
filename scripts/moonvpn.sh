#!/bin/bash

# --- Configuration ---
# Service name for the main Python application/bot in docker-compose.yml
BOT_SERVICE_NAME="bot"
# Default docker-compose file(s)
COMPOSE_FILES="-f docker-compose.yml"
# Add override files if they exist (e.g., for dev)
# if [ -f "docker-compose.override.yml" ]; then
#   COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.override.yml"
# fi

# --- Helper Functions ---

# Function to check docker compose command result
# Usage: check_result $? "Error message if failed"
check_result() {
    if [ $1 -ne 0 ]; then
        echo "❌ Error: $2" >&2
        exit $1
    fi
}

# Function to run commands inside a *running* bot container
# Usage: exec_in_bot <command_with_args...>
exec_in_bot() {
    echo "⏳ Executing in running '$BOT_SERVICE_NAME' container: $@"
    docker compose $COMPOSE_FILES exec --workdir /app "$BOT_SERVICE_NAME" "$@"
    check_result $? "Command execution failed inside the container."
}

# Function to run commands inside a *temporary* bot container
# Usage: run_in_temp_bot <command_with_args...>
run_in_temp_bot() {
    echo "⏳ Running in temporary '$BOT_SERVICE_NAME' container: $@"
    docker compose $COMPOSE_FILES run --rm --workdir /app "$BOT_SERVICE_NAME" "$@"
    check_result $? "Command execution failed inside temporary container."
}

# Function to print help message
usage() {
    echo "🚀 MoonVPN Project Management CLI (Improved) 🚀"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands (Lifecycle):"
    echo "  up [svc...]     Start specified services [svc...] or all if none specified (detached mode)."
    echo "  stop [svc...]   Stop specified services [svc...] or all if none specified (does not remove)."
    echo "  down            Stop and remove all services, networks (alias: rm)."
    echo "  restart [svc...] Restart specified services [svc...] or all if none specified."
    echo "  logs [svc]      Follow logs for all services or a specific service [svc]."
    echo "  status, ps      Show status of running services."
    echo "  build [svc...]  Build or rebuild images for specified services or all."
    echo ""
    echo "Commands (Development & Maintenance):"
    echo "  install         Install/update Python dependencies using Poetry (runs in temp container)."
    echo "  setup           Run the full setup: build, migrate, seed, start (use with caution!)."
    echo "  clean           Stop and remove containers AND associated volumes."
    echo "  migrate         Apply database migrations (alembic upgrade head) (runs in temp container)."
    echo "  revision <msg>  Create a new DB migration file (alembic revision --autogenerate). Message is required."
    echo "                  (runs in temp container)."
    echo "  seed            Run the main DB seeding script (scripts.seed_all) (runs in temp container)."
    echo ""
    echo "Commands (Interaction):"
    echo "  exec <cmd...>   Execute a custom command inside the *running* bot container."
    echo "  shell, bash     Open a bash shell inside the *running* bot container."
    echo ""
    echo "  help            Show this help message."
    echo ""
    exit 1
}

# --- Command Handling ---
COMMAND=$1
shift || true # Remove command, ignore error if no args provided

# Check if command is provided
if [ -z "$COMMAND" ]; then
    usage
fi

case "$COMMAND" in
    up|start)
        SERVICES_TO_START="$@"
        if [ -z "$SERVICES_TO_START" ]; then
            echo "🚀 Starting all MoonVPN services..."
            docker compose $COMPOSE_FILES up -d --remove-orphans
            check_result $? "Failed to start services."
            echo "✅ All services started."
        else
            echo "🚀 Starting specified services: $SERVICES_TO_START..."
            # Use --no-deps maybe? Let's stick to default compose behavior for now
            docker compose $COMPOSE_FILES up -d --remove-orphans $SERVICES_TO_START
            check_result $? "Failed to start specified services."
            echo "✅ Specified services started."
        fi
        ;;
    stop)
        SERVICES_TO_STOP="$@"
        if [ -z "$SERVICES_TO_STOP" ]; then
            echo "🛑 Stopping all MoonVPN services (not removing)..."
            docker compose $COMPOSE_FILES stop
            check_result $? "Failed to stop services."
            echo "✅ All services stopped."
        else
            echo "🛑 Stopping specified services: $SERVICES_TO_STOP..."
            docker compose $COMPOSE_FILES stop $SERVICES_TO_STOP
            check_result $? "Failed to stop specified services."
            echo "✅ Specified services stopped."
        fi
        ;;
    down|rm) # Added rm alias
        echo "🛑 Stopping and removing all MoonVPN services and networks..."
        docker compose $COMPOSE_FILES down
        check_result $? "Failed to stop and remove services."
        echo "✅ Services and networks removed."
        ;;
    restart)
        SERVICES_TO_RESTART="$@"
        TARGET_SERVICES_STR="" # String for messages and checks
        ALL_SERVICES=false

        if [ -z "$SERVICES_TO_RESTART" ]; then
            echo "🔄 Restarting all services..."
            TARGET_SERVICES_STR="all services"
            ALL_SERVICES=true
            docker compose $COMPOSE_FILES restart
            check_result $? "Failed to initiate restart for all services."
        else
            echo "🔄 Restarting specified services: $SERVICES_TO_RESTART..."
            TARGET_SERVICES_STR="specified services ($SERVICES_TO_RESTART)"
            docker compose $COMPOSE_FILES restart $SERVICES_TO_RESTART
            check_result $? "Failed to initiate restart for specified services."
        fi

        # --- Verification Step ---
        echo "⏳ Waiting for services to stabilize..."
        sleep 15 # Increased wait time to 15 seconds

        echo "🔎 Verifying status of restarted services..."

        # If specific services were restarted, check only those
        if ! $ALL_SERVICES; then
            FINAL_STATUS_OK=true
            for service in $SERVICES_TO_RESTART; do
                # Get status, filter for the service line, check if running/healthy/Up
                # Using 'docker compose ps' which shows state
                status=$(docker compose $COMPOSE_FILES ps "$service" | grep "$service")
                # Updated regex to include "Up" status
                if echo "$status" | grep -qE "(running|healthy|Up\\s)"; then 
                    echo "  ✅ Service '$service' is running."
                else
                    echo "  ❌ Service '$service' is NOT running. Status: $status"
                    # --- Added Log Output ---
                    echo "  📋 Displaying last 10 log lines for '$service':"
                    docker compose $COMPOSE_FILES logs --tail 10 "$service" || echo "  ⚠️ Could not retrieve logs for '$service'."
                    # --- End Added Log Output ---
                    FINAL_STATUS_OK=false
                fi
            done

            if $FINAL_STATUS_OK; then
                 echo "✅ Successfully restarted $TARGET_SERVICES_STR and they are running."
            else
                 echo "❌ Some specified services failed to restart correctly. Check logs ($0 logs <service_name>)."
                 exit 1 # Exit with error if any specified service failed
            fi
        else
            # If all services were restarted, do a general 'ps' and look for issues
            # This is less precise but gives a general idea
            DOCKER_PS_OUTPUT=$(docker compose $COMPOSE_FILES ps)
            echo "$DOCKER_PS_OUTPUT" # Show the status

            # Improved check for services not running properly
            echo "🔍 Checking status of each service:"
            SERVICES_LIST=$(docker compose $COMPOSE_FILES config --services)
            FINAL_STATUS_OK=true
            
            for service in $SERVICES_LIST; do
                # Get status for this specific service
                status=$(docker compose $COMPOSE_FILES ps "$service" | grep "$service")
                if echo "$status" | grep -qE "(Up|running|healthy)"; then 
                    echo "  ✅ Service '$service' is running."
                else
                    echo "  ❌ Service '$service' is NOT running. Status: $status"
                    echo "  📋 Displaying last 10 log lines for '$service':"
                    docker compose $COMPOSE_FILES logs --tail 10 "$service" || echo "  ⚠️ Could not retrieve logs for '$service'."
                    FINAL_STATUS_OK=false
                fi
            done
            
            if $FINAL_STATUS_OK; then
                echo "✅ All services restarted successfully and are running."
            else
                echo "❌ Some services did not restart correctly or are unhealthy. See status details above." >&2
                exit 1 # Exit with error if any service failed in 'all' restart
            fi
        fi
        ;;
    logs)
        SERVICE_NAME=$1
        
        echo "📜 Showing last 100 lines of logs${SERVICE_NAME:+ for $SERVICE_NAME}..."
        
        # Capture log output into a variable first
        log_output=$(docker compose $COMPOSE_FILES logs --no-color --no-log-prefix --tail 100 ${SERVICE_NAME:+"$SERVICE_NAME"} 2>&1)
        
        # Then print the captured output
        echo "$log_output"
        
        # Ensure script exits cleanly
        exit 0 # Explicitly exit after showing logs
        ;;
    status|ps)
        echo "📊 Current service status:"
        docker compose $COMPOSE_FILES ps
        ;;
    build)
        SERVICES_TO_BUILD="$@"
        echo "🛠️ Building images${SERVICES_TO_BUILD:+ for $SERVICES_TO_BUILD}..."
        docker compose $COMPOSE_FILES build $SERVICES_TO_BUILD
        check_result $? "Failed to build images."
        echo "✅ Build complete."
        ;;
    install)
        echo "📦 Installing dependencies via Poetry (in temporary container)..."
        run_in_temp_bot poetry install --no-root # Use run_in_temp_bot
        echo "✅ Dependencies installed/updated."
        ;;
    setup)
        echo "⚙️ Starting full project setup..."
        
        echo "[1/4] Building images..."
        docker compose $COMPOSE_FILES build
        check_result $? "Build failed"
        echo "✅ Images built."
        
        echo "[2/4] Applying database migrations..."
        run_in_temp_bot alembic upgrade head
        # run_in_temp_bot already checks result
        echo "✅ Migrations applied."

        echo "[3/4] Seeding database..."
        SEED_MODULE_PATH="scripts.seed_all"
        run_in_temp_bot python -m "$SEED_MODULE_PATH"
        # run_in_temp_bot already checks result
        echo "✅ Database seeded."
        
        echo "[4/4] Starting services..."
        docker compose $COMPOSE_FILES up -d --remove-orphans
        check_result $? "Failed to start services"
        echo "✅ Setup complete! Services are running."
        ;;
    clean)
        echo "🧹 Cleaning up environment (stopping containers and removing volumes)..."
        docker compose $COMPOSE_FILES down -v
        check_result $? "Failed to clean environment."
        echo "✅ Environment cleaned."
        ;;
    migrate)
        echo "💾 Applying database migrations (in temporary container)..."
        run_in_temp_bot alembic upgrade head
        # run_in_temp_bot already checks result
        echo "✅ Migrations finished."
        ;;
    revision)
        REVISION_MSG="$@"
        if [ -z "$REVISION_MSG" ]; then
            echo "❌ Error: Migration message is required." >&2
            echo "Usage: $0 revision <Your migration message here>" >&2
            exit 1
        fi
        echo "📝 Creating new migration: '$REVISION_MSG' (in temporary container)..."
        run_in_temp_bot alembic revision --autogenerate -m "$REVISION_MSG"
        # run_in_temp_bot already checks result
        echo "✅ Revision created successfully (check migrations/versions)."
        ;;
    exec)
        if [ $# -eq 0 ]; then
            echo "❌ Error: Please provide a command to execute." >&2
            echo "Usage: $0 exec <command...>" >&2
            exit 1
        fi
        # exec needs the running container, so use exec_in_bot
        exec_in_bot "$@"
        echo "✅ Command finished."
        ;;
    shell|bash)
        echo "💻 Opening shell in running '$BOT_SERVICE_NAME' container..."
        # shell needs the running container
        # Don't use helper for interactive session, check result manually
        docker compose $COMPOSE_FILES exec --workdir /app "$BOT_SERVICE_NAME" /bin/bash
        if [ $? -ne 0 ]; then
            echo "⚠️ Shell exited with non-zero status." >&2
        fi
        ;;
    seed)
        SEED_MODULE_PATH="scripts.seed_all"
        echo "🌱 Running main database seed script (module: $SEED_MODULE_PATH) (in temporary container)..."
        run_in_temp_bot python -m "$SEED_MODULE_PATH"
        # run_in_temp_bot already checks result
        echo "✅ Database seeding finished."
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "❌ Unknown command: $COMMAND" >&2
        usage
        ;;
esac

exit 0
