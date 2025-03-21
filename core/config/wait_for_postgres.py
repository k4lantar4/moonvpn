import os
import sys
import time
import socket
import psycopg2

# Get connection details from environment variables
host = os.environ.get("DB_HOST", "postgres")
port = int(os.environ.get("DB_PORT", "5432"))
user = os.environ.get("DB_USER", "moonvpn")
password = os.environ.get("DB_PASSWORD", "moonvpn")
dbname = os.environ.get("DB_NAME", "moonvpn")
max_attempts = int(os.environ.get("POSTGRES_MAX_ATTEMPTS", "60"))

def is_postgresql_ready():
    """Check if PostgreSQL server is ready to accept connections."""
    try:
        # First try a socket connection to see if the server is up
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
        
        # Then try a database connection to ensure the database exists
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=3
        )
        conn.close()
        return True
    except (socket.error, psycopg2.OperationalError):
        return False

def main():
    """Wait for PostgreSQL to be ready."""
    attempt = 0
    
    while attempt < max_attempts:
        if is_postgresql_ready():
            print(f"PostgreSQL is up and running on {host}:{port}! ✅")
            return 0
        
        attempt += 1
        print(f"Waiting for PostgreSQL on {host}:{port}... (Attempt {attempt}/{max_attempts})")
        time.sleep(1)
    
    print(f"Could not connect to PostgreSQL after {max_attempts} attempts! ❌")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 