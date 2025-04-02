#!/bin/bash

# MoonVPN Installation Script for Ubuntu 22.04 LTS

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Helper Functions --- #
print_message() {
    echo "--------------------------------------------------"
    echo " $1"
    echo "--------------------------------------------------"
}

# Function to ask yes/no questions
ask_yes_no() {
    while true; do
        read -p "$1 [y/N]: " yn
        case $yn in
            [Yy]* ) return 0;; # Yes
            [Nn]* | "" ) return 1;; # No or Enter
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# --- Gather User Input --- #
print_message "Gathering necessary information..."

read -p "Enter the domain name for your dashboard (e.g., vpn.yourdomain.com): " DOMAIN_NAME
while [[ -z "$DOMAIN_NAME" ]]; do
    echo "Domain name cannot be empty."
    read -p "Enter the domain name for your dashboard: " DOMAIN_NAME
done

read -p "Enter a valid email address (for SSL certificate notifications): " ADMIN_EMAIL
# Basic email validation
while ! echo "$ADMIN_EMAIL" | grep -E -q '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' ; do
    echo "Invalid email format. Please enter a valid email address."
    read -p "Enter a valid email address: " ADMIN_EMAIL
done

read -p "Enter your Telegram Bot Token: " TELEGRAM_BOT_TOKEN
while [[ -z "$TELEGRAM_BOT_TOKEN" ]]; do
    echo "Telegram Bot Token cannot be empty."
    read -p "Enter your Telegram Bot Token: " TELEGRAM_BOT_TOKEN
done

read -p "Enter the numeric ID of the required Telegram channel: " REQUIRED_CHANNEL_ID
while ! [[ "$REQUIRED_CHANNEL_ID" =~ ^-?[0-9]+$ ]]; do
    echo "Invalid input. Please enter the numeric channel ID (e.g., -100123456789)."
    read -p "Enter the numeric ID of the required Telegram channel: " REQUIRED_CHANNEL_ID
done

read -p "Enter the numeric Telegram User IDs of the admins, separated by commas (e.g., 12345,67890): " ADMIN_IDS_INPUT
while [[ -z "$ADMIN_IDS_INPUT" ]]; do
    echo "Admin IDs cannot be empty."
    read -p "Enter the numeric Telegram User IDs of the admins (comma-separated): " ADMIN_IDS_INPUT
done
# Validate comma-separated numbers (basic check)
ADMIN_IDS=$(echo "$ADMIN_IDS_INPUT" | sed 's/[^0-9,]//g') # Remove non-numeric/comma chars

read -p "Enter the numeric Telegram Group ID for Admin Management (MANAGE): " MANAGE_GROUP_ID
while ! [[ "$MANAGE_GROUP_ID" =~ ^-?[0-9]+$ ]]; do
    echo "Invalid input. Please enter the numeric group ID (e.g., -100123456789)."
    read -p "Enter the numeric Telegram Group ID for Admin Management (MANAGE): " MANAGE_GROUP_ID
done

read -p "Enter the numeric Telegram Group ID for Payment Transactions/Proofs (TRANSACTIONS): " TRANSACTIONS_GROUP_ID
while ! [[ "$TRANSACTIONS_GROUP_ID" =~ ^-?[0-9]+$ ]]; do
    echo "Invalid input. Please enter the numeric group ID (e.g., -100123456789)."
    read -p "Enter the numeric Telegram Group ID for Payment Transactions/Proofs (TRANSACTIONS): " TRANSACTIONS_GROUP_ID
done

read -p "Enter the numeric Telegram Group ID for Reports (REPORTS): " REPORTS_GROUP_ID
while ! [[ "$REPORTS_GROUP_ID" =~ ^-?[0-9]+$ ]]; do
    echo "Invalid input. Please enter the numeric group ID (e.g., -100123456789)."
    read -p "Enter the numeric Telegram Group ID for Reports (REPORTS): " REPORTS_GROUP_ID
done

read -p "Enter the numeric Telegram Group ID for System Outages (OUTAGES): " OUTAGES_GROUP_ID
while ! [[ "$OUTAGES_GROUP_ID" =~ ^-?[0-9]+$ ]]; do
    echo "Invalid input. Please enter the numeric group ID (e.g., -100123456789)."
    read -p "Enter the numeric Telegram Group ID for System Outages (OUTAGES): " OUTAGES_GROUP_ID
done

read -p "Enter a strong password for the MySQL database user 'moonvpn_user': " DB_PASSWORD
while [[ -z "$DB_PASSWORD" ]]; do
    echo "Database password cannot be empty."
    read -p "Enter a strong password for the MySQL database user 'moonvpn_user': " DB_PASSWORD
done

# Confirm information (optional but good practice)
print_message "Please confirm the following information:"
echo "Domain Name:        $DOMAIN_NAME"
echo "Admin Email:        $ADMIN_EMAIL"
echo "Telegram Bot Token: [HIDDEN]"
# echo "Telegram Bot Token: $TELEGRAM_BOT_TOKEN"
echo "Required Channel ID: $REQUIRED_CHANNEL_ID"
echo "Admin User IDs:     $ADMIN_IDS"
echo "Manage Group ID:    $MANAGE_GROUP_ID"
echo "Transactions Group ID: $TRANSACTIONS_GROUP_ID"
echo "Reports Group ID:   $REPORTS_GROUP_ID"
echo "Outages Group ID:   $OUTAGES_GROUP_ID"
echo "Database Password:  [HIDDEN]"
# echo "Database Password:  $DB_PASSWORD"

if ! ask_yes_no "Is this information correct?"; then
    echo "Installation aborted by user." >&2
    exit 1
fi

# --- System Update ---
print_message "Updating package lists..."
sudo apt update

print_message "Upgrading installed packages..."
sudo apt upgrade -y

# --- Install Python & Pip ---
print_message "Installing Python 3, pip, and venv..."
sudo apt install -y python3 python3-pip python3-venv

# Verify Python installation
python3 --version
pip3 --version

# --- Install MySQL Server & Client ---
print_message "Installing MySQL Server and Client..."
sudo apt install -y mysql-server mysql-client

# --- Install Nginx, Certbot, Git and other utilities ---
print_message "Installing Nginx, Certbot, Git, and other utilities..."
sudo apt install -y nginx python3-certbot-nginx git curl

# Verify Nginx installation
sudo systemctl status nginx --no-pager | cat

# --- Secure MySQL Installation & Database Setup --- #
print_message "Securing MySQL and setting up database..."

# Generate secure commands for MySQL setup
# Note: Avoid putting passwords directly in commands shown in history. Use temporary files or other methods if needed.
MDB_NAME="moonvpn_db"
MDB_USER="moonvpn_user"

# Use a temporary file for SQL commands to avoid password exposure in process list/history
SQL_COMMANDS_FILE=$(mktemp)

cat << EOF > "${SQL_COMMANDS_FILE}"
-- Set root password if it's not set (adjust based on initial MySQL state)
-- ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_SECURE_ROOT_PASSWORD';
-- FLUSH PRIVILEGES;

-- Remove anonymous users (MySQL 8 compatible)
DELETE FROM mysql.user WHERE User='';
-- Remove remote root login (MySQL 8 compatible)
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
-- Remove test database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';

-- Create project database
CREATE DATABASE IF NOT EXISTS ${MDB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Create project user
CREATE USER IF NOT EXISTS '${MDB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
-- Grant privileges to the project user on the project database
GRANT ALL PRIVILEGES ON ${MDB_NAME}.* TO '${MDB_USER}'@'localhost';
-- Apply changes
FLUSH PRIVILEGES;
EOF

# Execute the SQL commands
# The initial sudo mysql might prompt for the current root password if already set.
sudo mysql < "${SQL_COMMANDS_FILE}"

# Clean up temporary file
rm -f "${SQL_COMMANDS_FILE}"

print_message "MySQL secured and database/user created."

# --- Git Clone (Optional) --- #
# TODO: Add logic here to clone the repository if needed
# Example: if [ ! -d "../core_api" ]; then git clone <repo_url> .; fi

# --- Setup Python Virtual Environments & Install Dependencies --- #
PROJECT_ROOT=".." # Assuming script is run from scripts/ directory
CORE_API_DIR="${PROJECT_ROOT}/core_api"
TELEGRAM_BOT_DIR="${PROJECT_ROOT}/telegram_bot"

print_message "Setting up virtual environment and installing dependencies for Core API..."
python3 -m venv "${CORE_API_DIR}/venv"
source "${CORE_API_DIR}/venv/bin/activate"
pip install --upgrade pip
cd "${CORE_API_DIR}"
pip install -r requirements.txt
cd - # Go back to previous directory (scripts)
deactivate

print_message "Setting up virtual environment and installing dependencies for Telegram Bot..."
python3 -m venv "${TELEGRAM_BOT_DIR}/venv"
source "${TELEGRAM_BOT_DIR}/venv/bin/activate"
pip install --upgrade pip
cd "${TELEGRAM_BOT_DIR}"
pip install -r requirements.txt
cd - # Go back to previous directory (scripts)
deactivate

print_message "Python dependencies installed."

# --- Create .env files --- #
print_message "Creating .env configuration files..."

# Generate a strong random secret key for JWT
API_SECRET_KEY=$(openssl rand -hex 32)

# Create .env for Core API
CORE_API_ENV_FILE="${CORE_API_DIR}/.env"
cat << EOF > "${CORE_API_ENV_FILE}"
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=${MDB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${MDB_NAME}

# JWT Security Settings
SECRET_KEY=${API_SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 days
ALGORITHM=HS256

# OTP Settings
OTP_EXPIRE_SECONDS=180 # 3 minutes

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Telegram Bot Internal Communication (If needed later)
# TELEGRAM_BOT_SEND_OTP_URL=http://localhost:8888/internal/send-otp
# INTERNAL_API_KEY=generate_a_strong_key_here
EOF

# Create .env for Telegram Bot
TELEGRAM_BOT_ENV_FILE="${TELEGRAM_BOT_DIR}/.env"
cat << EOF > "${TELEGRAM_BOT_ENV_FILE}"
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
REQUIRED_CHANNEL_ID=${REQUIRED_CHANNEL_ID}
ADMIN_IDS=${ADMIN_IDS}
MANAGE_GROUP_ID=${MANAGE_GROUP_ID}
TRANSACTIONS_GROUP_ID=${TRANSACTIONS_GROUP_ID}
REPORTS_GROUP_ID=${REPORTS_GROUP_ID}
OUTAGES_GROUP_ID=${OUTAGES_GROUP_ID}

# Core API Base URL (Adjust if API runs elsewhere or on different port)
CORE_API_BASE_URL=http://127.0.0.1:8000

# Debug Mode (default to False for production)
DEBUG_MODE=False

# Internal Communication (If using HTTP callback from API)
# INTERNAL_API_KEY=use_the_same_key_as_in_core_api_env
# BOT_LISTEN_HOST=0.0.0.0
# BOT_LISTEN_PORT=8888
EOF

print_message ".env files created."

# --- Run Database Migrations --- #
print_message "Running database migrations for Core API..."

# Activate Core API venv and run alembic
cd "${CORE_API_DIR}"
source "venv/bin/activate"
alembic upgrade head
deactivate
cd "${PROJECT_ROOT}/scripts" # Go back to script directory

print_message "Database migrations completed."

# --- Configure Nginx --- #
print_message "Configuring Nginx reverse proxy..."

NGINX_CONF_FILE="/etc/nginx/sites-available/${DOMAIN_NAME}"
NGINX_ENABLED_LINK="/etc/nginx/sites-enabled/${DOMAIN_NAME}"

# Create Nginx server block configuration
cat << EOF | sudo tee "${NGINX_CONF_FILE}" > /dev/null
server {
    listen 80;
    listen [::]:80;

    server_name ${DOMAIN_NAME};

    # Increase client body size for potential uploads (adjust as needed)
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000; # FastAPI app running on port 8000
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s; # Increase timeout if needed
    }

    # Optional: Serve static files directly via Nginx for better performance
    # location /static {
    #     alias ${CORE_API_DIR}/app/static; # Adjust path if needed
    #     expires 1d; # Cache static files for 1 day
    #     access_log off;
    # }
}
EOF

# Enable the site by creating a symbolic link
sudo ln -sf "${NGINX_CONF_FILE}" "${NGINX_ENABLED_LINK}"

# Remove the default Nginx site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx to apply changes
sudo systemctl reload nginx

print_message "Nginx configured."

# --- Obtain SSL Certificate with Certbot --- #
print_message "Obtaining SSL certificate with Certbot..."

# Use certbot with the nginx plugin, non-interactively agreeing to TOS
# and providing email for renewal notices.
sudo certbot --nginx -d "${DOMAIN_NAME}" --non-interactive --agree-tos -m "${ADMIN_EMAIL}"

# Certbot should automatically reload nginx after successful configuration

print_message "SSL certificate obtained and Nginx updated."

# --- Setup Systemd Services --- #
print_message "Setting up systemd services for Core API and Telegram Bot..."

# Get the absolute path to the project root
ABS_PROJECT_ROOT=$(cd "${PROJECT_ROOT}" && pwd)
ABS_CORE_API_DIR="${ABS_PROJECT_ROOT}/core_api"
ABS_TELEGRAM_BOT_DIR="${ABS_PROJECT_ROOT}/telegram_bot"

# --- Core API Service --- #
API_SERVICE_FILE="/etc/systemd/system/moonvpn-api.service"
cat << EOF | sudo tee "${API_SERVICE_FILE}" > /dev/null
[Unit]
Description=MoonVPN Core API Service
After=network.target mysql.service redis-server.service

[Service]
User=root # Consider running as a non-root user for better security
Group=root # Adjust user/group if running as non-root
WorkingDirectory=${ABS_CORE_API_DIR}
Environment="PATH=${ABS_CORE_API_DIR}/venv/bin"
ExecStart=${ABS_CORE_API_DIR}/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# --- Telegram Bot Service --- #
BOT_SERVICE_FILE="/etc/systemd/system/moonvpn-bot.service"
cat << EOF | sudo tee "${BOT_SERVICE_FILE}" > /dev/null
[Unit]
Description=MoonVPN Telegram Bot Service
After=network.target moonvpn-api.service # Start after API (optional dependency)

[Service]
User=root # Consider running as a non-root user
Group=root # Adjust user/group
WorkingDirectory=${ABS_TELEGRAM_BOT_DIR}
Environment="PATH=${ABS_TELEGRAM_BOT_DIR}/venv/bin"
ExecStart=${ABS_TELEGRAM_BOT_DIR}/venv/bin/python app/main.py
Restart=always
RestartSec=5 # Longer restart interval for bot

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the services
sudo systemctl daemon-reload
sudo systemctl enable moonvpn-api.service
sudo systemctl enable moonvpn-bot.service
sudo systemctl start moonvpn-api.service
sudo systemctl start moonvpn-bot.service

# Check status (optional)
print_message "Checking service statuses..."
sudo systemctl status moonvpn-api.service --no-pager | cat
sudo systemctl status moonvpn-bot.service --no-pager | cat

print_message "Systemd services set up and started."

# --- Configure Firewall (UFW) --- #
print_message "Configuring Firewall (UFW)..."

# Allow essential ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Enable UFW (use --force to avoid interactive prompt)
sudo ufw --force enable

# Check UFW status
sudo ufw status verbose

print_message "Firewall configured and enabled."

# --- Final Message --- #
print_message "MoonVPN Installation Completed Successfully!"

echo "You should now be able to access your dashboard at: https://${DOMAIN_NAME}"
echo "Make sure your Telegram bot ('${TELEGRAM_BOT_TOKEN:0:10}...') is running and configured correctly."
echo "Check service status with: sudo systemctl status moonvpn-api" 
echo "Check service status with: sudo systemctl status moonvpn-bot"
echo "Check logs with: journalctl -u moonvpn-api -f"
echo "Check logs with: journalctl -u moonvpn-bot -f"

exit 0 