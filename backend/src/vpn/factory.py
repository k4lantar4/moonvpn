"""
Factory for creating VPN connectors
"""

from typing import Dict, Any, Type, Optional
from .base import BaseVPNConnector
from .exceptions import VPNNotSupportedError
import importlib
import logging

logger = logging.getLogger(__name__)

class VPNConnectorFactory:
    """Factory for creating appropriate connector based on server type"""
    
    # Registry of connector classes
    _connectors: Dict[str, Type[BaseVPNConnector]] = {}
    
    @classmethod
    def register(cls, server_type: str, connector_class: Type[BaseVPNConnector]) -> None:
        """Register a connector class for a server type
        
        Args:
            server_type: Server type identifier
            connector_class: Connector class to register
        """
        cls._connectors[server_type] = connector_class
    
    @classmethod
    def create_connector(cls, server: Any) -> BaseVPNConnector:
        """Create a connector for the given server
        
        Args:
            server: Server object
            
        Returns:
            BaseVPNConnector: An instantiated connector
            
        Raises:
            VPNNotSupportedError: If server type is not supported
        """
        server_type = server.type
        
        # Attempt to load the connector if not already registered
        if server_type not in cls._connectors:
            cls._load_connector(server_type)
            
        if server_type not in cls._connectors:
            raise VPNNotSupportedError(f"Unsupported server type: {server_type}")
            
        connector_class = cls._connectors[server_type]
        return connector_class(server)
    
    @classmethod
    def _load_connector(cls, server_type: str) -> None:
        """Attempt to dynamically load a connector module
        
        Args:
            server_type: Server type identifier
        """
        try:
            # Convert server_type to expected module path
            module_name = f"vpn.protocols.{server_type.lower()}.connector"
            module = importlib.import_module(module_name)
            
            # Look for a class that inherits from BaseVPNConnector
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseVPNConnector) and attr != BaseVPNConnector:
                    cls.register(server_type, attr)
                    logger.info(f"Dynamically loaded connector for {server_type}: {attr_name}")
                    return
                    
            logger.warning(f"No valid connector class found in module {module_name}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load connector for {server_type}: {str(e)}")
    
    @classmethod
    def list_supported_types(cls) -> list:
        """List all server types with registered connectors
        
        Returns:
            list: List of supported server types
        """
        return list(cls._connectors.keys())


# Register built-in connectors
def register_builtin_connectors():
    """Register built-in connector classes"""
    try:
        # Register the 3x-UI connector
        from vpn.protocols.threexui.connector import ThreeXUIConnector
        VPNConnectorFactory.register('3xui', ThreeXUIConnector)
    except ImportError:
        pass
        
    try:
        # Register OpenVPN connector if available
        from vpn.protocols.openvpn.connector import OpenVPNConnector
        VPNConnectorFactory.register('openvpn', OpenVPNConnector)
    except ImportError:
        pass
        
    try:
        # Register WireGuard connector if available
        from vpn.protocols.wireguard.connector import WireGuardConnector
        VPNConnectorFactory.register('wireguard', WireGuardConnector)
    except ImportError:
        pass

# Register builtin connectors when the module is imported
register_builtin_connectors() 