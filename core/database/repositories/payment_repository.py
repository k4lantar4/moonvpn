"""Repository for Payment model operations."""

import logging
from typing import Optional, Sequence, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.payment import Payment, PaymentStatus, PaymentType # Assuming enums are in model
from core.database.repositories.base_repo import BaseRepository
from core.schemas.payment import PaymentCreate, PaymentUpdate # Assuming schemas exist or will be created
from pydantic import BaseModel # For placeholder schemas
from decimal import Decimal # For placeholder schemas

logger = logging.getLogger(__name__)

class PaymentRepository(BaseRepository[Payment, PaymentCreate, PaymentUpdate]):
    """Repository for interacting with Payment data in the database."""

    def __init__(self):
        super().__init__(model=Payment)

    async def get_by_reference_id(self, db_session: AsyncSession, *, reference_id: str) -> Optional[Payment]:
        """Get a payment by its reference ID."""
        stmt = select(self._model).where(self._model.reference_id == reference_id)
        result = await db_session.execute(stmt)
        return result.scalars().first()

    async def get_user_payments(self, db_session: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get payments for a specific user with pagination."""
        stmt = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc()) # Order by most recent
            .offset(skip)
            .limit(limit)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()

    async def get_pending_card_payments(self, db_session: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get pending card payments (card or wallet_charge type) for admin review."""
        stmt = (
            select(self._model)
            .where(
                self._model.status == PaymentStatus.PENDING,
                self._model.payment_type.in_([PaymentType.CARD, PaymentType.WALLET_CHARGE])
            )
            .order_by(self._model.created_at.asc()) # Order by oldest first
            .offset(skip)
            .limit(limit)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()

# Placeholder schemas (Create these in core/schemas/payment.py)
class PaymentCreate(BaseModel):
    user_id: int
    amount: Decimal
    payment_type: PaymentType
    status: PaymentStatus
    plan_id: Optional[int] = None
    bank_card_id: Optional[int] = None
    reference_id: Optional[str] = None
    transaction_id: Optional[str] = None

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    admin_id: Optional[int] = None # Assuming admin confirms payment
    transaction_id: Optional[str] = None 