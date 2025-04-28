"""
Transaction repository for database operations
"""

from typing import List, Optional, Union
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from db.models.transaction import Transaction

class TransactionRepository:
    """Repository for transaction database operations"""
    
    def __init__(self, session: Union[AsyncSession, Session]):
        self.session = session
        self._is_async = isinstance(session, AsyncSession)
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        if self._is_async:
            return self._get_by_id_async(transaction_id)
        else:
            return self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    async def _get_by_id_async(self, transaction_id: int) -> Optional[Transaction]:
        """Async version of get_by_id"""
        return await self.session.get(Transaction, transaction_id)
    
    def get_user_transactions(self, user_id: int, limit: int = 5) -> List[Transaction]:
        """Get recent transactions for a user"""
        if self._is_async:
            return self._get_user_transactions_async(user_id, limit)
        else:
            return self.session.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(
                desc(Transaction.created_at)
            ).limit(limit).all()
    
    async def _get_user_transactions_async(self, user_id: int, limit: int = 5) -> List[Transaction]:
        """Async version of get_user_transactions"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    def create_transaction(self, transaction_data: dict) -> Transaction:
        """Create a new transaction"""
        if self._is_async:
            return self._create_transaction_async(transaction_data)
        else:
            transaction = Transaction(**transaction_data)
            self.session.add(transaction)
            self.session.flush()
            return transaction
    
    async def _create_transaction_async(self, transaction_data: dict) -> Transaction:
        """Async version of create_transaction"""
        transaction = Transaction(**transaction_data)
        self.session.add(transaction)
        await self.session.flush()
        return transaction
    
    def update_transaction_status(self, transaction_id: int, status: str) -> Optional[Transaction]:
        """Update transaction status"""
        if self._is_async:
            return self._update_transaction_status_async(transaction_id, status)
        else:
            transaction = self.get_by_id(transaction_id)
            if transaction:
                transaction.status = status
                self.session.flush()
            return transaction
    
    async def _update_transaction_status_async(self, transaction_id: int, status: str) -> Optional[Transaction]:
        """Async version of update_transaction_status"""
        transaction = await self.get_by_id(transaction_id)
        if transaction:
            transaction.status = status
            await self.session.flush()
        return transaction
    
    def get_transactions_by_type(self, user_id: int, type_: str) -> List[Transaction]:
        """Get transactions by type for a user"""
        if self._is_async:
            return self._get_transactions_by_type_async(user_id, type_)
        else:
            return self.session.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.type == type_
            ).order_by(
                desc(Transaction.created_at)
            ).all()
    
    async def _get_transactions_by_type_async(self, user_id: int, type_: str) -> List[Transaction]:
        """Async version of get_transactions_by_type"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.type == type_)
            .order_by(desc(Transaction.created_at))
        )
        return list(result.scalars().all())
    
    def get_transactions_by_status(self, user_id: int, status: str) -> List[Transaction]:
        """Get transactions by status for a user"""
        if self._is_async:
            return self._get_transactions_by_status_async(user_id, status)
        else:
            return self.session.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.status == status
            ).order_by(
                desc(Transaction.created_at)
            ).all()
    
    async def _get_transactions_by_status_async(self, user_id: int, status: str) -> List[Transaction]:
        """Async version of get_transactions_by_status"""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.status == status)
            .order_by(desc(Transaction.created_at))
        )
        return list(result.scalars().all()) 