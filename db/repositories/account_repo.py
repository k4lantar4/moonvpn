"""
ریپوزیتوری عملیات دیتابیسی مرتبط با اکانت‌ها
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models.client_account import ClientAccount, AccountStatus
from .base_repository import BaseRepository

class AccountRepository(BaseRepository[ClientAccount]):
    """ریپوزیتوری برای عملیات CRUD روی مدل ClientAccount"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با کلاس مدل ClientAccount"""
        super().__init__(session, ClientAccount)

    async def get_active_accounts(self) -> List[ClientAccount]:
        """دریافت تمام اکانت‌های فعال"""
        return await self.filter_by(is_active=True)

    async def get_active_by_user_id(self, user_id: int) -> List[ClientAccount]:
        """دریافت اکانت‌های فعال یک کاربر"""
        return await self.filter_by(user_id=user_id, status=AccountStatus.ACTIVE)

    async def get_user_accounts(self, user_id: int) -> List[ClientAccount]:
        """دریافت اکانت‌های یک کاربر"""
        return await self.filter_by(user_id=user_id)

    async def get_by_remote_uuid(self, remote_uuid: str) -> Optional[ClientAccount]:
        """دریافت اکانت با UUID پنل"""
        accounts = await self.filter_by(remote_uuid=remote_uuid)
        return accounts[0] if accounts else None

    async def get_accounts_by_inbound(self, inbound_id: int) -> List[ClientAccount]:
        """دریافت اکانت‌های یک اینباند"""
        return await self.filter_by(inbound_id=inbound_id)

    async def create_account(self, **kwargs) -> ClientAccount:
        """ایجاد اکانت جدید"""
        return await self.create(**kwargs)

    async def update_account(self, account_id: int, **kwargs) -> Optional[ClientAccount]:
        """به‌روزرسانی اکانت"""
        return await self.update(account_id, **kwargs)

    async def delete_account(self, account_id: int) -> bool:
        """
        حذف نرم اکانت (غیرفعال کردن)
        
        به جای حذف فیزیکی، اکانت را غیرفعال می‌کند
        """
        account = await self.get_by_id(account_id)
        if account:
            account.is_active = False
            await self.session.commit()
            return True
        return False
