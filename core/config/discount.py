"""
MoonVPN Telegram Bot - Discount Model

This module provides the DiscountCode model for managing promotional discounts.
"""

import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class DiscountCode:
    """Discount Code model for managing promotional codes."""
    
    # Discount types
    TYPE_PERCENTAGE = 'percentage'
    TYPE_FIXED = 'fixed'
    
    def __init__(self, discount_data: Dict[str, Any]):
        """
        Initialize a discount code object.
        
        Args:
            discount_data (Dict[str, Any]): Discount data from database
        """
        self.id = discount_data.get('id')
        self.code = discount_data.get('code')
        self.description = discount_data.get('description')
        self.discount_type = discount_data.get('discount_type')
        self.discount_value = float(discount_data.get('discount_value', 0))
        self.max_uses = discount_data.get('max_uses')
        self.current_uses = discount_data.get('current_uses', 0)
        self.min_purchase_amount = float(discount_data.get('min_purchase_amount', 0))
        self.is_active = discount_data.get('is_active', True)
        self.is_public = discount_data.get('is_public', True)
        self.start_date = discount_data.get('start_date')
        self.expiry_date = discount_data.get('expiry_date')
        self.created_by = discount_data.get('created_by')
        self.created_at = discount_data.get('created_at')
        self.updated_at = discount_data.get('updated_at')
        
        # Additional data from joins
        self.admin_username = discount_data.get('admin_username')
        
    @staticmethod
    def get_by_id(discount_id: int) -> Optional['DiscountCode']:
        """
        Get a discount code by ID.
        
        Args:
            discount_id (int): Discount code ID
            
        Returns:
            Optional[DiscountCode]: Discount code object or None if not found
        """
        # Try to get from cache first
        cached_discount = cache_get(f"discount:id:{discount_id}")
        if cached_discount:
            return DiscountCode(cached_discount)
        
        # Get from database with admin info
        query = """
            SELECT d.*, u.username as admin_username
            FROM discount_codes d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE d.id = %s
        """
        result = execute_query(query, (discount_id,), fetch="one")
        
        if result:
            # Cache discount data
            cache_set(f"discount:id:{discount_id}", dict(result), 300)  # Cache for 5 minutes
            return DiscountCode(result)
            
        return None
        
    @staticmethod
    def get_by_code(code: str) -> Optional['DiscountCode']:
        """
        Get a discount code by code string.
        
        Args:
            code (str): Discount code string
            
        Returns:
            Optional[DiscountCode]: Discount code object or None if not found
        """
        # Try to get from cache first
        cached_discount = cache_get(f"discount:code:{code}")
        if cached_discount:
            return DiscountCode(cached_discount)
        
        # Get from database
        query = """
            SELECT d.*, u.username as admin_username
            FROM discount_codes d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE d.code = %s
        """
        result = execute_query(query, (code,), fetch="one")
        
        if result:
            # Cache discount data
            cache_set(f"discount:code:{code}", dict(result), 300)
            return DiscountCode(result)
            
        return None
        
    @staticmethod
    def get_all(include_inactive: bool = False) -> List['DiscountCode']:
        """
        Get all discount codes.
        
        Args:
            include_inactive (bool, optional): Include inactive codes. Defaults to False.
            
        Returns:
            List[DiscountCode]: List of discount code objects
        """
        if include_inactive:
            query = """
                SELECT d.*, u.username as admin_username
                FROM discount_codes d
                LEFT JOIN users u ON d.created_by = u.id
                ORDER BY d.created_at DESC
            """
            results = execute_query(query)
        else:
            query = """
                SELECT d.*, u.username as admin_username
                FROM discount_codes d
                LEFT JOIN users u ON d.created_by = u.id
                WHERE d.is_active = TRUE
                ORDER BY d.created_at DESC
            """
            results = execute_query(query)
        
        return [DiscountCode(result) for result in results]
        
    @staticmethod
    def get_active() -> List['DiscountCode']:
        """
        Get all active discount codes.
        
        Returns:
            List[DiscountCode]: List of active discount code objects
        """
        now = datetime.now()
        
        query = """
            SELECT d.*, u.username as admin_username
            FROM discount_codes d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE d.is_active = TRUE
            AND (d.expiry_date IS NULL OR d.expiry_date > %s)
            AND (d.start_date IS NULL OR d.start_date <= %s)
            AND (d.max_uses IS NULL OR d.current_uses < d.max_uses)
            ORDER BY d.created_at DESC
        """
        results = execute_query(query, (now, now))
        
        return [DiscountCode(result) for result in results]
        
    @staticmethod
    def get_public_active() -> List['DiscountCode']:
        """
        Get all active public discount codes.
        
        Returns:
            List[DiscountCode]: List of active public discount code objects
        """
        now = datetime.now()
        
        query = """
            SELECT d.*, u.username as admin_username
            FROM discount_codes d
            LEFT JOIN users u ON d.created_by = u.id
            WHERE d.is_active = TRUE
            AND d.is_public = TRUE
            AND (d.expiry_date IS NULL OR d.expiry_date > %s)
            AND (d.start_date IS NULL OR d.start_date <= %s)
            AND (d.max_uses IS NULL OR d.current_uses < d.max_uses)
            ORDER BY d.created_at DESC
        """
        results = execute_query(query, (now, now))
        
        return [DiscountCode(result) for result in results]
        
    @staticmethod
    def create(code: Optional[str] = None, description: str = '', discount_type: str = TYPE_PERCENTAGE,
             discount_value: float = 10, max_uses: Optional[int] = None, 
             min_purchase_amount: float = 0, is_active: bool = True, is_public: bool = True,
             start_date: Optional[datetime] = None, expiry_date: Optional[datetime] = None,
             created_by: Optional[int] = None) -> Optional['DiscountCode']:
        """
        Create a new discount code.
        
        Args:
            code (Optional[str], optional): Discount code. Defaults to None (auto-generated).
            description (str, optional): Discount description. Defaults to ''.
            discount_type (str, optional): Discount type. Defaults to TYPE_PERCENTAGE.
            discount_value (float, optional): Discount value (percentage or fixed amount). Defaults to 10.
            max_uses (Optional[int], optional): Maximum uses. Defaults to None (unlimited).
            min_purchase_amount (float, optional): Minimum purchase amount. Defaults to 0.
            is_active (bool, optional): Active status. Defaults to True.
            is_public (bool, optional): Public status. Defaults to True.
            start_date (Optional[datetime], optional): Start date. Defaults to None.
            expiry_date (Optional[datetime], optional): Expiry date. Defaults to None.
            created_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            Optional[DiscountCode]: Discount code object or None if creation failed
        """
        # Generate code if not provided
        if not code:
            code = DiscountCode.generate_code()
            
        # Check if code already exists
        existing = DiscountCode.get_by_code(code)
        if existing:
            logger.error(f"Discount code '{code}' already exists")
            return None
            
        # Insert into database
        query = """
            INSERT INTO discount_codes (
                code, description, discount_type, discount_value, max_uses,
                min_purchase_amount, is_active, is_public, start_date, expiry_date, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        discount_id = execute_insert(query, (
            code, description, discount_type, discount_value, max_uses,
            min_purchase_amount, is_active, is_public, start_date, expiry_date, created_by
        ))
        
        if discount_id:
            # Return the created discount
            return DiscountCode.get_by_id(discount_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save discount code changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE discount_codes SET
                code = %s,
                description = %s,
                discount_type = %s,
                discount_value = %s,
                max_uses = %s,
                current_uses = %s,
                min_purchase_amount = %s,
                is_active = %s,
                is_public = %s,
                start_date = %s,
                expiry_date = %s,
                created_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.code,
            self.description,
            self.discount_type,
            self.discount_value,
            self.max_uses,
            self.current_uses,
            self.min_purchase_amount,
            self.is_active,
            self.is_public,
            self.start_date,
            self.expiry_date,
            self.created_by,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"discount:id:{self.id}")
            cache_delete(f"discount:code:{self.code}")
            
        return success
        
    def delete(self) -> bool:
        """
        Delete discount code from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Check if code has been used
        if self.current_uses and self.current_uses > 0:
            logger.error(f"Cannot delete discount code {self.code} as it has been used {self.current_uses} times")
            return False
            
        # Delete from database
        query = "DELETE FROM discount_codes WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear cache
            cache_delete(f"discount:id:{self.id}")
            cache_delete(f"discount:code:{self.code}")
            
        return success
        
    def activate(self) -> bool:
        """
        Activate discount code.
        
        Returns:
            bool: True if activation was successful, False otherwise
        """
        self.is_active = True
        return self.save()
        
    def deactivate(self) -> bool:
        """
        Deactivate discount code.
        
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        self.is_active = False
        return self.save()
        
    def increment_usage(self) -> bool:
        """
        Increment usage count of discount code.
        
        Returns:
            bool: True if increment was successful, False otherwise
        """
        self.current_uses += 1
        return self.save()
        
    def is_valid(self, purchase_amount: float = 0) -> Tuple[bool, Optional[str]]:
        """
        Check if discount code is valid.
        
        Args:
            purchase_amount (float, optional): Purchase amount. Defaults to 0.
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, reason)
        """
        now = datetime.now()
        
        if not self.is_active:
            return False, "Discount code is not active"
            
        if self.start_date and self.start_date > now:
            return False, f"Discount code is not valid yet. Valid from {self.start_date.strftime('%Y-%m-%d')}"
            
        if self.expiry_date and self.expiry_date < now:
            return False, f"Discount code has expired on {self.expiry_date.strftime('%Y-%m-%d')}"
            
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False, "Discount code has reached maximum uses"
            
        if self.min_purchase_amount > 0 and purchase_amount < self.min_purchase_amount:
            return False, f"Minimum purchase amount for this code is {self.min_purchase_amount}"
            
        return True, None
        
    def calculate_discount(self, amount: float) -> float:
        """
        Calculate discount amount.
        
        Args:
            amount (float): Original amount
            
        Returns:
            float: Discount amount
        """
        if not self.is_active:
            return 0
            
        if self.discount_type == self.TYPE_PERCENTAGE:
            # Cap percentage discount at 100%
            percentage = min(self.discount_value, 100)
            return (percentage / 100) * amount
        else:  # Fixed amount discount
            # Cap fixed discount at total amount
            return min(self.discount_value, amount)
            
    def get_creator(self):
        """
        Get the admin who created this discount code.
        
        Returns:
            Optional[User]: Admin user object or None if not found
        """
        if not self.created_by:
            return None
            
        from models.user import User
        return User.get_by_id(self.created_by)
        
    @staticmethod
    def generate_code(length: int = 8, prefix: str = '') -> str:
        """
        Generate a random discount code.
        
        Args:
            length (int, optional): Code length. Defaults to 8.
            prefix (str, optional): Code prefix. Defaults to ''.
            
        Returns:
            str: Generated code
        """
        chars = string.ascii_uppercase + string.digits
        code = prefix + ''.join(random.choice(chars) for _ in range(length))
        
        # Check if code already exists and regenerate if needed
        existing = DiscountCode.get_by_code(code)
        if existing:
            return DiscountCode.generate_code(length, prefix)
            
        return code
        
    @staticmethod
    def get_usage_stats() -> Dict[str, int]:
        """
        Get usage statistics.
        
        Returns:
            Dict[str, int]: Dictionary with usage statistics
        """
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_active THEN 1 END) as active,
                COUNT(CASE WHEN is_public THEN 1 END) as public,
                SUM(current_uses) as total_uses
            FROM discount_codes
        """
        result = execute_query(query, fetch="one")
        
        if not result:
            return {
                'total': 0,
                'active': 0,
                'public': 0,
                'total_uses': 0
            }
            
        return {
            'total': result.get('total', 0),
            'active': result.get('active', 0),
            'public': result.get('public', 0),
            'total_uses': result.get('total_uses', 0) or 0
        }
        
    @staticmethod
    def create_code_batch(count: int, prefix: str = '', description: str = '',
                         discount_type: str = TYPE_PERCENTAGE, discount_value: float = 10,
                         max_uses: int = 1, min_purchase_amount: float = 0,
                         is_public: bool = False, expires_in_days: int = 30,
                         created_by: Optional[int] = None) -> List['DiscountCode']:
        """
        Create a batch of discount codes.
        
        Args:
            count (int): Number of codes to create
            prefix (str, optional): Code prefix. Defaults to ''.
            description (str, optional): Discount description. Defaults to ''.
            discount_type (str, optional): Discount type. Defaults to TYPE_PERCENTAGE.
            discount_value (float, optional): Discount value. Defaults to 10.
            max_uses (int, optional): Maximum uses per code. Defaults to 1.
            min_purchase_amount (float, optional): Minimum purchase amount. Defaults to 0.
            is_public (bool, optional): Public status. Defaults to False.
            expires_in_days (int, optional): Expiry in days. Defaults to 30.
            created_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            List[DiscountCode]: List of created discount code objects
        """
        expiry_date = datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None
        created_codes = []
        
        for _ in range(count):
            code = DiscountCode.create(
                code=DiscountCode.generate_code(8, prefix),
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                max_uses=max_uses,
                min_purchase_amount=min_purchase_amount,
                is_active=True,
                is_public=is_public,
                expiry_date=expiry_date,
                created_by=created_by
            )
            if code:
                created_codes.append(code)
                
        return created_codes
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert discount code to dictionary.
        
        Returns:
            Dict[str, Any]: Discount code data as dictionary
        """
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses,
            'min_purchase_amount': self.min_purchase_amount,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'admin_username': self.admin_username
        } 