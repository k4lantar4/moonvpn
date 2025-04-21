"""
ریپوزیتوری برای عملیات پایگاه داده مربوط به تنظیمات
"""

import json
from typing import Optional, List, Any, Dict, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.setting import Setting
from .base_repository import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """ریپوزیتوری برای عملیات پایگاه داده تنظیمات"""

    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با جلسه دیتابیس"""
        super().__init__(session, Setting)
    
    async def get_setting(self, key: str) -> Optional[Setting]:
        """
        دریافت تنظیمات با کلید مشخص
        
        Args:
            key: کلید تنظیمات
            
        Returns:
            تنظیمات یافت شده یا None
        """
        query = select(Setting).where(Setting.key == key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_settings_by_scope(self, scope: str) -> List[Setting]:
        """
        دریافت همه تنظیمات در یک دامنه مشخص
        
        Args:
            scope: دامنه تنظیمات (system, bot, panel, payment)
            
        Returns:
            لیست تنظیمات
        """
        query = select(Setting).where(Setting.scope == scope)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """
        دریافت مقدار تنظیمات با تبدیل نوع خودکار
        
        Args:
            key: کلید تنظیمات
            default: مقدار پیش‌فرض در صورت عدم وجود
            
        Returns:
            مقدار تنظیمات با نوع مناسب
        """
        setting = await self.get_setting(key)
        if not setting:
            return default
        
        # تبدیل مقدار به نوع مناسب
        if setting.type == 'int':
            return int(setting.value)
        elif setting.type == 'float':
            return float(setting.value)
        elif setting.type == 'bool':
            return setting.value.lower() in ('true', '1', 'yes')
        elif setting.type == 'json':
            return json.loads(setting.value)
        
        # پیش‌فرض: به عنوان رشته برگردانده می‌شود
        return setting.value
    
    async def set_value(self, key: str, value: Any, setting_type: Optional[str] = None, 
                       scope: str = 'system', description: Optional[str] = None) -> Setting:
        """
        تنظیم یا بروزرسانی مقدار
        
        Args:
            key: کلید تنظیمات
            value: مقدار برای ذخیره
            setting_type: نوع داده (str, int, float, bool, json)
            scope: دامنه تنظیمات (system, bot, panel, payment)
            description: توضیحات
            
        Returns:
            تنظیمات ذخیره شده
        """
        # تشخیص خودکار نوع در صورت عدم تعیین
        if setting_type is None:
            if isinstance(value, bool):
                setting_type = 'bool'
                str_value = 'true' if value else 'false'
            elif isinstance(value, int):
                setting_type = 'int'
                str_value = str(value)
            elif isinstance(value, float):
                setting_type = 'float'
                str_value = str(value)
            elif isinstance(value, (dict, list)):
                setting_type = 'json'
                str_value = json.dumps(value)
            else:
                setting_type = 'str'
                str_value = str(value)
        else:
            # تبدیل به رشته برای ذخیره
            if setting_type == 'json':
                str_value = json.dumps(value)
            elif setting_type == 'bool':
                str_value = 'true' if value else 'false'
            else:
                str_value = str(value)
        
        # بررسی وجود تنظیمات فعلی
        setting = await self.get_setting(key)
        
        if setting:
            # بروزرسانی تنظیمات موجود
            setting.value = str_value
            setting.type = setting_type
            
            # بروزرسانی اختیاری فیلدهای دیگر
            if description is not None:
                setting.description = description
            if scope is not None:
                setting.scope = scope
                
            await self.session.commit()
            return setting
        else:
            # ایجاد تنظیمات جدید
            new_setting = Setting(
                key=key,
                value=str_value,
                type=setting_type,
                scope=scope,
                description=description
            )
            
            self.session.add(new_setting)
            await self.session.commit()
            await self.session.refresh(new_setting)
            return new_setting
    
    async def delete_setting(self, key: str) -> bool:
        """
        حذف تنظیمات با کلید مشخص
        
        Args:
            key: کلید تنظیمات
            
        Returns:
            موفقیت‌آمیز بودن عملیات
        """
        setting = await self.get_setting(key)
        if setting:
            await self.session.delete(setting)
            await self.session.commit()
            return True
        return False 