"""
Server synchronization manager for V2Ray servers.

This module provides:
- Multi-server synchronization
- Configuration management
- Health monitoring
- Automatic failover
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import F
import os
import json
import requests
from uuid import uuid4

from main.models import Server, ServerMonitor, User, Subscription, PanelConfig
from v2ray.models import Inbound, Client
# Temporarily comment out the import and replace with a dummy function
# from utils.notifications import send_telegram_notification

logger = logging.getLogger(__name__)

def send_telegram_notification(message, admin_only=False):
    """Temporary replacement for the missing send_telegram_notification function"""
    print(f"[NOTIFICATION] {message} (admin_only={admin_only})")

class ServerSyncManager:
    """Manager class for server synchronization."""
    
    def __init__(self):
        self.session = None
        self.sync_lock = asyncio.Lock()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def sync_server(self, server: Server) -> bool:
        """
        Synchronize a single server.
        
        Args:
            server: Server instance to sync
            
        Returns:
            True if sync successful, False otherwise
        """
        async with self.sync_lock:
            try:
                # Get server status
                status = await self._get_server_status(server)
                
                # Update server status
                server.is_active = status.get('is_active', False)
                server.is_synced = True
                server.last_sync = timezone.now()
                server.save()
                
                # Sync inbounds
                await self._sync_inbounds(server)
                
                # Sync clients
                await self._sync_clients(server)
                
                # Record monitoring data
                await self._record_monitoring_data(server, status)
                
                return True
            except Exception as e:
                logger.error(f"Error syncing server {server.name}: {str(e)}")
                server.is_synced = False
                server.save()
                return False
    
    async def sync_all_servers(self) -> Dict[str, int]:
        """
        Synchronize all active servers.
        
        Returns:
            Dict with sync results
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0
        }
        
        servers = Server.objects.filter(is_active=True)
        results['total'] = servers.count()
        
        tasks = [self.sync_server(server) for server in servers]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results_list:
            if isinstance(result, Exception):
                results['failed'] += 1
            elif result:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    async def _get_server_status(self, server: Server) -> Dict:
        """Get server status from API."""
        url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/status"
        async with self.session.get(url, timeout=30) as response:
            response.raise_for_status()
            return await response.json()
    
    async def _sync_inbounds(self, server: Server) -> None:
        """Synchronize server inbounds."""
        url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/inbounds"
        async with self.session.get(url, timeout=30) as response:
            response.raise_for_status()
            inbounds_data = await response.json()
            
            for inbound_data in inbounds_data:
                await self._update_inbound(server, inbound_data)
    
    async def _update_inbound(self, server: Server, inbound_data: Dict) -> None:
        """Update or create inbound."""
        Inbound.objects.update_or_create(
            server=server,
            port=inbound_data['port'],
            defaults={
                'protocol': inbound_data['protocol'],
                'settings': inbound_data['settings'],
                'stream_settings': inbound_data['stream_settings'],
                'remark': inbound_data['remark']
            }
        )
    
    async def _sync_clients(self, server: Server) -> None:
        """Synchronize server clients."""
        url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/clients"
        async with self.session.get(url, timeout=30) as response:
            response.raise_for_status()
            clients_data = await response.json()
            
            for client_data in clients_data:
                await self._update_client(server, client_data)
    
    async def _update_client(self, server: Server, client_data: Dict) -> None:
        """Update or create client."""
        try:
            user = User.objects.get(id=client_data['user_id'])
            inbound = Inbound.objects.get(
                server=server,
                port=client_data['inbound_port']
            )
            
            Client.objects.update_or_create(
                user=user,
                inbound=inbound,
                defaults={
                    'email': client_data['email'],
                    'uuid': client_data['uuid'],
                    'flow': client_data.get('flow', ''),
                    'total_gb': client_data['total_gb'],
                    'expire_days': client_data['expire_days'],
                    'enable': client_data['enable']
                }
            )
        except (User.DoesNotExist, Inbound.DoesNotExist) as e:
            logger.error(f"Error updating client: {str(e)}")
    
    async def _record_monitoring_data(self, server: Server, status: Dict) -> None:
        """Record server monitoring data."""
        ServerMonitor.objects.create(
            server=server,
            cpu_usage=status.get('cpu_usage', 0),
            memory_usage=status.get('memory_usage', 0),
            disk_usage=status.get('disk_usage', 0),
            uptime_seconds=status.get('uptime', 0),
            active_connections=status.get('active_connections', 0),
            network_in=status.get('network_in', 0),
            network_out=status.get('network_out', 0),
            network_speed_in=status.get('network_speed_in', 0),
            network_speed_out=status.get('network_speed_out', 0),
            load_average_1min=status.get('load_average_1min', 0),
            load_average_5min=status.get('load_average_5min', 0),
            load_average_15min=status.get('load_average_15min', 0),
            swap_usage=status.get('swap_usage', 0),
            io_read=status.get('io_read', 0),
            io_write=status.get('io_write', 0),
            io_speed_read=status.get('io_speed_read', 0),
            io_speed_write=status.get('io_speed_write', 0)
        )
    
    async def check_server_health(self, server: Server) -> Dict:
        """Check server health status."""
        try:
            status = await self._get_server_status(server)
            return {
                'is_healthy': status.get('is_active', False),
                'cpu_usage': status.get('cpu_usage', 0),
                'memory_usage': status.get('memory_usage', 0),
                'disk_usage': status.get('disk_usage', 0),
                'uptime': status.get('uptime', 0),
                'last_check': timezone.now()
            }
        except Exception as e:
            logger.error(f"Error checking server health: {str(e)}")
            return {
                'is_healthy': False,
                'error': str(e),
                'last_check': timezone.now()
            }
    
    async def get_server_metrics(self, server: Server, hours: int = 24) -> List[Dict]:
        """Get server metrics history."""
        try:
            url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/metrics"
            params = {'hours': hours}
            async with self.session.get(url, params=params, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error getting server metrics: {str(e)}")
            return []
    
    async def rotate_subscriptions(self, server: Server) -> None:
        """Rotate subscriptions to alternative server."""
        try:
            # Find alternative server
            alternative_server = Server.objects.filter(
                is_active=True,
                id__ne=server.id
            ).order_by("?").first()
            
            if not alternative_server:
                logger.warning(f"No alternative server available for rotation from {server.name}")
                return
            
            # Get unhealthy subscriptions
            subscriptions = server.v2ray_subscriptions.filter(
                status="active"
            )
            
            for subscription in subscriptions:
                await self._rotate_subscription(subscription, alternative_server)
                
        except Exception as e:
            logger.error(f"Error rotating subscriptions: {str(e)}")
    
    async def _rotate_subscription(self, subscription: 'Subscription', new_server: Server) -> None:
        """Rotate a single subscription to a new server."""
        try:
            # Create new client on alternative server
            client_data = {
                'email': subscription.client_email,
                'total_gb': subscription.data_limit_gb,
                'expire_days': subscription.remaining_days()
            }
            
            url = f"{settings.V2RAY_API_URL}/server/{new_server.sync_id}/clients"
            async with self.session.post(url, json=client_data, timeout=30) as response:
                response.raise_for_status()
                new_client = await response.json()
                
                # Update subscription
                subscription.server = new_server
                subscription.inbound_id = new_client['inbound_id']
                subscription.save()
                
                # Send notification
                await send_telegram_notification(
                    f"🔄 Subscription {subscription.id} rotated to server {new_server.name}"
                )
                
        except Exception as e:
            logger.error(f"Error rotating subscription {subscription.id}: {str(e)}")

class ThreeXUI_Connector:
    """Connector class for 3x-UI panel API."""
    
    def __init__(self, server=None, panel_url=None, username=None, password=None):
        """
        Initialize the connector with either a Server instance or direct credentials.
        
        Args:
            server: Server instance containing panel configuration
            panel_url: URL of the 3x-UI panel (e.g., https://panel.example.com:2053)
            username: Panel admin username
            password: Panel admin password
        """
        self.session = requests.Session()
        self.is_authenticated = False
        
        if server:
            self.server = server
            self.panel_url = server.panel_url
            self.username = server.username
            self.password = server.password
        else:
            self.server = None
            self.panel_url = panel_url
            self.username = username
            self.password = password
        
        # Clean up panel URL
        if self.panel_url and self.panel_url.endswith('/'):
            self.panel_url = self.panel_url[:-1]
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """Initialize the session and attempt authentication."""
        if not any([self.panel_url, self.username, self.password]):
            logger.warning("Missing panel credentials. Please provide panel URL, username, and password.")
            return
        
        if self.panel_url and self.username and self.password:
            self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the 3x-UI panel.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            login_url = f"{self.panel_url}/login"
            data = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(login_url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('success'):
                self.is_authenticated = True
                return True
            
            logger.error(f"Authentication failed: {result.get('msg', 'Unknown error')}")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make an HTTP request to the panel API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
        
        Returns:
            Optional[Dict]: JSON response if successful, None otherwise
        """
        if not self.is_authenticated and not self.authenticate():
            logger.error("Not authenticated and authentication failed")
            return None
        
        try:
            url = f"{self.panel_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {str(e)}")
            return None

    @staticmethod
    def sync_all_panels() -> None:
        """
        Sync data from all active panel configurations.
        """
        try:
            # Get all active panel configurations
            panel_configs = PanelConfig.objects.filter(is_active=True, disable_check=False)
            
            if not panel_configs.exists():
                logger.warning("No active panel configurations found")
                return
            
            for panel in panel_configs:
                try:
                    # Create connector instance for this panel
                    connector = ThreeXUI_Connector(
                        panel_url=panel.panel_url,
                        username=panel.username,
                        password=panel.password
                    )
                    
                    # Check if we can authenticate
                    if not connector.authenticate():
                        logger.error(f"Failed to authenticate with 3x-UI panel at {panel.panel_url}")
                        continue
                    
                    # Get server status
                    status = connector.get_server_status()
                    if not status:
                        logger.error(f"Failed to get server status from 3x-UI panel at {panel.panel_url}")
                        continue
                    
                    # Create or update server record
                    server_data = {
                        'url': panel.panel_url,
                        'host': panel.domain,
                        'port': panel.port,
                        'username': panel.username,
                        'password': panel.password,
                        'name': f"3x-UI Panel ({panel.name})",
                        'location': panel.location,
                        'type': 'xray',
                        'is_active': True,
                        'cpu_usage': status.get('cpu', 0),
                        'memory_usage': status.get('mem', 0),
                        'disk_usage': status.get('disk', 0)
                    }
                    
                    server, created = Server.objects.update_or_create(
                        sync_id=f"panel_{panel.server_id}",
                        defaults=server_data
                    )
                    
                    # Get all inbounds
                    inbounds = connector.get_inbounds()
                    if not inbounds:
                        logger.error(f"Failed to get inbounds from 3x-UI panel at {panel.panel_url}")
                        continue
                    
                    # Process each inbound
                    for inbound in inbounds:
                        inbound_id = inbound.get('id')
                        if not inbound_id:
                            continue
                        
                        # Get client details
                        clients = connector.get_client_stats(inbound_id)
                        if not clients:
                            logger.warning(f"No clients found for inbound {inbound_id} on panel {panel.panel_url}")
                            continue
                        
                        # Update client records
                        for client in clients:
                            email = client.get('email')
                            if not email:
                                continue
                            
                            # Update client traffic stats
                            # Note: Implement your client update logic here
                            pass
                    
                    # Update last check timestamp
                    panel.last_check = timezone.now()
                    panel.save()
                    
                    logger.info(f"Successfully synced data from 3x-UI panel at {panel.panel_url}")
                
                except Exception as e:
                    logger.error(f"Error syncing data from 3x-UI panel at {panel.panel_url}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in sync_all_panels: {str(e)}")
    
    def get_server_status(self) -> Optional[Dict]:
        """Get server status information."""
        return self._make_request('GET', '/panel/api/status')
    
    def get_inbounds(self) -> Optional[List[Dict]]:
        """Get all inbound configurations."""
        response = self._make_request('GET', '/panel/api/inbounds/list')
        return response.get('obj') if response else None
    
    def get_client_stats(self, inbound_id: int) -> Optional[List[Dict]]:
        """Get client statistics for an inbound."""
        response = self._make_request('GET', f'/panel/api/inbounds/getClientTraffics/{inbound_id}')
        return response.get('obj') if response else None
    
    def add_client(self, inbound_id: int, client_data: Dict) -> Optional[Dict]:
        """Add a new client to an inbound."""
        return self._make_request('POST', f'/panel/api/inbounds/{inbound_id}/addClient', json=client_data)
    
    def remove_client(self, inbound_id: int, email: str) -> Optional[Dict]:
        """Remove a client from an inbound."""
        return self._make_request('POST', f'/panel/api/inbounds/{inbound_id}/delClient/{email}')
    
    def update_client(self, inbound_id: int, email: str, settings: Dict) -> Optional[Dict]:
        """Update client settings."""
        return self._make_request('POST', f'/panel/api/inbounds/{inbound_id}/updateClient/{email}', json=settings)
    
    def reset_client_traffic(self, email: str) -> Optional[Dict]:
        """Reset client traffic statistics."""
        return self._make_request('POST', f'/panel/api/inbounds/resetClientTraffic/{email}')

def sync_panel():
    """
    Synchronize data from all 3x-UI panels to the database.
    This function fetches inbounds and clients from all panels and updates the database.
    
    Returns:
        dict: Results of sync operation with counts of successes and failures
    """
    try:
        # Get all active servers from database
        from main.models import Server
        servers = Server.objects.filter(is_active=True).exclude(url__isnull=True).exclude(url='')
        
        if not servers.exists():
            # Try to use environment variables if no servers in database
            panel_url = os.environ.get('PANEL_URL', '')
            username = os.environ.get('PANEL_USERNAME', '')
            password = os.environ.get('PANEL_PASSWORD', '')
            
            if all([panel_url, username, password]):
                logger.info("No servers in database, using environment variables")
                connector = ThreeXUI_Connector(panel_url=panel_url, username=username, password=password)
                return sync_single_panel(connector, None)
            else:
                logger.error("No 3x-UI panel servers configured in database or environment variables")
                return {"total": 0, "success": 0, "failed": 0}
        
        # Initialize results
        results = {
            "total": servers.count(),
            "success": 0,
            "failed": 0
        }
        
        # Sync each server
        for server in servers:
            connector = ThreeXUI_Connector(server)
            if sync_single_panel(connector, server):
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"3x-UI panel sync complete: {results['success']} succeeded, {results['failed']} failed")
        return results
        
    except Exception as e:
        logger.error(f"Error syncing data from 3x-UI panels: {str(e)}")
        return {"total": 0, "success": 0, "failed": 1}

def sync_single_panel(connector, server=None):
    """
    Synchronize data from a single 3x-UI panel to the database.
    
    Args:
        connector: ThreeXUI_Connector instance
        server: Server model instance or None
        
    Returns:
        bool: True if sync successful, False otherwise
    """
    try:
        # Check if login successful
        if not connector.is_authenticated:
            logger.error(f"Failed to authenticate with 3x-UI panel at {connector.panel_url}")
            return False
        
        # Get server status
        server_status = connector.get_server_status()
        if not server_status:
            logger.error(f"Failed to get server status from 3x-UI panel at {connector.panel_url}")
            return False
        
        # Get or create server in database if not provided
        from main.models import Server
        if not server:
            server, created = Server.objects.get_or_create(
                url=connector.panel_url,
                defaults={
                    'name': f"3x-UI Panel ({connector.panel_url})",
                    'host': connector.panel_url.split('://')[1].split(':')[0] if '://' in connector.panel_url else connector.panel_url,
                    'port': 443,  # Default port
                    'username': connector.username,
                    'password': connector.password,
                    'is_active': True,
                    'location': connector.location,
                    'type': 'v2ray'
                }
            )
        
        # Update server status
        server.is_active = True
        server.last_sync = timezone.now()
        server.cpu_usage = server_status.get('cpu', 0)
        server.memory_usage = server_status.get('mem', 0)
        server.disk_usage = server_status.get('disk', 0)
        server.save()
        
        # Get inbounds
        inbounds = connector.get_inbounds()
        if not inbounds:
            logger.error(f"Failed to get inbounds from 3x-UI panel at {connector.panel_url}")
            return False
        
        # Process inbounds
        for inbound_data in inbounds:
            inbound_id = inbound_data.get('id')
            protocol = inbound_data.get('protocol', '').lower()
            
            # Skip unsupported protocols
            if protocol not in ['vmess', 'vless', 'trojan']:
                continue
            
            # Get or create inbound in database
            from v2ray.models import Inbound
            inbound, created = Inbound.objects.get_or_create(
                panel_id=inbound_id,
                server=server,
                defaults={
                    'protocol': protocol,
                    'port': inbound_data.get('port', 0),
                    'tag': inbound_data.get('remark', ''),
                    'settings': json.dumps(inbound_data),
                    'is_active': True
                }
            )
            
            # Update inbound if it exists
            if not created:
                inbound.protocol = protocol
                inbound.port = inbound_data.get('port', 0)
                inbound.tag = inbound_data.get('remark', '')
                inbound.settings = json.dumps(inbound_data)
                inbound.is_active = True
                inbound.save()
            
            # Get clients for this inbound
            clients = connector.get_client_stats(inbound_id)
            if not clients:
                logger.warning(f"No clients found for inbound {inbound_id} on panel {connector.panel_url}")
                continue
            
            # Process clients
            for client_data in clients:
                email = client_data.get('email', '')
                
                # Skip clients without email
                if not email:
                    continue
                
                # Get or create client in database
                from v2ray.models import Client
                client, created = Client.objects.get_or_create(
                    email=email,
                    inbound=inbound,
                    defaults={
                        'uuid': client_data.get('id', ''),
                        'traffic_up': client_data.get('up', 0),
                        'traffic_down': client_data.get('down', 0),
                        'traffic_total': client_data.get('total', 0),
                        'expiry_time': datetime.fromtimestamp(client_data.get('expiryTime', 0) / 1000) if client_data.get('expiryTime', 0) > 0 else None,
                        'enable': client_data.get('enable', True),
                        'is_active': True
                    }
                )
                
                # Update client if it exists
                if not created:
                    client.uuid = client_data.get('id', '')
                    client.traffic_up = client_data.get('up', 0)
                    client.traffic_down = client_data.get('down', 0)
                    client.traffic_total = client_data.get('total', 0)
                    client.expiry_time = datetime.fromtimestamp(client_data.get('expiryTime', 0) / 1000) if client_data.get('expiryTime', 0) > 0 else None
                    client.enable = client_data.get('enable', True)
                    client.is_active = True
                    client.save()
                
                # Try to find subscription for this client
                try:
                    from main.models import Subscription
                    subscription = Subscription.objects.get(client_email=email)
                    subscription.save()
                except Exception as e:
                    logger.debug(f"No subscription found for client {email}: {str(e)}")
                    pass
        
        # Log sync success
        logger.info(f"Successfully synced data from 3x-UI panel at {connector.panel_url}")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing data from 3x-UI panel at {connector.panel_url}: {str(e)}")
        return False 