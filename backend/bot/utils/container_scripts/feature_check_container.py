"""
Feature check utilities for MoonVPN Telegram Bot.

This module contains functions for checking feature flags,
maintenance mode, and admin status.
"""

import logging
import aiohttp
import asyncio
import time
from functools import wraps
from typing import Callable, Any, Optional, Dict, Union, List

from telegram import Update
from telegram.ext import ContextTypes

from models import FeatureFlag, SystemConfig, User, Server
from core.utils.i18n import get_text

logger = logging.getLogger(__name__)

# Cache for server status
SERVER_STATUS_CACHE = {}
SERVER_CACHE_DURATION = 300  # seconds (5 minutes)

async def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature to check.
        
    Returns:
        True if the feature is enabled, False otherwise.
    """
    try:
        feature = await FeatureFlag.filter(name=feature_name).first()
        if feature:
            return feature.is_enabled
        return False
    except Exception as e:
        logger.error(f"Error checking feature {feature_name}: {str(e)}")
        return False

async def is_maintenance_mode() -> bool:
    """Check if maintenance mode is active.
    
    Returns:
        True if maintenance mode is active, False otherwise.
    """
    try:
        config = await SystemConfig.filter(key="maintenance_mode").first()
        if config:
            return config.value.lower() in ["true", "1", "yes"]
        return False
    except Exception as e:
        logger.error(f"Error checking maintenance mode: {str(e)}")
        return False

async def is_admin(user_id: Union[int, str]) -> bool:
    """Check if a user is an admin.
    
    Args:
        user_id: Telegram user ID.
        
    Returns:
        True if the user is an admin, False otherwise.
    """
    try:
        user = await User.filter(telegram_id=user_id).first()
        if user:
            return user.is_admin
        return False
    except Exception as e:
        logger.error(f"Error checking admin status for user {user_id}: {str(e)}")
        return False

async def get_admin_ids() -> List[int]:
    """Get all admin user IDs.
    
    Returns:
        List of admin user IDs.
    """
    try:
        admin_users = await User.filter(is_admin=True).all()
        return [user.telegram_id for user in admin_users]
    except Exception as e:
        logger.error(f"Error getting admin IDs: {str(e)}")
        return []

async def get_system_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a system configuration value.
    
    Args:
        key: Configuration key.
        default: Default value if key not found.
        
    Returns:
        Configuration value or default.
    """
    try:
        config = await SystemConfig.filter(key=key).first()
        if config:
            return config.value
        return default
    except Exception as e:
        logger.error(f"Error getting system config {key}: {str(e)}")
        return default

async def set_system_config(key: str, value: str) -> bool:
    """Set a system configuration value.
    
    Args:
        key: Configuration key.
        value: Configuration value.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        config, created = await SystemConfig.update_or_create(
            defaults={"value": value},
            key=key
        )
        return True
    except Exception as e:
        logger.error(f"Error setting system config {key}: {str(e)}")
        return False

async def toggle_feature(feature_name: str) -> bool:
    """Toggle a feature's enabled status.
    
    Args:
        feature_name: Name of the feature to toggle.
        
    Returns:
        New status of the feature (True if enabled, False if disabled).
    """
    try:
        feature = await FeatureFlag.filter(name=feature_name).first()
        if feature:
            feature.is_enabled = not feature.is_enabled
            await feature.save()
            return feature.is_enabled
            
        # Feature doesn't exist, create it and enable it
        feature = await FeatureFlag.create(name=feature_name, is_enabled=True)
        return True
    except Exception as e:
        logger.error(f"Error toggling feature {feature_name}: {str(e)}")
        return False

def is_payment_method_enabled(method: str) -> bool:
    """
    Check if a specific payment method is enabled.
    
    Args:
        method: The payment method to check ('card' or 'zarinpal')
        
    Returns:
        bool: True if the payment method is enabled, False otherwise
    """
    try:
        config = SystemConfig.objects.first()
        if not config:
            return method == 'card'  # Default to card payment if no config
        
        if method == 'card':
            return config.card_payment_enabled
        elif method == 'zarinpal':
            return config.zarinpal_enabled
        else:
            logger.warning(f"Unknown payment method: {method}")
            return False
    except Exception as e:
        logger.error(f"Error checking payment method '{method}': {e}")
        return method == 'card'  # Default to card payment on error

async def check_server_health(server_id: int) -> Dict[str, Any]:
    """
    Check the health of a server.
    
    Args:
        server_id: The ID of the server to check
        
    Returns:
        Dict: A dictionary containing server health information
    """
    # Check if we have a recent cached result
    cache_key = f"server_{server_id}"
    if cache_key in SERVER_STATUS_CACHE:
        cached_result = SERVER_STATUS_CACHE[cache_key]
        if time.time() - cached_result["timestamp"] < SERVER_CACHE_DURATION:
            return cached_result
    
    try:
        # Get server from database
        server = Server.objects.get(id=server_id)
        
        # Prepare result dictionary
        result = {
            "id": server.id,
            "name": server.name,
            "address": server.address,
            "is_active": server.is_active,
            "online": False,
            "latency": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "timestamp": time.time(),
            "error": None
        }
        
        # Skip health check if server is not active
        if not server.is_active:
            SERVER_STATUS_CACHE[cache_key] = result
            return result
            
        # Build API URL for health check
        url = f"http://{server.address}:{server.port}/api/health"
        auth = aiohttp.BasicAuth(server.username, server.password)
        
        # Measure response time
        start_time = time.time()
        
        try:
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=auth, timeout=5) as response:
                    latency = time.time() - start_time
                    
                    if response.status == 200:
                        # Parse response
                        data = await response.json()
                        
                        # Update result
                        result["online"] = True
                        result["latency"] = round(latency * 1000)  # Convert to ms
                        result["cpu_usage"] = data.get("cpu_usage", 0)
                        result["memory_usage"] = data.get("memory_usage", 0)
                    else:
                        result["error"] = f"HTTP Error: {response.status}"
                        
        except asyncio.TimeoutError:
            result["error"] = "Connection timeout"
        except Exception as e:
            result["error"] = str(e)
        
        # Cache result
        SERVER_STATUS_CACHE[cache_key] = result
        
        return result
    except Server.DoesNotExist:
        logger.error(f"Server {server_id} not found")
        return {
            "id": server_id,
            "name": "Unknown",
            "address": "Unknown",
            "is_active": False,
            "online": False,
            "latency": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "timestamp": time.time(),
            "error": "Server not found"
        }
    except Exception as e:
        logger.error(f"Error checking server health: {e}")
        return {
            "id": server_id,
            "name": "Unknown",
            "address": "Unknown",
            "is_active": False,
            "online": False,
            "latency": 0,
            "cpu_usage": 0,
            "memory_usage": 0,
            "timestamp": time.time(),
            "error": str(e)
        }

async def get_all_servers_health():
    """Get health status of all servers.
    
    Returns dict with:
        - total: total number of servers
        - online: number of online servers
        - offline: number of offline servers
        - servers: list of server status dicts
    """
    from models import Server
    
    servers = Server.get_all()
    total = len(servers)
    online = 0
    server_statuses = []
    
    for server in servers:
        # Consider active servers that have been successfully connected to as online
        if server.is_active:
            online += 1
            status = "online"
        else:
            status = "offline"
            
        server_statuses.append({
            "id": server.id,
            "name": server.name,
            "status": status,
            "location": server.location
        })
    
    return {
        "total": total,
        "online": online,
        "offline": total - online,
        "servers": server_statuses
    }

def require_feature(feature_name: str) -> Callable:
    """
    Decorator to check if a feature is enabled before executing a handler.
    If the feature is disabled, shows a message to the user.
    
    Args:
        feature_name: The name of the feature to check
        
    Returns:
        Callable: The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
            language_code = context.user_data.get("language", "en")
            
            # Check if the feature is enabled
            if not await is_feature_enabled(feature_name):
                # Send message that the feature is disabled
                message = get_text("feature_disabled", language_code).format(
                    feature=feature_name
                )
                
                if update.callback_query:
                    await update.callback_query.answer(message, show_alert=True)
                    await update.callback_query.edit_message_text(
                        get_text("feature_disabled_message", language_code),
                        reply_markup=None
                    )
                else:
                    await update.message.reply_text(message)
                
                return None
            
            # If maintenance mode is enabled and user is not an admin, block access
            if await is_maintenance_mode() and not await is_admin(update.effective_user.id):
                message = get_text("maintenance_mode_message", language_code)
                
                if update.callback_query:
                    await update.callback_query.answer(message, show_alert=True)
                else:
                    await update.message.reply_text(message)
                
                return None
            
            # Execute the handler
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    return decorator 