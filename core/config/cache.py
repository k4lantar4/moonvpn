"""
Cache implementation for service integration.
"""
from typing import Any, Optional
import json
import logging
from datetime import datetime, timedelta

import aioredis
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

class Cache:
    """Redis-based cache implementation."""
    
    def __init__(self):
        self._redis = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
            
        try:
            self._redis = await aioredis.create_redis_pool(
                settings.REDIS_URL,
                minsize=settings.REDIS_POOL_MIN_SIZE,
                maxsize=settings.REDIS_POOL_MAX_SIZE,
                timeout=settings.REDIS_TIMEOUT
            )
            self._initialized = True
            logger.info("Cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Cache initialization failed: {str(e)}"
            )
            
    async def cleanup(self) -> None:
        """Cleanup Redis connection."""
        if self._redis is not None:
            self._redis.close()
            await self._redis.wait_closed()
            self._initialized = False
            logger.info("Cache cleaned up successfully")
            
    def _check_initialized(self) -> None:
        """Check if cache is initialized."""
        if not self._initialized:
            raise HTTPException(
                status_code=500,
                detail="Cache not initialized"
            )
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._check_initialized()
        
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
                
            return json.loads(data)
            
        except Exception as e:
            logger.error(f"Failed to get from cache - key: {key}, error: {str(e)}")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300  # 5 minutes default
    ) -> None:
        """Set value in cache with TTL."""
        self._check_initialized()
        
        try:
            data = json.dumps(value)
            await self._redis.set(key, data, expire=ttl)
            
        except Exception as e:
            logger.error(f"Failed to set in cache - key: {key}, error: {str(e)}")
            
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._check_initialized()
        
        try:
            await self._redis.delete(key)
            
        except Exception as e:
            logger.error(f"Failed to delete from cache - key: {key}, error: {str(e)}")
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        self._check_initialized()
        
        try:
            return await self._redis.exists(key)
            
        except Exception as e:
            logger.error(f"Failed to check cache existence - key: {key}, error: {str(e)}")
            return False
            
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache."""
        self._check_initialized()
        
        try:
            return await self._redis.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Failed to increment cache - key: {key}, error: {str(e)}")
            return 0
            
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter in cache."""
        self._check_initialized()
        
        try:
            return await self._redis.decrby(key, amount)
            
        except Exception as e:
            logger.error(f"Failed to decrement cache - key: {key}, error: {str(e)}")
            return 0
            
    async def set_many(self, mapping: dict, ttl: int = 300) -> None:
        """Set multiple values in cache."""
        self._check_initialized()
        
        try:
            pipeline = self._redis.pipeline()
            for key, value in mapping.items():
                data = json.dumps(value)
                pipeline.set(key, data, expire=ttl)
            await pipeline.execute()
            
        except Exception as e:
            logger.error(f"Failed to set many in cache - error: {str(e)}")
            
    async def get_many(self, keys: list) -> dict:
        """Get multiple values from cache."""
        self._check_initialized()
        
        try:
            pipeline = self._redis.pipeline()
            for key in keys:
                pipeline.get(key)
            values = await pipeline.execute()
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = json.loads(value)
                    
            return result
            
        except Exception as e:
            logger.error(f"Failed to get many from cache - error: {str(e)}")
            return {}
            
    async def delete_many(self, keys: list) -> None:
        """Delete multiple values from cache."""
        self._check_initialized()
        
        try:
            pipeline = self._redis.pipeline()
            for key in keys:
                pipeline.delete(key)
            await pipeline.execute()
            
        except Exception as e:
            logger.error(f"Failed to delete many from cache - error: {str(e)}")
            
    async def clear(self) -> None:
        """Clear all cache data."""
        self._check_initialized()
        
        try:
            await self._redis.flushdb()
            
        except Exception as e:
            logger.error(f"Failed to clear cache - error: {str(e)}")
            
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for key in seconds."""
        self._check_initialized()
        
        try:
            ttl = await self._redis.ttl(key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"Failed to get TTL - key: {key}, error: {str(e)}")
            return None
            
    async def set_ttl(self, key: str, ttl: int) -> None:
        """Set TTL for key in seconds."""
        self._check_initialized()
        
        try:
            await self._redis.expire(key, ttl)
            
        except Exception as e:
            logger.error(f"Failed to set TTL - key: {key}, error: {str(e)}")
            
    async def remove_ttl(self, key: str) -> None:
        """Remove TTL from key."""
        self._check_initialized()
        
        try:
            await self._redis.persist(key)
            
        except Exception as e:
            logger.error(f"Failed to remove TTL - key: {key}, error: {str(e)}")

# Create singleton instance
cache = Cache() 