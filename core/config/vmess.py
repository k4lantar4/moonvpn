"""
VMess protocol implementation for 3x-UI
"""

import json
import base64
from typing import Dict, List, Any
from vpn.base import BaseVPNProtocol

class VMessProtocol(BaseVPNProtocol):
    """VMess protocol implementation for 3x-UI"""
    
    def __init__(self):
        """Initialize the VMess protocol"""
        self.protocol_id = "vmess"
        self.display_name = "VMess"
        self.description = "VMess protocol for V2Ray/Xray"
        self.icon = "mdi-vpn"
        
    def generate_config(self, server: Any, user: Any) -> str:
        """
        Generate VMess configuration for client
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            str: Configuration string in JSON format
        """
        server_address = server.host if ':' not in server.host else f"[{server.host}]"
        
        config = {
            "v": "2",
            "ps": f"{server.name}-{user.email}",
            "add": server_address,
            "port": user.port,
            "id": user.uuid,
            "aid": 0,
            "net": "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": "",
            "sni": ""
        }
        
        return json.dumps(config, indent=2)
    
    def generate_connection_links(self, server: Any, user: Any) -> Dict[str, str]:
        """
        Generate VMess connection links
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            Dict: Dictionary mapping link types to URLs
        """
        server_address = server.host if ':' not in server.host else f"[{server.host}]"
        
        config = {
            "v": "2",
            "ps": f"{server.name}-{user.email}",
            "add": server_address,
            "port": user.port,
            "id": user.uuid,
            "aid": 0,
            "net": "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": "",
            "sni": ""
        }
        
        # Base64 encode the config
        vmess_link = "vmess://" + base64.b64encode(json.dumps(config).encode()).decode()
        
        return {
            "vmess": vmess_link,
            "qrcode": vmess_link
        }
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """
        Get information about the protocol
        
        Returns:
            Dict: Protocol information
        """
        return {
            "id": self.protocol_id,
            "name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "supports_tls": True,
            "supports_ws": True,
            "supports_grpc": True,
            "supports_tcp": True,
            "supports_http": True,
            "client_apps": [
                {
                    "name": "V2rayNG",
                    "platform": "android",
                    "url": "https://play.google.com/store/apps/details?id=com.v2ray.ang"
                },
                {
                    "name": "Shadowrocket",
                    "platform": "ios",
                    "url": "https://apps.apple.com/us/app/shadowrocket/id932747118"
                },
                {
                    "name": "V2rayN",
                    "platform": "windows",
                    "url": "https://github.com/2dust/v2rayN/releases"
                },
                {
                    "name": "V2rayU",
                    "platform": "macos",
                    "url": "https://github.com/yanue/V2rayU/releases"
                }
            ]
        }
    
    def get_valid_server_types(self) -> List[str]:
        """
        Get list of valid server types for this protocol
        
        Returns:
            List[str]: List of valid server types
        """
        return ["3xui", "xray"]
    
    def validate_server_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate server configuration
        
        Args:
            config: Server configuration
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_fields = ["host", "port", "username", "password"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                return False
                
        return True 