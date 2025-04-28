"""
سرویس مدیریت کارت‌های بانکی
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.repositories.bank_card_repository import BankCardRepository
from db.models.bank_card import BankCard, RotationPolicy

logger = logging.getLogger(__name__)

class BankCardService:
    """سرویس مدیریت کارت‌های بانکی"""
    
    def __init__(self, session: AsyncSession):
        """
        راه‌اندازی سرویس با جلسه دیتابیس
        
        Args:
            session: جلسه ارتباط با دیتابیس
        """
        self.session = session
        self.repository = BankCardRepository(session)
    
    async def get_all_cards(self) -> List[BankCard]:
        """
        دریافت تمام کارت‌های بانکی
        
        Returns:
            List[BankCard]: لیست تمام کارت‌های بانکی
        """
        try:
            return await self.repository.get_all_cards()
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت لیست کارت‌های بانکی: {str(e)}")
            raise
    
    async def get_active_cards(self) -> List[BankCard]:
        """
        دریافت کارت‌های بانکی فعال
        
        Returns:
            List[BankCard]: لیست کارت‌های بانکی فعال
        """
        try:
            return await self.repository.get_active_cards()
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت لیست کارت‌های بانکی فعال: {str(e)}")
            raise
    
    async def get_card_by_id(self, card_id: int) -> Optional[BankCard]:
        """
        دریافت کارت بانکی با شناسه مشخص
        
        Args:
            card_id: شناسه کارت بانکی
            
        Returns:
            Optional[BankCard]: کارت بانکی یا None اگر یافت نشد
        """
        try:
            return await self.repository.get_by_id(card_id)
        except SQLAlchemyError as e:
            logger.error(f"خطا در دریافت کارت بانکی با شناسه {card_id}: {str(e)}")
            raise
    
    async def create_card(
        self, 
        card_number: str, 
        holder_name: str, 
        bank_name: str, 
        admin_user_id: int,
        is_active: bool = True,
        rotation_policy: str = "manual",
        rotation_interval_minutes: Optional[int] = None,
        telegram_channel_id: Optional[int] = None
    ) -> BankCard:
        """
        ایجاد کارت بانکی جدید
        
        Args:
            card_number: شماره کارت
            holder_name: نام دارنده کارت
            bank_name: نام بانک
            admin_user_id: شناسه کاربر ادمین
            is_active: وضعیت فعال بودن
            rotation_policy: سیاست چرخش
            rotation_interval_minutes: بازه زمانی چرخش
            telegram_channel_id: شناسه کانال تلگرام
            
        Returns:
            BankCard: کارت بانکی ایجاد شده
        """
        try:
            # تبدیل رشته سیاست چرخش به نوع شمارشی
            policy = RotationPolicy(rotation_policy)
            
            return await self.repository.create_card(
                card_number=card_number,
                holder_name=holder_name,
                bank_name=bank_name,
                admin_user_id=admin_user_id,
                is_active=is_active,
                rotation_policy=policy,
                rotation_interval_minutes=rotation_interval_minutes,
                telegram_channel_id=telegram_channel_id
            )
        except SQLAlchemyError as e:
            logger.error(f"خطا در ایجاد کارت بانکی: {str(e)}")
            raise
    
    async def update_card(self, card_id: int, update_data: Dict[str, Any]) -> Optional[BankCard]:
        """
        به‌روزرسانی کارت بانکی
        
        Args:
            card_id: شناسه کارت بانکی
            update_data: داده‌های به‌روزرسانی
            
        Returns:
            Optional[BankCard]: کارت بانکی به‌روزرسانی شده یا None اگر یافت نشد
        """
        try:
            # اگر سیاست چرخش در داده‌ها وجود داشت، آن را به نوع شمارشی تبدیل کنیم
            if 'rotation_policy' in update_data and isinstance(update_data['rotation_policy'], str):
                update_data['rotation_policy'] = RotationPolicy(update_data['rotation_policy'])
            
            return await self.repository.update_card(
                card_id=card_id,
                **update_data
            )
        except SQLAlchemyError as e:
            logger.error(f"خطا در به‌روزرسانی کارت بانکی با شناسه {card_id}: {str(e)}")
            raise
    
    async def toggle_card_status(self, card_id: int) -> Optional[BankCard]:
        """
        تغییر وضعیت فعال/غیرفعال کارت بانکی
        
        Args:
            card_id: شناسه کارت بانکی
            
        Returns:
            Optional[BankCard]: کارت بانکی به‌روزرسانی شده یا None اگر یافت نشد
        """
        try:
            return await self.repository.toggle_card_status(card_id)
        except SQLAlchemyError as e:
            logger.error(f"خطا در تغییر وضعیت کارت بانکی با شناسه {card_id}: {str(e)}")
            raise
    
    async def delete_card(self, card_id: int) -> bool:
        """
        حذف کارت بانکی
        
        Args:
            card_id: شناسه کارت بانکی
            
        Returns:
            bool: True اگر حذف موفقیت‌آمیز بود، False در غیر این صورت
        """
        try:
            return await self.repository.delete_card(card_id)
        except SQLAlchemyError as e:
            logger.error(f"خطا در حذف کارت بانکی با شناسه {card_id}: {str(e)}")
            raise 