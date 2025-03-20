"""
MoonVPN Telegram Bot - VPN Account Model

This module provides the VPNAccount model for managing VPN account data and operations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete
import api_client

logger = logging.getLogger(__name__)

class VPNAccount:
    """VPN Account model for managing account data and operations."""
    
    def __init__(self, account_data: Dict[str, Any]):
        """
        Initialize a VPN account object.
        
        Args:
            account_data (Dict[str, Any]): Account data from database
        """
        self.id = account_data.get('id')
        self.user_id = account_data.get('user_id')
        self.server_id = account_data.get('server_id')
        self.package_id = account_data.get('package_id')
        self.uuid = account_data.get('uuid', str(uuid.uuid4()))
        self.email = account_data.get('email', f"{self.uuid}@moonvpn.ir")
        self.traffic_used = account_data.get('traffic_used', 0)
        self.traffic_limit = account_data.get('traffic_limit', 0)
        self.start_date = account_data.get('start_date')
        self.expiry_date = account_data.get('expiry_date')
        self.status = account_data.get('status', 'active')
        self.inbound_id = account_data.get('inbound_id')
        self.created_at = account_data.get('created_at')
        self.updated_at = account_data.get('updated_at')
        
        # Additional data that might be included in joins
        self.server_name = account_data.get('server_name')
        self.location = account_data.get('location')
        self.package_name = account_data.get('package_name')
        self.package_duration = account_data.get('duration_days')
    
    @staticmethod
    def get_by_id(account_id: int) -> Optional['VPNAccount']:
        """
        Get a VPN account by ID.
        
        Args:
            account_id (int): VPN account ID
            
        Returns:
            Optional[VPNAccount]: VPN account object or None if not found
        """
        # Try to get from cache first
        cached_account = cache_get(f"vpn_account:id:{account_id}")
        if cached_account:
            return VPNAccount(cached_account)
        
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.id = %s
        """
        result = execute_query(query, (account_id,), fetch="one")
        
        if result:
            # Cache account data
            cache_set(f"vpn_account:id:{account_id}", dict(result), 300)  # Cache for 5 minutes
            return VPNAccount(result)
            
        return None
        
    @staticmethod
    def get_by_uuid(uuid: str) -> Optional['VPNAccount']:
        """
        Get a VPN account by UUID.
        
        Args:
            uuid (str): VPN account UUID
            
        Returns:
            Optional[VPNAccount]: VPN account object or None if not found
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.uuid = %s
        """
        result = execute_query(query, (uuid,), fetch="one")
            
        if result:
            # Cache account data
            account_id = result.get('id')
            if account_id:
                cache_set(f"vpn_account:id:{account_id}", dict(result), 300)  # Cache for 5 minutes
            return VPNAccount(result)
            
            return None
        
    @staticmethod
    def get_by_email(email: str) -> Optional['VPNAccount']:
        """
        Get a VPN account by email.
        
        Args:
            email (str): VPN account email
            
        Returns:
            Optional[VPNAccount]: VPN account object or None if not found
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.email = %s
        """
        result = execute_query(query, (email,), fetch="one")
        
        if result:
            # Cache account data
            account_id = result.get('id')
            if account_id:
                cache_set(f"vpn_account:id:{account_id}", dict(result), 300)  # Cache for 5 minutes
            return VPNAccount(result)
            
            return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List['VPNAccount']:
        """
        Get all VPN accounts for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[VPNAccount]: List of VPN account objects
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.user_id = %s
            ORDER BY va.expiry_date DESC
        """
        results = execute_query(query, (user_id,))
        
        return [VPNAccount(result) for result in results]
        
    @staticmethod
    def get_active_by_user_id(user_id: int) -> List['VPNAccount']:
        """
        Get active VPN accounts for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[VPNAccount]: List of active VPN account objects
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.user_id = %s AND va.status = 'active'
            ORDER BY va.expiry_date DESC
        """
        results = execute_query(query, (user_id,))
        
        return [VPNAccount(result) for result in results]
        
    @staticmethod
    def get_expired_accounts() -> List['VPNAccount']:
        """
        Get all expired VPN accounts.
        
        Returns:
            List[VPNAccount]: List of expired VPN account objects
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.expiry_date < NOW() AND va.status = 'active'
        """
        results = execute_query(query)
        
        return [VPNAccount(result) for result in results]
        
    @staticmethod
    def get_accounts_expiring_soon(days: int = 3) -> List['VPNAccount']:
        """
        Get all VPN accounts expiring soon.
        
        Args:
            days (int): Number of days to look ahead
            
        Returns:
            List[VPNAccount]: List of VPN account objects expiring soon
        """
        # Get from database with server and package info
        query = """
            SELECT va.*, s.name as server_name, s.location, 
                   p.name as package_name, p.duration_days
            FROM vpn_accounts va
            JOIN servers s ON va.server_id = s.id
            JOIN vpn_packages p ON va.package_id = p.id
            WHERE va.expiry_date BETWEEN NOW() AND (NOW() + INTERVAL %s DAY)
            AND va.status = 'active'
        """
        results = execute_query(query, (days,))
        
        return [VPNAccount(result) for result in results]
        
    @staticmethod
    def create(user_id: int, server_id: int, package_id: int, 
              uuid: str = None, email: str = None, traffic_limit: int = None,
              duration_days: int = None) -> Optional['VPNAccount']:
        """
        Create a new VPN account.
        
        Args:
            user_id (int): User ID
            server_id (int): Server ID
            package_id (int): Package ID
            uuid (str, optional): UUID for the account (generated if not provided)
            email (str, optional): Email for the account (generated if not provided)
            traffic_limit (int, optional): Traffic limit in bytes (from package if not provided)
            duration_days (int, optional): Duration in days (from package if not provided)
            
        Returns:
            Optional[VPNAccount]: VPN account object or None if creation failed
        """
        # Generate UUID and email if not provided
        if not uuid:
            uuid = str(uuid.uuid4())
        
        if not email:
            email = f"{uuid}@moonvpn.ir"
        
        # Get package info if needed
        if not traffic_limit or not duration_days:
            from models.subscription_plan import SubscriptionPlan
            package = SubscriptionPlan.get_by_id(package_id)
            
            if package:
                if not traffic_limit:
                    # Convert GB to bytes
                    traffic_limit = int(package.traffic_gb * 1024 * 1024 * 1024)
                
                if not duration_days:
                    duration_days = package.duration_days
            else:
                logger.error(f"Package with ID {package_id} not found")
                return None
        
        # Calculate expiry date
        start_date = datetime.now()
        expiry_date = start_date + timedelta(days=duration_days)
        
        # Insert into database
        query = """
            INSERT INTO vpn_accounts (
                user_id, server_id, package_id, uuid, email,
                traffic_limit, start_date, expiry_date, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, 'active'
            )
        """
        
        account_id = execute_insert(query, (
            user_id, server_id, package_id, uuid, email,
            traffic_limit, start_date, expiry_date
        ))
        
        if account_id:
            # Create account on the VPN server
            try:
                # Get the server info
                from models.server import Server
                server = Server.get_by_id(server_id)
                
                if server:
                    # Create client on the server
                    success = api_client.add_client(
                        server.inbound_id,
                        {
                            "id": uuid,
                            "email": email,
                            "flow": "",
                            "limitIp": 0,
                            "totalGB": traffic_limit,
                            "expiryTime": int(expiry_date.timestamp() * 1000),
                            "enable": True,
                            "tgId": ""
                        }
                    )
                    
                    if not success:
                        logger.error(f"Failed to create client on the server for account {account_id}")
                        
                        # Update account status
                        execute_update(
                            "UPDATE vpn_accounts SET status = 'error' WHERE id = %s",
                            (account_id,)
                        )
                        return None
                else:
                    logger.error(f"Server with ID {server_id} not found")
                    return None
            except Exception as e:
                logger.error(f"Error creating account on VPN server: {e}")
                
                # Update account status
                execute_update(
                    "UPDATE vpn_accounts SET status = 'error' WHERE id = %s",
                    (account_id,)
                )
                return None
            
            # Return the created account
            return VPNAccount.get_by_id(account_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save VPN account changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
    
        query = """
            UPDATE vpn_accounts SET
                server_id = %s,
                package_id = %s,
                uuid = %s,
                email = %s,
                traffic_used = %s,
                traffic_limit = %s,
                start_date = %s,
                expiry_date = %s,
                status = %s,
                inbound_id = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.server_id,
            self.package_id,
            self.uuid,
            self.email,
            self.traffic_used,
            self.traffic_limit,
            self.start_date,
            self.expiry_date,
            self.status,
            self.inbound_id,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"vpn_account:id:{self.id}")
            
        return success
        
    def update(self) -> bool:
        """
        Update VPN account in database and on VPN server.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Save to database first
        if not self.save():
            return False
            
        # Update on VPN server
        try:
            # Get the server info
            from models.server import Server
            server = Server.get_by_id(self.server_id)
            
            if server and server.inbound_id:
                # Update client on the server
                success = api_client.update_client(
                    server.inbound_id,
                    self.email,
                    {
                        "id": self.uuid,
                        "email": self.email,
                        "flow": "",
                        "limitIp": 0,
                        "totalGB": self.traffic_limit,
                        "expiryTime": int(datetime.timestamp(self.expiry_date) * 1000) if self.expiry_date else 0,
                        "enable": self.status == 'active',
                        "tgId": ""
                    }
                )
                
                if not success:
                    logger.error(f"Failed to update client on the server for account {self.id}")
                    return False
            else:
                logger.error(f"Server with ID {self.server_id} not found or has no inbound ID")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error updating account on VPN server: {e}")
            return False
    
    def delete(self) -> bool:
        """
        Delete VPN account from database and VPN server.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Delete from VPN server first
        try:
            # Get the server info
            from models.server import Server
            server = Server.get_by_id(self.server_id)
            
            if server and server.inbound_id:
                # Delete client from the server
                success = api_client.delete_client(server.inbound_id, self.email)
                
                if not success:
                    logger.error(f"Failed to delete client from the server for account {self.id}")
                    return False
            else:
                logger.error(f"Server with ID {self.server_id} not found or has no inbound ID")
                return False
        except Exception as e:
            logger.error(f"Error deleting account from VPN server: {e}")
            return False
    
        # Delete from database
        query = "DELETE FROM vpn_accounts WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear cache
            cache_delete(f"vpn_account:id:{self.id}")
            
        return success
        
    def renew(self, duration_days: int = None) -> bool:
        """
        Renew VPN account.
        
        Args:
            duration_days (int, optional): Duration in days (from package if not provided)
            
        Returns:
            bool: True if renewal was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Get package info if needed
        if not duration_days:
            from models.subscription_plan import SubscriptionPlan
            package = SubscriptionPlan.get_by_id(self.package_id)
            
            if package:
                duration_days = package.duration_days
            else:
                logger.error(f"Package with ID {self.package_id} not found")
                return False
        
        # Calculate new expiry date
        current_time = datetime.now()
        
        # If account is expired, start from now
        if self.expiry_date and self.expiry_date > current_time:
            self.expiry_date = self.expiry_date + timedelta(days=duration_days)
        else:
            self.expiry_date = current_time + timedelta(days=duration_days)
        
        # Update status
        self.status = 'active'
        
        # Save changes
        return self.update()
        
    def reset_traffic(self) -> bool:
        """
        Reset traffic usage.
        
        Returns:
            bool: True if reset was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Reset traffic on VPN server
        try:
            # Get the server info
            from models.server import Server
            server = Server.get_by_id(self.server_id)
            
            if server and server.inbound_id:
                # Reset traffic on the server
                success = api_client.reset_client_traffic(server.inbound_id, self.email)
                
                if not success:
                    logger.error(f"Failed to reset traffic on the server for account {self.id}")
                    return False
            else:
                logger.error(f"Server with ID {self.server_id} not found or has no inbound ID")
                return False
        except Exception as e:
            logger.error(f"Error resetting traffic on VPN server: {e}")
            return False
            
        # Reset traffic in database
        self.traffic_used = 0
        
        # Save changes
        return self.save()
        
    def suspend(self) -> bool:
        """
        Suspend VPN account.
        
        Returns:
            bool: True if suspension was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Update status
        self.status = 'suspended'
        
        # Save changes
        return self.update()
        
    def activate(self) -> bool:
        """
        Activate VPN account.
        
        Returns:
            bool: True if activation was successful, False otherwise
        """
        if not self.id:
                    return False
            
        # Update status
        self.status = 'active'
        
        # Save changes
        return self.update()
        
    def change_server(self, new_server_id: int) -> bool:
        """
        Change server for VPN account.
        
        Args:
            new_server_id (int): New server ID
            
        Returns:
            bool: True if server change was successful, False otherwise
        """
        if not self.id or self.server_id == new_server_id:
            return False
    
        # Delete from old server
        try:
            # Get the old server info
            from models.server import Server
            old_server = Server.get_by_id(self.server_id)
            
            if old_server and old_server.inbound_id:
                # Delete client from the old server
                success = api_client.delete_client(old_server.inbound_id, self.email)
                
                if not success:
                    logger.error(f"Failed to delete client from the old server for account {self.id}")
                    return False
            else:
                logger.error(f"Old server with ID {self.server_id} not found or has no inbound ID")
                return False
        except Exception as e:
            logger.error(f"Error deleting account from old server: {e}")
            return False
    
        # Get old server ID for rollback
        old_server_id = self.server_id
        
        # Update server ID
        self.server_id = new_server_id
        
        # Create on new server
        try:
            # Get the new server info
            from models.server import Server
            new_server = Server.get_by_id(new_server_id)
            
            if new_server and new_server.inbound_id:
                # Create client on the new server
                success = api_client.add_client(
                    new_server.inbound_id,
                    {
                        "id": self.uuid,
                        "email": self.email,
                        "flow": "",
                        "limitIp": 0,
                        "totalGB": self.traffic_limit,
                        "expiryTime": int(datetime.timestamp(self.expiry_date) * 1000) if self.expiry_date else 0,
                        "enable": self.status == 'active',
                        "tgId": ""
                    }
                )
                
                if not success:
                    logger.error(f"Failed to create client on the new server for account {self.id}")
                    
                    # Rollback server ID
                    self.server_id = old_server_id
                    return False
            else:
                logger.error(f"New server with ID {new_server_id} not found or has no inbound ID")
                
                # Rollback server ID
                self.server_id = old_server_id
                return False
        except Exception as e:
            logger.error(f"Error creating account on new server: {e}")
            
            # Rollback server ID
            self.server_id = old_server_id
            return False
            
        # Save changes
        return self.save()
        
    def get_server(self) -> Optional[Any]:
        """
        Get the server for this account.
        
        Returns:
            Optional[Server]: Server object or None if not found
        """
        if not self.server_id:
            return None
            
        from models.server import Server
        return Server.get_by_id(self.server_id)
        
    def get_package(self) -> Optional[Any]:
        """
        Get the package for this account.
        
        Returns:
            Optional[SubscriptionPlan]: Package object or None if not found
        """
        if not self.package_id:
            return None
            
        from models.subscription_plan import SubscriptionPlan
        return SubscriptionPlan.get_by_id(self.package_id)
        
    def get_user(self) -> Optional[Any]:
        """
        Get the user for this account.
        
        Returns:
            Optional[User]: User object or None if not found
        """
        if not self.user_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.user_id)
        
    def get_traffic_usage(self) -> Tuple[int, int]:
        """
        Get traffic usage from VPN server.
        
        Returns:
            Tuple[int, int]: (used traffic, total traffic) in bytes
        """
        try:
            # Get the server info
            from models.server import Server
            server = Server.get_by_id(self.server_id)
            
            if server and server.inbound_id:
                # Get client traffic from the server
                traffic = api_client.get_client_traffic(server.inbound_id, self.email)
                
                if traffic:
                    # Update traffic usage in database
                    self.traffic_used = traffic.get('up', 0) + traffic.get('down', 0)
                    self.save()
                    
                    return (self.traffic_used, self.traffic_limit)
            
            # Fallback to database values
            return (self.traffic_used, self.traffic_limit)
        except Exception as e:
            logger.error(f"Error getting traffic usage from VPN server: {e}")
            
            # Fallback to database values
            return (self.traffic_used, self.traffic_limit)
            
    def get_config(self, protocol: str = None) -> Dict[str, Any]:
        """
        Get VPN configuration.
        
        Args:
            protocol (str, optional): Protocol to use (vmess, vless, etc.)
            
        Returns:
            Dict[str, Any]: Configuration details
        """
        try:
            # Get account configuration from API
            config = api_client.get_account_config(self.id, protocol)
            
            if config and config.get('status') != 'error':
                return config
                
            # Fallback to generating config manually
            from models.server import Server
            server = Server.get_by_id(self.server_id)
            
            if not server:
                return {"status": "error", "message": "Server not found"}
                
            # Generate config based on protocol
            config = {
                "status": "success",
                "id": self.uuid,
                "host": server.host,
                "port": server.port,
                "protocol": protocol or server.protocol or "vmess",
                "ps": f"MoonVPN - {server.name or server.location}"
            }
            
            return config
        except Exception as e:
            logger.error(f"Error getting VPN configuration: {e}")
            return {"status": "error", "message": str(e)}
            
    def get_qrcode(self, protocol: str = None) -> str:
        """
        Get QR code for VPN configuration.
        
        Args:
            protocol (str, optional): Protocol to use (vmess, vless, etc.)
            
        Returns:
            str: QR code data URI
        """
        try:
            # Get account QR code from API
            config = self.get_config(protocol)
            
            if config and config.get('status') == 'success':
                # Generate QR code
                qrcode = api_client.generate_qrcode(config.get('config_link', ''))
                return qrcode
                
            return ""
        except Exception as e:
            logger.error(f"Error getting QR code: {e}")
            return ""
            
    def days_left(self) -> int:
        """
        Get days left until expiry.
        
        Returns:
            int: Number of days left
        """
        if not self.expiry_date:
            return 0
            
        now = datetime.now()
        
        if self.expiry_date < now:
            return 0
            
        delta = self.expiry_date - now
        return delta.days
        
    def hours_left(self) -> int:
        """
        Get hours left until expiry.
        
        Returns:
            int: Number of hours left
        """
        if not self.expiry_date:
            return 0
            
        now = datetime.now()
        
        if self.expiry_date < now:
            return 0
            
        delta = self.expiry_date - now
        return int(delta.total_seconds() / 3600)
        
    def is_expired(self) -> bool:
        """
        Check if account is expired.
        
        Returns:
            bool: True if account is expired, False otherwise
        """
        if not self.expiry_date:
            return True
            
        return self.expiry_date < datetime.now()
        
    def is_active(self) -> bool:
        """
        Check if account is active.
        
        Returns:
            bool: True if account is active, False otherwise
        """
        return self.status == 'active' and not self.is_expired()
        
    @staticmethod
    def check_expired_accounts() -> int:
        """
        Check and update status of expired accounts.
        
        Returns:
            int: Number of accounts updated
        """
        # Get expired accounts
        query = """
            UPDATE vpn_accounts
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE expiry_date < NOW() AND status = 'active'
            RETURNING id
        """
        
        results = execute_query(query)
        
        # Clear cache for updated accounts
        for result in results:
            account_id = result.get('id')
            if account_id:
                cache_delete(f"vpn_account:id:{account_id}")
                
        return len(results)
        
    @staticmethod
    def count_active_accounts() -> int:
        """
        Count active accounts.
        
        Returns:
            int: Number of active accounts
        """
        query = """
            SELECT COUNT(*) as count
            FROM vpn_accounts
            WHERE status = 'active'
        """
        
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def count_expired_accounts() -> int:
        """
        Count expired accounts.
        
        Returns:
            int: Number of expired accounts
        """
        query = """
            SELECT COUNT(*) as count
            FROM vpn_accounts
            WHERE status = 'expired'
        """
        
        result = execute_query(query, fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def count_accounts_by_server(server_id: int) -> int:
        """
        Count accounts on a server.
        
        Args:
            server_id (int): Server ID
            
        Returns:
            int: Number of accounts on the server
        """
        query = """
            SELECT COUNT(*) as count
            FROM vpn_accounts
            WHERE server_id = %s AND status = 'active'
        """
        
        result = execute_query(query, (server_id,), fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def get_account_stats() -> Dict[str, Any]:
        """
        Get account statistics.
        
        Returns:
            Dict[str, Any]: Account statistics
        """
        stats = {
            "total": 0,
            "active": 0,
            "expired": 0,
            "suspended": 0,
            "expiring_today": 0,
            "expiring_week": 0,
            "created_today": 0,
            "created_week": 0
        }
        
        # Get counts
        queries = {
            "total": "SELECT COUNT(*) as count FROM vpn_accounts",
            "active": "SELECT COUNT(*) as count FROM vpn_accounts WHERE status = 'active'",
            "expired": "SELECT COUNT(*) as count FROM vpn_accounts WHERE status = 'expired'",
            "suspended": "SELECT COUNT(*) as count FROM vpn_accounts WHERE status = 'suspended'",
            "expiring_today": """
                SELECT COUNT(*) as count FROM vpn_accounts 
                WHERE expiry_date BETWEEN NOW() AND (NOW() + INTERVAL '1 day')
                AND status = 'active'
            """,
            "expiring_week": """
                SELECT COUNT(*) as count FROM vpn_accounts 
                WHERE expiry_date BETWEEN NOW() AND (NOW() + INTERVAL '7 day')
                AND status = 'active'
            """,
            "created_today": """
                SELECT COUNT(*) as count FROM vpn_accounts 
                WHERE created_at >= (NOW() - INTERVAL '1 day')
            """,
            "created_week": """
                SELECT COUNT(*) as count FROM vpn_accounts 
                WHERE created_at >= (NOW() - INTERVAL '7 day')
            """
        }
        
        for key, query in queries.items():
            result = execute_query(query, fetch="one")
            stats[key] = result.get('count', 0) if result else 0
            
        return stats
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert VPN account to dictionary.
        
        Returns:
            Dict[str, Any]: VPN account data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'server_id': self.server_id,
            'package_id': self.package_id,
            'uuid': self.uuid,
            'email': self.email,
            'traffic_used': self.traffic_used,
            'traffic_limit': self.traffic_limit,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'inbound_id': self.inbound_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'server_name': self.server_name,
            'location': self.location,
            'package_name': self.package_name,
            'days_left': self.days_left(),
            'is_expired': self.is_expired(),
            'is_active': self.is_active()
        } 