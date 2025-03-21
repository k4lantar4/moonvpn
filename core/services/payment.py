"""
Payment service for MoonVPN.

This module contains the payment service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.db.repositories.payment import PaymentRepository
from app.db.repositories.user import UserRepository
from app.models.payment import Payment, PaymentCreate, PaymentUpdate
from app.core.config import settings

class PaymentService:
    """Payment service class."""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository
    ):
        """Initialize service."""
        self.payment_repository = payment_repository
        self.user_repository = user_repository
    
    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get a payment by ID."""
        return await self.payment_repository.get(payment_id)
    
    async def get_by_telegram_id(self, telegram_id: int) -> List[Payment]:
        """Get all payments for a user by Telegram ID."""
        return await self.payment_repository.get_by_telegram_id(telegram_id)
    
    async def get_by_authority(self, authority: str) -> Optional[Payment]:
        """Get a payment by authority token."""
        return await self.payment_repository.get_by_authority(authority)
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get a payment by transaction ID."""
        return await self.payment_repository.get_by_transaction_id(transaction_id)
    
    async def get_pending_payments(self) -> List[Payment]:
        """Get all pending payments."""
        return await self.payment_repository.get_pending_payments()
    
    async def create(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment."""
        # Check if user exists
        user = await self.user_repository.get_by_telegram_id(payment_data.telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create payment
        payment_dict = payment_data.model_dump()
        payment_dict["created_at"] = datetime.utcnow()
        payment_dict["status"] = "pending"
        
        return await self.payment_repository.create(payment_dict)
    
    async def update(self, payment_id: int, payment_data: PaymentUpdate) -> Optional[Payment]:
        """Update a payment."""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        update_data = payment_data.model_dump(exclude_unset=True)
        return await self.payment_repository.update(db_obj=payment, obj_in=update_data)
    
    async def delete(self, payment_id: int) -> bool:
        """Delete a payment."""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return await self.payment_repository.delete(payment)
    
    async def update_status(
        self,
        payment_id: int,
        status: str,
        transaction_id: Optional[str] = None
    ) -> Optional[Payment]:
        """Update a payment's status and transaction ID."""
        payment = await self.get_by_id(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return await self.payment_repository.update_status(payment_id, status, transaction_id)
    
    async def get_payment_stats(self, telegram_id: int) -> dict:
        """Get payment statistics for a user."""
        return await self.payment_repository.get_user_payment_stats(telegram_id)
    
    async def verify_payment(self, authority: str) -> bool:
        """Verify a payment using the payment gateway."""
        payment = await self.get_by_authority(authority)
        if not payment:
            return False
        
        # TODO: Implement payment gateway verification
        # This is a placeholder for the actual payment gateway integration
        return True
    
    async def process_payment_callback(self, authority: str, transaction_id: str) -> Optional[Payment]:
        """Process a payment callback from the payment gateway."""
        payment = await self.get_by_authority(authority)
        if not payment:
            return None
        
        # Update payment status
        return await self.update_status(payment.id, "completed", transaction_id) 