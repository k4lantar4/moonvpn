from sqlalchemy import select
from db.models.bank_card import BankCard
from db.repositories.base_repository import BaseRepository

class BankCardRepository(BaseRepository):
    model = BankCard

    async def get_by_id(self, session, card_id: int) -> BankCard | None:
        stmt = select(self.model).where(self.model.id == card_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() 