"""
Account Service

This module provides services for managing VPN accounts.
"""

import logging
import uuid
import os
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from io import BytesIO
import time

from core.database.models import User, VPNAccount, Server, SubscriptionPlan, Transaction
from core.services.panel.api import XUIClient
from core.bot.services.threexui_api import create_v2ray_account, delete_v2ray_account, update_v2ray_account, get_v2ray_account_traffic
import qrcode

logger = logging.getLogger(__name__)

# Initialize XUI client
xui_client = None
try:
    XUI_CONFIG = {
        "base_url": os.getenv("XUI_PANEL_URL", "http://localhost:8080"),
        "username": os.getenv("XUI_PANEL_USERNAME", "admin"),
        "password": os.getenv("XUI_PANEL_PASSWORD", "admin"),
    }
    xui_client = XUIClient(**XUI_CONFIG)
except Exception as e:
    logger.error(f"Failed to initialize XUI client: {e}")


class AccountService:
    """Service for managing VPN accounts."""
    
    def __init__(self, api_client):
        """Initialize the account service."""
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def get_user_accounts(user_id: int) -> List[VPNAccount]:
        """
        Get all accounts for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of VPNAccount objects
        """
        return VPNAccount.get_all(user_id=user_id)
    
    @staticmethod
    def get_account(account_id: int) -> Optional[VPNAccount]:
        """
        Get an account by ID.
        
        Args:
            account_id: Account ID
            
        Returns:
            VPNAccount object or None if not found
        """
        return VPNAccount.get_by_id(account_id)
    
    async def create_account(self, user_id, server_id, subscription_plan_id, email=None):
        """Create a new VPN account."""
        try:
            # Generate a random name if email is not provided
            if not email:
                email = f"user{user_id}_{int(time.time())}@moonvpn.ir"
            
            # Generate a random UUID
            uuid = str(uuid.uuid4())
            
            # Get subscription plan details
            subscription_plan = get_subscription_plan(subscription_plan_id)
            if not subscription_plan:
                self.logger.error(f"Subscription plan {subscription_plan_id} not found")
                return None
            
            # Get server details
            server = get_server(server_id)
            if not server:
                self.logger.error(f"Server {server_id} not found")
                return None
            
            # Calculate expiry date
            duration_days = subscription_plan.get("duration_days", 30)
            expiry_date = (datetime.now() + timedelta(days=duration_days)).isoformat()
            
            # Calculate traffic limit
            traffic_limit = subscription_plan.get("traffic_limit", 0)
            
            # Create account in database
            account = VPNAccount.create(
                user_id=user_id,
                server_id=server_id,
                subscription_plan_id=subscription_plan_id,
                name=f"{server.get('location', 'Unknown')} - {subscription_plan.get('name', 'Unknown')}",
                uuid=uuid,
                email=email,
                expiry_date=expiry_date,
                traffic_limit=traffic_limit,
                status="active"
            )
            
            if not account:
                self.logger.error("Failed to create account in database")
                return None
            
            # Create account on VPN server
            success = await self.create_account_on_server(account, server)
            
            if not success:
                # If failed to create on server, mark as failed in database
                account.update(status="failed")
                self.logger.error(f"Failed to create account on server {server_id}")
                return None
            
            # Update account with config
            config = await self.generate_config(account, server)
            if config:
                account.update(config=config)
            
            return account
        except Exception as e:
            self.logger.error(f"Error creating account: {e}")
            return None
    
    async def create_account_on_server(self, account, server):
        """Create account on VPN server."""
        try:
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Create payload for account creation
            payload = {
                "uuid": account.get("uuid"),
                "email": account.get("email"),
                "traffic": account.get("traffic_limit"),
                "expiry_time": account.get("expiry_date")
            }
            
            # Send request to server
            response = await self.api_client.post(
                f"{api_url}/users",
                json=payload,
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                return True
            
            self.logger.error(f"Failed to create account on server: {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating account on server: {e}")
            return False
    
    async def generate_config(self, account, server):
        """Generate VPN configuration for account."""
        try:
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Get config from server
            response = await self.api_client.get(
                f"{api_url}/users/{account.get('uuid')}/config",
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                return response.json()
            
            self.logger.error(f"Failed to get config from server: {response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error generating config: {e}")
            return None
    
    async def get_account_status(self, account_id):
        """Get account status from server."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return None
            
            # Get server details
            server = get_server(account.get("server_id"))
            if not server:
                self.logger.error(f"Server {account.get('server_id')} not found")
                return None
            
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Get account status from server
            response = await self.api_client.get(
                f"{api_url}/users/{account.get('uuid')}",
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                server_data = response.json()
                
                # Update account in database with latest traffic usage
                traffic_used = server_data.get("used_traffic", 0)
                up_traffic = server_data.get("up_traffic", 0)
                down_traffic = server_data.get("down_traffic", 0)
                
                update_account_traffic(
                    account_id, 
                    traffic_used, 
                    up_traffic, 
                    down_traffic
                )
                
                # Update last connect time if available
                if server_data.get("last_connect"):
                    account.update(last_connect=server_data.get("last_connect"))
                
                return {
                    "status": "active" if not account.is_expired() else "expired",
                    "traffic_used": traffic_used,
                    "up_traffic": up_traffic,
                    "down_traffic": down_traffic,
                    "expiry_date": account.get("expiry_date"),
                    "days_left": account.days_left(),
                    "is_expired": account.is_expired(),
                    "is_near_expiry": account.is_near_expiry(),
                    "has_sufficient_traffic": account.has_sufficient_traffic(),
                    "usage_percent": account.get_usage_percent()
                }
            
            self.logger.error(f"Failed to get account status from server: {response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting account status: {e}")
            return None
    
    async def renew_account(self, account_id, subscription_plan_id):
        """Renew an existing VPN account."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return False
            
            # Get subscription plan details
            subscription_plan = get_subscription_plan(subscription_plan_id)
            if not subscription_plan:
                self.logger.error(f"Subscription plan {subscription_plan_id} not found")
                return False
            
            # Get server details
            server = get_server(account.get("server_id"))
            if not server:
                self.logger.error(f"Server {account.get('server_id')} not found")
                return False
            
            # Calculate new expiry date
            duration_days = subscription_plan.get("duration_days", 30)
            
            # Extend account expiry in database
            success = extend_account_expiry(account_id, duration_days)
            if not success:
                self.logger.error(f"Failed to extend account expiry in database")
                return False
            
            # Get updated account
            account = get_account(account_id)
            
            # Update account on server
            success = await self.update_account_on_server(account, server)
            if not success:
                self.logger.error(f"Failed to update account on server")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error renewing account: {e}")
            return False
    
    async def update_account_on_server(self, account, server):
        """Update account on VPN server."""
        try:
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Create payload for account update
            payload = {
                "uuid": account.get("uuid"),
                "email": account.get("email"),
                "traffic": account.get("traffic_limit"),
                "expiry_time": account.get("expiry_date")
            }
            
            # Send request to server
            response = await self.api_client.put(
                f"{api_url}/users/{account.get('uuid')}",
                json=payload,
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                return True
            
            self.logger.error(f"Failed to update account on server: {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating account on server: {e}")
            return False
    
    async def reset_traffic(self, account_id):
        """Reset traffic usage for an account."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return False
            
            # Get server details
            server = get_server(account.get("server_id"))
            if not server:
                self.logger.error(f"Server {account.get('server_id')} not found")
                return False
            
            # Reset traffic in database
            success = reset_account_traffic(account_id)
            if not success:
                self.logger.error(f"Failed to reset traffic in database")
                return False
            
            # Reset traffic on server
            success = await self.reset_traffic_on_server(account, server)
            if not success:
                self.logger.error(f"Failed to reset traffic on server")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error resetting traffic: {e}")
            return False
    
    async def reset_traffic_on_server(self, account, server):
        """Reset traffic usage on VPN server."""
        try:
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Create payload for traffic reset
            payload = {
                "reset_traffic": True
            }
            
            # Send request to server
            response = await self.api_client.post(
                f"{api_url}/users/{account.get('uuid')}/reset",
                json=payload,
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                return True
            
            self.logger.error(f"Failed to reset traffic on server: {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error resetting traffic on server: {e}")
            return False
    
    async def change_server(self, account_id, new_server_id):
        """Change server for an account."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return False
            
            # Get old server details
            old_server = get_server(account.get("server_id"))
            if not old_server:
                self.logger.error(f"Old server {account.get('server_id')} not found")
                return False
            
            # Get new server details
            new_server = get_server(new_server_id)
            if not new_server:
                self.logger.error(f"New server {new_server_id} not found")
                return False
            
            # Delete account from old server
            success = await self.delete_account_from_server(account, old_server)
            if not success:
                self.logger.error(f"Failed to delete account from old server")
                return False
            
            # Update server ID in database
            success = change_account_server(account_id, new_server_id)
            if not success:
                self.logger.error(f"Failed to update server ID in database")
                return False
            
            # Get updated account
            account = get_account(account_id)
            
            # Create account on new server
            success = await self.create_account_on_server(account, new_server)
            if not success:
                # If failed to create on new server, try to restore on old server
                await self.create_account_on_server(account, old_server)
                change_account_server(account_id, account.get("server_id"))
                self.logger.error(f"Failed to create account on new server")
                return False
            
            # Update account name
            new_name = f"{new_server.get('location', 'Unknown')} - {account.get('name').split(' - ')[1]}"
            account.update(name=new_name)
            
            # Update account with new config
            config = await self.generate_config(account, new_server)
            if config:
                account.update(config=config)
            
            return True
        except Exception as e:
            self.logger.error(f"Error changing server: {e}")
            return False
    
    async def delete_account_from_server(self, account, server):
        """Delete account from VPN server."""
        try:
            # Get server connection details
            host = server.get("host")
            port = server.get("port")
            username = server.get("username")
            password = server.get("password")
            
            # Connect to server API
            api_url = f"https://{host}:{port}/api/v1"
            
            # Send request to server
            response = await self.api_client.delete(
                f"{api_url}/users/{account.get('uuid')}",
                auth=(username, password),
                verify=False
            )
            
            if response.status_code == 200:
                return True
            
            self.logger.error(f"Failed to delete account from server: {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting account from server: {e}")
            return False
    
    async def delete_account(self, account_id):
        """Delete a VPN account."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return False
            
            # Get server details
            server = get_server(account.get("server_id"))
            if not server:
                self.logger.error(f"Server {account.get('server_id')} not found")
                return False
            
            # Delete account from server
            success = await self.delete_account_from_server(account, server)
            if not success:
                self.logger.error(f"Failed to delete account from server")
                # Continue with database deletion even if server deletion fails
            
            # Delete account from database
            success = account.delete()
            if not success:
                self.logger.error(f"Failed to delete account from database")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting account: {e}")
            return False
    
    async def generate_qr_code(self, account_id):
        """Generate QR code for account configuration."""
        try:
            # Get account from database
            account = get_account(account_id)
            if not account:
                self.logger.error(f"Account {account_id} not found")
                return None
            
            # Get config
            config = account.get("config")
            if not config:
                self.logger.error(f"No config found for account {account_id}")
                return None
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Add config data to QR code
            qr.add_data(config.get("vmess_url", ""))
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to BytesIO
            img_io = BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            
            return img_io
        except Exception as e:
            self.logger.error(f"Error generating QR code: {e}")
            return None

    @staticmethod
    async def update_account(account_id: int, **kwargs) -> bool:
        """
        Update an account's properties.
        
        Args:
            account_id: ID of the account to update
            **kwargs: Properties to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Update account properties
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            
            # Save changes
            account.save()
            
            # Update account on V2Ray server if needed
            if "expiry_date" in kwargs or "total_traffic_gb" in kwargs or "is_active" in kwargs:
                server = Server.get_by_id(account.server_id)
                if not server:
                    logger.error(f"Server {account.server_id} not found")
                    return False
                
                # Calculate days until expiry
                if "expiry_date" in kwargs:
                    expiry_days = (kwargs["expiry_date"] - datetime.now()).days
                else:
                    expiry_days = account.days_left()
                
                # Get traffic limit
                if "total_traffic_gb" in kwargs:
                    traffic_gb = kwargs["total_traffic_gb"]
                else:
                    traffic_gb = account.total_traffic_gb
                
                # Get active status
                if "is_active" in kwargs:
                    is_active = kwargs["is_active"]
                else:
                    is_active = account.is_active
                
                # Update on V2Ray server
                success = await update_v2ray_account(
                    panel_id=server.panel_id,
                    inbound_id=account.inbound_id,
                    email=account.v2ray_email,
                    expiry_days=expiry_days,
                    traffic_gb=traffic_gb,
                    enable=is_active
                )
                
                if not success:
                    logger.error(f"Failed to update account {account_id} on V2Ray server")
                    return False
            
            logger.info(f"Updated account {account_id} with {kwargs}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating account: {e}")
            return False
    
    @staticmethod
    async def delete_account(account_id: int) -> bool:
        """
        Delete an account.
        
        Args:
            account_id: ID of the account to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Get server
            server = Server.get_by_id(account.server_id)
            if not server:
                logger.error(f"Server {account.server_id} not found")
                # Delete from database anyway
                account.delete()
                return True
            
            # Delete from V2Ray server
            success = await delete_v2ray_account(
                panel_id=server.panel_id,
                inbound_id=account.inbound_id,
                email=account.v2ray_email
            )
            
            if not success:
                logger.warning(f"Failed to delete account {account_id} from V2Ray server")
                # Continue with deletion from database
            
            # Delete from database
            account.delete()
            
            logger.info(f"Deleted account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            return False
    
    @staticmethod
    async def renew_account(account_id: int, days: int, add_traffic_gb: Optional[int] = None, 
                     payment_id: Optional[int] = None) -> bool:
        """
        Renew an account.
        
        Args:
            account_id: ID of the account to renew
            days: Number of days to add
            add_traffic_gb: Optional traffic to add in GB
            payment_id: Optional payment ID for tracking
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Calculate new expiry date
            if account.expiry_date < datetime.now():
                # If account is expired, set new expiry date from now
                new_expiry = datetime.now() + timedelta(days=days)
            else:
                # If account is not expired, add days to current expiry date
                new_expiry = account.expiry_date + timedelta(days=days)
            
            # Calculate new traffic
            new_traffic = account.total_traffic_gb
            if add_traffic_gb:
                new_traffic += add_traffic_gb
            
            # Update account
            account.expiry_date = new_expiry
            account.total_traffic_gb = new_traffic
            account.is_active = True
            
            if payment_id:
                account.payment_id = payment_id
                
            # Save changes
            account.save()
            
            # Update on V2Ray server
            server = Server.get_by_id(account.server_id)
            if not server:
                logger.error(f"Server {account.server_id} not found")
                return False
            
            success = await update_v2ray_account(
                panel_id=server.panel_id,
                inbound_id=account.inbound_id,
                email=account.v2ray_email,
                expiry_days=account.days_left(),
                traffic_gb=account.total_traffic_gb,
                enable=True
            )
            
            if not success:
                logger.error(f"Failed to renew account {account_id} on V2Ray server")
                return False
            
            # Create renewal transaction
            Transaction.create(
                user_id=account.user_id,
                account_id=account_id,
                amount=0,  # Will be updated by payment service
                payment_id=payment_id,
                transaction_type="renewal",
                status="completed",
                details={
                    "days": days,
                    "traffic_gb": add_traffic_gb,
                    "expiry_date": new_expiry.isoformat()
                }
            )
            
            logger.info(f"Renewed account {account_id} for {days} days")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing account: {e}")
            return False
    
    @staticmethod
    async def change_server(account_id: int, new_server_id: int) -> bool:
        """
        Change the server for an account.
        
        Args:
            account_id: ID of the account to update
            new_server_id: ID of the new server
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Get old server
            old_server = Server.get_by_id(account.server_id)
            if not old_server:
                logger.error(f"Old server {account.server_id} not found")
                # Continue with server change anyway
            else:
                # Delete from old V2Ray server
                await delete_v2ray_account(
                    panel_id=old_server.panel_id,
                    inbound_id=account.inbound_id,
                    email=account.v2ray_email
                )
            
            # Get new server
            new_server = Server.get_by_id(new_server_id)
            if not new_server:
                logger.error(f"New server {new_server_id} not found")
                return False
            
            # Get default inbound
            inbound_id = new_server.default_inbound_id
            if not inbound_id:
                logger.error(f"New server {new_server_id} has no default inbound ID")
                return False
            
            # Create on new V2Ray server
            expiry_days = account.days_left()
            if expiry_days <= 0:
                logger.error(f"Account {account_id} is expired")
                return False
            
            v2ray_account = await create_v2ray_account(
                panel_id=new_server.panel_id,
                inbound_id=inbound_id,
                email=account.v2ray_email,
                expiry_days=expiry_days,
                traffic_gb=account.total_traffic_gb
            )
            
            if not v2ray_account:
                logger.error(f"Failed to create account on new V2Ray server for account {account_id}")
                return False
            
            # Update account with new server and V2Ray info
            account.server_id = new_server_id
            account.inbound_id = inbound_id
            account.v2ray_uuid = v2ray_account.get("uuid", "")
            account.config.update({
                "uuid": v2ray_account.get("uuid", ""),
                "subscription_url": v2ray_account.get("subscription_url", ""),
                "qrcode": v2ray_account.get("qrcode", ""),
                "vless": v2ray_account.get("vless", ""),
                "vmess": v2ray_account.get("vmess", "")
            })
            account.save()
            
            logger.info(f"Changed server for account {account_id} from {account.server_id} to {new_server_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing server: {e}")
            return False
    
    @staticmethod
    async def reset_traffic(account_id: int) -> bool:
        """
        Reset traffic for an account.
        
        Args:
            account_id: ID of the account to reset traffic for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Reset traffic in database
            account.used_traffic_gb = 0
            account.save()
            
            # Reset traffic on V2Ray server
            server = Server.get_by_id(account.server_id)
            if not server:
                logger.error(f"Server {account.server_id} not found")
                return False
            
            success = await update_v2ray_account(
                panel_id=server.panel_id,
                inbound_id=account.inbound_id,
                email=account.v2ray_email,
                expiry_days=account.days_left(),
                traffic_gb=account.total_traffic_gb,
                enable=account.is_active
            )
            
            if not success:
                logger.error(f"Failed to reset traffic for account {account_id} on V2Ray server")
                return False
            
            logger.info(f"Reset traffic for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting traffic: {e}")
            return False
    
    @staticmethod
    async def add_traffic(account_id: int, traffic_gb: int, payment_id: Optional[int] = None) -> bool:
        """
        Add traffic to an account.
        
        Args:
            account_id: ID of the account to add traffic to
            traffic_gb: Amount of traffic to add in GB
            payment_id: Optional payment ID for tracking
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Add traffic
            new_traffic = account.total_traffic_gb + traffic_gb
            account.total_traffic_gb = new_traffic
            
            if payment_id:
                account.payment_id = payment_id
                
            # Save changes
            account.save()
            
            # Update on V2Ray server
            server = Server.get_by_id(account.server_id)
            if not server:
                logger.error(f"Server {account.server_id} not found")
                return False
            
            success = await update_v2ray_account(
                panel_id=server.panel_id,
                inbound_id=account.inbound_id,
                email=account.v2ray_email,
                expiry_days=account.days_left(),
                traffic_gb=new_traffic,
                enable=account.is_active
            )
            
            if not success:
                logger.error(f"Failed to add traffic for account {account_id} on V2Ray server")
                return False
            
            # Create transaction
            Transaction.create(
                user_id=account.user_id,
                account_id=account_id,
                amount=0,  # Will be updated by payment service
                payment_id=payment_id,
                transaction_type="add_traffic",
                status="completed",
                details={
                    "traffic_gb": traffic_gb,
                    "new_total": new_traffic
                }
            )
            
            logger.info(f"Added {traffic_gb} GB traffic to account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding traffic: {e}")
            return False
    
    @staticmethod
    async def sync_traffic(account_id: int) -> bool:
        """
        Sync traffic usage from V2Ray server.
        
        Args:
            account_id: ID of the account to sync traffic for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return False
            
            # Get server
            server = Server.get_by_id(account.server_id)
            if not server:
                logger.error(f"Server {account.server_id} not found")
                return False
            
            # Get traffic from V2Ray server
            traffic_data = await get_v2ray_account_traffic(
                panel_id=server.panel_id,
                email=account.v2ray_email
            )
            
            if not traffic_data:
                logger.error(f"Failed to get traffic data for account {account_id}")
                return False
            
            # Update traffic in database
            upload_gb = traffic_data.get("upload", 0) / (1024 * 1024 * 1024)
            download_gb = traffic_data.get("download", 0) / (1024 * 1024 * 1024)
            total_gb = upload_gb + download_gb
            
            account.used_traffic_gb = total_gb
            account.save()
            
            logger.info(f"Synced traffic for account {account_id}: {total_gb} GB used")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing traffic: {e}")
            return False
    
    @staticmethod
    async def get_configuration(account_id: int, config_type: str = "all") -> Dict[str, Any]:
        """
        Get configuration for an account.
        
        Args:
            account_id: ID of the account to get configuration for
            config_type: Type of configuration to get ('all', 'vless', 'vmess', 'subscription', 'qrcode')
            
        Returns:
            Configuration data
        """
        try:
            account = VPNAccount.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return {}
            
            # Get config from account
            config = account.config or {}
            
            if config_type == "all":
                return config
            elif config_type in config:
                return {config_type: config.get(config_type, "")}
            else:
                return {}
            
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return {} 