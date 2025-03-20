"""
Discount code management service for MoonVPN.
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal

logger = logging.getLogger(__name__)

class DiscountService:
    """Handles discount code management."""
    
    def __init__(self):
        """Initialize the discount service."""
        self._discount_codes = self._load_discount_codes()
    
    def _load_discount_codes(self) -> List[Dict[str, Any]]:
        """Load discount codes from database or cache."""
        # در یک پیاده‌سازی واقعی، کدها از دیتابیس بارگذاری می‌شوند
        # اینجا داده‌های نمونه برای نمایش فانکشنالیتی بازگردانده می‌شوند
        
        today = datetime.datetime.now()
        
        return [
            {
                'id': 1,
                'code': 'NEWUSER25',
                'is_percentage': True,
                'value': 25,  # 25% تخفیف
                'max_uses': 100,
                'current_uses': 37,
                'min_purchase': 0,
                'max_discount': 500000,  # حداکثر 500,000 تومان تخفیف
                'start_date': (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
                'expiry_date': (today + datetime.timedelta(days=60)).strftime('%Y-%m-%d'),
                'is_active': True,
                'description': 'کد تخفیف کاربران جدید'
            },
            {
                'id': 2,
                'code': 'SUMMER50',
                'is_percentage': True,
                'value': 50,  # 50% تخفیف
                'max_uses': 50,
                'current_uses': 12,
                'min_purchase': 0,
                'max_discount': 750000,  # حداکثر 750,000 تومان تخفیف
                'start_date': (today - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
                'expiry_date': (today + datetime.timedelta(days=25)).strftime('%Y-%m-%d'),
                'is_active': True,
                'description': 'کمپین تابستانی'
            },
            {
                'id': 3,
                'code': 'FIX200K',
                'is_percentage': False,
                'value': 200000,  # 200,000 تومان تخفیف ثابت
                'max_uses': 30,
                'current_uses': 30,
                'min_purchase': 500000,  # حداقل خرید 500,000 تومان
                'max_discount': 200000,
                'start_date': (today - datetime.timedelta(days=60)).strftime('%Y-%m-%d'),
                'expiry_date': (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
                'is_active': False,
                'description': 'تخفیف ثابت ویژه'
            },
            {
                'id': 4,
                'code': 'VIP30',
                'is_percentage': True,
                'value': 30,  # 30% تخفیف
                'max_uses': 999,
                'current_uses': 0,
                'min_purchase': 1000000,  # حداقل خرید 1,000,000 تومان
                'max_discount': 0,  # بدون محدودیت
                'start_date': (today + datetime.timedelta(days=15)).strftime('%Y-%m-%d'),
                'expiry_date': (today + datetime.timedelta(days=45)).strftime('%Y-%m-%d'),
                'is_active': False,
                'description': 'کد تخفیف مشتریان ویژه'
            }
        ]
    
    def get_all_discount_codes(self) -> List[Dict[str, Any]]:
        """Get all discount codes.
        
        Returns:
            List of discount code dictionaries
        """
        return self._discount_codes
    
    def get_active_discount_codes(self) -> List[Dict[str, Any]]:
        """Get only active discount codes.
        
        Returns:
            List of active discount code dictionaries
        """
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        active_codes = []
        for code in self._discount_codes:
            if (code['is_active'] and 
                code['start_date'] <= today and 
                code['expiry_date'] >= today and
                (code['max_uses'] == 0 or code['current_uses'] < code['max_uses'])):
                active_codes.append(code)
        
        return active_codes
    
    def get_discount_code_by_id(self, code_id: int) -> Optional[Dict[str, Any]]:
        """Get discount code by ID.
        
        Args:
            code_id: The ID of the discount code
            
        Returns:
            Discount code dictionary or None if not found
        """
        for code in self._discount_codes:
            if code['id'] == code_id:
                return code
        return None
    
    def get_discount_code_by_code(self, code_text: str) -> Optional[Dict[str, Any]]:
        """Get discount code by code text.
        
        Args:
            code_text: The text of the discount code
            
        Returns:
            Discount code dictionary or None if not found
        """
        for code in self._discount_codes:
            if code['code'].upper() == code_text.upper():
                return code
        return None
    
    def create_discount_code(
        self, 
        code: str, 
        is_percentage: bool, 
        value: Union[int, float], 
        description: str, 
        expiry_date: str, 
        max_uses: int = 0, 
        min_purchase: int = 0, 
        max_discount: int = 0
    ) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Create a new discount code.
        
        Args:
            code: The discount code
            is_percentage: Whether the discount is a percentage or a fixed amount
            value: Discount value
            description: Description of the discount
            expiry_date: Expiry date (YYYY-MM-DD)
            max_uses: Maximum number of times the code can be used (0 for unlimited)
            min_purchase: Minimum purchase amount required
            max_discount: Maximum discount amount (0 for unlimited)
            
        Returns:
            Tuple of (success, result) where result is either the discount info or error message
        """
        try:
            # در یک پیاده‌سازی واقعی، اینجا کد در دیتابیس ذخیره می‌شود
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # بررسی یکتا بودن کد
            existing_code = self.get_discount_code_by_code(code)
            if existing_code:
                return False, "این کد تخفیف قبلاً تعریف شده است."
            
            # بررسی مقدار تخفیف
            if is_percentage and (value <= 0 or value > 100):
                return False, "درصد تخفیف باید بین 1 تا 100 باشد."
            elif not is_percentage and value <= 0:
                return False, "مقدار تخفیف ثابت باید بیشتر از صفر باشد."
            
            # تعیین شناسه جدید
            new_id = max([c['id'] for c in self._discount_codes], default=0) + 1
            
            # ساخت اطلاعات کد تخفیف
            discount_info = {
                'id': new_id,
                'code': code.upper(),
                'is_percentage': is_percentage,
                'value': value,
                'max_uses': max_uses,
                'current_uses': 0,
                'min_purchase': min_purchase,
                'max_discount': max_discount,
                'start_date': today,
                'expiry_date': expiry_date,
                'is_active': True,
                'description': description
            }
            
            # افزودن کد تخفیف به لیست کدها
            self._discount_codes.append(discount_info)
            
            # در یک پیاده‌سازی واقعی، اینجا کد در دیتابیس ذخیره می‌شود
            
            return True, discount_info
                
        except Exception as e:
            logger.error(f"Error creating discount code: {e}")
            return False, f"خطا در ایجاد کد تخفیف: {str(e)}"
    
    def update_discount_code(
        self,
        code_id: int,
        **kwargs
    ) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Update an existing discount code.
        
        Args:
            code_id: The ID of the discount code to update
            **kwargs: Fields to update
            
        Returns:
            Tuple of (success, result) where result is either the updated discount info or error message
        """
        try:
            # یافتن کد تخفیف با شناسه مورد نظر
            code = self.get_discount_code_by_id(code_id)
            if not code:
                return False, f"کد تخفیف با شناسه {code_id} یافت نشد."
            
            # بررسی و اعمال تغییرات
            for key, value in kwargs.items():
                if key in code:
                    # بررسی‌های اعتبارسنجی
                    if key == 'code' and value != code['code']:
                        # بررسی یکتا بودن کد جدید
                        existing_code = self.get_discount_code_by_code(value)
                        if existing_code and existing_code['id'] != code_id:
                            return False, "این کد تخفیف قبلاً برای کد تخفیف دیگری تعریف شده است."
                        code['code'] = value.upper()
                    elif key == 'value':
                        if code['is_percentage'] and (value <= 0 or value > 100):
                            return False, "درصد تخفیف باید بین 1 تا 100 باشد."
                        elif not code['is_percentage'] and value <= 0:
                            return False, "مقدار تخفیف ثابت باید بیشتر از صفر باشد."
                        code['value'] = value
                    elif key == 'is_percentage' and value != code['is_percentage']:
                        # اگر نوع تخفیف تغییر کرده، مقدار را بررسی کنیم
                        if value and (code['value'] <= 0 or code['value'] > 100):
                            return False, "برای تخفیف درصدی، مقدار باید بین 1 تا 100 باشد."
                        code['is_percentage'] = value
                    else:
                        code[key] = value
            
            # در یک پیاده‌سازی واقعی، اینجا تغییرات در دیتابیس ذخیره می‌شود
            
            return True, code
                
        except Exception as e:
            logger.error(f"Error updating discount code: {e}")
            return False, f"خطا در بروزرسانی کد تخفیف: {str(e)}"
    
    def delete_discount_code(self, code_id: int) -> Tuple[bool, str]:
        """Delete a discount code.
        
        Args:
            code_id: The ID of the discount code to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # یافتن کد تخفیف با شناسه مورد نظر
            for i, code in enumerate(self._discount_codes):
                if code['id'] == code_id:
                    # حذف کد از لیست
                    del self._discount_codes[i]
                    
                    # در یک پیاده‌سازی واقعی، اینجا حذف از دیتابیس انجام می‌شود
                    
                    return True, f"کد تخفیف {code['code']} با موفقیت حذف شد."
            
            return False, f"کد تخفیف با شناسه {code_id} یافت نشد."
                
        except Exception as e:
            logger.error(f"Error deleting discount code: {e}")
            return False, f"خطا در حذف کد تخفیف: {str(e)}"
    
    def validate_discount_code(self, code_text: str, amount: Union[int, float]) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Validate a discount code for use.
        
        Args:
            code_text: The discount code to validate
            amount: The purchase amount
            
        Returns:
            Tuple of (success, result) where result is either the discount info or error message
        """
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # یافتن کد تخفیف
            code = self.get_discount_code_by_code(code_text)
            if not code:
                return False, "کد تخفیف نامعتبر است."
            
            # بررسی فعال بودن کد
            if not code['is_active']:
                return False, "این کد تخفیف فعال نیست."
            
            # بررسی تاریخ کد
            if today < code['start_date']:
                return False, "این کد تخفیف هنوز فعال نشده است."
            if today > code['expiry_date']:
                return False, "این کد تخفیف منقضی شده است."
            
            # بررسی تعداد استفاده
            if code['max_uses'] > 0 and code['current_uses'] >= code['max_uses']:
                return False, "استفاده از این کد تخفیف به حداکثر مجاز رسیده است."
            
            # بررسی حداقل مبلغ خرید
            if amount < code['min_purchase']:
                return False, f"حداقل مبلغ خرید برای استفاده از این کد {code['min_purchase']} تومان است."
            
            # محاسبه مقدار تخفیف
            discount_amount = 0
            if code['is_percentage']:
                discount_amount = amount * (code['value'] / 100)
                # اعمال حداکثر مقدار تخفیف اگر تعیین شده باشد
                if code['max_discount'] > 0 and discount_amount > code['max_discount']:
                    discount_amount = code['max_discount']
            else:  # fixed amount
                discount_amount = code['value']
                if discount_amount > amount:
                    discount_amount = amount
            
            result = {
                'code_id': code['id'],
                'code': code['code'],
                'is_percentage': code['is_percentage'],
                'value': code['value'],
                'original_amount': amount,
                'discount_amount': discount_amount,
                'final_amount': amount - discount_amount
            }
            
            return True, result
                
        except Exception as e:
            logger.error(f"Error validating discount code: {e}")
            return False, f"خطا در بررسی کد تخفیف: {str(e)}"
    
    def use_discount_code(self, code_text: str) -> bool:
        """Increment usage count for a discount code.
        
        Args:
            code_text: The discount code used
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # یافتن کد تخفیف
            code = self.get_discount_code_by_code(code_text)
            if not code:
                return False
            
            # افزایش تعداد استفاده
            code['current_uses'] += 1
            
            # در یک پیاده‌سازی واقعی، اینجا تغییرات در دیتابیس ذخیره می‌شود
            
            return True
                
        except Exception as e:
            logger.error(f"Error incrementing discount code usage: {e}")
            return False 