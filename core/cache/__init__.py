"""
Cache Module

This module provides caching functionality for the application.
"""

from core.cache.cache import Cache, get_cache
from core.cache.decorators import cached
from core.cache.panel import (
    cache_panel_data,
    get_cached_panel_data,
    invalidate_panel_cache,
    invalidate_specific_panel_cache,
)
from core.cache.redis import get_redis

__all__ = [
    "Cache",
    "get_cache",
    "cached",
    "cache_panel_data",
    "get_cached_panel_data",
    "invalidate_panel_cache",
    "invalidate_specific_panel_cache",
    "get_redis",
]
