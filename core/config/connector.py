"""
3x-UI Connector for VPN module
"""

import logging
import os
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from django.utils import timezone

from vpn.base import BaseVPNConnector
from vpn.exceptions import VPNConnectionError, VPNAuthenticationError, VPNSyncError

logger = logging.getLogger(__name__)

class ThreeXUIConnector(BaseVPNConnector):
    """
    Connector class for 3x-UI panel API based on the official documentation.
    Handles authentication, session management, and API calls to the 3x-UI panel.
    """
    
    def __init__(self, server):
        """
        Initialize the connector with server object or panel credentials.
        
        Args:
            server: Server object from database
        """
        self.server = server
        self.panel_url = server.url
        self.username = server.username
        self.password = server.password
        self.location = server.location
        self.server_id = server.id
        
        # Check if we should use mock data
        self.use_mock_data = os.environ.get('USE_MOCK_PANEL_DATA', 'false').lower() == 'true'
        
        # Remove trailing slash from URL if present
        if self.panel_url and self.panel_url.endswith('/'):
            self.panel_url = self.panel_url[:-1]
            
        # Session management
        self.session = requests.Session()
        self.cookies = None
        self.is_authenticated_flag = False
        self.last_auth_time = None
        self.auth_expiry = 3600  # Session expiry in seconds (1 hour)
        
        # Logging
        self.logger = logging.getLogger('threexui')
        
        # Auto login if credentials are provided or using mock data
        if self.use_mock_data:
            self.is_authenticated_flag = True
            self.last_auth_time = datetime.now()
            self.logger.info("Using mock data for 3x-UI panel")
        elif self.panel_url and self.username and self.password:
            self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the 3x-UI panel and store session cookies.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        # If using mock data, always return success
        if self.use_mock_data:
            self.is_authenticated_flag = True
            self.last_auth_time = datetime.now()
            return True
            
        # Check if we need to re-authenticate
        if self.is_authenticated_flag and self.last_auth_time:
            elapsed = (datetime.now() - self.last_auth_time).total_seconds()
            if elapsed < self.auth_expiry:
                return True
        
        try:
            login_url = f"{self.panel_url}/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(login_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.cookies = self.session.cookies
                    self.is_authenticated_flag = True
                    self.last_auth_time = datetime.now()
                    self.logger.info(f"Successfully authenticated with 3x-UI panel at {self.panel_url}")
                    return True
                else:
                    self.logger.error(f"Login failed: {data.get('msg')}")
            else:
                self.logger.error(f"Login failed with status code: {response.status_code}")
            
            self.is_authenticated_flag = False
            return False
            
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            self.is_authenticated_flag = False
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if the connector is currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if self.use_mock_data:
            return True
            
        if self.is_authenticated_flag and self.last_auth_time:
            elapsed = (datetime.now() - self.last_auth_time).total_seconds()
            if elapsed < self.auth_expiry:
                return True
            else:
                # Session expired, need to re-authenticate
                return self.authenticate()
        return False
    
    def _request(self, method, endpoint, data=None, params=None, retry=True):
        """
        Make an authenticated request to the 3x-UI API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request payload for POST/PUT requests
            params: URL parameters for GET requests
            retry: Whether to retry on authentication failure
            
        Returns:
            Response data or None on failure
        """
        if not self.is_authenticated() and not self.authenticate():
            self.logger.error("Not authenticated and login failed")
            return None
        
        # If using mock data, return mock responses
        if self.use_mock_data:
            return self._get_mock_response(endpoint, method, data)
            
        url = f"{self.panel_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, json=data)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check if we need to re-authenticate
            if response.status_code == 401 and retry:
                self.logger.info("Session expired, re-authenticating...")
                self.is_authenticated_flag = False
                if self.authenticate():
                    return self._request(method, endpoint, data, params, retry=False)
                return None
            
            if response.status_code != 200:
                self.logger.error(f"API request failed with status code: {response.status_code}")
                return None
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"API request error: {str(e)}")
            return None
    
    def _get_mock_response(self, endpoint, method, data=None):
        """
        Generate mock responses for testing without a real panel.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            
        Returns:
            Mock response data
        """
        # Server status endpoint
        if endpoint == '/panel/api/server/status':
            return {
                'success': True,
                'obj': {
                    'cpu': 25,
                    'mem': 40,
                    'disk': 30,
                    'xray_state': 'running',
                    'xray_version': '1.8.1'
                }
            }
            
        # Inbounds list endpoint
        elif endpoint == '/panel/api/inbounds/list':
            return {
                'success': True,
                'obj': [
                    {
                        'id': 1,
                        'protocol': 'vmess',
                        'port': 8443,
                        'remark': 'Default VMess',
                        'enable': True,
                        'up': 1024 * 1024 * 100,  # 100 MB
                        'down': 1024 * 1024 * 200,  # 200 MB
                        'total': 1024 * 1024 * 1024 * 10,  # 10 GB
                        'settings': '{"clients":[{"id":"8f91b6a0-e8ee-11ea-adc1-0242ac120002","alterId":0,"email":"user1@example.com"}]}'
                    },
                    {
                        'id': 2,
                        'protocol': 'vless',
                        'port': 8444,
                        'remark': 'Default VLESS',
                        'enable': True,
                        'up': 1024 * 1024 * 150,  # 150 MB
                        'down': 1024 * 1024 * 250,  # 250 MB
                        'total': 1024 * 1024 * 1024 * 20,  # 20 GB
                        'settings': '{"clients":[{"id":"9f91b6a0-e8ee-11ea-adc1-0242ac120003","flow":"","email":"user2@example.com"}]}'
                    }
                ]
            }
            
        # Get inbound endpoint
        elif endpoint.startswith('/panel/api/inbounds/get/'):
            inbound_id = int(endpoint.split('/')[-1])
            if inbound_id == 1:
                return {
                    'success': True,
                    'obj': {
                        'id': 1,
                        'protocol': 'vmess',
                        'port': 8443,
                        'remark': 'Default VMess',
                        'enable': True,
                        'up': 1024 * 1024 * 100,  # 100 MB
                        'down': 1024 * 1024 * 200,  # 200 MB
                        'total': 1024 * 1024 * 1024 * 10,  # 10 GB
                        'settings': '{"clients":[{"id":"8f91b6a0-e8ee-11ea-adc1-0242ac120002","alterId":0,"email":"user1@example.com"}]}',
                        'clientStats': [
                            {
                                'id': '8f91b6a0-e8ee-11ea-adc1-0242ac120002',
                                'email': 'user1@example.com',
                                'up': 1024 * 1024 * 50,  # 50 MB
                                'down': 1024 * 1024 * 100,  # 100 MB
                                'total': 1024 * 1024 * 1024 * 5,  # 5 GB
                                'expiryTime': int((datetime.now() + timedelta(days=30)).timestamp() * 1000),
                                'enable': True
                            }
                        ]
                    }
                }
            elif inbound_id == 2:
                return {
                    'success': True,
                    'obj': {
                        'id': 2,
                        'protocol': 'vless',
                        'port': 8444,
                        'remark': 'Default VLESS',
                        'enable': True,
                        'up': 1024 * 1024 * 150,  # 150 MB
                        'down': 1024 * 1024 * 250,  # 250 MB
                        'total': 1024 * 1024 * 1024 * 20,  # 20 GB
                        'settings': '{"clients":[{"id":"9f91b6a0-e8ee-11ea-adc1-0242ac120003","flow":"","email":"user2@example.com"}]}',
                        'clientStats': [
                            {
                                'id': '9f91b6a0-e8ee-11ea-adc1-0242ac120003',
                                'email': 'user2@example.com',
                                'up': 1024 * 1024 * 75,  # 75 MB
                                'down': 1024 * 1024 * 125,  # 125 MB
                                'total': 1024 * 1024 * 1024 * 10,  # 10 GB
                                'expiryTime': int((datetime.now() + timedelta(days=60)).timestamp() * 1000),
                                'enable': True
                            }
                        ]
                    }
                }
            else:
                return {'success': False, 'msg': 'Inbound not found'}
                
        # Add client endpoint
        elif endpoint == '/panel/api/inbounds/addClient':
            return {'success': True, 'msg': 'Client added successfully'}
            
        # Delete client endpoint
        elif endpoint.startswith('/panel/api/inbounds/delClient/'):
            return {'success': True, 'msg': 'Client deleted successfully'}
            
        # Reset client traffic endpoint
        elif endpoint.startswith('/panel/api/inbounds/resetClientTraffic/'):
            return {'success': True, 'msg': 'Client traffic reset successfully'}
            
        # Online clients endpoint
        elif endpoint == '/panel/api/inbounds/onlines':
            return {
                'success': True,
                'obj': [
                    {
                        'email': 'user1@example.com',
                        'inboundId': 1,
                        'ip': '192.168.1.100',
                        'up': 1024 * 1024 * 10,  # 10 MB
                        'down': 1024 * 1024 * 20,  # 20 MB
                    }
                ]
            }
            
        # Default response for unknown endpoints
        return {'success': False, 'msg': 'Unknown endpoint'}
    
    def get_inbounds(self):
        """
        Get all inbounds from the panel.
        
        Returns:
            List of inbound objects or None on failure
        """
        response = self._request('GET', '/panel/api/inbounds/list')
        if response and response.get('success'):
            return response.get('obj', [])
        return None
    
    def get_inbound(self, inbound_id):
        """
        Get a specific inbound by ID.
        
        Args:
            inbound_id: ID of the inbound to retrieve
            
        Returns:
            Inbound object or None on failure
        """
        response = self._request('GET', f'/panel/api/inbounds/get/{inbound_id}')
        if response and response.get('success'):
            return response.get('obj')
        return None
    
    def get_clients(self, inbound_id):
        """
        Get all clients for a specific inbound.
        
        Args:
            inbound_id: ID of the inbound
            
        Returns:
            List of client objects or None on failure
        """
        inbound = self.get_inbound(inbound_id)
        if inbound and 'clientStats' in inbound:
            return inbound['clientStats']
        return None
    
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users across all inbounds.
        
        Returns:
            List of user dictionaries
        """
        users = []
        inbounds = self.get_inbounds()
        
        if not inbounds:
            return []
            
        for inbound in inbounds:
            inbound_id = inbound.get('id')
            clients = self.get_clients(inbound_id)
            
            if not clients:
                continue
                
            for client in clients:
                users.append({
                    'email': client.get('email', ''),
                    'inbound_id': inbound_id,
                    'protocol': inbound.get('protocol', ''),
                    'up': client.get('up', 0),
                    'down': client.get('down', 0),
                    'total': client.get('total', 0),
                    'expiry_time': client.get('expiryTime', 0),
                    'enable': client.get('enable', False)
                })
                
        return users
    
    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by email across all inbounds.
        
        Args:
            email: User email to search for
            
        Returns:
            Dict: User information or None if not found
        """
        inbounds = self.get_inbounds()
        if not inbounds:
            return None
            
        for inbound in inbounds:
            inbound_id = inbound.get('id')
            clients = self.get_clients(inbound_id)
            
            if not clients:
                continue
                
            for client in clients:
                if client.get('email') == email:
                    return {
                        'email': email,
                        'inbound_id': inbound_id,
                        'protocol': inbound.get('protocol', ''),
                        'uuid': client.get('id', ''),
                        'up': client.get('up', 0),
                        'down': client.get('down', 0),
                        'total': client.get('total', 0),
                        'expiry_time': client.get('expiryTime', 0),
                        'enable': client.get('enable', False)
                    }
                    
        return None
    
    def get_user_traffic(self, email: str) -> Dict[str, int]:
        """
        Get traffic usage for a specific user.
        
        Args:
            email: User email
            
        Returns:
            Dict: Traffic usage information
        """
        user = self.get_user(email)
        if not user:
            return {'up': 0, 'down': 0, 'total': 0}
            
        return {
            'up': user.get('up', 0),
            'down': user.get('down', 0),
            'total': user.get('up', 0) + user.get('down', 0)
        }
    
    def add_user(self, email: str, **kwargs) -> bool:
        """
        Add a new client to an inbound.
        
        Args:
            email: Client email (unique identifier)
            **kwargs: Additional parameters
                inbound_id: ID of the inbound
                uuid: Client UUID (generated if not provided)
                traffic_limit_gb: Traffic limit in GB (0 for unlimited)
                expire_days: Number of days until expiration
            
        Returns:
            bool: True if successful, False otherwise
        """
        inbound_id = kwargs.get('inbound_id')
        uuid = kwargs.get('uuid')
        traffic_limit_gb = kwargs.get('traffic_limit_gb', 0)
        expire_days = kwargs.get('expire_days', 30)
        
        # If no inbound_id provided, find a suitable one
        if not inbound_id:
            inbounds = self.get_inbounds()
            if not inbounds:
                self.logger.error("No inbounds found")
                return False
                
            # Find first enabled inbound
            for inbound in inbounds:
                if inbound.get('enable', False):
                    inbound_id = inbound.get('id')
                    break
                    
            if not inbound_id:
                self.logger.error("No enabled inbounds found")
                return False
        
        # Get inbound to determine protocol
        inbound = self.get_inbound(inbound_id)
        if not inbound:
            self.logger.error(f"Inbound {inbound_id} not found")
            return False
            
        protocol = inbound.get('protocol', '').lower()
        
        # Generate UUID if not provided
        if not uuid:
            uuid = str(uuid4())
            
        # Calculate expiry time
        total_gb = traffic_limit_gb
        expiry_time = int((datetime.now() + timedelta(days=expire_days)).timestamp() * 1000)
        
        # Prepare client settings based on protocol
        settings = {}
        if protocol == 'vmess':
            settings = {
                "id": uuid,
                "alterId": 0,
                "email": email,
                "limitIp": 0,
                "totalGB": total_gb,
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": "",
                "subId": ""
            }
        elif protocol == 'vless':
            settings = {
                "id": uuid,
                "flow": "",
                "email": email,
                "limitIp": 0,
                "totalGB": total_gb,
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": "",
                "subId": ""
            }
        elif protocol == 'trojan':
            settings = {
                "password": uuid,
                "email": email,
                "limitIp": 0,
                "totalGB": total_gb,
                "expiryTime": expiry_time,
                "enable": True,
                "tgId": "",
                "subId": ""
            }
        else:
            self.logger.error(f"Unsupported protocol: {protocol}")
            return False
            
        # Make API request to add client
        endpoint = f"/panel/api/inbounds/addClient"
        data = {
            "id": inbound_id,
            "settings": json.dumps(settings)
        }
        
        response = self._request('POST', endpoint, data=data)
        if response and response.get('success'):
            self.logger.info(f"Successfully added client {email} to inbound {inbound_id}")
            return True
            
        self.logger.error(f"Failed to add client: {response.get('msg') if response else 'Unknown error'}")
        return False
    
    def remove_user(self, email: str) -> bool:
        """
        Remove a client from the server.
        
        Args:
            email: Client email to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        user = self.get_user(email)
        if not user:
            self.logger.error(f"User {email} not found")
            return False
            
        inbound_id = user.get('inbound_id')
        endpoint = f"/panel/api/inbounds/delClient/{inbound_id}/{email}"
        response = self._request('POST', endpoint)
        
        if response and response.get('success'):
            self.logger.info(f"Successfully removed client {email} from inbound {inbound_id}")
            return True
            
        self.logger.error(f"Failed to remove client: {response.get('msg') if response else 'Unknown error'}")
        return False
    
    def update_user(self, email: str, **kwargs) -> bool:
        """
        Update a user's configuration.
        
        Args:
            email: User email/identifier
            **kwargs: User parameters to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        # In 3x-UI, updating a user requires removing and re-adding them
        user = self.get_user(email)
        if not user:
            self.logger.error(f"User {email} not found")
            return False
            
        # Remove existing user
        if not self.remove_user(email):
            self.logger.error(f"Failed to remove user {email} for update")
            return False
            
        # Get existing values and update with new ones
        inbound_id = kwargs.get('inbound_id', user.get('inbound_id'))
        uuid = kwargs.get('uuid', user.get('uuid'))
        
        # Calculate remaining days if expiry_time exists
        remaining_days = 30  # Default
        expiry_time = user.get('expiry_time', 0)
        if expiry_time > 0:
            expiry_date = datetime.fromtimestamp(expiry_time / 1000)
            remaining_days = (expiry_date - datetime.now()).days
            remaining_days = max(1, remaining_days)  # At least 1 day
            
        expire_days = kwargs.get('expire_days', remaining_days)
        
        # Traffic limit
        total = user.get('total', 0)
        traffic_limit_gb = kwargs.get('traffic_limit_gb', total / (1024 * 1024 * 1024) if total > 0 else 0)
        
        # Add user with updated values
        return self.add_user(
            email,
            inbound_id=inbound_id,
            uuid=uuid,
            traffic_limit_gb=traffic_limit_gb,
            expire_days=expire_days
        )
    
    def reset_user_traffic(self, email: str) -> bool:
        """
        Reset traffic counters for a user.
        
        Args:
            email: User email/identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        user = self.get_user(email)
        if not user:
            self.logger.error(f"User {email} not found")
            return False
            
        inbound_id = user.get('inbound_id')
        endpoint = f"/panel/api/inbounds/resetClientTraffic/{inbound_id}/{email}"
        response = self._request('POST', endpoint)
        
        if response and response.get('success'):
            self.logger.info(f"Successfully reset traffic for client {email}")
            return True
            
        self.logger.error(f"Failed to reset traffic: {response.get('msg') if response else 'Unknown error'}")
        return False
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get server status information.
        
        Returns:
            Dict: Server status information
        """
        response = self._request('GET', '/panel/api/server/status')
        if response and response.get('success'):
            return response.get('obj', {})
        return {'status': 'error', 'cpu': 0, 'mem': 0, 'disk': 0}
    
    def get_online_users(self) -> List[Dict[str, Any]]:
        """
        Get all currently online users.
        
        Returns:
            List: Online user information
        """
        response = self._request('GET', '/panel/api/inbounds/onlines')
        if response and response.get('success'):
            return response.get('obj', [])
        return []
    
    def get_user_config(self, email: str, **kwargs) -> Dict[str, Any]:
        """
        Get user configuration for connecting to VPN.
        
        Args:
            email: User email/identifier
            **kwargs: Additional parameters
            
        Returns:
            Dict: Configuration information with connection links
        """
        user = self.get_user(email)
        if not user:
            return {}
            
        inbound_id = user.get('inbound_id')
        inbound = self.get_inbound(inbound_id)
        if not inbound:
            return {}
            
        protocol = inbound.get('protocol', '').lower()
        port = inbound.get('port')
        host = self.server.host
        
        uuid = user.get('uuid')
        
        result = {
            'protocol': protocol,
            'host': host,
            'port': port,
            'uuid': uuid,
            'email': email,
            'links': {}
        }
        
        # Generate the appropriate connection links based on protocol
        server_address = host if ':' not in host else f"[{host}]"
        
        if protocol == 'vmess':
            vmess_config = {
                "v": "2",
                "ps": f"MoonVPN-{self.server.name}-{email}",
                "add": server_address,
                "port": port,
                "id": uuid,
                "aid": 0,
                "net": "tcp",
                "type": "none",
                "host": "",
                "path": "",
                "tls": "",
                "sni": ""
            }
            
            import base64
            import json
            
            # Base64 encode the config
            vmess_link = "vmess://" + base64.b64encode(json.dumps(vmess_config).encode()).decode()
            result['links']['vmess'] = vmess_link
            
        elif protocol == 'vless':
            # vless://uuid@server:port?encryption=none&type=tcp#remark
            vless_link = f"vless://{uuid}@{server_address}:{port}?encryption=none&type=tcp#{self.server.name}-{email}"
            result['links']['vless'] = vless_link
            
        elif protocol == 'trojan':
            # trojan://password@server:port?sni=sni.com#remark
            trojan_link = f"trojan://{uuid}@{server_address}:{port}?sni={server_address}#{self.server.name}-{email}"
            result['links']['trojan'] = trojan_link
            
        return result 