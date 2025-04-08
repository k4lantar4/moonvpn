"""
Redis Client

This module provides a Redis client for the application.
"""

import logging
from typing import Optional

import redis.asyncio as redis

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get or create a Redis client instance.
    
    Returns:
        redis.Redis: Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        logger.info(f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=False,  # We'll handle decoding ourselves
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            _redis_client = None
            raise
            
    return _redis_client 