"""
Payment repository for MoonVPN.

This module contains the Payment repository class that handles database operations for payments.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.payment import Payment
from app.models.payment import Payment as PaymentSchema

class PaymentRepository(BaseRepository[Payment]):
    """Payment repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Payment, session)
    
    async def get_by_telegram_id(self, telegram_id: int) -> List[Payment]:
        """Get all payments for a user by Telegram ID."""
        query = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_authority(self, authority: str) -> Optional[Payment]:
        """Get a payment by authority token."""
        query = select(self.model).where(self.model.authority == authority)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get a payment by transaction ID."""
        query = select(self.model).where(self.model.transaction_id == transaction_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_pending_payments(self) -> List[Payment]:
        """Get all pending payments."""
        query = select(self.model).where(self.model.status == "pending")
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, payment: PaymentSchema) -> Payment:
        """Create a payment from a Pydantic schema."""
        payment_data = payment.model_dump(exclude={"id"})
        return await self.create(payment_data)
    
    async def update_status(
        self,
        payment_id: int,
        status: str,
        transaction_id: Optional[str] = None
    ) -> Optional[Payment]:
        """Update a payment's status and transaction ID."""
        payment = await self.get(payment_id)
        if payment:
            update_data = {"status": status}
            if transaction_id:
                update_data["transaction_id"] = transaction_id
            return await self.update(db_obj=payment, obj_in=update_data)
        return None
    
    async def get_user_payment_stats(self, telegram_id: int) -> dict:
        """Get payment statistics for a user."""
        query = select(self.model).where(
            self.model.telegram_id == telegram_id,
            self.model.status == "completed"
        )
        result = await self.session.execute(query)
        payments = list(result.scalars().all())
        
        total_amount = sum(payment.amount for payment in payments)
        total_payments = len(payments)
        
        return {
            "total_amount": total_amount,
            "total_payments": total_payments,
            "average_amount": total_amount / total_payments if total_payments > 0 else 0
        } 