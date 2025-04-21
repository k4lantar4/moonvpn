"""
Transaction repository for database operations
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.transaction import Transaction

class TransactionRepository:
    """Repository for transaction database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        return await self.session.get(Transaction, transaction_id)
    
    async def get_user_transactions(self, user_id: int, limit: int = 5) -> List[Transaction]:
        """Get recent transactions for a user"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_transaction(self, transaction_data: dict) -> Transaction:
        """Create a new transaction"""
        transaction = Transaction(**transaction_data)
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
    
    async def update_transaction_status(self, transaction_id: int, status: str) -> Optional[Transaction]:
        """Update transaction status"""
        transaction = await self.get_by_id(transaction_id)
        if transaction:
            transaction.status = status
            await self.session.commit()
            await self.session.refresh(transaction)
        return transaction
    
    async def get_transactions_by_type(self, user_id: int, type_: str) -> List[Transaction]:
        """Get transactions by type for a user"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.type == type_)
            .order_by(desc(Transaction.created_at))
        )
        return list(result.scalars().all())
    
    async def get_transactions_by_status(self, user_id: int, status: str) -> List[Transaction]:
        """Get transactions by status for a user"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.status == status)
            .order_by(desc(Transaction.created_at))
        )
        return list(result.scalars().all()) 