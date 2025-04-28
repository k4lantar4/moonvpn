# سرویس مدیریت تنظیمات پویا

"""
سرویس مدیریت تنظیمات پویای سیستم
"""

import logging
import json
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.setting_repo import SettingRepository

logger = logging.getLogger(__name__)


class SettingsService:
    """سرویس مدیریت تنظیمات پویای سیستم با پشتیبانی از انواع داده متنوع"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.repository = SettingRepository(session)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        دریافت مقدار تنظیمات با کلید مشخص
        
        Args:
            key: کلید تنظیمات
            default: مقدار پیش‌فرض در صورت عدم وجود
            
        Returns:
            مقدار تنظیمات با نوع مناسب
        """
        try:
            return await self.repository.get_value(key, default)
        except Exception as e:
            logger.error(f"Error getting setting {key}: {str(e)}")
            return default
    
    # Alias for get() method for compatibility
    async def get_setting_value(self, key: str, default: Any = None) -> Any:
        """
        دریافت مقدار تنظیمات با کلید مشخص (نام مستعار برای متد get)
        
        Args:
            key: کلید تنظیمات
            default: مقدار پیش‌فرض در صورت عدم وجود
            
        Returns:
            مقدار تنظیمات با نوع مناسب
        """
        return await self.get(key, default)
    
    async def set(self, key: str, value: Any, setting_type: Optional[str] = None, 
                 scope: str = 'system', description: Optional[str] = None) -> bool:
        """
        تنظیم یا بروزرسانی مقدار
        
        Args:
            key: کلید تنظیمات
            value: مقدار برای ذخیره
            setting_type: نوع داده (str, int, float, bool, json)
            scope: دامنه تنظیمات (system, bot, panel, payment)
            description: توضیحات
            
        Returns:
            موفقیت‌آمیز بودن عملیات
        """
        try:
            await self.repository.set_value(key, value, setting_type, scope, description)
            return True
        except Exception as e:
            logger.error(f"Error setting value for {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        حذف تنظیمات با کلید مشخص
        
        Args:
            key: کلید تنظیمات
            
        Returns:
            موفقیت‌آمیز بودن عملیات
        """
        try:
            return await self.repository.delete_setting(key)
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {str(e)}")
            return False
    
    async def get_all_by_scope(self, scope: str) -> Dict[str, Any]:
        """
        دریافت همه تنظیمات در یک دامنه مشخص
        
        Args:
            scope: دامنه تنظیمات (system, bot, panel, payment)
            
        Returns:
            دیکشنری از تنظیمات
        """
        try:
            settings = await self.repository.get_settings_by_scope(scope)
            result = {}
            
            for setting in settings:
                # استفاده از تابع get_value برای تبدیل مقدار به نوع مناسب
                result[setting.key] = await self.repository.get_value(setting.key)
                
            return result
        except Exception as e:
            logger.error(f"Error getting settings for scope {scope}: {str(e)}")
            return {}
    
    async def get_bot_settings(self) -> Dict[str, Any]:
        """
        دریافت تنظیمات مربوط به بات
        
        Returns:
            دیکشنری از تنظیمات بات
        """
        return await self.get_all_by_scope('bot')
    
    async def get_panel_settings(self) -> Dict[str, Any]:
        """
        دریافت تنظیمات مربوط به پنل
        
        Returns:
            دیکشنری از تنظیمات پنل
        """
        return await self.get_all_by_scope('panel')
    
    async def get_payment_settings(self) -> Dict[str, Any]:
        """
        دریافت تنظیمات مربوط به پرداخت
        
        Returns:
            دیکشنری از تنظیمات پرداخت
        """
        return await self.get_all_by_scope('payment')
    
    async def update_bot_settings(self, settings: Dict[str, Any]) -> bool:
        """
        بروزرسانی تنظیمات بات با یک دیکشنری
        
        Args:
            settings: دیکشنری تنظیمات
            
        Returns:
            موفقیت‌آمیز بودن عملیات
        """
        success = True
        for key, value in settings.items():
            if not await self.set(key, value, scope='bot'):
                success = False
        return success
