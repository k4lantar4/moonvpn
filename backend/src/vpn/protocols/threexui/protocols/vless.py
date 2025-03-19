"""
VLESS protocol implementation for 3x-UI
"""

import json
from typing import Dict, List, Any
from vpn.base import BaseVPNProtocol

class VLESSProtocol(BaseVPNProtocol):
    """VLESS protocol implementation for 3x-UI"""
    
    def __init__(self):
        """Initialize the VLESS protocol"""
        self.protocol_id = "vless"
        self.display_name = "VLESS"
        self.description = "VLESS protocol for V2Ray/Xray"
        self.icon = "mdi-vpn"
        
    def generate_config(self, server: Any, user: Any) -> str:
        """
        Generate VLESS configuration for client
        
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
            "sni": "",
            "flow": ""
        }
        
        return json.dumps(config, indent=2)
    
    def generate_connection_links(self, server: Any, user: Any) -> Dict[str, str]:
        """
        Generate VLESS connection links
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            Dict: Dictionary mapping link types to URLs
        """
        server_address = server.host if ':' not in server.host else f"[{server.host}]"
        
        # vless://uuid@server:port?encryption=none&type=tcp#remark
        vless_link = f"vless://{user.uuid}@{server_address}:{user.port}?encryption=none&type=tcp#{server.name}-{user.email}"
        
        return {
            "vless": vless_link,
            "qrcode": vless_link
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
            "supports_xtls": True,
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