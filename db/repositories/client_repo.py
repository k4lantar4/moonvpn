"""
Client account repository for database operations
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.client_account import ClientAccount, AccountStatus
from .base_repository import BaseRepository

class ClientRepository(BaseRepository[ClientAccount]):
    """Repository for client account database operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ClientAccount)
    
    async def get_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """Get client account by ID"""
        return await super().get_by_id(account_id)
    
    async def get_active_accounts_by_user_id(self, user_id: int) -> List[ClientAccount]:
        """Get all active accounts for a user"""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.status == AccountStatus.ACTIVE,
                self.model.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_account(self, account_data: dict) -> ClientAccount:
        """Create a new client account"""
        return await super().create(account_data)
    
    async def update_account_status(self, account_id: int, status: AccountStatus) -> Optional[ClientAccount]:
        """Update account status"""
        return await super().update(account_id, {"status": status})
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete a client account"""
        return await super().delete(account_id)
    
    async def get_expired_accounts(self) -> List[ClientAccount]:
        """Get all expired accounts"""
        query = select(self.model).where(
            and_(
                self.model.status == AccountStatus.ACTIVE,
                self.model.expires_at <= datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_accounts_by_panel_id(self, panel_id: int) -> List[ClientAccount]:
        """Get all accounts for a panel"""
        query = select(self.model).where(self.model.panel_id == panel_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_account_traffic(self, account_id: int, traffic_used: int) -> Optional[ClientAccount]:
        """Update account traffic usage"""
        return await super().update(account_id, {"traffic_used": traffic_used}) 