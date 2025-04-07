"""
Cache System

This module provides caching functionality for the application using Redis.
It supports key-value storage with automatic expiration, cache invalidation,
and specialized caching for panel responses and user sessions.
"""

import json
import logging
import pickle
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

import redis.asyncio as redis
from fastapi import Depends

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Type variable for function return types
T = TypeVar('T')

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
        """Set the expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time-to-live
            
        Returns:
            bool: True if successful, False otherwise
        """
        await self.setup()
        try:
            return bool(await self.redis.expire(self._make_key(key), int(ttl.total_seconds())))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {str(e)}")
            return False


# Cache instance
_cache: Optional[Cache] = None


async def get_cache() -> Cache:
    """
    Get or create a Cache instance.
    
    Returns:
        Cache: Cache instance
    """
    global _cache
    if _cache is None:
        redis_client = await get_redis()
        _cache = Cache(redis_client)
    return _cache


def cached(key_prefix: str, ttl: Optional[timedelta] = None):
    """
    Cache decorator for async functions.
    
    This decorator adds caching to an async function. The function's result
    is cached using a key derived from the key_prefix and the function's arguments.
    
    Args:
        key_prefix: Prefix for the cache key
        ttl: Time-to-live for cached results (optional)
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a cache key based on the arguments
            arg_str = ':'.join(str(arg) for arg in args if not isinstance(arg, redis.Redis) and not isinstance(arg, Cache))
            kwarg_str = ':'.join(f"{k}={v}" for k, v in sorted(kwargs.items()) if k != 'cache' and k != 'redis')
            
            cache_key = f"{key_prefix}:{arg_str}:{kwarg_str}"
            
            # Get or create cache
            cache = kwargs.get('cache')
            if cache is None:
                cache = await get_cache()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cast(T, cached_result)
            
            # Call the function and cache the result
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
            
        return wrapper
        
    return decorator


# Specialized cache wrappers for different types of data

async def cache_panel_data(panel_id: int, key: str, data: Any, ttl: Optional[timedelta] = None) -> bool:
    """
    Cache panel-specific data.
    
    Args:
        panel_id: Panel ID
        key: Data key
        data: Data to cache
        ttl: Time-to-live (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    cache_key = f"panel:{panel_id}:{key}"
    return await cache.set(cache_key, data, ttl=ttl)


async def get_cached_panel_data(panel_id: int, key: str, default: Any = None) -> Any:
    """
    Get cached panel-specific data.
    
    Args:
        panel_id: Panel ID
        key: Data key
        default: Default value if not found
        
    Returns:
        Any: Cached data or default
    """
    cache = await get_cache()
    cache_key = f"panel:{panel_id}:{key}"
    return await cache.get(cache_key, default=default)


async def invalidate_panel_cache(panel_id: int) -> bool:
    """
    Invalidate all cached data for a panel.
    
    Args:
        panel_id: Panel ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    try:
        redis_client = await get_redis()
        cursor = 0
        pattern = f"{cache.prefix}:panel:{panel_id}:*"
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
        return True
    except Exception as e:
        logger.error(f"Error invalidating panel cache for panel {panel_id}: {str(e)}")
        return False


async def invalidate_specific_panel_cache(panel_id: int, key_pattern: str) -> bool:
    """
    Invalidate specific cached data for a panel.
    
    Args:
        panel_id: Panel ID
        key_pattern: Pattern to match keys
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    try:
        redis_client = await get_redis()
        cursor = 0
        pattern = f"{cache.prefix}:panel:{panel_id}:{key_pattern}"
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
        return True
    except Exception as e:
        logger.error(f"Error invalidating specific panel cache for panel {panel_id}: {str(e)}")
        return False
