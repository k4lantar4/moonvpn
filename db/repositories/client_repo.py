"""
Client account repository for database operations
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.client_account import ClientAccount

class ClientRepository:
    """Repository for client account database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, account_id: int) -> Optional[ClientAccount]:
        """Get client account by ID"""
        return await self.session.get(ClientAccount, account_id)
    
    async def get_active_accounts_by_user_id(self, user_id: int) -> List[ClientAccount]:
        """Get all active accounts for a user"""
        result = await self.session.execute(
            select(ClientAccount).where(
                and_(
                    ClientAccount.user_id == user_id,
                    ClientAccount.status == "active",
                    ClientAccount.expires_at > datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())
    
    async def create_account(self, account_data: dict) -> ClientAccount:
        """Create a new client account"""
        account = ClientAccount(**account_data)
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def update_account_status(self, account_id: int, status: str) -> Optional[ClientAccount]:
        """Update account status"""
        account = await self.get_by_id(account_id)
        if account:
            account.status = status
            await self.session.commit()
            await self.session.refresh(account)
        return account
    
    async def delete_account(self, account_id: int) -> bool:
        """Delete a client account"""
        account = await self.get_by_id(account_id)
        if account:
            await self.session.delete(account)
            await self.session.commit()
            return True
        return False
    
    async def get_expired_accounts(self) -> List[ClientAccount]:
        """Get all expired accounts"""
        result = await self.session.execute(
            select(ClientAccount).where(
                and_(
                    ClientAccount.status == "active",
                    ClientAccount.expires_at <= datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_accounts_by_panel_id(self, panel_id: int) -> List[ClientAccount]:
        """Get all accounts for a panel"""
        result = await self.session.execute(
            select(ClientAccount).where(ClientAccount.panel_id == panel_id)
        )
        return list(result.scalars().all())
    
    async def update_account_traffic(self, account_id: int, traffic_used: int) -> Optional[ClientAccount]:
        """Update account traffic usage"""
        account = await self.get_by_id(account_id)
        if account:
            account.traffic_used = traffic_used
            await self.session.commit()
            await self.session.refresh(account)
        return account 