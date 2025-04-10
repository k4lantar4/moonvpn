"""Repository for Wallet model operations."""

import logging
from typing import Optional, Sequence, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.wallet import Wallet
from core.database.repositories.base_repo import BaseRepository
from core.schemas.wallet import WalletCreate, WalletUpdate # Schemas now exist in the proper location

logger = logging.getLogger(__name__)

class WalletRepository(BaseRepository[Wallet, WalletCreate, WalletUpdate]):
    """Repository for interacting with Wallet data in the database."""

    def __init__(self):
        super().__init__(model=Wallet)

    async def get_by_user_id(self, db_session: AsyncSession, *, user_id: int) -> Optional[Wallet]:
        """Get a wallet by its associated user ID."""
        stmt = select(self._model).where(self._model.user_id == user_id)
        result = await db_session.execute(stmt)
        return result.scalars().first()

    # Add other specific Wallet methods if needed, e.g.:
    # async def increment_balance(self, db_session: AsyncSession, wallet_id: int, amount: Decimal) -> Wallet:
    #     ...
    # async def decrement_balance(self, db_session: AsyncSession, wallet_id: int, amount: Decimal) -> Wallet:
    #     ... 