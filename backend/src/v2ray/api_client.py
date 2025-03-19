import requests
import json
import logging
import uuid
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .models import Inbound, Client, SyncLog, ClientConfig
from main.models import Server, Subscription

logger = logging.getLogger(__name__)

class ThreeXUIClient:
    """Client for interacting with 3x-UI API"""
    
    def __init__(self, server):
        """Initialize the client with a server instance"""
        self.server = server
        self.base_url = server.url.rstrip('/')
        self.username = server.username
        self.password = server.password
        self.session = requests.Session()
        self.timeout = getattr(settings, 'THREEXUI_API_TIMEOUT', 30)
        self.session_expiry = getattr(settings, 'THREEXUI_SESSION_EXPIRY', 3600)
        self.max_retries = getattr(settings, 'THREEXUI_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'THREEXUI_RETRY_DELAY', 2)  # seconds
    
    def _handle_response(self, response):
        """Handle API response and check for errors"""
        try:
            response.raise_for_status()
            data = response.json()
            if data.get('success') is False:
                logger.error(f"API error: {data.get('msg')}")
                return None
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text[:100]}...")
            return None
    
    def _request_with_retry(self, method, url, **kwargs):
        """Make a request with retry logic"""
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.session.request(method, url, **kwargs)
                result = self._handle_response(response)
                
                # Check if session expired and reauthenticate
                if not result and 'login' in response.url and retries < self.max_retries - 1:
                    logger.info("Session expired, attempting to re-login")
                    self.server.session_cookie = None
                    self.server.session_expiry = None
                    self.server.save()
                    if self.login():
                        retries += 1
                        continue
                
                return result
            except Exception as e:
                logger.error(f"Request error (attempt {retries+1}/{self.max_retries}): {str(e)}")
                retries += 1
                if retries < self.max_retries:
                    # Wait before retrying
                    import time
                    time.sleep(self.retry_delay)
                    continue
                return None
        return None
    
    def login(self):
        """Login to 3x-UI panel and store session cookie"""
        # Check if we already have a valid session
        if self.server.is_session_valid():
            # Load existing session cookie
            try:
                self.session.cookies.update(json.loads(self.server.session_cookie))
                
                # Verify session is valid by making a test request
                test_url = f"{self.base_url}/panel/api/server/status"
                response = self.session.get(test_url, timeout=self.timeout)
                if response.status_code == 200 and 'login' not in response.url:
                    return True
                
                # Session invalid, clear it
                logger.info("Saved session invalid, getting a new one")
                self.server.session_cookie = None
                self.server.session_expiry = None
                self.server.save()
            except Exception as e:
                logger.error(f"Error loading saved session: {str(e)}")
                self.server.session_cookie = None
                self.server.session_expiry = None
                self.server.save()
        
        # Login to get a new session
        try:
            url = f"{self.base_url}/login"
            data = {
                "username": self.username,
                "password": self.password
            }
            response = self.session.post(url, json=data, timeout=self.timeout)
            result = self._handle_response(response)
            
            if result and result.get('success'):
                # Store session cookie
                self.server.session_cookie = json.dumps(dict(self.session.cookies))
                self.server.session_expiry = timezone.now() + timedelta(seconds=self.session_expiry)
                self.server.save()
                
                # Log successful login
                logger.info(f"Successfully logged in to 3x-UI panel at {self.base_url}")
                return True
            
            # Log login failure
            logger.error(f"Failed to login to 3x-UI panel at {self.base_url}: {result.get('msg') if result else 'No response'}")
            return False
        except Exception as e:
            logger.error(f"Login error for 3x-UI panel at {self.base_url}: {str(e)}")
            return False
    
    def get_server_status(self):
        """Get server status information"""
        if not self.login():
            return None
        
        url = f"{self.base_url}/panel/api/server/status"
        return self._request_with_retry('GET', url, timeout=self.timeout)
    
    def get_inbounds(self):
        """Get all inbounds from the panel"""
        if not self.login():
            return None
        
        url = f"{self.base_url}/panel/api/inbounds/list"
        result = self._request_with_retry('GET', url, timeout=self.timeout)
        
        if result and result.get('success'):
            return result.get('obj', [])
        
        return None
    
    def get_inbound(self, inbound_id):
        """Get a specific inbound by ID"""
        if not self.login():
            return None
        
        url = f"{self.base_url}/panel/api/inbounds/get/{inbound_id}"
        result = self._request_with_retry('GET', url, timeout=self.timeout)
        
        if result and result.get('success'):
            return result.get('obj')
        
        return None
    
    def add_client(self, inbound_id, email, uuid_str=None, traffic_limit_gb=0, expiry_time=None):
        """Add a client to an inbound"""
        if not self.login():
            return None
        
        try:
            # Get inbound to determine protocol
            inbound = self.get_inbound(inbound_id)
            if not inbound:
                logger.error(f"Inbound {inbound_id} not found")
                return False
            
            protocol = inbound.get('protocol', 'vmess')
            
            # Create a client object based on protocol
            if not uuid_str:
                uuid_str = str(uuid.uuid4())
            
            # Generate client settings based on protocol
            client = {
                "email": email,
                "enable": True,
                "uuid": uuid_str if protocol in ['vmess', 'vless'] else None,
                "password": uuid_str if protocol == 'trojan' else None,
                "flow": "" if protocol == 'vless' else None,
                "alterId": 0 if protocol == 'vmess' else None,
            }
            
            # Set expiry time if provided
            if expiry_time:
                client["expiryTime"] = int(expiry_time.timestamp() * 1000)
            
            # Set traffic limit if provided
            if traffic_limit_gb > 0:
                client["total"] = traffic_limit_gb * 1024 * 1024 * 1024
            
            # Remove None values
            client = {k: v for k, v in client.items() if v is not None}
            
            # Create request data
            url = f"{self.base_url}/panel/api/inbounds/addClient"
            data = {
                "id": inbound_id,
                "client": client
            }
            
            result = self._request_with_retry('POST', url, json=data, timeout=self.timeout)
            
            if result and result.get('success'):
                logger.info(f"Successfully added client {email} to inbound {inbound_id}")
                
                # Generate client config
                self.generate_client_config(inbound_id, email, uuid_str, protocol)
                
                return True
            
            logger.error(f"Failed to add client {email} to inbound {inbound_id}: {result.get('msg') if result else 'No response'}")
            return False
        except Exception as e:
            logger.error(f"Add client error: {str(e)}")
            return False
    
    def generate_client_config(self, inbound_id, email, uuid_str, protocol):
        """Generate client configuration links"""
        if not self.login():
            return None
        
        try:
            # Get inbound details
            inbound = self.get_inbound(inbound_id)
            if not inbound:
                logger.error(f"Inbound {inbound_id} not found")
                return None
            
            # Get server domain/address
            domain = self.base_url.replace('http://', '').replace('https://', '').split(':')[0]
            
            # Generate config links based on protocol
            vmess_link = ""
            vless_link = ""
            trojan_link = ""
            shadowsocks_link = ""
            subscription_url = f"{self.base_url}/sub/{email}"
            
            if protocol == 'vmess':
                port = inbound.get('port')
                network = inbound.get('streamSettings', {}).get('network', 'tcp')
                
                # Generate VMess config
                vmess_config = {
                    "v": "2",
                    "ps": f"{domain}-{email}",
                    "add": domain,
                    "port": port,
                    "id": uuid_str,
                    "aid": 0,
                    "net": network,
                    "type": "none",
                    "host": "",
                    "path": "/",
                    "tls": ""
                }
                
                import base64
                vmess_link = f"vmess://{base64.b64encode(json.dumps(vmess_config).encode()).decode()}"
            
            elif protocol == 'vless':
                port = inbound.get('port')
                network = inbound.get('streamSettings', {}).get('network', 'tcp')
                security = inbound.get('streamSettings', {}).get('security', 'none')
                
                vless_link = f"vless://{uuid_str}@{domain}:{port}?type={network}&security={security}&path=/"
            
            elif protocol == 'trojan':
                port = inbound.get('port')
                
                trojan_link = f"trojan://{uuid_str}@{domain}:{port}"
            
            # Save client config
            client = Client.objects.filter(
                inbound__inbound_id=inbound_id,
                email=email
            ).first()
            
            if client:
                ClientConfig.objects.update_or_create(
                    client=client,
                    defaults={
                        'vmess_link': vmess_link,
                        'vless_link': vless_link,
                        'trojan_link': trojan_link,
                        'shadowsocks_link': shadowsocks_link,
                        'subscription_url': subscription_url,
                        'qrcode_data': vmess_link or vless_link or trojan_link or shadowsocks_link
                    }
                )
                logger.info(f"Generated config for client {email}")
                return True
            
            logger.error(f"Client {email} not found in database")
            return False
        
        except Exception as e:
            logger.error(f"Generate client config error: {str(e)}")
            return False
    
    def remove_client(self, inbound_id, email):
        """Remove a client from an inbound"""
        if not self.login():
            return False
        
        url = f"{self.base_url}/panel/api/inbounds/delClient/{inbound_id}/{email}"
        result = self._request_with_retry('POST', url, timeout=self.timeout)
        
        if result and result.get('success'):
            logger.info(f"Successfully removed client {email} from inbound {inbound_id}")
            return True
        
        logger.error(f"Failed to remove client {email} from inbound {inbound_id}: {result.get('msg') if result else 'No response'}")
        return False
    
    def update_client_traffic(self, inbound_id, email, traffic_limit_gb):
        """Update a client's traffic limit"""
        if not self.login():
            return False
        
        # Convert traffic limit from GB to bytes
        traffic_limit = traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0
        
        url = f"{self.base_url}/panel/api/inbounds/updateClientTraffic/{inbound_id}/{email}"
        data = {
            "id": inbound_id,
            "email": email,
            "total": traffic_limit
        }
        
        result = self._request_with_retry('POST', url, json=data, timeout=self.timeout)
        
        if result and result.get('success'):
            logger.info(f"Successfully updated traffic limit for client {email} to {traffic_limit_gb} GB")
            return True
        
        logger.error(f"Failed to update traffic limit for client {email}: {result.get('msg') if result else 'No response'}")
        return False
    
    def update_client_expiry(self, inbound_id, email, expiry_time):
        """Update a client's expiry time"""
        if not self.login():
            return False
        
        # Format expiry time
        expiry_time_ms = int(expiry_time.timestamp() * 1000)
        
        url = f"{self.base_url}/panel/api/inbounds/updateClientExpiryTime/{inbound_id}/{email}"
        data = {
            "id": inbound_id,
            "email": email,
            "expiryTime": expiry_time_ms
        }
        
        result = self._request_with_retry('POST', url, json=data, timeout=self.timeout)
        
        if result and result.get('success'):
            logger.info(f"Successfully updated expiry time for client {email} to {expiry_time}")
            return True
        
        logger.error(f"Failed to update expiry time for client {email}: {result.get('msg') if result else 'No response'}")
        return False
    
    def get_client_traffic(self, inbound_id, email=None):
        """Get client traffic statistics"""
        if not self.login():
            return None
        
        url = f"{self.base_url}/panel/api/inbounds/getClientTraffics/{inbound_id}"
        result = self._request_with_retry('GET', url, timeout=self.timeout)
        
        if result and result.get('success'):
            clients = result.get('obj', [])
            
            # Filter by email if provided
            if email:
                clients = [c for c in clients if c.get('email') == email]
                
                if clients:
                    return clients[0]
                logger.warning(f"Client {email} not found in traffic statistics")
                return None
            
            return clients
        
        logger.error(f"Failed to get client traffic statistics: {result.get('msg') if result else 'No response'}")
        return None
    
    def reset_client_traffic(self, inbound_id, email):
        """Reset a client's traffic usage"""
        if not self.login():
            return False
        
        url = f"{self.base_url}/panel/api/inbounds/resetClientTraffic/{inbound_id}/{email}"
        result = self._request_with_retry('POST', url, timeout=self.timeout)
        
        if result and result.get('success'):
            logger.info(f"Successfully reset traffic usage for client {email}")
            return True
        
        logger.error(f"Failed to reset traffic usage for client {email}: {result.get('msg') if result else 'No response'}")
        return False
    
    def get_client_url(self, inbound_id, email):
        """Get client connection URL"""
        if not self.login():
            return None
        
        url = f"{self.base_url}/panel/api/inbounds/getClientUrl/{inbound_id}/{email}"
        result = self._request_with_retry('GET', url, timeout=self.timeout)
        
        if result and result.get('success'):
            return result.get('obj')
        
        return None


def sync_server(server_id):
    """Sync a server with the 3x-UI panel"""
    try:
        server = Server.objects.get(id=server_id)
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            server=server,
            status='running',
            message="Starting server synchronization"
        )
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Get inbounds
        inbounds = client.get_inbounds()
        if not inbounds:
            sync_log.status = 'failed'
            sync_log.message = "Failed to get inbounds from server"
            sync_log.save()
            return False
        
        # Store inbounds
        for inbound_data in inbounds:
            inbound_id = inbound_data.get('id')
            
            # Skip if inbound doesn't have an ID
            if not inbound_id:
                continue
            
            # Parse settings
            try:
                settings = json.loads(inbound_data.get('settings', '{}'))
            except:
                settings = {}
            
            # Parse stream settings
            try:
                stream_settings = json.loads(inbound_data.get('streamSettings', '{}'))
            except:
                stream_settings = {}
            
            # Update or create inbound
            inbound, created = Inbound.objects.update_or_create(
                server=server,
                inbound_id=inbound_id,
                defaults={
                    'protocol': inbound_data.get('protocol', ''),
                    'tag': inbound_data.get('remark', ''),
                    'port': inbound_data.get('port', 0),
                    'network': stream_settings.get('network', ''),
                    'enable': inbound_data.get('enable', False),
                    'expiry_time': datetime.fromtimestamp(inbound_data.get('expiryTime', 0) / 1000) if inbound_data.get('expiryTime', 0) > 0 else None,
                    'listen': inbound_data.get('listen', ''),
                    'total': inbound_data.get('total', 0),
                    'remark': inbound_data.get('remark', ''),
                    'up': inbound_data.get('up', 0),
                    'down': inbound_data.get('down', 0),
                    'last_sync': timezone.now()
                }
            )
            
            # Get client traffic
            client_traffic = client.get_client_traffic(inbound_id)
            
            if client_traffic:
                for traffic_data in client_traffic:
                    email = traffic_data.get('email', '')
                    
                    # Skip if email is empty
                    if not email:
                        continue
                    
                    # Update or create client
                    client_obj, created = Client.objects.update_or_create(
                        inbound=inbound,
                        email=email,
                        defaults={
                            'client_id': traffic_data.get('id', ''),
                            'enable': traffic_data.get('enable', True),
                            'expiry_time': datetime.fromtimestamp(traffic_data.get('expiryTime', 0) / 1000) if traffic_data.get('expiryTime', 0) > 0 else None,
                            'total': traffic_data.get('total', 0),
                            'up': traffic_data.get('up', 0),
                            'down': traffic_data.get('down', 0),
                            'last_sync': timezone.now()
                        }
                    )
                    
                    # Update subscription if client is linked to one
                    try:
                        subscription = Subscription.objects.get(client_email=email)
                        
                        # Update data usage
                        total_gb = client_obj.total / (1024 * 1024 * 1024) if client_obj.total > 0 else 0
                        used_gb = (client_obj.up + client_obj.down) / (1024 * 1024 * 1024)
                        
                        subscription.data_usage_gb = used_gb
                        
                        # Update status if expired
                        if client_obj.expiry_time and client_obj.expiry_time < timezone.now():
                            subscription.status = 'expired'
                        elif not client_obj.enable:
                            subscription.status = 'suspended'
                        
                        subscription.save()
                    except Subscription.DoesNotExist:
                        # No subscription linked to this client
                        pass
        
        # Update sync log
        sync_log.status = 'completed'
        sync_log.message = "Synchronization completed successfully"
        sync_log.save()
        
        return True
    
    except Exception as e:
        logger.error(f"Server sync error: {str(e)}")
        
        # Update sync log if exists
        if 'sync_log' in locals():
            sync_log.status = 'failed'
            sync_log.message = f"Synchronization failed: {str(e)}"
            sync_log.save()
        
        return False


def create_client(subscription_id):
    """Create a client in the 3x-UI panel for a subscription"""
    try:
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Skip if subscription is not active
        if subscription.status != 'active':
            logger.warning(f"Subscription {subscription_id} is not active, skipping client creation")
            return False
        
        # Get server
        server = subscription.server
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Generate unique email if not set
        if not subscription.client_email:
            username = subscription.user.username.replace('@', '').replace('.', '')
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            subscription.client_email = f"{username}_{random_suffix}@v2ray.local"
            subscription.save()
        
        # Find a suitable inbound
        inbounds = Inbound.objects.filter(server=server, enable=True)
        
        if not inbounds.exists():
            logger.error(f"No suitable inbound found for server {server.id}")
            return False
        
        # Pick the first active inbound
        inbound = inbounds.first()
        
        # Calculate expiry time
        expiry_time = subscription.end_date
        
        # Create client
        result = client.add_client(
            inbound.inbound_id,
            subscription.client_email,
            traffic_limit_gb=subscription.data_limit_gb,
            expiry_time=expiry_time
        )
        
        if result:
            # Update subscription with inbound details
            subscription.inbound_id = inbound.inbound_id
            subscription.save()
            
            # Link client to subscription
            client_obj = Client.objects.filter(
                inbound=inbound,
                email=subscription.client_email
            ).first()
            
            if client_obj:
                client_obj.subscription_id = subscription.id
                client_obj.save()
            
            logger.info(f"Created client for subscription {subscription_id}")
            return True
        
        logger.error(f"Failed to create client for subscription {subscription_id}")
        return False
    
    except Exception as e:
        logger.error(f"Create client error: {str(e)}")
        return False


def delete_client(subscription_id):
    """Delete a client from the 3x-UI panel"""
    try:
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Skip if no client email or inbound ID
        if not subscription.client_email or not subscription.inbound_id:
            logger.warning(f"Subscription {subscription_id} has no client details, skipping deletion")
            return False
        
        # Get server
        server = subscription.server
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Delete client
        result = client.remove_client(
            subscription.inbound_id,
            subscription.client_email
        )
        
        if result:
            # Delete client from database
            Client.objects.filter(
                inbound__server=server,
                inbound__inbound_id=subscription.inbound_id,
                email=subscription.client_email
            ).delete()
            
            # Update subscription
            subscription.client_email = None
            subscription.inbound_id = None
            subscription.client_config = None
            subscription.save()
            
            logger.info(f"Deleted client for subscription {subscription_id}")
            return True
        
        logger.error(f"Failed to delete client for subscription {subscription_id}")
        return False
    
    except Exception as e:
        logger.error(f"Delete client error: {str(e)}")
        return False


def update_client_traffic(subscription_id, traffic_limit_gb):
    """Update a client's traffic limit"""
    try:
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Skip if no client email or inbound ID
        if not subscription.client_email or not subscription.inbound_id:
            logger.warning(f"Subscription {subscription_id} has no client details, skipping traffic update")
            return False
        
        # Get server
        server = subscription.server
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Update client traffic
        result = client.update_client_traffic(
            subscription.inbound_id,
            subscription.client_email,
            traffic_limit_gb
        )
        
        if result:
            # Update subscription
            subscription.data_limit_gb = traffic_limit_gb
            subscription.save()
            
            # Update client in database
            client_obj = Client.objects.filter(
                inbound__server=server,
                inbound__inbound_id=subscription.inbound_id,
                email=subscription.client_email
            ).first()
            
            if client_obj:
                client_obj.total = traffic_limit_gb * 1024 * 1024 * 1024
                client_obj.save()
            
            logger.info(f"Updated traffic limit for subscription {subscription_id} to {traffic_limit_gb} GB")
            return True
        
        logger.error(f"Failed to update traffic limit for subscription {subscription_id}")
        return False
    
    except Exception as e:
        logger.error(f"Update client traffic error: {str(e)}")
        return False


def update_client_expiry(subscription_id, expiry_time):
    """Update a client's expiry time"""
    try:
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Skip if no client email or inbound ID
        if not subscription.client_email or not subscription.inbound_id:
            logger.warning(f"Subscription {subscription_id} has no client details, skipping expiry update")
            return False
        
        # Get server
        server = subscription.server
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Update client expiry
        result = client.update_client_expiry(
            subscription.inbound_id,
            subscription.client_email,
            expiry_time
        )
        
        if result:
            # Update subscription
            subscription.end_date = expiry_time
            subscription.save()
            
            # Update client in database
            client_obj = Client.objects.filter(
                inbound__server=server,
                inbound__inbound_id=subscription.inbound_id,
                email=subscription.client_email
            ).first()
            
            if client_obj:
                client_obj.expiry_time = expiry_time
                client_obj.save()
            
            logger.info(f"Updated expiry time for subscription {subscription_id} to {expiry_time}")
            return True
        
        logger.error(f"Failed to update expiry time for subscription {subscription_id}")
        return False
    
    except Exception as e:
        logger.error(f"Update client expiry error: {str(e)}")
        return False


def reset_client_traffic(subscription_id):
    """Reset a client's traffic usage"""
    try:
        # Get subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Skip if no client email or inbound ID
        if not subscription.client_email or not subscription.inbound_id:
            logger.warning(f"Subscription {subscription_id} has no client details, skipping traffic reset")
            return False
        
        # Get server
        server = subscription.server
        
        # Create API client
        client = ThreeXUIClient(server)
        
        # Reset client traffic
        result = client.reset_client_traffic(
            subscription.inbound_id,
            subscription.client_email
        )
        
        if result:
            # Update subscription
            subscription.data_usage_gb = 0
            subscription.save()
            
            # Update client in database
            client_obj = Client.objects.filter(
                inbound__server=server,
                inbound__inbound_id=subscription.inbound_id,
                email=subscription.client_email
            ).first()
            
            if client_obj:
                client_obj.up = 0
                client_obj.down = 0
                client_obj.save()
            
            logger.info(f"Reset traffic usage for subscription {subscription_id}")
            return True
        
        logger.error(f"Failed to reset traffic usage for subscription {subscription_id}")
        return False
    
    except Exception as e:
        logger.error(f"Reset client traffic error: {str(e)}")
        return False 