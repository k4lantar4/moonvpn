"""
Client Cache Module

This module provides a cache system for client data using Redis.
It handles caching client traffic, status, and configuration to reduce
API calls to the panels.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection pool
_redis_pool = None


async def get_redis() -> redis.Redis:
    """Get a Redis connection from the connection pool.
    
    Returns:
        redis.Redis: Redis connection
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )
    
    return redis.Redis(connection_pool=_redis_pool)


class ClientCache:
    """Cache system for client data.
    
    This class provides methods for caching and retrieving client data,
    including traffic, status, and configuration.
    """
    
    # Cache key prefixes
    TRAFFIC_PREFIX = f"{settings.CACHE_KEY_PREFIX}:client:traffic:"
    STATUS_PREFIX = f"{settings.CACHE_KEY_PREFIX}:client:status:"
    CONFIG_PREFIX = f"{settings.CACHE_KEY_PREFIX}:client:config:"
    ONLINE_PREFIX = f"{settings.CACHE_KEY_PREFIX}:client:online:"
    
    # Default TTLs in seconds
    TRAFFIC_TTL = 300  # 5 minutes
    STATUS_TTL = 300   # 5 minutes
    CONFIG_TTL = 3600  # 1 hour
    ONLINE_TTL = 60    # 1 minute
    
    @staticmethod
    async def cache_client_traffic(client_id: Union[int, str], traffic_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache client traffic data.
        
        Args:
            client_id: Client ID or email
            traffic_data: Traffic data to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.TRAFFIC_PREFIX}{client_id}"
        
        try:
            # Add timestamp to the data
            traffic_data["cached_at"] = datetime.utcnow().isoformat()
            
            # Store in Redis
            await redis_client.set(
                key, 
                json.dumps(traffic_data),
                ex=ttl or ClientCache.TRAFFIC_TTL
            )
            logger.debug(f"Cached traffic data for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache traffic data for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_client_traffic(client_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get cached client traffic data.
        
        Args:
            client_id: Client ID or email
            
        Returns:
            Optional[Dict[str, Any]]: Cached traffic data if found, None otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.TRAFFIC_PREFIX}{client_id}"
        
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached traffic data for client {client_id}: {str(e)}")
            return None
    
    @staticmethod
    async def cache_client_status(client_id: Union[int, str], status_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache client status data.
        
        Args:
            client_id: Client ID or email
            status_data: Status data to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.STATUS_PREFIX}{client_id}"
        
        try:
            # Add timestamp to the data
            status_data["cached_at"] = datetime.utcnow().isoformat()
            
            # Store in Redis
            await redis_client.set(
                key, 
                json.dumps(status_data),
                ex=ttl or ClientCache.STATUS_TTL
            )
            logger.debug(f"Cached status data for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache status data for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_client_status(client_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get cached client status data.
        
        Args:
            client_id: Client ID or email
            
        Returns:
            Optional[Dict[str, Any]]: Cached status data if found, None otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.STATUS_PREFIX}{client_id}"
        
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached status data for client {client_id}: {str(e)}")
            return None
    
    @staticmethod
    async def cache_client_config(client_id: Union[int, str], config_data: Dict[str, Any], ttl: int = None) -> bool:
        """Cache client configuration data.
        
        Args:
            client_id: Client ID or email
            config_data: Configuration data to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.CONFIG_PREFIX}{client_id}"
        
        try:
            # Add timestamp to the data
            config_data["cached_at"] = datetime.utcnow().isoformat()
            
            # Store in Redis
            await redis_client.set(
                key, 
                json.dumps(config_data),
                ex=ttl or ClientCache.CONFIG_TTL
            )
            logger.debug(f"Cached configuration data for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache configuration data for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_client_config(client_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get cached client configuration data.
        
        Args:
            client_id: Client ID or email
            
        Returns:
            Optional[Dict[str, Any]]: Cached configuration data if found, None otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.CONFIG_PREFIX}{client_id}"
        
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached configuration data for client {client_id}: {str(e)}")
            return None
    
    @staticmethod
    async def set_client_online(client_id: Union[int, str], is_online: bool, ttl: int = None) -> bool:
        """Set client online status.
        
        Args:
            client_id: Client ID or email
            is_online: Whether the client is online
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            bool: True if set successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.ONLINE_PREFIX}{client_id}"
        
        try:
            if is_online:
                # Store online status with timestamp
                data = {
                    "online": True,
                    "last_seen": datetime.utcnow().isoformat()
                }
                await redis_client.set(
                    key, 
                    json.dumps(data),
                    ex=ttl or ClientCache.ONLINE_TTL
                )
            else:
                # Remove online status
                await redis_client.delete(key)
                
            logger.debug(f"Set online status for client {client_id}: {is_online}")
            return True
        except Exception as e:
            logger.error(f"Failed to set online status for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def is_client_online(client_id: Union[int, str]) -> bool:
        """Check if client is online based on cached data.
        
        Args:
            client_id: Client ID or email
            
        Returns:
            bool: True if client is online, False otherwise
        """
        redis_client = await get_redis()
        key = f"{ClientCache.ONLINE_PREFIX}{client_id}"
        
        try:
            data = await redis_client.get(key)
            return bool(data)
        except Exception as e:
            logger.error(f"Failed to get online status for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def clear_client_cache(client_id: Union[int, str]) -> bool:
        """Clear all cached data for a client.
        
        Args:
            client_id: Client ID or email
            
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        redis_client = await get_redis()
        keys = [
            f"{ClientCache.TRAFFIC_PREFIX}{client_id}",
            f"{ClientCache.STATUS_PREFIX}{client_id}",
            f"{ClientCache.CONFIG_PREFIX}{client_id}",
            f"{ClientCache.ONLINE_PREFIX}{client_id}"
        ]
        
        try:
            for key in keys:
                await redis_client.delete(key)
            logger.debug(f"Cleared all cached data for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cached data for client {client_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_online_clients() -> List[str]:
        """Get list of online client IDs/emails.
        
        Returns:
            List[str]: List of online client IDs/emails
        """
        redis_client = await get_redis()
        pattern = f"{ClientCache.ONLINE_PREFIX}*"
        
        try:
            keys = await redis_client.keys(pattern)
            return [key.replace(ClientCache.ONLINE_PREFIX, "") for key in keys]
        except Exception as e:
            logger.error(f"Failed to get online clients: {str(e)}")
            return []
    
    @staticmethod
    async def close():
        """Close Redis connection pool."""
        global _redis_pool
        if _redis_pool:
            await _redis_pool.disconnect()
            _redis_pool = None 