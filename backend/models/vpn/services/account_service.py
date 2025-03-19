"""
Account Service for VPN management.

This module provides services for managing VPN accounts.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from django.utils import timezone
from django.db import transaction

from backend.models.vpn.account import VPNAccount
from backend.models.vpn.server import Server, Location
from backend.models.vpn.services.panel_client import PanelClient

logger = logging.getLogger(__name__)

class AccountService:
    """Service for managing VPN accounts."""
    
    @staticmethod
    async def create_account(
        user_id: int,
        server_id: Optional[int] = None,
        location_id: Optional[int] = None,
        subscription_days: int = 30,
        traffic_limit_gb: int = 100,
        max_connections: int = 1,
        email: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Optional[VPNAccount]:
        """
        Create a new VPN account.
        
        Args:
            user_id: User ID
            server_id: Server ID (optional, will be selected by load if not provided)
            location_id: Location ID (optional, will be selected by availability if not provided)
            subscription_days: Subscription duration in days
            traffic_limit_gb: Traffic limit in GB
            max_connections: Maximum number of concurrent connections
            email: Custom email (optional, will be generated if not provided)
            remark: Custom remark (optional)
            
        Returns:
            Created VPN account or None if creation failed
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            # Get user
            user = User.objects.get(id=user_id)
            
            # Select server if not provided
            server = None
            if server_id:
                server = Server.objects.get(id=server_id, is_active=True)
            elif location_id:
                server = PanelClient.get_best_server_in_location(location_id)
            else:
                server = PanelClient.get_server_by_load()
                
            if not server:
                logger.error("No suitable server found")
                return None
                
            # Generate email if not provided
            if not email:
                import uuid
                email = f"{user.username}_{uuid.uuid4().hex[:8]}@moonvpn.ir"
                
            # Generate remark if not provided
            if not remark:
                remark = f"MoonVPN-{user.username}"
                
            # Create account in database
            with transaction.atomic():
                account = VPNAccount.objects.create(
                    user=user,
                    server=server,
                    email=email,
                    expires_at=timezone.now() + timezone.timedelta(days=subscription_days),
                    total_traffic_gb=traffic_limit_gb,
                    used_traffic_gb=0,
                    status='pending',
                    remark=remark,
                    max_connections=max_connections
                )
                
                # Create account on the panel
                success = await AccountService._create_account_on_panel(
                    account.id,
                    subscription_days,
                    traffic_limit_gb
                )
                
                if success:
                    account.status = 'active'
                    account.last_sync = timezone.now()
                    account.save(update_fields=['status', 'last_sync'])
                    
                    # Update server statistics
                    server.current_clients += 1
                    server.update_load_factor()
                    
                    return account
                else:
                    # If panel creation failed, mark as failed in database
                    account.status = 'disabled'
                    account.save(update_fields=['status'])
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return None
    
    @staticmethod
    async def _create_account_on_panel(account_id: int, subscription_days: int, traffic_limit_gb: int) -> bool:
        """
        Create an account on the panel.
        
        Args:
            account_id: Account ID
            subscription_days: Subscription duration in days
            traffic_limit_gb: Traffic limit in GB
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Get panel client
            client = PanelClient(server_instance=account.server)
            
            # Get inbounds
            inbounds = await client.get_inbounds()
            
            # Find suitable inbound for new clients
            if not inbounds:
                logger.error("No inbounds found on the panel")
                return False
                
            # Use the first inbound (can be customized based on needs)
            inbound_id = inbounds[0].get('id')
            
            # Create client on the panel
            success = await client.add_client(
                inbound_id,
                account.email,
                str(account.uuid),
                subscription_days,
                traffic_limit_gb
            )
            
            return success
        except Exception as e:
            logger.error(f"Error creating account on panel: {e}")
            return False
    
    @staticmethod
    async def sync_account_traffic(account_id: int) -> bool:
        """
        Sync account traffic with the panel.
        
        Args:
            account_id: Account ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Skip if account is not active
            if account.status != 'active':
                return True
                
            # Get panel client
            client = PanelClient(server_instance=account.server)
            
            # Get inbounds
            inbounds = await client.get_inbounds()
            
            if not inbounds:
                logger.error("No inbounds found on the panel")
                return False
                
            # Find inbound with our client
            for inbound in inbounds:
                inbound_id = inbound.get('id')
                traffic_data = await client.get_client_traffic(inbound_id, account.email)
                
                # If client found, update traffic data
                if 'error' not in traffic_data:
                    total_bytes = traffic_data.get('total', 0)
                    # Convert bytes to GB
                    used_traffic_gb = round(total_bytes / (1024 * 1024 * 1024), 2)
                    
                    account.used_traffic_gb = used_traffic_gb
                    account.last_sync = timezone.now()
                    
                    # Check if traffic exceeded
                    if used_traffic_gb >= account.total_traffic_gb:
                        account.status = 'traffic_exceeded'
                        
                    # Check if expired
                    if account.expires_at < timezone.now():
                        account.status = 'expired'
                        
                    account.save(update_fields=['used_traffic_gb', 'last_sync', 'status'])
                    return True
                    
            logger.warning(f"Client not found in any inbound: {account.email}")
            return False
            
        except Exception as e:
            logger.error(f"Error syncing account traffic: {e}")
            return False
    
    @staticmethod
    async def sync_all_accounts() -> Dict[int, bool]:
        """
        Sync all active accounts.
        
        Returns:
            Dictionary mapping account IDs to sync status
        """
        active_accounts = VPNAccount.objects.filter(status='active')
        results = {}
        
        for account in active_accounts:
            success = await AccountService.sync_account_traffic(account.id)
            results[account.id] = success
            
        return results
    
    @staticmethod
    async def renew_account(account_id: int, additional_days: int) -> bool:
        """
        Renew an account.
        
        Args:
            account_id: Account ID
            additional_days: Additional days to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Calculate new expiry time
            new_expires_at = max(account.expires_at, timezone.now()) + timezone.timedelta(days=additional_days)
            
            # Update in database
            account.expires_at = new_expires_at
            
            # If account was expired, reactivate it
            if account.status == 'expired':
                account.status = 'active'
                
            account.save(update_fields=['expires_at', 'status'])
            
            # If account is not on panel, create it
            if account.status != 'active':
                remaining_days = (new_expires_at - timezone.now()).days
                success = await AccountService._create_account_on_panel(
                    account.id,
                    remaining_days,
                    account.total_traffic_gb
                )
                
                if success:
                    account.status = 'active'
                    account.save(update_fields=['status'])
                    return True
                else:
                    return False
                    
            # Update on panel
            client = PanelClient(server_instance=account.server)
            inbounds = await client.get_inbounds()
            
            for inbound in inbounds:
                inbound_id = inbound.get('id')
                clients = await client.get_clients(inbound_id)
                
                client_found = False
                for client_data in clients:
                    if client_data.get('email') == account.email:
                        client_found = True
                        
                        # Prepare updated client data
                        client_data['expiryTime'] = int(new_expires_at.timestamp() * 1000)
                        
                        # Update client
                        success = await client.update_client(inbound_id, account.email, client_data)
                        
                        if success:
                            account.last_sync = timezone.now()
                            account.save(update_fields=['last_sync'])
                            return True
                            
            if not client_found:
                # If client not found on panel, create it
                remaining_days = (new_expires_at - timezone.now()).days
                success = await AccountService._create_account_on_panel(
                    account.id,
                    remaining_days,
                    account.total_traffic_gb
                )
                
                if success:
                    account.status = 'active'
                    account.last_sync = timezone.now()
                    account.save(update_fields=['status', 'last_sync'])
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error renewing account: {e}")
            return False
    
    @staticmethod
    async def reset_account_traffic(account_id: int) -> bool:
        """
        Reset account traffic.
        
        Args:
            account_id: Account ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Reset in database
            account.used_traffic_gb = 0
            
            # If account was traffic_exceeded, reactivate it
            if account.status == 'traffic_exceeded':
                account.status = 'active'
                
            account.save(update_fields=['used_traffic_gb', 'status'])
            
            # Reset on panel
            client = PanelClient(server_instance=account.server)
            inbounds = await client.get_inbounds()
            
            for inbound in inbounds:
                inbound_id = inbound.get('id')
                success = await client.reset_client_traffic(inbound_id, account.email)
                
                if success:
                    account.last_sync = timezone.now()
                    account.save(update_fields=['last_sync'])
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error resetting account traffic: {e}")
            return False
    
    @staticmethod
    async def change_account_server(account_id: int, new_server_id: int, initiated_by: str = 'admin') -> bool:
        """
        Change account server.
        
        Args:
            account_id: Account ID
            new_server_id: New server ID
            initiated_by: Who initiated the migration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Skip if already on the target server
            if account.server_id == new_server_id:
                return True
                
            # Get new server
            new_server = Server.objects.get(id=new_server_id, is_active=True)
            
            # Start migration
            migration = account.migrate_to_server(new_server, initiated_by)
            
            # Remove from old panel
            old_client = PanelClient(server_instance=account.server)
            inbounds = await old_client.get_inbounds()
            
            old_success = False
            for inbound in inbounds:
                inbound_id = inbound.get('id')
                if await old_client.delete_client(inbound_id, account.email):
                    old_success = True
                    break
                    
            # Create on new panel
            remaining_days = max(0, (account.expires_at - timezone.now()).days)
            new_success = await AccountService._create_account_on_panel(
                account.id,
                remaining_days,
                account.total_traffic_gb
            )
            
            # Update migration record
            migration.completed_at = timezone.now()
            migration.success = new_success
            migration.save(update_fields=['completed_at', 'success'])
            
            return new_success
            
        except Exception as e:
            logger.error(f"Error changing account server: {e}")
            return False
    
    @staticmethod
    async def delete_account(account_id: int) -> bool:
        """
        Delete an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.objects.select_related('server').get(id=account_id)
            
            # Remove from panel
            client = PanelClient(server_instance=account.server)
            inbounds = await client.get_inbounds()
            
            panel_deleted = False
            for inbound in inbounds:
                inbound_id = inbound.get('id')
                if await client.delete_client(inbound_id, account.email):
                    panel_deleted = True
                    break
                    
            # Update server statistics
            if account.status == 'active':
                account.server.current_clients -= 1
                account.server.update_load_factor()
                
            # Delete from database
            account.delete()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            return False 