"""
VPN Manager implementation
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from vpn.base import BaseVPNManager
from vpn.factory import VPNConnectorFactory
from vpn.exceptions import VPNError, VPNConnectionError, VPNSyncError

logger = logging.getLogger(__name__)

class VPNManager(BaseVPNManager):
    """
    VPN Manager for synchronizing and managing VPN servers and users
    """
    
    def __init__(self, server_model=None, vpn_account_model=None):
        """
        Initialize the VPN Manager
        
        Args:
            server_model: Server model class (optional, will be imported if not provided)
            vpn_account_model: VPN Account model class (optional, will be imported if not provided)
        """
        self.logger = logging.getLogger('vpn.manager')
        
        # Import models if not provided
        if server_model is None:
            from vpn.models import Server
            self.server_model = Server
        else:
            self.server_model = server_model
            
        if vpn_account_model is None:
            from vpn.models import VPNAccount
            self.vpn_account_model = VPNAccount
        else:
            self.vpn_account_model = vpn_account_model
    
    def sync_server(self, server_id: int) -> bool:
        """
        Synchronize a specific server
        
        Args:
            server_id: ID of the server to sync
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            server = self.server_model.objects.get(id=server_id, is_active=True)
        except self.server_model.DoesNotExist:
            self.logger.error(f"Server with ID {server_id} not found or not active")
            return False
            
        try:
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(server)
            
            # Authenticate with the server
            if not connector.authenticate():
                self.logger.error(f"Failed to authenticate with server {server.name}")
                return False
                
            # Get server status and update in database
            status = connector.get_server_status()
            if status:
                server.cpu_usage = status.get('cpu', 0)
                server.memory_usage = status.get('mem', 0)
                server.disk_usage = status.get('disk', 0)
                server.status = 'online' if status.get('xray_state') == 'running' else 'error'
                server.last_sync = timezone.now()
                server.save(update_fields=['cpu_usage', 'memory_usage', 'disk_usage', 'status', 'last_sync'])
                
            # Get all users from the server
            server_users = connector.get_users()
            if server_users is None:
                self.logger.error(f"Failed to get users from server {server.name}")
                return False
                
            # Get all VPN accounts for this server from database
            db_accounts = self.vpn_account_model.objects.filter(server=server)
            
            # Create a mapping of email to account for easier lookup
            db_accounts_map = {account.email: account for account in db_accounts}
            
            # Track which accounts were found on the server
            found_emails = set()
            
            # Update existing accounts and create new ones
            with transaction.atomic():
                for user in server_users:
                    email = user.get('email')
                    if not email:
                        continue
                        
                    found_emails.add(email)
                    
                    # Check if account exists in database
                    if email in db_accounts_map:
                        # Update existing account
                        account = db_accounts_map[email]
                        account.upload = user.get('up', 0)
                        account.download = user.get('down', 0)
                        account.total_traffic = user.get('up', 0) + user.get('down', 0)
                        
                        # Update expiry time if provided
                        expiry_time = user.get('expiry_time')
                        if expiry_time:
                            # Convert from milliseconds timestamp to datetime
                            account.expiry_date = datetime.fromtimestamp(expiry_time / 1000)
                            
                        account.is_active = user.get('enable', True)
                        account.last_sync = timezone.now()
                        account.save(update_fields=[
                            'upload', 'download', 'total_traffic', 
                            'expiry_date', 'is_active', 'last_sync'
                        ])
                    else:
                        # Create new account in database
                        expiry_date = None
                        expiry_time = user.get('expiry_time')
                        if expiry_time:
                            expiry_date = datetime.fromtimestamp(expiry_time / 1000)
                            
                        # Create a new account
                        # Note: This will create an orphaned account if no user is associated
                        # In a real implementation, you might want to handle this differently
                        self.vpn_account_model.objects.create(
                            server=server,
                            email=email,
                            protocol=user.get('protocol', ''),
                            upload=user.get('up', 0),
                            download=user.get('down', 0),
                            total_traffic=user.get('up', 0) + user.get('down', 0),
                            expiry_date=expiry_date,
                            is_active=user.get('enable', True),
                            last_sync=timezone.now()
                        )
                        
                # Mark accounts that no longer exist on the server as inactive
                for email, account in db_accounts_map.items():
                    if email not in found_emails and account.is_active:
                        account.is_active = False
                        account.last_sync = timezone.now()
                        account.save(update_fields=['is_active', 'last_sync'])
                        
            self.logger.info(f"Successfully synchronized server {server.name}")
            return True
            
        except VPNError as e:
            self.logger.error(f"VPN error during sync of server {server_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.exception(f"Error during sync of server {server_id}: {str(e)}")
            return False
    
    def sync_all_servers(self) -> Dict[str, int]:
        """
        Synchronize all active servers
        
        Returns:
            Dict: Results with counts of success and failure
        """
        results = {
            'total': 0,
            'success': 0,
            'failed': 0
        }
        
        # Get all active servers
        servers = self.server_model.objects.filter(is_active=True)
        results['total'] = servers.count()
        
        for server in servers:
            try:
                if self.sync_server(server.id):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                self.logger.exception(f"Error syncing server {server.id}: {str(e)}")
                results['failed'] += 1
                
        return results
    
    def get_server_metrics(self, server_id: int) -> Dict[str, Any]:
        """
        Get performance metrics for a server
        
        Args:
            server_id: ID of the server
            
        Returns:
            Dict: Server metrics
        """
        try:
            server = self.server_model.objects.get(id=server_id, is_active=True)
        except self.server_model.DoesNotExist:
            return {'error': 'Server not found or not active'}
            
        try:
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(server)
            
            # Authenticate with the server
            if not connector.authenticate():
                return {'error': 'Failed to authenticate with server'}
                
            # Get server status
            status = connector.get_server_status()
            if not status:
                return {'error': 'Failed to get server status'}
                
            # Get online users
            online_users = connector.get_online_users()
            
            # Prepare metrics
            metrics = {
                'cpu': status.get('cpu', 0),
                'memory': status.get('mem', 0),
                'disk': status.get('disk', 0),
                'xray_state': status.get('xray_state', 'unknown'),
                'xray_version': status.get('xray_version', 'unknown'),
                'online_users_count': len(online_users) if online_users else 0,
                'online_users': online_users if online_users else [],
                'timestamp': timezone.now().isoformat()
            }
            
            return metrics
            
        except VPNError as e:
            return {'error': f"VPN error: {str(e)}"}
        except Exception as e:
            return {'error': f"Error: {str(e)}"}
    
    def add_user_to_server(self, user_id: int, server_id: int, **kwargs) -> bool:
        """
        Add a user to a server
        
        Args:
            user_id: ID of the user
            server_id: ID of the server
            **kwargs: Additional parameters
                email: Email for the VPN account (default: user's email or generated)
                traffic_limit_gb: Traffic limit in GB (default: from plan or 0)
                expire_days: Number of days until expiration (default: from plan or 30)
                protocol: VPN protocol to use (default: server's default protocol)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import User model here to avoid circular imports
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user and server
            try:
                user = User.objects.get(id=user_id)
                server = self.server_model.objects.get(id=server_id, is_active=True)
            except User.DoesNotExist:
                self.logger.error(f"User with ID {user_id} not found")
                return False
            except self.server_model.DoesNotExist:
                self.logger.error(f"Server with ID {server_id} not found or not active")
                return False
                
            # Get or create email for VPN account
            email = kwargs.get('email')
            if not email:
                # Use user's email or username if available
                email = getattr(user, 'email', None) or getattr(user, 'username', None)
                if not email:
                    # Generate a unique email based on user ID and timestamp
                    email = f"user{user_id}_{int(time.time())}@moonvpn.local"
            
            # Check if account already exists
            existing_account = self.vpn_account_model.objects.filter(
                user=user,
                server=server,
                is_active=True
            ).first()
            
            if existing_account:
                self.logger.warning(f"User {user_id} already has an active account on server {server_id}")
                return True
                
            # Get traffic limit and expiry from kwargs or user's plan
            traffic_limit_gb = kwargs.get('traffic_limit_gb', 0)
            expire_days = kwargs.get('expire_days', 30)
            
            # Get protocol from kwargs or server default
            protocol = kwargs.get('protocol', server.default_protocol)
            
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(server)
            
            # Authenticate with the server
            if not connector.authenticate():
                self.logger.error(f"Failed to authenticate with server {server.name}")
                return False
                
            # Add user to the server
            success = connector.add_user(
                email,
                traffic_limit_gb=traffic_limit_gb,
                expire_days=expire_days
            )
            
            if not success:
                self.logger.error(f"Failed to add user {user_id} to server {server_id}")
                return False
                
            # Get user details from server to get UUID and other info
            user_info = connector.get_user(email)
            if not user_info:
                self.logger.error(f"Failed to get user info for {email} from server {server_id}")
                return False
                
            # Calculate expiry date
            expiry_date = timezone.now() + timedelta(days=expire_days)
            
            # Create VPN account in database
            with transaction.atomic():
                account = self.vpn_account_model.objects.create(
                    user=user,
                    server=server,
                    email=email,
                    protocol=protocol,
                    uuid=user_info.get('uuid', ''),
                    upload=0,
                    download=0,
                    total_traffic=0,
                    traffic_limit=traffic_limit_gb * 1024 * 1024 * 1024 if traffic_limit_gb > 0 else 0,
                    expiry_date=expiry_date,
                    is_active=True,
                    last_sync=timezone.now()
                )
                
            self.logger.info(f"Successfully added user {user_id} to server {server_id}")
            return True
            
        except VPNError as e:
            self.logger.error(f"VPN error adding user {user_id} to server {server_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.exception(f"Error adding user {user_id} to server {server_id}: {str(e)}")
            return False
    
    def remove_user_from_server(self, user_id: int, server_id: int) -> bool:
        """
        Remove a user from a server
        
        Args:
            user_id: ID of the user
            server_id: ID of the server
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import User model here to avoid circular imports
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user and server
            try:
                user = User.objects.get(id=user_id)
                server = self.server_model.objects.get(id=server_id)
            except User.DoesNotExist:
                self.logger.error(f"User with ID {user_id} not found")
                return False
            except self.server_model.DoesNotExist:
                self.logger.error(f"Server with ID {server_id} not found")
                return False
                
            # Get active account for this user on this server
            try:
                account = self.vpn_account_model.objects.get(
                    user=user,
                    server=server,
                    is_active=True
                )
            except self.vpn_account_model.DoesNotExist:
                self.logger.warning(f"No active account found for user {user_id} on server {server_id}")
                return True
                
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(server)
            
            # Authenticate with the server
            if not connector.authenticate():
                self.logger.error(f"Failed to authenticate with server {server.name}")
                return False
                
            # Remove user from the server
            success = connector.remove_user(account.email)
            
            # Mark account as inactive in database regardless of server operation result
            # This ensures database consistency even if server operation fails
            with transaction.atomic():
                account.is_active = False
                account.last_sync = timezone.now()
                account.save(update_fields=['is_active', 'last_sync'])
                
            if not success:
                self.logger.warning(f"Failed to remove user {account.email} from server {server_id}, but marked inactive in database")
                
            self.logger.info(f"Successfully removed user {user_id} from server {server_id}")
            return True
            
        except VPNError as e:
            self.logger.error(f"VPN error removing user {user_id} from server {server_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.exception(f"Error removing user {user_id} from server {server_id}: {str(e)}")
            return False
    
    def move_user(self, user_id: int, from_server_id: int, to_server_id: int) -> bool:
        """
        Move a user from one server to another
        
        Args:
            user_id: ID of the user
            from_server_id: ID of the source server
            to_server_id: ID of the destination server
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Import User model here to avoid circular imports
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user and servers
            try:
                user = User.objects.get(id=user_id)
                from_server = self.server_model.objects.get(id=from_server_id)
                to_server = self.server_model.objects.get(id=to_server_id, is_active=True)
            except User.DoesNotExist:
                self.logger.error(f"User with ID {user_id} not found")
                return False
            except self.server_model.DoesNotExist as e:
                self.logger.error(f"Server not found: {str(e)}")
                return False
                
            # Get active account for this user on source server
            try:
                from_account = self.vpn_account_model.objects.get(
                    user=user,
                    server=from_server,
                    is_active=True
                )
            except self.vpn_account_model.DoesNotExist:
                self.logger.error(f"No active account found for user {user_id} on server {from_server_id}")
                return False
                
            # Check if user already has an account on destination server
            existing_account = self.vpn_account_model.objects.filter(
                user=user,
                server=to_server,
                is_active=True
            ).first()
            
            if existing_account:
                self.logger.warning(f"User {user_id} already has an active account on server {to_server_id}")
                # Remove from source server only
                return self.remove_user_from_server(user_id, from_server_id)
                
            # Calculate remaining traffic and days
            remaining_traffic_gb = 0
            if from_account.traffic_limit > 0:
                used_traffic = from_account.upload + from_account.download
                remaining_traffic = max(0, from_account.traffic_limit - used_traffic)
                remaining_traffic_gb = remaining_traffic / (1024 * 1024 * 1024)
                
            remaining_days = 30  # Default
            if from_account.expiry_date:
                remaining_days = max(1, (from_account.expiry_date - timezone.now()).days)
                
            # Add user to destination server
            success = self.add_user_to_server(
                user_id,
                to_server_id,
                email=from_account.email,
                traffic_limit_gb=remaining_traffic_gb,
                expire_days=remaining_days,
                protocol=from_account.protocol
            )
            
            if not success:
                self.logger.error(f"Failed to add user {user_id} to server {to_server_id}")
                return False
                
            # Remove user from source server
            success = self.remove_user_from_server(user_id, from_server_id)
            
            if not success:
                self.logger.warning(f"Failed to remove user {user_id} from server {from_server_id}")
                # Continue anyway since user was added to destination server
                
            self.logger.info(f"Successfully moved user {user_id} from server {from_server_id} to {to_server_id}")
            return True
            
        except VPNError as e:
            self.logger.error(f"VPN error moving user {user_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.exception(f"Error moving user {user_id}: {str(e)}")
            return False
    
    def get_server_load(self) -> Dict[int, float]:
        """
        Get the load for all servers
        
        Returns:
            Dict: Server ID to load percentage mapping
        """
        result = {}
        
        # Get all active servers
        servers = self.server_model.objects.filter(is_active=True)
        
        for server in servers:
            try:
                # Calculate load based on CPU, memory, and active users
                # This is a simplified formula - you might want to adjust based on your needs
                cpu_weight = 0.4
                memory_weight = 0.3
                users_weight = 0.3
                
                # Get active users count
                active_users_count = self.vpn_account_model.objects.filter(
                    server=server,
                    is_active=True
                ).count()
                
                # Normalize users count (assuming max 100 users per server)
                normalized_users = min(1.0, active_users_count / 100)
                
                # Calculate load
                load = (
                    cpu_weight * (server.cpu_usage / 100) +
                    memory_weight * (server.memory_usage / 100) +
                    users_weight * normalized_users
                )
                
                result[server.id] = round(load * 100, 2)  # Convert to percentage
                
            except Exception as e:
                self.logger.error(f"Error calculating load for server {server.id}: {str(e)}")
                result[server.id] = 100.0  # Assume full load on error
                
        return result
    
    def get_best_server(self, **kwargs) -> Optional[int]:
        """
        Get the best server based on load and other factors
        
        Args:
            **kwargs: Filter parameters
                location: Preferred location
                protocol: Required protocol
                min_uptime: Minimum uptime in days
            
        Returns:
            int or None: Best server ID or None if no suitable server
        """
        # Get filter parameters
        location = kwargs.get('location')
        protocol = kwargs.get('protocol')
        min_uptime = kwargs.get('min_uptime')
        
        # Start with all active servers
        servers = self.server_model.objects.filter(is_active=True)
        
        # Apply filters
        if location:
            servers = servers.filter(location=location)
            
        if protocol:
            servers = servers.filter(protocols__contains=protocol)
            
        if min_uptime:
            # Calculate minimum creation date
            min_date = timezone.now() - timedelta(days=min_uptime)
            servers = servers.filter(created_at__lte=min_date)
            
        # If no servers match filters, return None
        if not servers.exists():
            return None
            
        # Get server loads
        loads = self.get_server_load()
        
        # Find server with lowest load
        best_server_id = None
        lowest_load = float('inf')
        
        for server in servers:
            load = loads.get(server.id, 100.0)
            if load < lowest_load:
                lowest_load = load
                best_server_id = server.id
                
        return best_server_id 