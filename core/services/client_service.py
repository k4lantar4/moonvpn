"""
Client service for managing VPN client accounts
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.client_repo import ClientRepository
from db.models.client_account import ClientAccount

class ClientService:
    """Service for managing VPN client accounts"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.client_repo = ClientRepository(session)
    
    async def get_user_active_accounts(self, user_id: int) -> List[ClientAccount]:
        """Get all active VPN accounts for a user"""
        return await self.client_repo.get_active_accounts_by_user_id(user_id)
    
    async def get_account_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """Get a client account by ID"""
        return await self.client_repo.get_by_id(account_id)
    
    async def create_client_account(self, user_id: int, panel_id: int, inbound_id: int, plan_id: int) -> ClientAccount:
        """Create a new client account"""
        return await self.client_repo.create_account(
            user_id=user_id,
            panel_id=panel_id,
            inbound_id=inbound_id,
            plan_id=plan_id,
            status="active",
            created_at=datetime.utcnow()
        )
    
    async def update_account_status(self, account_id: int, status: str) -> Optional[ClientAccount]:
        """Update account status"""
        return await self.client_repo.update_account_status(account_id, status)
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete a client account"""
        return await self.client_repo.delete_account(account_id)
    
    async def get_expired_accounts(self) -> List[ClientAccount]:
        """Get all expired accounts"""
        return await self.client_repo.get_expired_accounts()
    
    async def get_accounts_by_panel(self, panel_id: int) -> List[ClientAccount]:
        """Get all accounts for a panel"""
        return await self.client_repo.get_accounts_by_panel_id(panel_id)
    
    async def update_account_traffic(self, account_id: int, traffic_used: int) -> Optional[ClientAccount]:
        """Update account traffic usage"""
        return await self.client_repo.update_account_traffic(account_id, traffic_used) 