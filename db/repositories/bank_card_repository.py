from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from db.models.bank_card import BankCard, RotationPolicy
from db.repositories.base_repository import BaseRepository

class BankCardRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با جلسه دیتابیس و مدل"""
        super().__init__(session, BankCard)
    
    model = BankCard

    async def get_by_id(self, card_id: int) -> Optional[BankCard]:
        """دریافت کارت بانکی با شناسه مشخص"""
        stmt = select(self.model).where(self.model.id == card_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_cards(self) -> List[BankCard]:
        """دریافت تمام کارت‌های بانکی"""
        stmt = select(self.model).order_by(self.model.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_active_cards(self) -> List[BankCard]:
        """دریافت کارت‌های بانکی فعال"""
        stmt = select(self.model).where(self.model.is_active == True).order_by(self.model.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_card(
        self, 
        card_number: str, 
        holder_name: str, 
        bank_name: str, 
        admin_user_id: int,
        is_active: bool = True,
        rotation_policy: RotationPolicy = RotationPolicy.MANUAL,
        rotation_interval_minutes: Optional[int] = None,
        telegram_channel_id: Optional[int] = None
    ) -> BankCard:
        """ایجاد کارت بانکی جدید"""
        card = BankCard(
            card_number=card_number,
            holder_name=holder_name,
            bank_name=bank_name,
            admin_user_id=admin_user_id,
            is_active=is_active,
            rotation_policy=rotation_policy,
            rotation_interval_minutes=rotation_interval_minutes,
            telegram_channel_id=telegram_channel_id
        )
        self.session.add(card)
        await self.session.flush()
        await self.session.refresh(card)
        return card
    
    async def update_card(
        self, 
        card_id: int, 
        **kwargs
    ) -> Optional[BankCard]:
        """به‌روزرسانی کارت بانکی"""
        stmt = update(self.model).where(self.model.id == card_id).values(**kwargs).returning(self.model)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()
    
    async def toggle_card_status(self, card_id: int) -> Optional[BankCard]:
        """تغییر وضعیت فعال/غیرفعال کارت بانکی"""
        card = await self.get_by_id(card_id)
        if not card:
            return None
        
        # تغییر وضعیت
        card.is_active = not card.is_active
        await self.session.flush()
        return card
    
    async def delete_card(self, card_id: int) -> bool:
        """حذف کارت بانکی"""
        stmt = delete(self.model).where(self.model.id == card_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0 