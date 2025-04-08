import logging
from typing import Optional

import redis

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client singleton
_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    """Returns a Redis client instance.
    
    The client is created with a connection pool and cached for reuse.
    
    Returns:
        redis.Redis: A configured Redis client
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            # Create connection pool
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=10,  # Default max connections
                decode_responses=True,  # Automatically decode responses to strings
                socket_timeout=5,  # Socket timeout in seconds
                socket_connect_timeout=5,  # Connection timeout
                retry_on_timeout=True,  # Retry on timeout
            )
            
            # Create Redis client
            _redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            _redis_client.ping()
            logger.info("Successfully connected to Redis")
            
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    return _redis_client

def check_redis_connection() -> bool:
    """Check if Redis connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        redis_client = get_redis()
        return redis_client.ping()
    except redis.RedisError as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return False 