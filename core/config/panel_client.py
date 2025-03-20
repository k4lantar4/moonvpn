"""
Panel Client for 3x-UI integration.

This module provides classes for interacting with 3x-UI panels.
"""

import logging
import requests
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from django.utils import timezone

from backend.models.vpn.server import Server

logger = logging.getLogger(__name__)

class PanelClient:
    """Client for interacting with 3x-UI panels."""
    
    def __init__(self, server_id=None, server_instance=None):
        """
        Initialize the client.
        
        Args:
            server_id: ID of the server to connect to
            server_instance: Server instance
        """
        if not server_id and not server_instance:
            raise ValueError("Either server_id or server_instance must be provided")
            
        if server_instance:
            self.server = server_instance
        else:
            self.server = Server.objects.get(id=server_id)
            
        self.host = self.server.host
        self.port = self.server.port
        self.username = self.server.username
        self.password = self.server.password
        self.base_path = self.server.base_path
        self.session = requests.Session()
        
        # Load session cookie if available
        cookies = self.server.get_session_cookies()
        if cookies:
            self.session.cookies.update(cookies)
    
    async def ensure_authenticated(self):
        """
        Ensure the client is authenticated with the panel.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        # Try a simple authenticated request
        try:
            test_response = await self.make_request("GET", "/panel/api/status", skip_auth_check=True)
            if test_response.status_code == 200:
                return True
        except Exception as e:
            logger.warning(f"Authentication test failed: {e}")
            
        # If not authenticated, login
        login_payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            login_url = f"https://{self.host}:{self.port}{self.base_path}/login"
            
            # Make login request
            response = await asyncio.to_thread(
                lambda: self.session.post(login_url, data=login_payload, allow_redirects=False)
            )
            
            # Check for successful login (usually a redirect)
            if response.status_code == 302 or "Location" in response.headers:
                # Save session cookies to database
                self.server.set_session_cookies(dict(self.session.cookies))
                return True
            else:
                logger.error(f"Login failed: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def make_request(self, method, endpoint, skip_auth_check=False, **kwargs):
        """
        Make a request to the panel.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            skip_auth_check: Whether to skip authentication check
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        if not skip_auth_check:
            authenticated = await self.ensure_authenticated()
            if not authenticated:
                raise Exception("Failed to authenticate with the panel")
                
        url = f"https://{self.host}:{self.port}{self.base_path.rstrip('/')}{endpoint}"
        
        try:
            response = await asyncio.to_thread(
                lambda: self.session.request(method, url, **kwargs)
            )
            return response
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    async def make_request_with_retry(self, method, endpoint, max_retries=3, retry_delay=2, **kwargs):
        """
        Make a request with automatic retry for transient errors.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            max_retries: Maximum number of retries
            retry_delay: Delay between retries (seconds)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = await self.make_request(method, endpoint, **kwargs)
                
                # Check if rate limited
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    retry_count += 1
                    continue
                    
                return response
                
            except requests.exceptions.ConnectionError as e:
                # Connection errors may be transient
                retry_count += 1
                logger.warning(f"Connection error (retry {retry_count}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay * (2 ** retry_count))  # Exponential backoff
                
            except Exception as e:
                # Don't retry for other errors
                logger.error(f"Request failed: {str(e)}")
                raise
                
        raise Exception(f"Max retries exceeded for {endpoint}")
    
    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get all inbounds from the panel.
        
        Returns:
            List of inbound configurations
        """
        response = await self.make_request_with_retry("GET", "/panel/api/inbounds")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("obj", [])
        else:
            logger.error(f"Failed to get inbounds: {response.status_code} {response.text}")
            return []
    
    async def get_clients(self, inbound_id: int) -> List[Dict[str, Any]]:
        """
        Get all clients for an inbound.
        
        Args:
            inbound_id: Inbound ID
            
        Returns:
            List of client configurations
        """
        response = await self.make_request_with_retry("GET", f"/panel/api/inbounds/{inbound_id}/clients")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("obj", [])
        else:
            logger.error(f"Failed to get clients: {response.status_code} {response.text}")
            return []
    
    async def add_client(self, inbound_id: int, email: str, uuid: str = None, subscription_days: int = 30, traffic_limit_gb: int = 100) -> bool:
        """
        Add a client to an inbound.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            uuid: Client UUID (optional)
            subscription_days: Subscription duration in days
            traffic_limit_gb: Traffic limit in GB
            
        Returns:
            True if successful, False otherwise
        """
        import uuid as uuid_module
        
        # Generate UUID if not provided
        if not uuid:
            uuid = str(uuid_module.uuid4())
            
        # Prepare client data
        client_data = {
            "email": email,
            "uuid": uuid,
            "enable": True,
            "expiryTime": int((timezone.now() + timezone.timedelta(days=subscription_days)).timestamp() * 1000),
            "total": traffic_limit_gb * 1024 * 1024 * 1024,  # Convert GB to bytes
        }
        
        response = await self.make_request_with_retry(
            "POST",
            f"/panel/api/inbounds/{inbound_id}/clients",
            json=client_data
        )
        
        if response.status_code in (200, 201):
            return True
        else:
            logger.error(f"Failed to add client: {response.status_code} {response.text}")
            return False
    
    async def update_client(self, inbound_id: int, email: str, client_data: Dict[str, Any]) -> bool:
        """
        Update a client.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            client_data: Updated client data
            
        Returns:
            True if successful, False otherwise
        """
        # Get current client ID
        clients = await self.get_clients(inbound_id)
        client = next((c for c in clients if c.get('email') == email), None)
        
        if not client:
            logger.error(f"Client not found: {email}")
            return False
            
        client_id = client.get('id')
        
        response = await self.make_request_with_retry(
            "PUT",
            f"/panel/api/inbounds/{inbound_id}/clients/{client_id}",
            json=client_data
        )
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Failed to update client: {response.status_code} {response.text}")
            return False
    
    async def delete_client(self, inbound_id: int, email: str) -> bool:
        """
        Delete a client.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            True if successful, False otherwise
        """
        # Get current client ID
        clients = await self.get_clients(inbound_id)
        client = next((c for c in clients if c.get('email') == email), None)
        
        if not client:
            logger.warning(f"Client not found for deletion: {email}")
            return True  # Consider it a success if already gone
            
        client_id = client.get('id')
        
        response = await self.make_request_with_retry(
            "DELETE",
            f"/panel/api/inbounds/{inbound_id}/clients/{client_id}"
        )
        
        if response.status_code in (200, 204):
            return True
        else:
            logger.error(f"Failed to delete client: {response.status_code} {response.text}")
            return False
    
    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """
        Reset client traffic.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            True if successful, False otherwise
        """
        # Get current client
        clients = await self.get_clients(inbound_id)
        client = next((c for c in clients if c.get('email') == email), None)
        
        if not client:
            logger.error(f"Client not found: {email}")
            return False
            
        client_id = client.get('id')
        
        response = await self.make_request_with_retry(
            "POST",
            f"/panel/api/inbounds/{inbound_id}/clients/{client_id}/reset"
        )
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"Failed to reset client traffic: {response.status_code} {response.text}")
            return False
    
    async def get_client_traffic(self, inbound_id: int, email: str) -> Dict[str, Any]:
        """
        Get client traffic statistics.
        
        Args:
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            Client traffic data
        """
        # Get current client
        clients = await self.get_clients(inbound_id)
        client = next((c for c in clients if c.get('email') == email), None)
        
        if not client:
            logger.error(f"Client not found: {email}")
            return {"up": 0, "down": 0, "total": 0, "error": "Client not found"}
            
        return {
            "up": client.get('up', 0),
            "down": client.get('down', 0),
            "total": client.get('up', 0) + client.get('down', 0),
            "limit": client.get('total', 0),
            "enable": client.get('enable', False),
            "expiryTime": client.get('expiryTime', 0),
        }
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get server status.
        
        Returns:
            Server status data
        """
        response = await self.make_request_with_retry("GET", "/panel/api/status")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("obj", {})
        else:
            logger.error(f"Failed to get server status: {response.status_code} {response.text}")
            return {"status": "error", "error": response.text}
    
    @staticmethod
    async def check_server_health(server_id: Optional[int] = None) -> Dict[int, bool]:
        """
        Check health for all servers or a specific server.
        
        Args:
            server_id: Optional server ID to check
            
        Returns:
            Dictionary mapping server IDs to health status
        """
        if server_id:
            servers = [Server.objects.get(id=server_id)]
        else:
            servers = Server.objects.filter(is_active=True)
            
        results = {}
        
        for server in servers:
            client = PanelClient(server_instance=server)
            
            try:
                authenticated = await client.ensure_authenticated()
                
                if authenticated:
                    response = await client.make_request("GET", "/panel/api/status")
                    
                    if response.status_code == 200:
                        # Server is healthy
                        if not server.is_active:
                            server.is_active = True
                            server.save(update_fields=['is_active', 'updated_at'])
                            
                        results[server.id] = True
                    else:
                        # Server is having issues
                        server.is_active = False
                        server.save(update_fields=['is_active', 'updated_at'])
                        results[server.id] = False
                else:
                    # Authentication failed
                    server.is_active = False
                    server.save(update_fields=['is_active', 'updated_at'])
                    results[server.id] = False
                    
            except Exception as e:
                # Server is down or unreachable
                logger.error(f"Server {server.name} is down: {str(e)}")
                server.is_active = False
                server.save(update_fields=['is_active', 'updated_at'])
                results[server.id] = False
                
        return results
    
    @staticmethod
    def get_server_by_load() -> Optional[Server]:
        """
        Get the server with the lowest load.
        
        Returns:
            Server instance or None if no servers available
        """
        return Server.objects.filter(is_active=True).order_by('load_factor', 'current_clients').first()
    
    @staticmethod
    def get_best_server_in_location(location_id: int) -> Optional[Server]:
        """
        Get the best server in a location.
        
        Args:
            location_id: Location ID
            
        Returns:
            Server instance or None if no servers available
        """
        return Server.objects.filter(
            is_active=True,
            location_id=location_id
        ).order_by('load_factor', 'current_clients').first() 