import json
import logging
from typing import Any, Optional, Union
from redis import Redis
from core.database.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
    REDIS_SSL,
    CACHE_TTL,
    CACHE_PREFIX
)

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis cache manager for handling caching operations"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                ssl=REDIS_SSL,
                decode_responses=True
            )
            # Test connection
            self.redis.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            raise

    def _get_key(self, key: str) -> str:
        """Get full cache key with prefix"""
        return f"{CACHE_PREFIX}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = self._get_key(key)
            value = self.redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting value from cache: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            full_key = self._get_key(key)
            value_json = json.dumps(value)
            self.redis.set(full_key, value_json, ex=ttl or CACHE_TTL)
            return True
        except Exception as e:
            logger.error(f"Error setting value in cache: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            full_key = self._get_key(key)
            self.redis.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting value from cache: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            full_key = self._get_key(key)
            return bool(self.redis.exists(full_key))
        except Exception as e:
            logger.error(f"Error checking key existence in cache: {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cache keys with prefix"""
        try:
            pattern = f"{CACHE_PREFIX}*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache"""
        try:
            full_keys = [self._get_key(key) for key in keys]
            values = self.redis.mget(full_keys)
            return {
                key: json.loads(value) if value else None
                for key, value in zip(keys, values)
            }
        except Exception as e:
            logger.error(f"Error getting multiple values from cache: {str(e)}")
            return {}

    def set_many(self, items: dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache"""
        try:
            pipeline = self.redis.pipeline()
            for key, value in items.items():
                full_key = self._get_key(key)
                value_json = json.dumps(value)
                pipeline.set(full_key, value_json, ex=ttl or CACHE_TTL)
            pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Error setting multiple values in cache: {str(e)}")
            return False

    def delete_many(self, keys: list[str]) -> bool:
        """Delete multiple values from cache"""
        try:
            full_keys = [self._get_key(key) for key in keys]
            self.redis.delete(*full_keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting multiple values from cache: {str(e)}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in cache"""
        try:
            full_key = self._get_key(key)
            return self.redis.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"Error incrementing value in cache: {str(e)}")
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value in cache"""
        try:
            full_key = self._get_key(key)
            return self.redis.decrby(full_key, amount)
        except Exception as e:
            logger.error(f"Error decrementing value in cache: {str(e)}")
            return None

    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key"""
        try:
            full_key = self._get_key(key)
            return self.redis.ttl(full_key)
        except Exception as e:
            logger.error(f"Error getting TTL from cache: {str(e)}")
            return None

    def set_ttl(self, key: str, ttl: int) -> bool:
        """Set TTL for key"""
        try:
            full_key = self._get_key(key)
            return bool(self.redis.expire(full_key, ttl))
        except Exception as e:
            logger.error(f"Error setting TTL in cache: {str(e)}")
            return False

# Create global cache instance
cache = CacheManager() 