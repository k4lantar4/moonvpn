"""Repository for BankCard model operations."""

import logging
from typing import Optional, Sequence, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.bank_card import BankCard
from core.database.repositories.base_repo import BaseRepository
from core.schemas.bank_card import BankCardCreate, BankCardUpdate # Assuming schemas exist or will be created
from pydantic import BaseModel # For placeholder schemas

logger = logging.getLogger(__name__)

class BankCardRepository(BaseRepository[BankCard, BankCardCreate, BankCardUpdate]):
    """Repository for interacting with BankCard data in the database."""

    def __init__(self):
        super().__init__(model=BankCard)

    async def get_active_cards(self, db_session: AsyncSession, *, skip: int = 0, limit: int = 100) -> Sequence[BankCard]:
        """Get all active bank cards."""
        stmt = (
            select(self._model)
            .where(self._model.is_active == True)
            .order_by(self._model.card_holder)
            .offset(skip)
            .limit(limit)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()

    # Add other specific methods if needed

# Placeholder schemas (Create these in core/schemas/bank_card.py)
class BankCardCreate(BaseModel):
    card_number: str
    card_holder: str
    bank_name: Optional[str] = None
    is_active: bool = True

class BankCardUpdate(BaseModel):
    card_number: Optional[str] = None
    card_holder: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = None 