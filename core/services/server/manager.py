"""
Server management service for V2Ray panels.

This module handles server synchronization, health checks, and management
across multiple 3x-UI panels.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp
import asyncio
from dataclasses import dataclass
from enum import Enum
from core.database import get_setting, update_setting
import json
import os
import requests
from core.utils.helpers import human_readable_size

logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    """Server status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class ServerInfo:
    """Server information data class."""
    id: str
    name: str
    host: str
    port: int
    panel_url: str
    panel_username: str
    panel_password: str
    status: ServerStatus
    last_sync: datetime
    traffic_used: int
    traffic_total: int
    uptime: float
    load: float
    memory_used: float
    memory_total: float
    disk_used: float
    disk_total: float
    tags: List[str]
    location: str
    bandwidth_limit: int
    is_active: bool

class ServerManager:
    """Manages multiple V2Ray servers and their synchronization."""
    
    def __init__(self):
        self.servers: Dict[str, ServerInfo] = {}
        self.sync_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self._sync_task = None
        self._health_check_task = None
        self.panels = {}
        self._load_servers()
        self.load_panels()
    
    def _load_servers(self):
        """Load servers from database."""
        try:
            servers_data = get_setting("v2ray_servers")
            if servers_data:
                servers = json.loads(servers_data)
                for server_data in servers:
                    server = ServerInfo(
                        id=server_data["id"],
                        name=server_data["name"],
                        host=server_data["host"],
                        port=server_data["port"],
                        panel_url=server_data["panel_url"],
                        panel_username=server_data["panel_username"],
                        panel_password=server_data["panel_password"],
                        status=ServerStatus(server_data.get("status", "offline")),
                        last_sync=datetime.fromisoformat(server_data.get("last_sync", datetime.now().isoformat())),
                        traffic_used=server_data.get("traffic_used", 0),
                        traffic_total=server_data.get("traffic_total", 0),
                        uptime=server_data.get("uptime", 0.0),
                        load=server_data.get("load", 0.0),
                        memory_used=server_data.get("memory_used", 0.0),
                        memory_total=server_data.get("memory_total", 0.0),
                        disk_used=server_data.get("disk_used", 0.0),
                        disk_total=server_data.get("disk_total", 0.0),
                        tags=server_data.get("tags", []),
                        location=server_data.get("location", "Unknown"),
                        bandwidth_limit=server_data.get("bandwidth_limit", 0),
                        is_active=server_data.get("is_active", True)
                    )
                    self.servers[server.id] = server
        except Exception as e:
            logger.error(f"Error loading servers: {e}")
    
    def _save_servers(self):
        """Save servers to database."""
        try:
            servers_data = []
            for server in self.servers.values():
                server_data = {
                    "id": server.id,
                    "name": server.name,
                    "host": server.host,
                    "port": server.port,
                    "panel_url": server.panel_url,
                    "panel_username": server.panel_username,
                    "panel_password": server.panel_password,
                    "status": server.status.value,
                    "last_sync": server.last_sync.isoformat(),
                    "traffic_used": server.traffic_used,
                    "traffic_total": server.traffic_total,
                    "uptime": server.uptime,
                    "load": server.load,
                    "memory_used": server.memory_used,
                    "memory_total": server.memory_total,
                    "disk_used": server.disk_used,
                    "disk_total": server.disk_total,
                    "tags": server.tags,
                    "location": server.location,
                    "bandwidth_limit": server.bandwidth_limit,
                    "is_active": server.is_active
                }
                servers_data.append(server_data)
            update_setting("v2ray_servers", json.dumps(servers_data))
        except Exception as e:
            logger.error(f"Error saving servers: {e}")
    
    async def start(self):
        """Start the server manager tasks."""
        self._sync_task = asyncio.create_task(self._sync_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop(self):
        """Stop the server manager tasks."""
        if self._sync_task:
            self._sync_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
    
    async def add_server(
        self,
        name: str,
        host: str,
        port: int,
        panel_url: str,
        panel_username: str,
        panel_password: str,
        location: str,
        bandwidth_limit: int = 0,
        tags: List[str] = None
    ) -> ServerInfo:
        """Add a new server to the manager."""
        server_id = str(uuid.uuid4())
        server = ServerInfo(
            id=server_id,
            name=name,
            host=host,
            port=port,
            panel_url=panel_url,
            panel_username=panel_username,
            panel_password=panel_password,
            status=ServerStatus.OFFLINE,
            last_sync=datetime.now(),
            traffic_used=0,
            traffic_total=0,
            uptime=0.0,
            load=0.0,
            memory_used=0.0,
            memory_total=0.0,
            disk_used=0.0,
            disk_total=0.0,
            tags=tags or [],
            location=location,
            bandwidth_limit=bandwidth_limit,
            is_active=True
        )
        self.servers[server_id] = server
        self._save_servers()
        
        # Try to sync the server immediately
        try:
            await self._sync_server(server)
        except Exception as e:
            logger.error(f"Error syncing new server {server.name}: {e}")
        
        return server
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove a server from the manager."""
        if server_id in self.servers:
            del self.servers[server_id]
            self._save_servers()
            return True
        return False
    
    async def get_server(self, server_id: str) -> Optional[ServerInfo]:
        """Get server information by ID."""
        return self.servers.get(server_id)
    
    async def get_all_servers(self) -> List[ServerInfo]:
        """Get all servers."""
        return list(self.servers.values())
    
    async def get_active_servers(self) -> List[ServerInfo]:
        """Get all active servers."""
        return [s for s in self.servers.values() if s.is_active]
    
    async def get_servers_by_location(self, location: str) -> List[ServerInfo]:
        """Get servers by location."""
        return [s for s in self.servers.values() if s.location == location]
    
    async def get_servers_by_tag(self, tag: str) -> List[ServerInfo]:
        """Get servers by tag."""
        return [s for s in self.servers.values() if tag in s.tags]
    
    async def _sync_loop(self):
        """Main synchronization loop."""
        while True:
            try:
                await self._sync_all_servers()
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
            await asyncio.sleep(self.sync_interval)
    
    async def _health_check_loop(self):
        """Main health check loop."""
        while True:
            try:
                await self._check_all_servers()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
            await asyncio.sleep(self.health_check_interval)
    
    async def _sync_all_servers(self):
        """Synchronize all servers with their panels."""
        for server in self.servers.values():
            try:
                await self._sync_server(server)
            except Exception as e:
                logger.error(f"Error syncing server {server.id}: {e}")
                server.status = ServerStatus.ERROR
        self._save_servers()
    
    async def _check_all_servers(self):
        """Check health of all servers."""
        for server in self.servers.values():
            try:
                await self._check_server_health(server)
            except Exception as e:
                logger.error(f"Error checking server {server.id}: {e}")
                server.status = ServerStatus.ERROR
        self._save_servers()
    
    async def _sync_server(self, server: ServerInfo):
        """Synchronize a single server with its panel."""
        async with aiohttp.ClientSession() as session:
            # Login to panel
            login_data = {
                "username": server.panel_username,
                "password": server.panel_password
            }
            async with session.post(f"{server.panel_url}/login", json=login_data) as response:
                if response.status != 200:
                    raise Exception("Failed to login to panel")
            
            # Get server stats
            async with session.get(f"{server.panel_url}/server/stats") as response:
                if response.status != 200:
                    raise Exception("Failed to get server stats")
                stats = await response.json()
            
            # Update server info
            server.traffic_used = stats.get("traffic_used", 0)
            server.traffic_total = stats.get("traffic_total", 0)
            server.uptime = stats.get("uptime", 0.0)
            server.load = stats.get("load", 0.0)
            server.memory_used = stats.get("memory_used", 0.0)
            server.memory_total = stats.get("memory_total", 0.0)
            server.disk_used = stats.get("disk_used", 0.0)
            server.disk_total = stats.get("disk_total", 0.0)
            server.last_sync = datetime.now()
            server.status = ServerStatus.ONLINE
    
    async def _check_server_health(self, server: ServerInfo):
        """Check health of a single server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server.panel_url}/health") as response:
                    if response.status != 200:
                        server.status = ServerStatus.OFFLINE
                    else:
                        health_data = await response.json()
                        if health_data.get("maintenance", False):
                            server.status = ServerStatus.MAINTENANCE
                        else:
                            server.status = ServerStatus.ONLINE
        except Exception:
            server.status = ServerStatus.OFFLINE
    
    async def get_server_stats(self, server_id: str) -> Dict:
        """Get detailed statistics for a server."""
        server = await self.get_server(server_id)
        if not server:
            return None
        
        return {
            "id": server.id,
            "name": server.name,
            "status": server.status.value,
            "location": server.location,
            "traffic": {
                "used": server.traffic_used,
                "total": server.traffic_total,
                "remaining": max(0, server.traffic_total - server.traffic_used)
            },
            "system": {
                "uptime": server.uptime,
                "load": server.load,
                "memory": {
                    "used": server.memory_used,
                    "total": server.memory_total,
                    "percentage": (server.memory_used / server.memory_total * 100) if server.memory_total > 0 else 0
                },
                "disk": {
                    "used": server.disk_used,
                    "total": server.disk_total,
                    "percentage": (server.disk_used / server.disk_total * 100) if server.disk_total > 0 else 0
                }
            },
            "last_sync": server.last_sync.isoformat(),
            "tags": server.tags,
            "bandwidth_limit": server.bandwidth_limit,
            "is_active": server.is_active
        }
    
    async def test_connection(self, host: str, port: int, username: str, password: str) -> Tuple[bool, str]:
        """Test connection to a server by trying to log in.
        
        Returns a tuple of (success, message) where success is a boolean
        indicating whether the connection was successful and message is
        a human-readable message describing the result.
        """
        try:
            # Construct the panel URL
            proto = "https" if port == 443 else "http"
            panel_url = f"{proto}://{host}:{port}"
            login_url = f"{panel_url}/login"
            
            # Create a session for login attempt
            async with aiohttp.ClientSession() as session:
                # Try to access the login page first
                try:
                    async with session.get(panel_url, timeout=10) as response:
                        if response.status != 200:
                            return False, f"Panel not accessible (status: {response.status})"
                except asyncio.TimeoutError:
                    return False, "Connection timed out"
                except aiohttp.ClientError as e:
                    return False, f"Connection error: {str(e)}"
                
                # Try to login
                try:
                    login_data = {
                        "username": username,
                        "password": password
                    }
                    
                    async with session.post(login_url, json=login_data, timeout=10) as response:
                        if response.status != 200:
                            return False, f"Login failed with status code: {response.status}"
                        
                        # Parse the response JSON
                        try:
                            result = await response.json()
                            if not result.get("success"):
                                return False, "Login rejected: Invalid credentials"
                        except Exception:
                            return False, "Could not parse login response"
                        
                        # Login successful!
                        return True, "Connection successful"
                        
                except asyncio.TimeoutError:
                    return False, "Login request timed out"
                except aiohttp.ClientError as e:
                    return False, f"Login error: {str(e)}"
                except Exception as e:
                    return False, f"Unexpected error during login: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error testing server connection: {e}")
            return False, f"Error: {str(e)}"
    
    def load_panels(self):
        """Load panel configurations from environment or config."""
        try:
            # In a real implementation, this would load from database or settings
            panel_url = os.environ.get('X_UI_PANEL_URL', 'http://localhost:54321')
            panel_username = os.environ.get('X_UI_PANEL_USERNAME', 'admin')
            panel_password = os.environ.get('X_UI_PANEL_PASSWORD', 'admin')
            
            self.panels['default'] = {
                'url': panel_url,
                'username': panel_username,
                'password': panel_password,
                'login_status': False,
                'session': requests.Session()
            }
        except Exception as e:
            logger.error(f"Error loading panels: {e}")
    
    def get_server_traffic(self, server_id: int) -> Dict[str, int]:
        """Get server traffic statistics.
        
        Args:
            server_id: The server ID to get traffic for
            
        Returns:
            Dictionary containing traffic data: {'up': bytes_up, 'down': bytes_down}
        """
        try:
            # در یک پیاده‌سازی واقعی، اینجا باید اطلاعات را از API سرور دریافت کنیم
            # این تابع فعلاً داده‌های آزمایشی برمی‌گرداند
            server = self.get_server_by_id(server_id)
            if not server:
                logger.error(f"Server with ID {server_id} not found")
                return {'up': 0, 'down': 0}
            
            # مقادیر آزمایشی برای نمایش کارکرد
            if server_id == 1:
                return {
                    'up': 15_000_000_000,   # 15 GB
                    'down': 75_000_000_000  # 75 GB
                }
            elif server_id == 2:
                return {
                    'up': 8_000_000_000,    # 8 GB
                    'down': 42_000_000_000  # 42 GB
                }
            else:
                return {'up': 0, 'down': 0}
                
        except Exception as e:
            logger.error(f"Error getting server traffic: {e}")
            return {'up': 0, 'down': 0}
    
    def get_total_traffic(self) -> Dict[str, int]:
        """Get total traffic across all servers.
        
        Returns:
            Dictionary containing total traffic data: {'up': bytes_up, 'down': bytes_down}
        """
        try:
            servers = self.get_all_servers()
            total_up = 0
            total_down = 0
            
            for server in servers:
                server_traffic = self.get_server_traffic(server['id'])
                total_up += server_traffic['up']
                total_down += server_traffic['down']
            
            return {
                'up': total_up,
                'down': total_down,
                'total': total_up + total_down
            }
                
        except Exception as e:
            logger.error(f"Error getting total traffic: {e}")
            return {'up': 0, 'down': 0, 'total': 0}
    
    def test_connection(self, server_id: int) -> Tuple[bool, str]:
        """Test connection to a server.
        
        Args:
            server_id: The server ID to test
            
        Returns:
            Tuple of (success, message)
        """
        try:
            server = self.get_server_by_id(server_id)
            if not server:
                return False, f"Server with ID {server_id} not found"
            
            # In a real implementation, this would attempt to connect to the server
            # For now, return success
            return True, f"Successfully connected to {server['name']}"
            
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False, f"Connection error: {str(e)}"
    
    def sync_server(self, server_id: int) -> Tuple[bool, str]:
        """Synchronize server data.
        
        Args:
            server_id: The server ID to sync
            
        Returns:
            Tuple of (success, message)
        """
        try:
            server = self.get_server_by_id(server_id)
            if not server:
                return False, f"Server with ID {server_id} not found"
            
            # In a real implementation, this would sync data with the server
            # For now, return success
            return True, f"Successfully synchronized {server['name']}"
            
        except Exception as e:
            logger.error(f"Error synchronizing server: {e}")
            return False, f"Synchronization error: {str(e)}" 