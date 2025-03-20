"""
User service for managing users, roles and access control.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from core.config import settings
from core.database import get_db

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users and access control."""
    
    def __init__(self):
        """Initialize user service."""
        self.db = get_db()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.db.users.find_one({'user_id': user_id})
            return user
        except Exception as e:
            logger.error("Error getting user: %s", str(e))
            return None
    
    async def create_user(
        self,
        user_id: int,
        username: str,
        first_name: str,
        last_name: Optional[str] = None,
        role: str = 'user'
    ) -> Tuple[bool, Any]:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = await self.get_user(user_id)
            if existing_user:
                return False, "این کاربر قبلاً ثبت شده است"
            
            # Create user
            user_data = {
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'status': 'active',
                'created_at': datetime.now(),
                'last_active': datetime.now(),
                'vpn_accounts': [],
                'total_traffic': 0,
                'total_spent': 0
            }
            
            result = await self.db.users.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            
            return True, user_data
            
        except Exception as e:
            logger.error("Error creating user: %s", str(e))
            return False, "خطا در ایجاد کاربر"
    
    async def update_user(
        self,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Update user data."""
        try:
            # Get existing user
            user = await self.get_user(user_id)
            if not user:
                return False, "کاربر یافت نشد"
            
            # Update user data
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                updated_user = await self.get_user(user_id)
                return True, updated_user
            return False, "خطا در بروزرسانی اطلاعات کاربر"
            
        except Exception as e:
            logger.error("Error updating user: %s", str(e))
            return False, "خطا در بروزرسانی اطلاعات کاربر"
    
    async def update_last_active(self, user_id: int) -> bool:
        """Update user's last active timestamp."""
        try:
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$set': {'last_active': datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error updating last active: %s", str(e))
            return False
    
    async def get_active_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get list of users active in the last N days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            users = await self.db.users.find({
                'last_active': {'$gte': cutoff_date}
            }).to_list(length=None)
            return users
        except Exception as e:
            logger.error("Error getting active users: %s", str(e))
            return []
    
    async def get_top_users(
        self,
        metric: str = 'traffic',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by traffic or spending."""
        try:
            sort_field = 'total_traffic' if metric == 'traffic' else 'total_spent'
            users = await self.db.users.find().sort(
                sort_field, -1
            ).limit(limit).to_list(length=None)
            return users
        except Exception as e:
            logger.error("Error getting top users: %s", str(e))
            return []
    
    async def add_vpn_account(
        self,
        user_id: int,
        account_data: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Add a VPN account to user's accounts."""
        try:
            # Get existing user
            user = await self.get_user(user_id)
            if not user:
                return False, "کاربر یافت نشد"
            
            # Add account to user's accounts
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$push': {'vpn_accounts': account_data}}
            )
            
            if result.modified_count > 0:
                updated_user = await self.get_user(user_id)
                return True, updated_user
            return False, "خطا در افزودن اکانت VPN"
            
        except Exception as e:
            logger.error("Error adding VPN account: %s", str(e))
            return False, "خطا در افزودن اکانت VPN"
    
    async def update_vpn_account(
        self,
        user_id: int,
        account_id: str,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Update a VPN account in user's accounts."""
        try:
            # Get existing user
            user = await self.get_user(user_id)
            if not user:
                return False, "کاربر یافت نشد"
            
            # Update account in user's accounts
            result = await self.db.users.update_one(
                {
                    'user_id': user_id,
                    'vpn_accounts.id': account_id
                },
                {'$set': {f'vpn_accounts.$.{k}': v for k, v in update_data.items()}}
            )
            
            if result.modified_count > 0:
                updated_user = await self.get_user(user_id)
                return True, updated_user
            return False, "خطا در بروزرسانی اکانت VPN"
            
        except Exception as e:
            logger.error("Error updating VPN account: %s", str(e))
            return False, "خطا در بروزرسانی اکانت VPN"
    
    async def remove_vpn_account(
        self,
        user_id: int,
        account_id: str
    ) -> Tuple[bool, Any]:
        """Remove a VPN account from user's accounts."""
        try:
            # Get existing user
            user = await self.get_user(user_id)
            if not user:
                return False, "کاربر یافت نشد"
            
            # Remove account from user's accounts
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$pull': {'vpn_accounts': {'id': account_id}}}
            )
            
            if result.modified_count > 0:
                updated_user = await self.get_user(user_id)
                return True, updated_user
            return False, "خطا در حذف اکانت VPN"
            
        except Exception as e:
            logger.error("Error removing VPN account: %s", str(e))
            return False, "خطا در حذف اکانت VPN"
    
    async def update_user_traffic(
        self,
        user_id: int,
        traffic: int
    ) -> bool:
        """Update user's total traffic usage."""
        try:
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$inc': {'total_traffic': traffic}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error updating user traffic: %s", str(e))
            return False
    
    async def update_user_spending(
        self,
        user_id: int,
        amount: int
    ) -> bool:
        """Update user's total spending."""
        try:
            result = await self.db.users.update_one(
                {'user_id': user_id},
                {'$inc': {'total_spent': amount}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error updating user spending: %s", str(e))
            return False
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            user = await self.get_user(user_id)
            if not user:
                return {
                    'total_traffic': 0,
                    'total_spent': 0,
                    'active_accounts': 0,
                    'expired_accounts': 0
                }
            
            # Count active and expired accounts
            now = datetime.now()
            active_accounts = 0
            expired_accounts = 0
            
            for account in user.get('vpn_accounts', []):
                expiry = datetime.strptime(account['expiry_date'], '%Y-%m-%d')
                if expiry > now:
                    active_accounts += 1
                else:
                    expired_accounts += 1
            
            return {
                'total_traffic': user.get('total_traffic', 0),
                'total_spent': user.get('total_spent', 0),
                'active_accounts': active_accounts,
                'expired_accounts': expired_accounts
            }
            
        except Exception as e:
            logger.error("Error getting user stats: %s", str(e))
            return {
                'total_traffic': 0,
                'total_spent': 0,
                'active_accounts': 0,
                'expired_accounts': 0
            }
    
    async def get_user_roles(self) -> List[str]:
        """Get list of available user roles."""
        return ['admin', 'seller', 'user']
    
    async def check_permission(
        self,
        user_id: int,
        required_role: str
    ) -> bool:
        """Check if user has required role."""
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            roles = await self.get_user_roles()
            user_role_index = roles.index(user['role'])
            required_role_index = roles.index(required_role)
            
            return user_role_index <= required_role_index
            
        except Exception as e:
            logger.error("Error checking permission: %s", str(e))
            return False 