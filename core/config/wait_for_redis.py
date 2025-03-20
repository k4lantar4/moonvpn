import os
import sys
import time
import socket
import redis

# Get connection details from environment variables
host = os.environ.get("REDIS_HOST", "redis")
port = int(os.environ.get("REDIS_PORT", "6379"))
password = os.environ.get("REDIS_PASSWORD", "")
max_attempts = int(os.environ.get("REDIS_MAX_ATTEMPTS", "60"))

def is_redis_ready():
    """Check if Redis server is ready to accept connections."""
    try:
        # First try a socket connection to see if the server is up
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
        
        # Then try a Redis ping to verify the server is responding
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            socket_timeout=3
        )
        r.ping()
        return True
    except (socket.error, redis.RedisError):
        return False

def main():
    """Wait for Redis to be ready."""
    attempt = 0
    
    while attempt < max_attempts:
        if is_redis_ready():
            print(f"Redis is up and running on {host}:{port}! ✅")
            return 0
        
        attempt += 1
        print(f"Waiting for Redis on {host}:{port}... (Attempt {attempt}/{max_attempts})")
        time.sleep(1)
    
    print(f"Could not connect to Redis after {max_attempts} attempts! ❌")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 