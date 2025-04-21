from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.transaction import Transaction, TransactionStatus, TransactionType
from db.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for handling Transaction model database operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Transaction)
    
    async def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: TransactionType,
        order_id: Optional[int] = None,
        status: TransactionStatus = TransactionStatus.PENDING
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            order_id=order_id,
            status=status
        )
        return await self.create(transaction)
    
    async def get_user_transactions(
        self,
        user_id: int,
        status: Optional[TransactionStatus] = None,
        type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """Get all transactions for a specific user with optional filters."""
        conditions = [Transaction.user_id == user_id]
        
        if status:
            conditions.append(Transaction.status == status)
        if type:
            conditions.append(Transaction.type == type)
            
        query = select(Transaction).where(and_(*conditions))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_transaction_status(
        self,
        transaction_id: int,
        status: TransactionStatus
    ) -> Optional[Transaction]:
        """Update the status of a transaction."""
        transaction = await self.get_by_id(transaction_id)
        if transaction:
            transaction.status = status
            return await self.update(transaction)
        return None
    
    async def get_pending_transactions(self) -> List[Transaction]:
        """Get all pending transactions."""
        query = select(Transaction).where(Transaction.status == TransactionStatus.PENDING)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_successful_transactions_by_order(self, order_id: int) -> List[Transaction]:
        """Get all successful transactions for a specific order."""
        query = select(Transaction).where(
            and_(
                Transaction.order_id == order_id,
                Transaction.status == TransactionStatus.SUCCESS
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()) 