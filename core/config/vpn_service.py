"""
VPN Service for MoonVPN Telegram Bot

This module implements the VPN service functionality for handling VPN account operations
including status checks, account creation, and management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException

from app.core.config import settings
from app.bot.utils.logger import setup_logger
from app.core.database.models import VPNAccount, Server, User, Plan
from app.core.database.session import get_db
from app.core.services.panel_client import PanelClient
from app.core.services.vpn import VPNAccountService
from app.core.services.server import ServerService

# Initialize logger
logger = setup_logger(__name__)

class VPNService:
    """Service class for handling VPN-related operations."""
    
    def __init__(self):
        """Initialize VPN service with required dependencies."""
        self.panel_client = PanelClient()
        self.vpn_account_service = VPNAccountService()
        self.server_service = ServerService()
    
    async def create_account(
        self,
        user_id: int,
        plan_id: str,
        location_id: str,
        db: Any
    ) -> VPNAccount:
        """Create a new VPN account for a user."""
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get available server in location
            server = db.query(Server).filter(
                Server.location_id == location_id,
                Server.is_active == True
            ).first()
            
            if not server:
                raise HTTPException(
                    status_code=404,
                    detail="No available servers in selected location"
                )
            
            # Generate unique account ID
            account_id = str(uuid.uuid4())
            
            # Create account in panel
            panel_response = await self.panel_client.create_client(
                server_id=server.id,
                account_id=account_id,
                email=user.email,
                plan_id=plan_id
            )
            
            if not panel_response.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create account in VPN panel"
                )
            
            # Create account in database
            account = VPNAccount(
                id=account_id,
                user_id=user_id,
                server_id=server.id,
                plan_id=plan_id,
                status="active",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),  # Default 30 days
                traffic_limit=panel_response.get("traffic_limit", 0),
                traffic_used=0
            )
            
            db.add(account)
            db.commit()
            db.refresh(account)
            
            logger.info(f"Created VPN account {account_id} for user {user_id}")
            return account
            
        except Exception as e:
            logger.error(f"Error creating VPN account: {str(e)}")
            raise
    
    async def get_account_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get the status of a user's VPN account.
        
        Args:
            user_id: The Telegram user ID
            
        Returns:
            Dict containing account status information
        """
        try:
            # Get user's VPN account
            account = await self.vpn_account_service.get_by_user_id(user_id)
            
            if not account:
                return {
                    "has_account": False,
                    "message": "شما هنوز هیچ حساب VPN فعالی ندارید.",
                    "action": "buy"
                }
            
            # Get server status
            server = await self.server_service.get_by_id(account.server_id)
            if not server:
                return {
                    "has_account": True,
                    "status": "error",
                    "message": "خطا در دریافت اطلاعات سرور",
                    "action": "support"
                }
            
            # Calculate remaining time
            now = datetime.utcnow()
            remaining_days = (account.expiry_date - now).days
            
            # Format traffic usage
            used_traffic = account.used_traffic / (1024 * 1024 * 1024)  # Convert to GB
            total_traffic = account.total_traffic / (1024 * 1024 * 1024)  # Convert to GB
            
            return {
                "has_account": True,
                "status": "active" if remaining_days > 0 else "expired",
                "message": (
                    f"🔍 *وضعیت حساب VPN*\n\n"
                    f"📅 تاریخ انقضا: {account.expiry_date.strftime('%Y-%m-%d')}\n"
                    f"⏳ روزهای باقیمانده: {remaining_days}\n"
                    f"📊 مصرف ترافیک: {used_traffic:.2f}GB از {total_traffic:.2f}GB\n"
                    f"🌍 سرور: {server.location.name}\n"
                    f"⚡️ وضعیت: {'فعال' if remaining_days > 0 else 'منقضی شده'}"
                ),
                "action": "renew" if remaining_days <= 7 else None,
                "account": account
            }
            
        except Exception as e:
            logger.error(f"Error getting account status: {str(e)}")
            return {
                "has_account": False,
                "status": "error",
                "message": "خطا در دریافت اطلاعات حساب",
                "action": "support"
            }
    
    async def get_account_config(
        self,
        account_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Get the configuration details for a VPN account."""
        try:
            account = db.query(VPNAccount).filter(VPNAccount.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Get configuration from panel
            config = await self.panel_client.get_client_config(
                server_id=account.server_id,
                account_id=account_id
            )
            
            return {
                "id": account.id,
                "server": config.get("server"),
                "port": config.get("port"),
                "protocol": config.get("protocol"),
                "settings": config.get("settings", {}),
                "qr_code": config.get("qr_code")
            }
            
        except Exception as e:
            logger.error(f"Error getting account config: {str(e)}")
            raise
    
    async def reset_traffic(
        self,
        account_id: str,
        db: Any
    ) -> bool:
        """Reset the traffic usage for a VPN account."""
        try:
            account = db.query(VPNAccount).filter(VPNAccount.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Reset traffic in panel
            panel_response = await self.panel_client.reset_client_traffic(
                server_id=account.server_id,
                account_id=account_id
            )
            
            if not panel_response.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to reset traffic in VPN panel"
                )
            
            # Reset traffic in database
            account.traffic_used = 0
            db.commit()
            
            logger.info(f"Reset traffic for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting traffic: {str(e)}")
            raise
    
    async def change_server(
        self,
        account_id: str,
        new_location_id: str,
        db: Any
    ) -> VPNAccount:
        """Change the server location for a VPN account."""
        try:
            account = db.query(VPNAccount).filter(VPNAccount.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Get new server
            new_server = db.query(Server).filter(
                Server.location_id == new_location_id,
                Server.is_active == True
            ).first()
            
            if not new_server:
                raise HTTPException(
                    status_code=404,
                    detail="No available servers in selected location"
                )
            
            # Migrate account in panel
            panel_response = await self.panel_client.migrate_client(
                old_server_id=account.server_id,
                new_server_id=new_server.id,
                account_id=account_id
            )
            
            if not panel_response.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to migrate account in VPN panel"
                )
            
            # Update account server
            account.server_id = new_server.id
            db.commit()
            
            logger.info(f"Migrated account {account_id} to new server")
            return account
            
        except Exception as e:
            logger.error(f"Error changing server: {str(e)}")
            raise
    
    async def get_available_locations(self, db: Any) -> List[Dict[str, Any]]:
        """Get list of available server locations."""
        try:
            locations = db.query(Server.location_id).distinct().all()
            return [
                {
                    "id": location[0],
                    "name": location[0].replace("_", " ").title(),
                    "server_count": db.query(Server).filter(
                        Server.location_id == location[0],
                        Server.is_active == True
                    ).count()
                }
                for location in locations
            ]
            
        except Exception as e:
            logger.error(f"Error getting available locations: {str(e)}")
            raise

    async def get_renewal_plans(self, db: Any) -> List[Dict[str, Any]]:
        """
        Get available renewal plans for VPN subscriptions.
        
        Args:
            db: Database session
            
        Returns:
            List of available renewal plans
        """
        try:
            plans = db.query(Plan).filter(Plan.is_active == True).all()
            return [
                {
                    "id": plan.id,
                    "name": plan.name,
                    "price": plan.price,
                    "duration": plan.duration,
                    "traffic_limit": plan.traffic_limit,
                    "description": plan.description
                }
                for plan in plans
            ]
        except Exception as e:
            logger.error(f"Error getting renewal plans: {str(e)}")
            raise

    async def renew_subscription(
        self,
        user_id: int,
        plan_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """
        Renew a user's VPN subscription.
        
        Args:
            user_id: Telegram user ID
            plan_id: Selected plan ID
            db: Database session
            
        Returns:
            Dict containing renewal status and details
        """
        try:
            # Get user's current account
            account = await self.vpn_account_service.get_by_user_id(user_id)
            if not account:
                raise HTTPException(
                    status_code=404,
                    detail="No active VPN account found"
                )
            
            # Get selected plan
            plan = db.query(Plan).filter(Plan.id == plan_id).first()
            if not plan:
                raise HTTPException(
                    status_code=404,
                    detail="Selected plan not found"
                )
            
            # Calculate new expiry date
            current_expiry = account.expiry_date
            if current_expiry > datetime.utcnow():
                # Add to current expiry if subscription is still active
                new_expiry = current_expiry + timedelta(days=plan.duration)
            else:
                # Start from current date if subscription is expired
                new_expiry = datetime.utcnow() + timedelta(days=plan.duration)
            
            # Update account in panel
            panel_response = await self.panel_client.update_client(
                server_id=account.server_id,
                account_id=account.id,
                expiry_date=new_expiry,
                traffic_limit=plan.traffic_limit
            )
            
            if not panel_response.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update account in VPN panel"
                )
            
            # Update account in database
            account.expiry_date = new_expiry
            account.traffic_limit = plan.traffic_limit
            account.traffic_used = 0  # Reset traffic usage
            db.commit()
            
            return {
                "success": True,
                "message": (
                    f"✅ اشتراک شما با موفقیت تمدید شد!\n\n"
                    f"📅 تاریخ انقضای جدید: {new_expiry.strftime('%Y-%m-%d')}\n"
                    f"📊 ترافیک: {plan.traffic_limit / (1024 * 1024 * 1024):.2f}GB\n"
                    f"⏳ مدت زمان: {plan.duration} روز"
                ),
                "account": account
            }
            
        except Exception as e:
            logger.error(f"Error renewing subscription: {str(e)}")
            raise 