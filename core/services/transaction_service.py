from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.transaction import Transaction, TransactionStatus, TransactionType
from db.repositories.transaction_repository import TransactionRepository
from core.services.user_service import UserService


class TransactionService:
    """Service for handling transaction-related business logic."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repository = TransactionRepository(session)
        self.user_service = UserService(session)
    
    async def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: TransactionType,
        order_id: Optional[int] = None
    ) -> Transaction:
        """Create a new transaction and handle related business logic."""
        transaction = await self.transaction_repository.create_transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            order_id=order_id
        )
        
        # If it's a deposit, we'll update the user's balance immediately
        if type == TransactionType.DEPOSIT and transaction.status == TransactionStatus.SUCCESS:
            await self.user_service.update_balance(user_id, amount)
            
        return transaction
    
    async def get_user_transactions(
        self,
        user_id: int,
        status: Optional[TransactionStatus] = None,
        type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """Get all transactions for a user with optional filters."""
        return await self.transaction_repository.get_user_transactions(
            user_id=user_id,
            status=status,
            type=type
        )
    
    async def process_transaction(
        self,
        transaction_id: int,
        new_status: TransactionStatus
    ) -> Optional[Transaction]:
        """Process a transaction by updating its status and handling related logic."""
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None
            
        # Update transaction status
        updated_transaction = await self.transaction_repository.update_transaction_status(
            transaction_id=transaction_id,
            status=new_status
        )
        
        if new_status == TransactionStatus.SUCCESS:
            # Handle successful transaction
            if transaction.type == TransactionType.DEPOSIT:
                await self.user_service.update_balance(
                    transaction.user_id,
                    transaction.amount
                )
            elif transaction.type == TransactionType.WITHDRAWAL:
                await self.user_service.update_balance(
                    transaction.user_id,
                    -transaction.amount
                )
                
        return updated_transaction
    
    async def get_pending_transactions(self) -> List[Transaction]:
        """Get all pending transactions."""
        return await self.transaction_repository.get_pending_transactions()
    
    async def get_order_transactions(self, order_id: int) -> List[Transaction]:
        """Get all successful transactions for a specific order."""
        return await self.transaction_repository.get_successful_transactions_by_order(order_id)
    
    async def calculate_total_paid_for_order(self, order_id: int) -> float:
        """Calculate total amount paid for an order through successful transactions."""
        transactions = await self.get_order_transactions(order_id)
        return sum(t.amount for t in transactions) 