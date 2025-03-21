import logging
import uuid
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from payments.models import Payment
from core.services.panel.client import ThreeXUIClient

logger = logging.getLogger(__name__)

class AccountService:
    """
    Service for managing VPN accounts and integrating with 3x-UI panel
    """
    
    @staticmethod
    def get_panel_client():
        """
        Get a configured instance of ThreeXUIClient
        
        Returns:
            ThreeXUIClient: Configured panel client
        """
        panel_url = settings.X_UI_PANEL_URL
        panel_username = settings.X_UI_PANEL_USERNAME
        panel_password = settings.X_UI_PANEL_PASSWORD
        
        return ThreeXUIClient(
            base_url=panel_url,
            username=panel_username,
            password=panel_password
        )
    
    @staticmethod
    def generate_account_email(user, payment=None):
        """
        Generate a unique email/identifier for a VPN account
        
        Args:
            user: User object
            payment: Optional payment object
            
        Returns:
            str: Generated email/identifier
        """
        # If user has a username or email, use it as a base
        if hasattr(user, 'username') and user.username:
            base = user.username.lower()
        elif hasattr(user, 'email') and user.email:
            base = user.email.split('@')[0].lower()
        else:
            # Generate a random base
            base = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        # Clean the base (remove special characters)
        base = ''.join(c for c in base if c.isalnum() or c == '_').strip()
        
        # Add a random suffix
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        
        # Add timestamp to ensure uniqueness
        timestamp = int(datetime.now().timestamp()) % 10000
        
        # Format: base_suffix_timestamp
        email = f"{base}_{suffix}_{timestamp}"
        
        return email
    
    @staticmethod
    def create_account_from_payment(payment):
        """
        Create a VPN account based on a completed payment
        
        Args:
            payment: Payment object (must be in COMPLETED status)
            
        Returns:
            tuple: (success, account_data, error_message)
        """
        if payment.status != Payment.COMPLETED:
            return False, None, "Payment is not completed"
        
        # Check if inbound_id is set in payment
        if not payment.inbound_id:
            return False, None, "No inbound ID specified in payment"
        
        # Get traffic and duration from payment
        traffic_bytes = payment.traffic_amount
        duration_days = payment.duration_days
        inbound_id = payment.inbound_id
        
        try:
            # Initialize panel client
            client = AccountService.get_panel_client()
            
            # Generate email/identifier for the account
            email = AccountService.generate_account_email(payment.user, payment)
            
            # Create client in panel
            client_data = client.create_client(
                inbound_id=inbound_id,
                email=email,
                traffic_limit=traffic_bytes,
                expire_days=duration_days,
                enable=True
            )
            
            if not client_data:
                return False, None, "Failed to create client in panel"
            
            # Generate subscription link
            subscription_link = client.generate_client_link(inbound_id, email)
            
            # Get client status for complete information
            status = client.get_client_status(inbound_id, email)
            
            # Combine data
            account_data = {
                "email": email,
                "inbound_id": inbound_id,
                "traffic_limit_bytes": traffic_bytes,
                "duration_days": duration_days,
                "expiry_date": status.get("expiry_date"),
                "days_left": status.get("days_left"),
                "subscription_link": subscription_link,
                "payment_id": str(payment.id),
                "client_data": client_data
            }
            
            # TODO: Store account data in database if needed
            
            logger.info(f"Created VPN account for payment {payment.id}: {email}")
            
            return True, account_data, None
            
        except Exception as e:
            logger.exception(f"Error creating VPN account for payment {payment.id}: {str(e)}")
            return False, None, f"Error creating account: {str(e)}"
    
    @staticmethod
    def get_account_status(inbound_id, email):
        """
        Get status of a VPN account
        
        Args:
            inbound_id: Inbound ID
            email: Client email/identifier
            
        Returns:
            dict: Account status
        """
        try:
            client = AccountService.get_panel_client()
            status = client.get_client_status(inbound_id, email)
            
            # Generate subscription link
            subscription_link = client.generate_client_link(inbound_id, email)
            
            # Add subscription link to status
            status["subscription_link"] = subscription_link
            
            # Format traffic values for human readability
            status["traffic_used_formatted"] = AccountService.format_bytes(status.get("total_used_bytes", 0))
            status["traffic_limit_formatted"] = AccountService.format_bytes(status.get("total_limit_bytes", 0))
            status["traffic_remaining_formatted"] = AccountService.format_bytes(status.get("remaining_bytes", 0))
            
            return status
            
        except Exception as e:
            logger.exception(f"Error getting account status: {str(e)}")
            return {"error": str(e), "active": False}
    
    @staticmethod
    def extend_account(inbound_id, email, additional_days, additional_traffic_bytes=None):
        """
        Extend an existing VPN account
        
        Args:
            inbound_id: Inbound ID
            email: Client email/identifier
            additional_days: Days to add
            additional_traffic_bytes: Additional traffic in bytes
            
        Returns:
            tuple: (success, message)
        """
        try:
            client = AccountService.get_panel_client()
            result = client.extend_client(
                inbound_id=inbound_id,
                client_email=email,
                additional_days=additional_days,
                additional_traffic=additional_traffic_bytes
            )
            
            if result:
                # Get updated status
                status = client.get_client_status(inbound_id, email)
                
                logger.info(f"Extended account {email}: +{additional_days} days, +{AccountService.format_bytes(additional_traffic_bytes or 0)} traffic")
                
                return True, {
                    "message": "Account extended successfully",
                    "new_expiry": status.get("expiry_date"),
                    "days_left": status.get("days_left"),
                    "traffic_limit": AccountService.format_bytes(status.get("total_limit_bytes", 0))
                }
            else:
                return False, "Failed to extend account"
                
        except Exception as e:
            logger.exception(f"Error extending account: {str(e)}")
            return False, f"Error extending account: {str(e)}"
    
    @staticmethod
    def reset_account_traffic(inbound_id, email):
        """
        Reset traffic usage for an account
        
        Args:
            inbound_id: Inbound ID
            email: Client email/identifier
            
        Returns:
            tuple: (success, message)
        """
        try:
            client = AccountService.get_panel_client()
            result = client.reset_client_traffic(inbound_id, email)
            
            if result:
                logger.info(f"Reset traffic for account {email}")
                return True, "Traffic reset successfully"
            else:
                return False, "Failed to reset traffic"
                
        except Exception as e:
            logger.exception(f"Error resetting account traffic: {str(e)}")
            return False, f"Error resetting traffic: {str(e)}"
    
    @staticmethod
    def delete_account(inbound_id, email):
        """
        Delete a VPN account
        
        Args:
            inbound_id: Inbound ID
            email: Client email/identifier
            
        Returns:
            tuple: (success, message)
        """
        try:
            client = AccountService.get_panel_client()
            result = client.delete_client(inbound_id, email)
            
            if result:
                logger.info(f"Deleted account {email}")
                return True, "Account deleted successfully"
            else:
                return False, "Failed to delete account"
                
        except Exception as e:
            logger.exception(f"Error deleting account: {str(e)}")
            return False, f"Error deleting account: {str(e)}"
    
    @staticmethod
    def get_all_inbounds():
        """
        Get all available inbounds from the panel
        
        Returns:
            list: Inbound configurations
        """
        try:
            client = AccountService.get_panel_client()
            inbounds = client.get_inbounds()
            
            # Add some extra info and format the inbounds for easy consumption
            for inbound in inbounds:
                inbound["protocol_display"] = inbound.get("protocol", "").upper()
                inbound["client_count"] = len(client.get_clients(inbound.get("id")))
                
            return inbounds
            
        except Exception as e:
            logger.exception(f"Error getting inbounds: {str(e)}")
            return []
    
    @staticmethod
    def get_server_stats():
        """
        Get server statistics
        
        Returns:
            dict: Server statistics
        """
        try:
            client = AccountService.get_panel_client()
            stats = client.get_server_stats()
            
            # Format memory and disk usage
            if "mem" in stats:
                mem = stats["mem"]
                mem["usage_percent"] = (mem.get("current", 0) / mem.get("total", 1)) * 100 if mem.get("total") else 0
                mem["current_formatted"] = AccountService.format_bytes(mem.get("current", 0) * 1024 * 1024)  # MB to bytes
                mem["total_formatted"] = AccountService.format_bytes(mem.get("total", 0) * 1024 * 1024)  # MB to bytes
            
            if "disk" in stats:
                disk = stats["disk"]
                disk["usage_percent"] = (disk.get("current", 0) / disk.get("total", 1)) * 100 if disk.get("total") else 0
                disk["current_formatted"] = AccountService.format_bytes(disk.get("current", 0) * 1024 * 1024)  # MB to bytes
                disk["total_formatted"] = AccountService.format_bytes(disk.get("total", 0) * 1024 * 1024)  # MB to bytes
            
            # Format uptime
            if "uptime" in stats:
                uptime_seconds = stats["uptime"]
                days, remainder = divmod(uptime_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                stats["uptime_formatted"] = f"{days}d {hours}h {minutes}m {seconds}s"
            
            return stats
            
        except Exception as e:
            logger.exception(f"Error getting server stats: {str(e)}")
            return {}
    
    @staticmethod
    def format_bytes(size_bytes):
        """
        Format bytes to human-readable string
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}" 