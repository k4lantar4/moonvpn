"""
MoonVPN Telegram Bot - User Model

This module provides the User model for managing user data and operations.
"""

import logging
import re
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import enum

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database.base import BaseModel

logger = logging.getLogger(__name__)

class UserStatus(enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(BaseModel):
    """
    User model representing a MoonVPN user.
    Handles user authentication, profile information, and relationships.
    """
    
    # Basic Information
    username = Column(String(50), unique=True, nullable=False, index=True)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(100), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    
    # Profile
    telegram_id = Column(String(50), unique=True, nullable=True)
    telegram_username = Column(String(50), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), nullable=True)
    
    # Relationships
    vpn_accounts = relationship("VPNAccount", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    points_transactions = relationship("PointsTransaction", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("LiveChatSession", back_populates="user", cascade="all, delete-orphan")
    
    # Role and Permissions
    role_id = Column(Integer, ForeignKey("role.id"), nullable=True)
    role = relationship("Role", back_populates="users")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.language:
            self.language = "en"
    
    def verify_phone(self, code: str) -> bool:
        """Verify user's phone number with given code."""
        if not self.verification_code or not self.verification_code_expires:
            return False
        
        if datetime.utcnow() > self.verification_code_expires:
            return False
        
        if self.verification_code != code:
            return False
        
        self.is_verified = True
        self.verification_code = None
        self.verification_code_expires = None
        return True
    
    def generate_verification_code(self) -> str:
        """Generate a new verification code."""
        import random
        self.verification_code = str(random.randint(100000, 999999))
        self.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
        return self.verification_code
    
    def update_login_attempt(self, success: bool) -> None:
        """Update login attempt counter."""
        if success:
            self.failed_login_attempts = 0
            self.last_login = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.status = UserStatus.SUSPENDED
    
    def has_active_subscription(self) -> bool:
        """Check if user has any active subscription."""
        return any(sub.is_active for sub in self.subscriptions)
    
    def get_active_vpn_account(self) -> Optional["VPNAccount"]:
        """Get user's active VPN account if any."""
        for account in self.vpn_accounts:
            if account.is_active:
                return account
        return None

    def __str__(self):
        return self.username

    def __init__(self, user_data: Dict[str, Any]):
        """
        Initialize a user object.
        
        Args:
            user_data (Dict[str, Any]): User data from database
        """
        self.id = user_data.get('id')
        self.telegram_id = user_data.get('telegram_id')
        self.username = user_data.get('username')
        self.first_name = user_data.get('first_name')
        self.last_name = user_data.get('last_name')
        self.phone = user_data.get('phone')
        self.language = user_data.get('language', 'fa')
        self.role = user_data.get('role', 'user')
        self.wallet_balance = float(user_data.get('wallet_balance', 0))
        self.referral_code = user_data.get('referral_code')
        self.referred_by = user_data.get('referred_by')
        self.is_active = user_data.get('is_active', True)
        self.created_at = user_data.get('created_at')
        self.updated_at = user_data.get('updated_at')
        
    @classmethod
    def get_by_username(cls, db, username):
        """Get user by username"""
        try:
            return db.query(cls).filter(cls.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    @classmethod
    def get_by_email(cls, db, email):
        """Get user by email"""
        try:
            return db.query(cls).filter(cls.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    def set_password(self, password):
        """Set user password"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        """Verify user password"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.password_hash)

    def is_admin(self):
        """Check if user is admin"""
        return self.is_superuser or self.is_staff

    def to_dict(self):
        """Convert user to dictionary"""
        data = super().to_dict()
        # Remove sensitive data
        data.pop('password_hash', None)
        return data

    @staticmethod
    def get_by_telegram_id(telegram_id: int) -> Optional['User']:
        """
        Get a user by Telegram ID.
        
        Args:
            telegram_id (int): Telegram user ID
            
        Returns:
            Optional[User]: User object or None if not found
        """
        # Try to get from cache first
        cached_user = cache_get(f"user:telegram:{telegram_id}")
        if cached_user:
            return User(cached_user)
        
        # Get from database
        query = "SELECT * FROM users WHERE telegram_id = %s"
        result = execute_query(query, (telegram_id,), fetch="one")
        
        if result:
            # Cache user data
            cache_set(f"user:telegram:{telegram_id}", dict(result), 300)  # Cache for 5 minutes
            return User(result)
            
        return None
        
    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """
        Get a user by ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[User]: User object or None if not found
        """
        # Try to get from cache first
        cached_user = cache_get(f"user:id:{user_id}")
        if cached_user:
            return User(cached_user)
        
        # Get from database
        query = "SELECT * FROM users WHERE id = %s"
        result = execute_query(query, (user_id,), fetch="one")
        
        if result:
            # Cache user data
            cache_set(f"user:id:{user_id}", dict(result), 300)  # Cache for 5 minutes
            return User(result)
            
        return None
        
    @staticmethod
    def get_by_referral_code(referral_code: str) -> Optional['User']:
        """
        Get a user by referral code.
        
        Args:
            referral_code (str): Referral code
            
        Returns:
            Optional[User]: User object or None if not found
        """
        query = "SELECT * FROM users WHERE referral_code = %s"
        result = execute_query(query, (referral_code,), fetch="one")
        
        if result:
            return User(result)
            
        return None
        
    @staticmethod
    def create(telegram_id: int, username: str = None, first_name: str = None, 
               last_name: str = None, language: str = 'fa', phone: str = None,
               referred_by: int = None) -> Optional['User']:
        """
        Create a new user.
        
        Args:
            telegram_id (int): Telegram user ID
            username (str, optional): Telegram username
            first_name (str, optional): First name
            last_name (str, optional): Last name
            language (str, optional): Language code, default 'fa'
            phone (str, optional): Phone number
            referred_by (int, optional): User ID who referred this user
            
        Returns:
            Optional[User]: User object or None if creation failed
        """
        # Check if user already exists
        existing_user = User.get_by_telegram_id(telegram_id)
        if existing_user:
            # Update user data if needed
            if (username and username != existing_user.username or
                first_name and first_name != existing_user.first_name or
                last_name and last_name != existing_user.last_name or
                language and language != existing_user.language):
                
                existing_user.username = username or existing_user.username
                existing_user.first_name = first_name or existing_user.first_name
                existing_user.last_name = last_name or existing_user.last_name
                existing_user.language = language or existing_user.language
                
                existing_user.save()
            
            return existing_user
            
        # Generate referral code
        referral_code = User._generate_referral_code()
        
        # Insert new user
        query = """
            INSERT INTO users (
                telegram_id, username, first_name, last_name, 
                language, phone, referral_code, referred_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        user_id = execute_insert(query, (
            telegram_id, username, first_name, last_name, 
            language, phone, referral_code, referred_by
        ))
        
        if user_id:
            # Handle referral if provided
            if referred_by:
                User._process_referral(user_id, referred_by)
                
            # Retrieve the user
            return User.get_by_id(user_id)
            
        return None
        
    @staticmethod
    def _generate_referral_code() -> str:
        """
        Generate a unique referral code.
        
        Returns:
            str: Unique referral code
        """
        while True:
            # Generate a short, unique referral code
            code = str(uuid.uuid4())[:8].upper()
            
            # Check if code already exists
            query = "SELECT id FROM users WHERE referral_code = %s"
            result = execute_query(query, (code,), fetch="one")
            
            if not result:
                return code
                
    @staticmethod
    def _process_referral(user_id: int, referrer_id: int) -> None:
        """
        Process a user referral.
        
        Args:
            user_id (int): New user ID
            referrer_id (int): Referrer user ID
        """
        # Add to referrals table
        query = """
            INSERT INTO referrals (
                referrer_id, referred_id, status
            ) VALUES (
                %s, %s, 'registered'
            )
        """
        
        execute_insert(query, (referrer_id, user_id))
        
        # Notify the referrer
        referrer = User.get_by_id(referrer_id)
        if referrer:
            # Track this activity for notification later
            User.add_activity(referrer_id, 'new_referral', {'referred_id': user_id})
            
    def save(self) -> bool:
        """
        Save user changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE users SET
                username = %s,
                first_name = %s,
                last_name = %s,
                phone = %s,
                language = %s,
                role = %s,
                wallet_balance = %s,
                referral_code = %s,
                referred_by = %s,
                is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.username,
            self.first_name,
            self.last_name,
            self.phone,
            self.language,
            self.role,
            self.wallet_balance,
            self.referral_code,
            self.referred_by,
            self.is_active,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"user:id:{self.id}")
            cache_delete(f"user:telegram:{self.telegram_id}")
            
        return success
        
    def update_language(self, language: str) -> bool:
        """
        Update user language.
        
        Args:
            language (str): Language code
            
        Returns:
            bool: True if language was updated, False otherwise
        """
        self.language = language
        return self.save()
        
    def update_phone(self, phone: str) -> bool:
        """
        Update user phone.
        
        Args:
            phone (str): Phone number
            
        Returns:
            bool: True if phone was updated, False otherwise
        """
        # Validate phone format
        if phone and not re.match(r'^\+?[0-9]{10,15}$', phone):
            return False
            
        self.phone = phone
        return self.save()
        
    def add_to_wallet(self, amount: float, description: str = None) -> bool:
        """
        Add an amount to user wallet.
        
        Args:
            amount (float): Amount to add
            description (str, optional): Description of the transaction
            
        Returns:
            bool: True if amount was added, False otherwise
        """
        if amount <= 0:
            return False
            
        self.wallet_balance += amount
        
        # Log wallet transaction
        if self.save():
            User.add_wallet_transaction(self.id, amount, 'credit', description)
            return True
            
        return False
        
    def deduct_from_wallet(self, amount: float, description: str = None) -> bool:
        """
        Deduct an amount from user wallet.
        
        Args:
            amount (float): Amount to deduct
            description (str, optional): Description of the transaction
            
        Returns:
            bool: True if amount was deducted, False otherwise
        """
        if amount <= 0 or self.wallet_balance < amount:
            return False
            
        self.wallet_balance -= amount
        
        # Log wallet transaction
        if self.save():
            User.add_wallet_transaction(self.id, amount, 'debit', description)
            return True
            
        return False
        
    @staticmethod
    def add_wallet_transaction(user_id: int, amount: float, 
                              transaction_type: str, description: str = None) -> bool:
        """
        Add a wallet transaction record.
        
        Args:
            user_id (int): User ID
            amount (float): Transaction amount
            transaction_type (str): Transaction type ('credit' or 'debit')
            description (str, optional): Description of the transaction
            
        Returns:
            bool: True if transaction was added, False otherwise
        """
        query = """
            INSERT INTO user_activities (
                user_id, activity_type, activity_data
            ) VALUES (
                %s, 'wallet_transaction', %s
            )
        """
        
        transaction_data = {
            'amount': amount,
            'type': transaction_type,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        import json
        result = execute_insert(query, (user_id, json.dumps(transaction_data)))
        
        return result is not None
        
    @staticmethod
    def add_activity(user_id: int, activity_type: str, activity_data: Dict[str, Any] = None) -> bool:
        """
        Add a user activity record.
        
        Args:
            user_id (int): User ID
            activity_type (str): Activity type
            activity_data (Dict[str, Any], optional): Activity data
            
        Returns:
            bool: True if activity was added, False otherwise
        """
        query = """
            INSERT INTO user_activities (
                user_id, activity_type, activity_data
            ) VALUES (
                %s, %s, %s
            )
        """
        
        import json
        activity_data = activity_data or {}
        activity_data['timestamp'] = datetime.now().isoformat()
        
        result = execute_insert(query, (user_id, activity_type, json.dumps(activity_data)))
        
        return result is not None
        
    def get_vpn_accounts(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get user's VPN accounts.
        
        Args:
            status (str, optional): Filter by status ('active', 'expired', etc.)
            
        Returns:
            List[Dict[str, Any]]: List of VPN accounts
        """
        if status:
            query = """
                SELECT va.*, s.name as server_name, s.location, p.name as package_name
                FROM vpn_accounts va
                JOIN servers s ON va.server_id = s.id
                JOIN vpn_packages p ON va.package_id = p.id
                WHERE va.user_id = %s AND va.status = %s
                ORDER BY va.expiry_date DESC
            """
            params = (self.id, status)
        else:
            query = """
                SELECT va.*, s.name as server_name, s.location, p.name as package_name
                FROM vpn_accounts va
                JOIN servers s ON va.server_id = s.id
                JOIN vpn_packages p ON va.package_id = p.id
                WHERE va.user_id = %s
                ORDER BY va.expiry_date DESC
            """
            params = (self.id,)
            
        return execute_query(query, params)
        
    def get_active_vpn_accounts(self) -> List[Dict[str, Any]]:
        """
        Get user's active VPN accounts.
        
        Returns:
            List[Dict[str, Any]]: List of active VPN accounts
        """
        return self.get_vpn_accounts('active')
        
    def get_payments(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get user's payment records.
        
        Args:
            status (str, optional): Filter by status ('pending', 'completed', etc.)
            
        Returns:
            List[Dict[str, Any]]: List of payment records
        """
        if status:
            query = """
                SELECT * FROM payments
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
            """
            params = (self.id, status)
        else:
            query = """
                SELECT * FROM payments
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            params = (self.id,)
            
        return execute_query(query, params)
        
    def get_referrals(self) -> List[Dict[str, Any]]:
        """
        Get user's referrals.
        
        Returns:
            List[Dict[str, Any]]: List of referrals
        """
        query = """
            SELECT r.*, u.username, u.first_name, u.last_name
            FROM referrals r
            JOIN users u ON r.referred_id = u.id
            WHERE r.referrer_id = %s
            ORDER BY r.created_at DESC
        """
        
        return execute_query(query, (self.id,))
        
    def count_referrals(self) -> int:
        """
        Count user's referrals.
        
        Returns:
            int: Number of referrals
        """
        query = "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = %s"
        result = execute_query(query, (self.id,), fetch="one")
        
        return result.get('count', 0) if result else 0
        
    def get_support_tickets(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get user's support tickets.
        
        Args:
            status (str, optional): Filter by status ('open', 'closed', etc.)
            
        Returns:
            List[Dict[str, Any]]: List of support tickets
        """
        if status:
            query = """
                SELECT * FROM support_tickets
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
            """
            params = (self.id, status)
        else:
            query = """
                SELECT * FROM support_tickets
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            params = (self.id,)
            
        return execute_query(query, params)
        
    def is_superadmin(self) -> bool:
        """
        Check if user is a superadmin.
        
        Returns:
            bool: True if user is a superadmin, False otherwise
        """
        return self.role == 'superadmin'
        
    def make_admin(self) -> bool:
        """
        Make user an admin.
        
        Returns:
            bool: True if user was made admin, False otherwise
        """
        self.role = 'admin'
        return self.save()
        
    def revoke_admin(self) -> bool:
        """
        Revoke admin privileges from user.
        
        Returns:
            bool: True if admin privileges were revoked, False otherwise
        """
        if self.role == 'superadmin':
            return False
            
        self.role = 'user'
        return self.save()
        
    def deactivate(self) -> bool:
        """
        Deactivate user.
        
        Returns:
            bool: True if user was deactivated, False otherwise
        """
        self.is_active = False
        return self.save()
        
    def activate(self) -> bool:
        """
        Activate user.
        
        Returns:
            bool: True if user was activated, False otherwise
        """
        self.is_active = True
        return self.save()
        
    @staticmethod
    def list_users(offset: int = 0, limit: int = 20, search: str = None, 
                 role: str = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        List users.
        
        Args:
            offset (int, optional): Pagination offset
            limit (int, optional): Pagination limit
            search (str, optional): Search term for username, first_name, or last_name
            role (str, optional): Filter by role
            active_only (bool, optional): Include only active users
            
        Returns:
            List[Dict[str, Any]]: List of users
        """
        params = []
        conditions = []
        
        if active_only:
            conditions.append("is_active = TRUE")
            
        if role:
            conditions.append("role = %s")
            params.append(role)
            
        if search:
            search_term = f"%{search}%"
            conditions.append("(username ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s)")
            params.extend([search_term, search_term, search_term])
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM users
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        
        return execute_query(query, tuple(params))
        
    @staticmethod
    def count_users(search: str = None, role: str = None, active_only: bool = True) -> int:
        """
        Count users.
        
        Args:
            search (str, optional): Search term for username, first_name, or last_name
            role (str, optional): Filter by role
            active_only (bool, optional): Include only active users
            
        Returns:
            int: Number of users
        """
        params = []
        conditions = []
        
        if active_only:
            conditions.append("is_active = TRUE")
            
        if role:
            conditions.append("role = %s")
            params.append(role)
            
        if search:
            search_term = f"%{search}%"
            conditions.append("(username ILIKE %s OR first_name ILIKE %s OR last_name ILIKE %s)")
            params.extend([search_term, search_term, search_term])
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"SELECT COUNT(*) as count FROM users {where_clause}"
        
        result = execute_query(query, tuple(params) if params else None, fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def get_new_users_count(days: int = 7) -> int:
        """
        Get count of new users in the last X days.
        
        Args:
            days (int, optional): Number of days to look back
            
        Returns:
            int: Number of new users
        """
        query = """
            SELECT COUNT(*) as count FROM users
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """
        
        result = execute_query(query, (days,), fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def get_user_stats() -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dict[str, Any]: User statistics
        """
        total_users = User.count_users()
        active_users = User.count_users(active_only=True)
        admins = User.count_users(role='admin')
        superadmins = User.count_users(role='superadmin')
        new_users_today = User.get_new_users_count(1)
        new_users_week = User.get_new_users_count(7)
        new_users_month = User.get_new_users_count(30)
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'admins': admins,
            'superadmins': superadmins,
            'new_users_today': new_users_today,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month
        } 