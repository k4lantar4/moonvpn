"""
VPN service for managing servers, traffic, and user accounts.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
import asyncio

from core.config import settings
from core.utils.helpers import format_size, format_number
from core.database import get_db

logger = logging.getLogger(__name__)

class VPNService:
    """Service for managing VPN servers and user accounts."""
    
    def __init__(self):
        """Initialize VPN service."""
        self.api_url = settings.PANEL_API_URL
        self.api_key = settings.PANEL_API_KEY
        self.db = get_db()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """Make HTTP request to panel API."""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    f"{self.api_url}/{endpoint}",
                    headers=headers,
                    **kwargs
                ) as response:
                    if response.status == 200:
                        return True, await response.json()
                    else:
                        error_data = await response.json()
                        logger.error(
                            "Panel API error: %s %s - %s",
                            method, endpoint, error_data.get('message', 'Unknown error')
                        )
                        return False, error_data.get('message', 'خطای ناشناخته')
                        
        except aiohttp.ClientError as e:
            logger.error("Panel API connection error: %s", str(e))
            return False, "خطا در ارتباط با پنل"
        except Exception as e:
            logger.error("Unexpected error in panel API request: %s", str(e))
            return False, "خطای غیرمنتظره"
    
    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of all VPN servers."""
        success, result = await self._make_request('GET', 'servers')
        if success:
            return result['servers']
        return []
    
    async def get_server_status(self) -> List[Dict[str, Any]]:
        """Get detailed status of all servers."""
        success, result = await self._make_request('GET', 'servers/status')
        if success:
            return result['status']
        return []
    
    async def get_server_settings(self) -> Dict[str, Any]:
        """Get server settings."""
        success, result = await self._make_request('GET', 'servers/settings')
        if success:
            return result['settings']
        return {
            'security': {
                'protocol': 'Unknown',
                'encryption': 'Unknown',
                'authentication': 'Unknown'
            },
            'performance': {
                'max_users': 0,
                'bandwidth_limit': 0,
                'tcp_buffer': 0
            },
            'backup': {
                'enabled': False,
                'schedule': 'Never',
                'retention': 0
            }
        }
    
    async def create_server(
        self,
        name: str,
        host: str,
        port: int,
        location_id: str
    ) -> Tuple[bool, Any]:
        """Create a new VPN server."""
        data = {
            'name': name,
            'host': host,
            'port': port,
            'location_id': location_id
        }
        return await self._make_request('POST', 'servers', json=data)
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get list of available server locations."""
        success, result = await self._make_request('GET', 'locations')
        if success:
            return result['locations']
        return []
    
    async def get_traffic_stats(self, period: str = 'daily') -> Dict[str, Any]:
        """Get traffic usage statistics for the specified period."""
        success, result = await self._make_request('GET', f'traffic/stats/{period}')
        if success:
            return result['stats']
        return {
            'total_usage': 0,
            'active_users': 0,
            'average_usage': 0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hourly_breakdown': []
        }
    
    async def get_top_users(self, period: str = 'daily', limit: int = 5) -> List[Dict[str, Any]]:
        """Get top traffic users for the specified period."""
        success, result = await self._make_request(
            'GET',
            f'traffic/top-users/{period}',
            params={'limit': limit}
        )
        if success:
            return result['users']
        return []
    
    async def get_traffic_alerts(self) -> List[Dict[str, Any]]:
        """Get traffic usage alerts."""
        success, result = await self._make_request('GET', 'traffic/alerts')
        if success:
            return result['alerts']
        return []
    
    async def create_user_account(
        self,
        username: str,
        password: str,
        server_id: str,
        duration_days: int,
        traffic_limit_gb: Optional[int] = None
    ) -> Tuple[bool, Any]:
        """Create a new VPN user account."""
        data = {
            'username': username,
            'password': password,
            'server_id': server_id,
            'duration_days': duration_days
        }
        if traffic_limit_gb:
            data['traffic_limit'] = traffic_limit_gb * 1024 * 1024 * 1024  # Convert GB to bytes
        
        return await self._make_request('POST', 'users', json=data)
    
    async def get_user_traffic(self, username: str) -> Dict[str, Any]:
        """Get traffic usage for a specific user."""
        success, result = await self._make_request('GET', f'users/{username}/traffic')
        if success:
            return result['traffic']
        return {
            'total_usage': 0,
            'upload': 0,
            'download': 0,
            'last_connected': None
        }
    
    async def change_user_server(
        self,
        username: str,
        new_server_id: str
    ) -> Tuple[bool, Any]:
        """Change user's VPN server."""
        data = {'server_id': new_server_id}
        return await self._make_request(
            'POST',
            f'users/{username}/change-server',
            json=data
        )
    
    async def extend_user_account(
        self,
        username: str,
        days: int,
        traffic_gb: Optional[int] = None
    ) -> Tuple[bool, Any]:
        """Extend user's VPN account duration and/or traffic limit."""
        data = {'days': days}
        if traffic_gb:
            data['traffic'] = traffic_gb * 1024 * 1024 * 1024  # Convert GB to bytes
        
        return await self._make_request(
            'POST',
            f'users/{username}/extend',
            json=data
        )
    
    async def disable_user_account(self, username: str) -> Tuple[bool, Any]:
        """Disable a user's VPN account."""
        return await self._make_request('POST', f'users/{username}/disable')
    
    async def enable_user_account(self, username: str) -> Tuple[bool, Any]:
        """Enable a user's VPN account."""
        return await self._make_request('POST', f'users/{username}/enable')
    
    async def delete_user_account(self, username: str) -> Tuple[bool, Any]:
        """Delete a user's VPN account."""
        return await self._make_request('DELETE', f'users/{username}') 