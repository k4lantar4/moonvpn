"""
Transaction Service for logging all financial operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.transaction_repo import TransactionRepository
from db.models.transaction import Transaction  # Keep for type hinting if needed
from db.models.enums import TransactionStatus, PaymentMethod # Import enums
from db.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionSchema

class TransactionService:
    """Service for creating and managing financial transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = TransactionRepository(session)

    async def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: str, # e.g., 'deposit', 'withdrawal', 'purchase', 'refund'
        status: str, # e.g., 'pending', 'completed', 'failed'
        description: Optional[str] = None,
        payment_method: Optional[str] = None, # Added parameter
        related_entity_id: Optional[int] = None, # e.g., order_id
        related_entity_type: Optional[str] = None # e.g., 'order'
    ) -> Optional[TransactionSchema]:
        """
        Creates a new transaction record.
        Does not modify user balance - that's WalletService's job.
        """
        transaction_data = TransactionCreate(
            user_id=user_id,
            amount=amount,
            type=type,
            status=status,
            description=description or f"{type.capitalize()} transaction",
            payment_method=payment_method, # Pass to schema
            created_at=datetime.utcnow(),
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type
        )
        # The repository handles the creation and session.add()
        # Use the correct repository method (_create_transaction_async for async session)
        transaction = await self.transaction_repo._create_transaction_async(transaction_data.model_dump())
        if transaction:
            # Convert the ORM model to the Pydantic schema before returning
            return TransactionSchema.model_validate(transaction)
        return None
        # No commit here

    async def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionSchema]:
        """Get transaction by ID."""
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if transaction:
            return TransactionSchema.from_orm(transaction)
        return None

    async def get_user_transactions(self, user_id: int, limit: int = 10, offset: int = 0) -> List[TransactionSchema]:
        """Get transactions for a specific user."""
        transactions = await self.transaction_repo.get_by_user_id(user_id, limit=limit, offset=offset)
        return [TransactionSchema.from_orm(t) for t in transactions]

    async def update_transaction_status(
        self, 
        transaction_id: int, 
        status: TransactionStatus, 
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TransactionSchema]:
        """Update the status of a transaction."""
        update_data = TransactionUpdate(status=status, description=description, metadata=metadata)
        # The repository handles the update logic
        updated_transaction = await self.transaction_repo.update(transaction_id, update_data)
        if updated_transaction:
             return TransactionSchema.from_orm(updated_transaction)
        return None
        # No commit here

    async def find_by_related_entity(self, entity_id: int, entity_type: str) -> List[TransactionSchema]:
        """Find transactions related to a specific entity (e.g., an order)."""
        transactions = await self.transaction_repo.find_by_related_entity(entity_id, entity_type)
        return [TransactionSchema.from_orm(t) for t in transactions] 