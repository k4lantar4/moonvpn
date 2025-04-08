"""
Cache Decorators

This module provides decorators for caching function results.
"""

import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from core.cache.cache import Cache, get_cache

logger = logging.getLogger(__name__)

# Type variable for function return types
T = TypeVar('T')


def cached(key_prefix: str, ttl: Optional[timedelta] = None):
    """
    Decorator for caching function results.
    
    Args:
        key_prefix: Prefix for cache keys
        ttl: Time-to-live for cached results
        
    Returns:
        Callable: Decorator function
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a cache key based on the arguments
            cache_args = [str(arg) for arg in args[1:]]  # Skip 'self' if it exists
            cache_kwargs = {k: str(v) for k, v in kwargs.items()}
            args_key = json.dumps([cache_args, cache_kwargs], sort_keys=True)
            cache_key = f"{key_prefix}:{func.__name__}:{args_key}"
            
            # Get cache
            cache = await get_cache()
            
            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cast(T, cached_result)
            
            # Not in cache, call the function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator 