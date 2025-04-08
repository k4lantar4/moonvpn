"""
Panel Cache

This module provides panel-specific caching functionality.
"""

import logging
from datetime import timedelta
from typing import Any, Optional

from core.cache.cache import get_cache

logger = logging.getLogger(__name__)


async def cache_panel_data(panel_id: int, key: str, data: Any, ttl: Optional[timedelta] = None) -> bool:
    """
    Cache data for a specific panel.
    
    Args:
        panel_id: Panel ID
        key: Cache key suffix
        data: Data to cache
        ttl: Time-to-live
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    full_key = f"panel:{panel_id}:{key}"
    return await cache.set(full_key, data, ttl)


async def get_cached_panel_data(panel_id: int, key: str, default: Any = None) -> Any:
    """
    Get cached data for a specific panel.
    
    Args:
        panel_id: Panel ID
        key: Cache key suffix
        default: Default value if not found
        
    Returns:
        Any: Cached data or default
    """
    cache = await get_cache()
    full_key = f"panel:{panel_id}:{key}"
    return await cache.get(full_key, default)


async def invalidate_panel_cache(panel_id: int) -> bool:
    """
    Invalidate all cached data for a specific panel.
    
    Args:
        panel_id: Panel ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    
    # We need to manually scan for keys since we're using a pattern
    try:
        redis = cache.redis
        await cache.setup()  # Ensure Redis is connected
        
        cursor = 0
        pattern = f"{cache.prefix}:panel:{panel_id}:*"
        deleted_count = 0
        
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted = await redis.delete(*keys)
                deleted_count += deleted
            if cursor == 0:
                break
                
        logger.info(f"Invalidated {deleted_count} cache keys for panel {panel_id}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating cache for panel {panel_id}: {str(e)}")
        return False


async def invalidate_specific_panel_cache(panel_id: int, key_pattern: str) -> bool:
    """
    Invalidate specific cached data for a panel.
    
    Args:
        panel_id: Panel ID
        key_pattern: Pattern for keys to invalidate
        
    Returns:
        bool: True if successful, False otherwise
    """
    cache = await get_cache()
    
    try:
        redis = cache.redis
        await cache.setup()  # Ensure Redis is connected
        
        cursor = 0
        pattern = f"{cache.prefix}:panel:{panel_id}:{key_pattern}"
        deleted_count = 0
        
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted = await redis.delete(*keys)
                deleted_count += deleted
            if cursor == 0:
                break
                
        logger.info(f"Invalidated {deleted_count} specific cache keys for panel {panel_id}")
        return True
    except Exception as e:
        logger.error(f"Error invalidating specific cache for panel {panel_id}: {str(e)}")
        return False 