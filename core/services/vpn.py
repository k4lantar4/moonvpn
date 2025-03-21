"""
VPN service for MoonVPN.

This module contains the VPN service class that handles all VPN-related operations,
including user management, subscription handling, and system monitoring.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
from fastapi import HTTPException

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription
from app.models.server import Server

# Setup logging
logger = logging.getLogger(__name__)

class VPNService:
    """Service class for handling VPN operations."""
    
    def __init__(self):
        """Initialize the VPN service."""
        self.panel_url = settings.PANEL_API_URL
        self.username = settings.PANEL_API_USERNAME
        self.password = settings.PANEL_API_PASSWORD.get_secret_value()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the VPN panel API."""
        session = await self._get_session()
        url = f"{self.panel_url}{endpoint}"
        
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                elif response.status == 403:
                    raise HTTPException(status_code=403, detail="Access denied")
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail="Resource not found")
                elif response.status >= 500:
                    raise HTTPException(status_code=500, detail="Server error")
                
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error making request to VPN panel: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to VPN panel")
    
    async def register_user(self, telegram_id: int, email: str) -> User:
        """Register a new user in the VPN system."""
        try:
            # Create user in panel
            data = {
                "username": f"user_{telegram_id}",
                "email": email,
                "password": f"moonvpn_{telegram_id}",  # Temporary password
                "expire": (datetime.now() + timedelta(days=1)).timestamp(),
                "data_limit": 0,  # Unlimited
                "status": "active"
            }
            
            response = await self._make_request(
                "POST",
                "/api/v1/users",
                json=data,
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            # Create user in database
            user = User(
                telegram_id=telegram_id,
                email=email,
                panel_id=response["id"],
                username=response["username"],
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # TODO: Save user to database
            
            return user
            
        except Exception as e:
            logger.error(f"Error registering user {telegram_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to register user")
    
    async def get_user_status(self, telegram_id: int) -> Dict[str, Any]:
        """Get the status of a user's VPN subscription."""
        try:
            # TODO: Get user from database
            
            # Get user status from panel
            response = await self._make_request(
                "GET",
                f"/api/v1/users/{telegram_id}",
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            return {
                "subscription": response["status"],
                "expires": datetime.fromtimestamp(response["expire"]).strftime("%Y-%m-%d %H:%M:%S"),
                "active": response["status"] == "active",
                "data_used": f"{response['used_traffic'] / 1024 / 1024 / 1024:.2f} GB"
            }
            
        except Exception as e:
            logger.error(f"Error getting status for user {telegram_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user status")
    
    async def get_all_users(self) -> List[User]:
        """Get all users from the VPN system."""
        try:
            # Get users from panel
            response = await self._make_request(
                "GET",
                "/api/v1/users",
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            # TODO: Get users from database and merge with panel data
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            raise HTTPException(status_code=500, detail="Failed to get users list")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get the overall system status."""
        try:
            # Get system status from panel
            response = await self._make_request(
                "GET",
                "/api/v1/system/status",
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            return {
                "active_users": response["active_users"],
                "total_users": response["total_users"],
                "system_load": response["system_load"],
                "uptime": response["uptime"]
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system status")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            # Get system stats from panel
            response = await self._make_request(
                "GET",
                "/api/v1/system/stats",
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            return {
                "total_traffic": f"{response['total_traffic'] / 1024 / 1024 / 1024:.2f} GB",
                "active_connections": response["active_connections"],
                "revenue": response["revenue"],
                "new_users_today": response["new_users_today"]
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system stats")
    
    async def update_subscription(self, telegram_id: int, plan_id: str) -> Subscription:
        """Update a user's subscription plan."""
        try:
            # TODO: Get user from database
            
            # Update subscription in panel
            data = {
                "expire": (datetime.now() + timedelta(days=30)).timestamp(),  # TODO: Get plan duration
                "status": "active"
            }
            
            response = await self._make_request(
                "PUT",
                f"/api/v1/users/{telegram_id}",
                json=data,
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            # TODO: Update subscription in database
            
            return Subscription(
                user_id=telegram_id,
                plan_id=plan_id,
                status="active",
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),  # TODO: Get plan duration
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error updating subscription for user {telegram_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update subscription")
    
    async def get_available_servers(self) -> List[Server]:
        """Get list of available VPN servers."""
        try:
            # Get servers from panel
            response = await self._make_request(
                "GET",
                "/api/v1/servers",
                auth=aiohttp.BasicAuth(self.username, self.password)
            )
            
            servers = []
            for server_data in response:
                server = Server(
                    id=server_data["id"],
                    name=server_data["name"],
                    host=server_data["host"],
                    port=server_data["port"],
                    protocol=server_data["protocol"],
                    status=server_data["status"],
                    load=server_data["load"],
                    created_at=datetime.fromtimestamp(server_data["created_at"]),
                    updated_at=datetime.fromtimestamp(server_data["updated_at"])
                )
                servers.append(server)
            
            return servers
            
        except Exception as e:
            logger.error(f"Error getting available servers: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available servers")
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close() 