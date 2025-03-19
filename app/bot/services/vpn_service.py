"""
VPN Service for MoonVPN Telegram Bot.

This module handles VPN account management, server interactions,
and account status monitoring.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException

from app.core.config import settings
from app.bot.utils.logger import setup_logger
from app.core.database.models import VPNAccount, Server, User
from app.core.database.session import get_db
from app.core.services.panel_client import PanelClient

# Initialize logger
logger = setup_logger(__name__)

class VPNService:
    """Service for managing VPN accounts and server interactions."""
    
    def __init__(self):
        """Initialize the VPN service."""
        self.panel_client = PanelClient()
    
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
    
    async def get_account_status(
        self,
        account_id: str,
        db: Any
    ) -> Dict[str, Any]:
        """Get the current status of a VPN account."""
        try:
            account = db.query(VPNAccount).filter(VPNAccount.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Get status from panel
            panel_status = await self.panel_client.get_client_status(
                server_id=account.server_id,
                account_id=account_id
            )
            
            # Update account status
            account.status = panel_status.get("status", account.status)
            account.traffic_used = panel_status.get("traffic_used", account.traffic_used)
            account.last_check = datetime.utcnow()
            
            db.commit()
            
            return {
                "id": account.id,
                "status": account.status,
                "traffic_limit": account.traffic_limit,
                "traffic_used": account.traffic_used,
                "expires_at": account.expires_at,
                "server_location": account.server.location.name
            }
            
        except Exception as e:
            logger.error(f"Error getting account status: {str(e)}")
            raise
    
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