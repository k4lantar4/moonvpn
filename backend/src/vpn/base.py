"""
Base classes for VPN module
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

class BaseVPNConnector(ABC):
    """Base class for VPN panel connectors"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the VPN panel
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if the connector is authenticated
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        pass
    
    @abstractmethod
    def get_server_status(self) -> Dict[str, Any]:
        """Get the status of the VPN server
        
        Returns:
            Dict: Server status information
        """
        pass
    
    @abstractmethod
    def get_users(self) -> List[Dict[str, Any]]:
        """Get a list of all users on the server
        
        Returns:
            List[Dict]: List of user information dictionaries
        """
        pass
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific user
        
        Args:
            user_id: Identifier for the user
            
        Returns:
            Dict or None: User information if found, None otherwise
        """
        pass
    
    @abstractmethod
    def add_user(self, email: str, **kwargs) -> bool:
        """Add a new user to the server
        
        Args:
            email: User email/identifier
            **kwargs: Additional user parameters
            
        Returns:
            bool: True if user added successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_user(self, email: str) -> bool:
        """Remove a user from the server
        
        Args:
            email: User email/identifier
            
        Returns:
            bool: True if user removed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def update_user(self, email: str, **kwargs) -> bool:
        """Update a user's configuration
        
        Args:
            email: User email/identifier
            **kwargs: User parameters to update
            
        Returns:
            bool: True if user updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_user_traffic(self, email: str) -> Dict[str, int]:
        """Get traffic usage for a specific user
        
        Args:
            email: User email/identifier
            
        Returns:
            Dict: Traffic usage information
        """
        pass
    
    @abstractmethod
    def reset_user_traffic(self, email: str) -> bool:
        """Reset traffic counters for a user
        
        Args:
            email: User email/identifier
            
        Returns:
            bool: True if traffic reset successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_user_config(self, email: str, **kwargs) -> Dict[str, Any]:
        """Get user configuration for connecting to VPN
        
        Args:
            email: User email/identifier
            **kwargs: Additional parameters
            
        Returns:
            Dict: Configuration information
        """
        pass
    
    @abstractmethod
    def get_online_users(self) -> List[Dict[str, Any]]:
        """Get list of currently online users
        
        Returns:
            List[Dict]: List of online user information
        """
        pass


class BaseVPNManager(ABC):
    """Base class for VPN server management"""
    
    @abstractmethod
    def sync_server(self, server_id: int) -> bool:
        """Synchronize a specific server
        
        Args:
            server_id: ID of the server to sync
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        pass
    
    @abstractmethod
    def sync_all_servers(self) -> Dict[str, int]:
        """Synchronize all active servers
        
        Returns:
            Dict: Results with counts of success and failure
        """
        pass
    
    @abstractmethod
    def get_server_metrics(self, server_id: int) -> Dict[str, Any]:
        """Get performance metrics for a server
        
        Args:
            server_id: ID of the server
            
        Returns:
            Dict: Server metrics
        """
        pass
    
    @abstractmethod
    def add_user_to_server(self, user_id: int, server_id: int, **kwargs) -> bool:
        """Add a user to a server
        
        Args:
            user_id: ID of the user
            server_id: ID of the server
            **kwargs: Additional parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_user_from_server(self, user_id: int, server_id: int) -> bool:
        """Remove a user from a server
        
        Args:
            user_id: ID of the user
            server_id: ID of the server
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def move_user(self, user_id: int, from_server_id: int, to_server_id: int) -> bool:
        """Move a user from one server to another
        
        Args:
            user_id: ID of the user
            from_server_id: ID of the source server
            to_server_id: ID of the destination server
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_server_load(self) -> Dict[int, float]:
        """Get the load for all servers
        
        Returns:
            Dict: Server ID to load percentage mapping
        """
        pass
    
    @abstractmethod
    def get_best_server(self, **kwargs) -> Optional[int]:
        """Get the best server based on load and other factors
        
        Args:
            **kwargs: Filter parameters
            
        Returns:
            int or None: Best server ID or None if no suitable server
        """
        pass


class BaseVPNProtocol(ABC):
    """Base class for VPN protocols"""
    
    @abstractmethod
    def generate_config(self, server: Any, user: Any) -> str:
        """Generate configuration for client
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            str: Configuration string
        """
        pass
    
    @abstractmethod
    def generate_connection_links(self, server: Any, user: Any) -> Dict[str, str]:
        """Generate connection links
        
        Args:
            server: Server object
            user: User object
            
        Returns:
            Dict: Dictionary mapping link types to URLs
        """
        pass
    
    @abstractmethod
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get information about the protocol
        
        Returns:
            Dict: Protocol information
        """
        pass
    
    @abstractmethod
    def get_valid_server_types(self) -> List[str]:
        """Get list of valid server types for this protocol
        
        Returns:
            List[str]: List of valid server types
        """
        pass
    
    @abstractmethod
    def validate_server_config(self, config: Dict[str, Any]) -> bool:
        """Validate server configuration
        
        Args:
            config: Server configuration
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass


class VPNProtocolRegistry:
    """Registry of available VPN protocols"""
    
    _protocols = {}
    
    @classmethod
    def register(cls, protocol_id: str, protocol_class: type):
        """Register a protocol implementation
        
        Args:
            protocol_id: Unique identifier for the protocol
            protocol_class: The protocol implementation class
        """
        if not issubclass(protocol_class, BaseVPNProtocol):
            raise TypeError("Protocol class must extend BaseVPNProtocol")
        cls._protocols[protocol_id] = protocol_class
    
    @classmethod
    def get_protocol(cls, protocol_id: str) -> Optional[type]:
        """Get a protocol implementation by ID
        
        Args:
            protocol_id: Protocol ID
            
        Returns:
            Protocol class or None if not found
        """
        return cls._protocols.get(protocol_id)
    
    @classmethod
    def list_protocols(cls) -> List[str]:
        """List all registered protocols
        
        Returns:
            List[str]: List of protocol IDs
        """
        return list(cls._protocols.keys())
    
    @classmethod
    def create_protocol(cls, protocol_id: str, **kwargs) -> BaseVPNProtocol:
        """Create a protocol instance
        
        Args:
            protocol_id: Protocol ID
            **kwargs: Arguments for the protocol constructor
            
        Returns:
            BaseVPNProtocol: Protocol instance
            
        Raises:
            ValueError: If protocol not found
        """
        protocol_class = cls.get_protocol(protocol_id)
        if not protocol_class:
            raise ValueError(f"Protocol not found: {protocol_id}")
        return protocol_class(**kwargs) 