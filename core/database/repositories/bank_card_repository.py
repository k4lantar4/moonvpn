"""Repository for BankCard model operations."""

import logging
from typing import Optional, Sequence, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.bank_card import BankCard
from core.database.repositories.base_repo import BaseRepository
from core.schemas.bank_card import BankCardCreate, BankCardUpdate # Schemas now exist in the proper location

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
            .order_by(self._model.owner_name) # Updated to match model field name
            .offset(skip)
            .limit(limit)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()

    # Add other specific methods if needed 