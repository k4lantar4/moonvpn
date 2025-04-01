import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import base64
import qrcode
from io import BytesIO
import json

from app.utils.sync_panel_client import SyncPanelClient, PanelClientError
from app.models.panel import Panel as PanelModel
from app.models.client import Client as ClientModel
from app.db.session import SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PanelException(Exception):
    """Base exception for panel service errors."""
    pass

class PanelConnectionError(PanelException):
    """Error when connecting to the panel."""
    pass

class PanelAuthenticationError(PanelException):
    """Error when authenticating with the panel."""
    pass

class PanelClientNotFoundError(PanelException):
    """Error when a client could not be found."""
    pass

class PanelInboundNotFoundError(PanelException):
    """Error when an inbound could not be found."""
    pass

class PanelService:
    """
    High-level service for interacting with VPN panels.
    Abstracts away the specific panel API implementation details.
    """
    
    def __init__(self, panel_id: Optional[int] = None):
        """
        Initialize the panel service.
        
        Args:
            panel_id: Database ID of the panel to use (if None, uses default panel)
        """
        self.panel_id = panel_id
        self._client = None
        self._panel_info = None
        
    def __enter__(self):
        """Support context manager pattern."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        self.close()
        
    def close(self):
        """Close the panel client connection."""
        if self._client:
            self._client.close()
            self._client = None
    
    def _get_panel_info(self) -> Dict[str, Any]:
        """
        Get panel connection information from the database.
        
        Returns:
            Dictionary with panel connection details
            
        Raises:
            PanelException: If panel info could not be retrieved
        """
        # If we already have panel info cached, return it
        if self._panel_info:
            return self._panel_info
            
        try:
            # Create a new DB session
            db = SessionLocal()
            
            try:
                # Query the panel by ID or get the default (active) panel
                if self.panel_id:
                    panel = db.query(PanelModel).filter(PanelModel.id == self.panel_id).first()
                else:
                    # Get the first active panel
                    panel = db.query(PanelModel).filter(PanelModel.is_active == True).first()
                    
                if not panel:
                    raise PanelException("No active panel found in the database")
                    
                # Extract connection details
                panel_info = {
                    "id": panel.id,
                    "name": panel.name,
                    "base_url": panel.url,
                    "username": panel.admin_username,
                    "password": panel.admin_password,
                    "default_inbound_id": panel.default_inbound_id
                }
                
                # Cache the panel info
                self._panel_info = panel_info
                return panel_info
                
            finally:
                # Always close the DB session
                db.close()
                
        except Exception as e:
            logger.exception(f"Error retrieving panel info: {e}")
            raise PanelException(f"Failed to get panel information: {str(e)}")
    
    def _get_client(self) -> SyncPanelClient:
        """
        Get or create a panel client instance.
        
        Returns:
            SyncPanelClient instance
            
        Raises:
            PanelConnectionError: If connection fails
        """
        if self._client:
            return self._client
            
        try:
            # Get panel connection info
            panel_info = self._get_panel_info()
            
            # Create a new client
            client = SyncPanelClient(
                base_url=panel_info["base_url"],
                username=panel_info["username"],
                password=panel_info["password"]
            )
            
            # Cache the client
            self._client = client
            return client
            
        except PanelException:
            # Re-raise existing panel exceptions
            raise
        except Exception as e:
            logger.exception(f"Error creating panel client: {e}")
            raise PanelConnectionError(f"Failed to connect to panel: {str(e)}")
            
    def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get all inbounds from the panel.
        
        Returns:
            List of inbound objects
            
        Raises:
            PanelConnectionError: If connection fails
            PanelAuthenticationError: If authentication fails
        """
        try:
            client = self._get_client()
            return client.get_inbounds()
        except PanelClientError as e:
            if "login" in str(e).lower():
                raise PanelAuthenticationError(f"Authentication failed: {str(e)}")
            raise PanelConnectionError(f"Failed to get inbounds: {str(e)}")
            
    def get_inbound_detail(self, inbound_id: int) -> Dict[str, Any]:
        """
        Get details for a specific inbound.
        
        Args:
            inbound_id: ID of the inbound
            
        Returns:
            Inbound details dictionary
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            Other panel exceptions for connection issues
        """
        try:
            # Get all inbounds first
            inbounds = self.get_inbounds()
            
            # Find specific inbound by ID
            inbound = next((i for i in inbounds if i.get('id') == inbound_id), None)
            
            if not inbound:
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
                
            return inbound
            
        except PanelInboundNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get inbound details: {str(e)}")
            raise PanelException(f"Failed to get inbound details: {str(e)}")
            
    def add_client(self, email: str, total_gb: int = 1, expire_days: int = 30, 
                 limit_ip: int = 0, inbound_id: Optional[int] = None,
                 client_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new client to the panel.
        
        Args:
            email: Email/remark for the client
            total_gb: Traffic limit in GB (0 for unlimited)
            expire_days: Days until expiration (0 for unlimited)
            limit_ip: Number of simultaneous connections allowed (0 for unlimited)
            inbound_id: ID of the inbound (if None, uses default inbound)
            client_uuid: Custom UUID (generated if None)
            
        Returns:
            Client information dictionary
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Add the client to the inbound
            result = client.add_client_to_inbound(
                inbound_id=inbound_id,
                remark=email,
                total_gb=total_gb,
                expire_days=expire_days,
                limit_ip=limit_ip,
                client_uuid=client_uuid
            )
            
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            raise PanelConnectionError(f"Failed to add client: {str(e)}")
            
    def remove_client(self, email: str, inbound_id: Optional[int] = None) -> bool:
        """
        Remove a client from the panel.
        
        Args:
            email: Email/remark of the client to remove
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Remove the client
            result = client.remove_client(inbound_id, email)
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            if "client" in str(e).lower() and "not found" in str(e).lower():
                raise PanelClientNotFoundError(f"Client with email {email} not found")
            raise PanelConnectionError(f"Failed to remove client: {str(e)}")
            
    def get_client(self, email: str, inbound_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get client details from the panel.
        
        Args:
            email: Email/remark of the client
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            Client information dictionary
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Get the client
            result = client.get_client(inbound_id, email)
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            raise PanelConnectionError(f"Failed to get client: {str(e)}")
            
    def update_client(self, email: str, total_gb: Optional[int] = None,
                   expire_days: Optional[int] = None, limit_ip: Optional[int] = None,
                   inbound_id: Optional[int] = None) -> bool:
        """
        Update client settings on the panel.
        
        Args:
            email: Email/remark of the client
            total_gb: New traffic limit in GB (None to keep current)
            expire_days: New expiration in days (None to keep current)
            limit_ip: New connection limit (None to keep current)
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Update the client
            result = client.update_client(
                inbound_id=inbound_id,
                client_email=email,
                new_total_gb=total_gb,
                new_expire_days=expire_days,
                new_limit_ip=limit_ip
            )
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            if "client" in str(e).lower() and "not found" in str(e).lower():
                raise PanelClientNotFoundError(f"Client with email {email} not found")
            raise PanelConnectionError(f"Failed to update client: {str(e)}")
            
    def enable_client(self, email: str, inbound_id: Optional[int] = None) -> bool:
        """
        Enable a client on the panel.
        
        Args:
            email: Email/remark of the client
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Enable the client
            result = client.enable_disable_client(inbound_id, email, enable=True)
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            if "client" in str(e).lower() and "not found" in str(e).lower():
                raise PanelClientNotFoundError(f"Client with email {email} not found")
            raise PanelConnectionError(f"Failed to enable client: {str(e)}")
            
    def disable_client(self, email: str, inbound_id: Optional[int] = None) -> bool:
        """
        Disable a client on the panel.
        
        Args:
            email: Email/remark of the client
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Disable the client
            result = client.enable_disable_client(inbound_id, email, enable=False)
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            if "client" in str(e).lower() and "not found" in str(e).lower():
                raise PanelClientNotFoundError(f"Client with email {email} not found")
            raise PanelConnectionError(f"Failed to disable client: {str(e)}")
            
    def get_client_traffic(self, email: str, inbound_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get traffic statistics for a client.
        
        Args:
            email: Email/remark of the client
            inbound_id: ID of the inbound (if None, uses default inbound)
            
        Returns:
            Traffic statistics dictionary
            
        Raises:
            PanelInboundNotFoundError: If inbound is not found
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            client = self._get_client()
            
            # If no inbound_id provided, get the default one
            if inbound_id is None:
                inbound = self.get_inbound_detail(inbound_id)
                inbound_id = inbound.get("id")
                
            # Get client traffic
            result = client.get_client_traffic(inbound_id, email)
            
            if not result:
                raise PanelClientNotFoundError(f"Client with email {email} not found in inbound {inbound_id}")
                
            return result
            
        except PanelInboundNotFoundError:
            # Re-raise inbound not found error
            raise
        except PanelClientError as e:
            if "inbound" in str(e).lower() and "not found" in str(e).lower():
                raise PanelInboundNotFoundError(f"Inbound with ID {inbound_id} not found")
            if "client" in str(e).lower() and "not found" in str(e).lower():
                raise PanelClientNotFoundError(f"Client with email {email} not found")
            raise PanelConnectionError(f"Failed to get client traffic: {str(e)}")
            
    def sync_client_with_db(self, client_db_id: int) -> Dict[str, Any]:
        """
        Synchronize a client from the database with the panel.
        
        Args:
            client_db_id: Database ID of the client
            
        Returns:
            Updated client information
            
        Raises:
            Various panel exceptions for connection issues
        """
        try:
            # Create a new DB session
            db = SessionLocal()
            
            try:
                # Get the client from the database
                client_db = db.query(ClientModel).filter(ClientModel.id == client_db_id).first()
                if not client_db:
                    raise PanelException(f"Client with ID {client_db_id} not found in database")
                    
                # Check if client exists on the panel
                try:
                    client_info = self.get_client(email=client_db.email)
                    
                    # Client exists, update its settings
                    self.update_client(
                        email=client_db.email,
                        total_gb=client_db.total_gb,
                        expire_days=None,  # Don't update expiry directly
                        limit_ip=client_db.limit_ip
                    )
                    
                    # Enable/disable based on client status
                    if client_db.status == "active":
                        self.enable_client(email=client_db.email)
                    elif client_db.status == "disabled":
                        self.disable_client(email=client_db.email)
                        
                    return client_info
                    
                except PanelClientNotFoundError:
                    # Client doesn't exist, create it
                    # Calculate expiry days from end_date
                    expire_days = 0
                    if client_db.end_date:
                        delta = client_db.end_date - datetime.now()
                        expire_days = max(0, delta.days)
                        
                    # Add the client to the panel
                    client_info = self.add_client(
                        email=client_db.email,
                        total_gb=client_db.total_gb,
                        expire_days=expire_days,
                        limit_ip=client_db.limit_ip,
                        client_uuid=client_db.uuid if hasattr(client_db, "uuid") else None
                    )
                    
                    return client_info
                    
            finally:
                # Always close the DB session
                db.close()
                
        except Exception as e:
            logger.exception(f"Error syncing client with panel: {e}")
            raise PanelException(f"Failed to sync client with panel: {str(e)}")

    def get_client_config(self, email: str, inbound_id: Optional[int] = None, protocol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration details for a client, including connection link.
        
        Args:
            email: Email/remark of the client
            inbound_id: Inbound ID (if None, searches all inbounds)
            protocol: Protocol type to filter by (vmess, vless, trojan, etc.)
            
        Returns:
            Dictionary with client configuration details
            
        Raises:
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            # Get client details first
            client = self.get_client(email=email, inbound_id=inbound_id)
            
            # Get inbound details
            inbound = self.get_inbound_detail(inbound_id=client['inbound_id'])
            
            # Check if protocol matches (if specified)
            if protocol and inbound.get('protocol', '').lower() != protocol.lower():
                raise PanelException(f"Client uses {inbound.get('protocol')} protocol, but {protocol} was requested")
            
            # Extract configuration details
            client_protocol = inbound.get('protocol', '').lower()
            port = inbound.get('port', 443)
            
            # Get panel info for domain/address
            panel_info = self._get_panel_info()
            server_address = panel_info.get('address', '')
            if not server_address:
                # Try to extract from base_url if address not explicitly set
                from urllib.parse import urlparse
                parsed_url = urlparse(panel_info.get('base_url', ''))
                server_address = parsed_url.netloc.split(':')[0]  # Extract domain only
            
            # Get stream settings
            stream_settings = inbound.get('stream_settings', {})
            network = stream_settings.get('network', 'tcp')
            security = stream_settings.get('security', 'none')
            
            # Prepare configuration object
            config = {
                'client_id': client.get('id'),
                'uuid': client.get('uuid'),
                'email': client.get('email'),
                'protocol': client_protocol,
                'port': port,
                'address': server_address,
                'network': network,
                'security': security,
                'enabled': client.get('enable', False),
                'inbound_id': client['inbound_id'],
                'created_at': client.get('created_at'),
                'expire_time': client.get('expiryTime'),
                'total_traffic': client.get('totalGB', 0),
                'used_traffic': client.get('up', 0) + client.get('down', 0)
            }
            
            # Generate connection link based on protocol
            if client_protocol == 'vmess':
                config['link'] = self._generate_vmess_link(
                    uuid=client.get('uuid'),
                    address=server_address,
                    port=port,
                    network=network,
                    security=security,
                    remark=client.get('email', 'MoonVPN')
                )
            elif client_protocol == 'vless':
                config['link'] = self._generate_vless_link(
                    uuid=client.get('uuid'),
                    address=server_address,
                    port=port,
                    network=network,
                    security=security,
                    remark=client.get('email', 'MoonVPN')
                )
            elif client_protocol == 'trojan':
                config['link'] = self._generate_trojan_link(
                    password=client.get('uuid'),
                    address=server_address,
                    port=port,
                    network=network,
                    security=security,
                    remark=client.get('email', 'MoonVPN')
                )
            else:
                config['link'] = ''
                logger.warning(f"Unknown protocol {client_protocol}, cannot generate link")
            
            return config
            
        except PanelClientNotFoundError:
            raise
        except PanelInboundNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get client config: {str(e)}")
            raise PanelException(f"Failed to get client config: {str(e)}")
    
    def get_client_qrcode(self, email: str, inbound_id: Optional[int] = None, protocol: Optional[str] = None) -> str:
        """
        Generate QR code for client configuration link.
        
        Args:
            email: Email/remark of the client
            inbound_id: Inbound ID (if None, searches all inbounds)
            protocol: Protocol type to filter by (vmess, vless, trojan, etc.)
            
        Returns:
            Base64 encoded PNG image of QR code
            
        Raises:
            PanelClientNotFoundError: If client is not found
            Other panel exceptions for connection issues
        """
        try:
            # Get client config to get the link
            config = self.get_client_config(email=email, inbound_id=inbound_id, protocol=protocol)
            link = config.get('link', '')
            
            if not link:
                raise PanelException("Cannot generate QR code: empty configuration link")
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(link)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        except PanelClientNotFoundError:
            raise
        except PanelInboundNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate QR code: {str(e)}")
            raise PanelException(f"Failed to generate QR code: {str(e)}")
    
    def _generate_vmess_link(self, uuid: str, address: str, port: int, 
                           network: str = 'tcp', security: str = 'none', 
                           remark: str = 'MoonVPN') -> str:
        """
        Generate a vmess:// link for V2Ray client.
        
        Args:
            uuid: Client UUID
            address: Server address
            port: Server port
            network: Network type (tcp, ws, etc.)
            security: Security type (none, tls, etc.)
            remark: Client remark/name
            
        Returns:
            vmess:// link
        """
        import json
        import base64
        
        config = {
            "v": "2",
            "ps": remark,
            "add": address,
            "port": str(port),
            "id": uuid,
            "aid": "0",
            "net": network,
            "type": "none",
            "host": "",
            "path": "",
            "tls": "tls" if security == "tls" else ""
        }
        
        config_str = json.dumps(config)
        b64_config = base64.b64encode(config_str.encode()).decode()
        return f"vmess://{b64_config}"
    
    def _generate_vless_link(self, uuid: str, address: str, port: int, 
                           network: str = 'tcp', security: str = 'none', 
                           remark: str = 'MoonVPN') -> str:
        """
        Generate a vless:// link for V2Ray client.
        
        Args:
            uuid: Client UUID
            address: Server address
            port: Server port
            network: Network type (tcp, ws, etc.)
            security: Security type (none, tls, etc.)
            remark: Client remark/name
            
        Returns:
            vless:// link
        """
        security_param = f"security={security}" if security != "none" else ""
        network_param = f"type={network}" if network != "tcp" else ""
        
        params = "&".join(filter(None, [security_param, network_param]))
        if params:
            params = f"?{params}"
        
        return f"vless://{uuid}@{address}:{port}{params}#{remark}"
    
    def _generate_trojan_link(self, password: str, address: str, port: int, 
                            network: str = 'tcp', security: str = 'tls', 
                            remark: str = 'MoonVPN') -> str:
        """
        Generate a trojan:// link for Trojan client.
        
        Args:
            password: Client password/UUID
            address: Server address
            port: Server port
            network: Network type (tcp, ws, etc.)
            security: Security type (usually tls)
            remark: Client remark/name
            
        Returns:
            trojan:// link
        """
        network_param = f"type={network}" if network != "tcp" else ""
        security_param = f"security={security}" if security != "tls" else ""
        
        params = "&".join(filter(None, [network_param, security_param]))
        if params:
            params = f"?{params}"
        
        return f"trojan://{password}@{address}:{port}{params}#{remark}" 