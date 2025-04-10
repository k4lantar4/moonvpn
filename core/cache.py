"""Redis client setup and utilities."""

import logging
from typing import Optional

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

# Assuming settings are available, adjust import if necessary
try:
    from core.config import settings
except ImportError:
    logging.warning("core.config.settings not found during cache module import.")
    settings = None # Or load a default mock

logger = logging.getLogger(__name__)

# Async Redis client singleton and pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None

async def init_redis_pool() -> Optional[redis.Redis]:
    """
    Initializes the asynchronous Redis connection pool and client.
    Should be called during application startup.

    Returns:
        The initialized Redis client instance if successful, otherwise None.
    """
    global _redis_pool, _redis_client
    if _redis_pool and _redis_client:
        logger.info("Redis pool and client already initialized.")
        return _redis_client

    if not settings or not settings.REDIS_URL:
        logger.warning("REDIS_URL not found in settings. Skipping Redis initialization.")
        return None

    try:
        logger.info(f"Initializing Redis connection pool for URL: {settings.REDIS_URL}")
        # Create connection pool using URL
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=10,  # Adjust as needed
            decode_responses=True, # Decode responses to strings
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        # Create Redis client
        _redis_client = redis.Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Successfully connected to Redis and pool initialized.")
        return _redis_client

    except RedisError as e:
        logger.error(f"Failed to initialize Redis connection pool: {e}", exc_info=True)
        _redis_pool = None
        _redis_client = None
        # Depending on requirements, you might want to raise the exception
        # raise ConnectionError(f"Failed to connect to Redis: {e}") from e
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during Redis initialization: {e}", exc_info=True)
        _redis_pool = None
        _redis_client = None
        return None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Returns the initialized asynchronous Redis client instance.

    Ensures the pool is initialized before returning the client.
    Might trigger initialization if not already done.

    Returns:
        The Redis client instance if initialized, otherwise None.
    """
    if _redis_client:
        return _redis_client

    # Attempt to initialize if not already done (e.g., if accessed before startup)
    logger.warning("Redis client accessed before explicit initialization. Attempting lazy init.")
    client = await init_redis_pool()
    return client


async def close_redis_pool():
    """Closes the Redis connection pool. Should be called during application shutdown."""
    global _redis_pool, _redis_client
    if _redis_pool:
        logger.info("Closing Redis connection pool.")
        try:
            await _redis_pool.disconnect()
            _redis_pool = None
            _redis_client = None
            logger.info("Redis connection pool closed.")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}", exc_info=True)
    else:
        logger.info("Redis pool already closed or not initialized.")

async def check_redis_connection() -> bool:
    """Asynchronously check if Redis connection is working."""
    client = await get_redis_client()
    if not client:
        return False
    try:
        return await client.ping()
    except RedisError as e:
        logger.error(f"Redis connection check failed: {e}")
        return False
