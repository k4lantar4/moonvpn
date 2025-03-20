"""
Trojan protocol implementation for 3x-UI
"""

import json
from typing import Dict, List, Any
from vpn.base import BaseVPNProtocol

class TrojanProtocol(BaseVPNProtocol):
    """Trojan protocol implementation for 3x-UI"""
    
    def __init__(self):
        """Initialize the Trojan protocol"""
        self.protocol_id = "trojan"
        self.display_name = "Trojan"
        self.description = "Trojan protocol for V2Ray/Xray"
        self.icon = "mdi-shield-vpn"
        
    def generate_config(self, server: Any, user: Any) -> str:
        """
        Generate Trojan configuration for client
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            str: Configuration string in JSON format
        """
        server_address = server.host if ':' not in server.host else f"[{server.host}]"
        
        config = {
            "run_type": "client",
            "local_addr": "127.0.0.1",
            "local_port": 1080,
            "remote_addr": server_address,
            "remote_port": user.port,
            "password": [user.uuid],
            "log_level": 1,
            "ssl": {
                "verify": True,
                "verify_hostname": True,
                "sni": server_address,
                "alpn": ["h2", "http/1.1"],
                "reuse_session": True,
                "session_ticket": False,
                "curves": ""
            },
            "tcp": {
                "no_delay": True,
                "keep_alive": True,
                "reuse_port": False,
                "fast_open": False,
                "fast_open_qlen": 20
            }
        }
        
        return json.dumps(config, indent=2)
    
    def generate_connection_links(self, server: Any, user: Any) -> Dict[str, str]:
        """
        Generate Trojan connection links
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            Dict: Dictionary mapping link types to URLs
        """
        server_address = server.host if ':' not in server.host else f"[{server.host}]"
        
        # trojan://password@server:port?sni=sni.com#remark
        trojan_link = f"trojan://{user.uuid}@{server_address}:{user.port}?sni={server_address}#{server.name}-{user.email}"
        
        return {
            "trojan": trojan_link,
            "qrcode": trojan_link
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
                    "name": "Trojan-Qt5",
                    "platform": "windows",
                    "url": "https://github.com/Trojan-Qt5/Trojan-Qt5/releases"
                },
                {
                    "name": "Trojan-Qt5",
                    "platform": "macos",
                    "url": "https://github.com/Trojan-Qt5/Trojan-Qt5/releases"
                }
            ]
        }
    
    def get_valid_server_types(self) -> List[str]:
        """
        Get list of valid server types for this protocol
        
        Returns:
            List[str]: List of valid server types
        """
        return ["3xui", "xray", "trojan-go"]
    
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