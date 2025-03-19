#!/bin/bash
set -e

echo "🚀 Starting moonvpn Telegram Bot..."

echo "🔍 Checking environment..."
python -c "import os; print(f'Working directory: {os.getcwd()}')"
python -c "import sys; print(f'Python path: {sys.path}')"

echo "⏳ Waiting for database to be ready..."
python wait_for_db.py

echo "✅ Entrypoint completed successfully!"
echo "🤖 Running command: $@"

# Function to check if PostgreSQL is ready
function postgres_ready() {
  python -c 'import psycopg2; import os; import time; \
    while True: \
      try: \
        conn = psycopg2.connect( \
          dbname=os.environ.get("DB_NAME", "moonvpn"), \
          user=os.environ.get("DB_USER", "postgres"), \
          password=os.environ.get("DB_PASSWORD", "postgres"), \
          host=os.environ.get("DB_HOST", "db"), \
          port=os.environ.get("DB_PORT", "5432")); \
        conn.close(); \
        break; \
      except psycopg2.OperationalError: \
        print("PostgreSQL not ready yet. Waiting..."); \
        time.sleep(1); \
  '
}

# Function to check if Redis is ready
function redis_ready() {
  python -c 'import redis; import os; import time; \
    while True: \
      try: \
        r = redis.Redis( \
          host=os.environ.get("REDIS_HOST", "redis"), \
          port=int(os.environ.get("REDIS_PORT", "6379")), \
          password=os.environ.get("REDIS_PASSWORD", ""), \
          db=0); \
        r.ping(); \
        break; \
      except (redis.exceptions.ConnectionError, redis.exceptions.AuthenticationError): \
        print("Redis not ready yet. Waiting..."); \
        time.sleep(1); \
  '
}

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
postgres_ready

# Wait for Redis to be ready
echo "Waiting for Redis..."
redis_ready

# Wait for backend to be ready
echo "Waiting for backend API..."
python -c '
import requests
import time
import os

backend_url = os.environ.get("BACKEND_URL", "http://backend:8000")
health_endpoint = f"{backend_url}/health/"
max_retries = 30
retry = 0

while retry < max_retries:
    try:
        response = requests.get(health_endpoint, timeout=2)
        if response.status_code == 200:
            print("Backend API is ready!")
            break
    except requests.exceptions.RequestException:
        pass
    
    retry += 1
    print(f"Backend API not ready yet. Waiting... ({retry}/{max_retries})")
    time.sleep(2)

if retry >= max_retries:
    print("WARNING: Could not connect to backend API. Continuing anyway...")
'

# Check if the Telegram bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN environment variable is not set!"
    exit 1
fi

echo "Bot setup complete. Starting application..."

# Execute the command passed to the entrypoint
exec "$@"
