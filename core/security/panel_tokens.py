"""
Panel Token Management

This module provides security functions for managing API tokens
for 3x-ui panels, including secure storage, retrieval, and renewal.
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

import redis.asyncio as redis
from cryptography.fernet import Fernet

from core.config import get_settings
from core.security import encrypt_text, decrypt_text

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


class PanelTokenManager:
    """Manager for panel API tokens.
    
    This class provides methods for:
    - Secure storage and retrieval of panel API tokens
    - Automatic token renewal
    - Token validation
    """
    
    # Redis key prefixes
    TOKEN_PREFIX = f"{settings.CACHE_KEY_PREFIX}:panel:token:"
    
    # Default settings
    DEFAULT_TOKEN_TTL = 43200  # 12 hours in seconds
    DEFAULT_RENEW_BEFORE = 3600  # Renew if less than 1 hour remaining
    
    @staticmethod
    async def store_token(
        panel_id: int,
        token: str,
        expires_at: Optional[datetime] = None,
        ttl: int = DEFAULT_TOKEN_TTL
    ) -> bool:
        """Store a panel API token securely.
        
        Args:
            panel_id: Panel ID
            token: API token
            expires_at: Token expiration datetime (if known)
            ttl: Time-to-live in Redis in seconds
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{PanelTokenManager.TOKEN_PREFIX}{panel_id}"
        
        try:
            # Encrypt token
            encrypted_token = encrypt_text(token, settings.PANEL_ENCRYPTION_KEY)
            
            # Prepare token data
            token_data = {
                "panel_id": panel_id,
                "token": encrypted_token,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if expires_at:
                token_data["expires_at"] = expires_at.isoformat()
                
                # Calculate TTL based on expiration time
                now = datetime.utcnow()
                if expires_at > now:
                    ttl = int((expires_at - now).total_seconds())
            
            # Store in Redis
            await redis_client.set(
                key,
                json.dumps(token_data),
                ex=ttl
            )
            
            logger.debug(f"Stored API token for panel {panel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store API token for panel {panel_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_token(panel_id: int) -> Optional[str]:
        """Get a panel API token.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Optional[str]: API token if found and valid, None otherwise
        """
        redis_client = await get_redis()
        key = f"{PanelTokenManager.TOKEN_PREFIX}{panel_id}"
        
        try:
            # Get token data from Redis
            data = await redis_client.get(key)
            if not data:
                logger.debug(f"No API token found for panel {panel_id}")
                return None
            
            token_data = json.loads(data)
            
            # Check if token has expired
            if "expires_at" in token_data:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                if expires_at <= datetime.utcnow():
                    logger.debug(f"API token for panel {panel_id} has expired")
                    return None
            
            # Decrypt token
            encrypted_token = token_data.get("token")
            if not encrypted_token:
                logger.error(f"Invalid token data for panel {panel_id}: missing token")
                return None
            
            token = decrypt_text(encrypted_token, settings.PANEL_ENCRYPTION_KEY)
            
            return token
        except Exception as e:
            logger.error(f"Failed to get API token for panel {panel_id}: {str(e)}")
            return None
    
    @staticmethod
    async def delete_token(panel_id: int) -> bool:
        """Delete a panel API token.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        redis_client = await get_redis()
        key = f"{PanelTokenManager.TOKEN_PREFIX}{panel_id}"
        
        try:
            result = await redis_client.delete(key)
            logger.debug(f"Deleted API token for panel {panel_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete API token for panel {panel_id}: {str(e)}")
            return False
    
    @staticmethod
    async def should_renew_token(panel_id: int, renew_before: int = DEFAULT_RENEW_BEFORE) -> bool:
        """Check if a token should be renewed.
        
        Args:
            panel_id: Panel ID
            renew_before: Seconds before expiration to trigger renewal
            
        Returns:
            bool: True if token should be renewed, False otherwise
        """
        redis_client = await get_redis()
        key = f"{PanelTokenManager.TOKEN_PREFIX}{panel_id}"
        
        try:
            # Get token data from Redis
            data = await redis_client.get(key)
            if not data:
                # No token found, should obtain a new one
                return True
            
            token_data = json.loads(data)
            
            # Check if token will expire soon
            if "expires_at" in token_data:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                now = datetime.utcnow()
                
                time_remaining = (expires_at - now).total_seconds()
                if time_remaining < renew_before:
                    logger.debug(f"API token for panel {panel_id} will expire soon, renewal needed")
                    return True
            
            # Check Redis TTL
            ttl = await redis_client.ttl(key)
            if ttl < renew_before:
                logger.debug(f"API token for panel {panel_id} will expire soon in Redis, renewal needed")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking token renewal for panel {panel_id}: {str(e)}")
            # On error, assume renewal is needed
            return True
    
    @staticmethod
    async def get_token_info(panel_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a token (excluding the token itself).
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Optional[Dict[str, Any]]: Token information if found, None otherwise
        """
        redis_client = await get_redis()
        key = f"{PanelTokenManager.TOKEN_PREFIX}{panel_id}"
        
        try:
            # Get token data from Redis
            data = await redis_client.get(key)
            if not data:
                return None
            
            token_data = json.loads(data)
            
            # Remove sensitive information
            if "token" in token_data:
                del token_data["token"]
            
            # Add TTL information
            ttl = await redis_client.ttl(key)
            token_data["ttl_seconds"] = ttl
            
            return token_data
        except Exception as e:
            logger.error(f"Failed to get token info for panel {panel_id}: {str(e)}")
            return None
    
    @staticmethod
    async def close():
        """Close Redis connection pool."""
        global _redis_pool
        if _redis_pool:
            await _redis_pool.disconnect() 