"""
Cache System

This module provides caching functionality for the application using Redis.
It supports key-value storage with automatic expiration and cache invalidation.
"""

import logging
import pickle
from datetime import timedelta
from typing import Any, Optional, TypeVar

import redis.asyncio as redis
from fastapi import Depends

from core.config import get_settings
from core.cache.redis import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()

# Type variable for function return types
T = TypeVar('T')


class Cache:
    """
    Redis-based cache implementation.
    
    This class provides methods for caching data in Redis with automatic
    serialization/deserialization and key prefixing.
    """
    
    def __init__(self, redis_client: redis.Redis = None):
        """
        Initialize the cache.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis = redis_client
        self.prefix = settings.CACHE_KEY_PREFIX
        self.default_ttl = timedelta(seconds=settings.CACHE_DEFAULT_TTL)
        
    async def setup(self):
        """Set up the cache (connect to Redis if not done already)."""
        if self.redis is None:
            self.redis = await get_redis()
    
    def _make_key(self, key: str) -> str:
        """Add prefix to the key.
        
        Args:
            key: Original key
            
        Returns:
            str: Prefixed key
        """
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value to return if key not found
            
        Returns:
            Any: Cached value or default
        """
        await self.setup()
        try:
            result = await self.redis.get(self._make_key(key))
            if result is None:
                return default
            return pickle.loads(result)
        except Exception as e:
            logger.error(f"Error getting key {key} from cache: {str(e)}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live (optional, uses default if not provided)
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self.setup()
        try:
            full_key = self._make_key(key)
            serialized = pickle.dumps(value)
            expiry = ttl or self.default_ttl
            return await self.redis.set(full_key, serialized, ex=int(expiry.total_seconds()))
        except Exception as e:
            logger.error(f"Error setting key {key} in cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        await self.setup()
        try:
            return bool(await self.redis.delete(self._make_key(key)))
        except Exception as e:
            logger.error(f"Error deleting key {key} from cache: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists, False otherwise
        """
        await self.setup()
        try:
            return bool(await self.redis.exists(self._make_key(key)))
        except Exception as e:
            logger.error(f"Error checking key {key} in cache: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all keys with the current prefix.
        
        Returns:
            bool: True if successful, False otherwise
        """
        await self.setup()
        try:
            cursor = 0
            pattern = f"{self.prefix}:*"
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a value in the cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by (default: 1)
            
        Returns:
            int: New value
        """
        await self.setup()
        try:
            return await self.redis.incrby(self._make_key(key), amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key} in cache: {str(e)}")
            return 0
    
    async def expire(self, key: str, ttl: timedelta) -> bool:
        """Set expiration on a key.
        
        Args:
            key: Cache key
            ttl: Time-to-live
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self.setup()
        try:
            return bool(await self.redis.expire(
                self._make_key(key), 
                int(ttl.total_seconds())
            ))
        except Exception as e:
            logger.error(f"Error setting expiry for key {key} in cache: {str(e)}")
            return False


async def get_cache() -> Cache:
    """
    Get a cache instance.
    
    Returns:
        Cache: Cache instance
    """
    redis_client = await get_redis()
    return Cache(redis_client) 