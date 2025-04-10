from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repo import BaseRepository
from core.database.models.transaction import Transaction # Assuming model
from core.schemas.transaction import TransactionCreate, TransactionUpdate # Assuming schemas

class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self):
        super().__init__(Transaction) # Initialize with Transaction

    # Use AsyncSession
    async def get_by_user_id(
        self, db: AsyncSession, user_id: int, *, skip: int = 0, limit: int = 100
    ) -> List[Transaction]: # Return list of Transactions
        statement = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def find_by_reference_id(self, db: AsyncSession, reference_id: int) -> List[Transaction]:
        """Find transactions by their reference ID."""
        statement = select(self.model).where(self.model.reference_id == reference_id)
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_transactions_by_type(self, db: AsyncSession, user_id: int, transaction_type: str) -> List[Transaction]:
        """Get transactions for a user filtered by type."""
        statement = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.type == transaction_type) # Assuming type is stored as string/Enum value
            .order_by(desc(self.model.created_at))
        )
        result = await db.execute(statement)
        return result.scalars().all()

    # Add other transaction-specific query methods if needed
    # e.g., get_deposits, get_purchases, etc. 