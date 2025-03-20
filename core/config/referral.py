"""
MoonVPN Telegram Bot - Referral Model

This module provides the Referral model for managing user referrals and rewards.
"""

import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class Referral:
    """Referral model for managing user referrals and rewards."""
    
    # Referral status constants
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    
    # Reward types
    REWARD_WALLET_CREDIT = 'wallet_credit'
    REWARD_DISCOUNT_CODE = 'discount_code'
    REWARD_ACCOUNT_EXTENSION = 'account_extension'
    
    def __init__(self, referral_data: Dict[str, Any]):
        """
        Initialize a referral object.
        
        Args:
            referral_data (Dict[str, Any]): Referral data from database
        """
        self.id = referral_data.get('id')
        self.referrer_id = referral_data.get('referrer_id')
        self.referred_id = referral_data.get('referred_id')
        self.referral_code = referral_data.get('referral_code')
        self.status = referral_data.get('status', self.STATUS_PENDING)
        self.reward_type = referral_data.get('reward_type')
        self.reward_amount = float(referral_data.get('reward_amount', 0))
        self.reward_details = referral_data.get('reward_details', {})
        self.created_at = referral_data.get('created_at')
        self.completed_at = referral_data.get('completed_at')
        
        # Additional data from joins
        self.referrer_username = referral_data.get('referrer_username')
        self.referrer_first_name = referral_data.get('referrer_first_name')
        self.referred_username = referral_data.get('referred_username')
        self.referred_first_name = referral_data.get('referred_first_name')
        
    @staticmethod
    def get_by_id(referral_id: int) -> Optional['Referral']:
        """
        Get a referral by ID.
        
        Args:
            referral_id (int): Referral ID
            
        Returns:
            Optional[Referral]: Referral object or None if not found
        """
        query = """
            SELECT r.*, 
                  u1.username as referrer_username, u1.first_name as referrer_first_name,
                  u2.username as referred_username, u2.first_name as referred_first_name
            FROM referrals r
            LEFT JOIN users u1 ON r.referrer_id = u1.id
            LEFT JOIN users u2 ON r.referred_id = u2.id
            WHERE r.id = %s
        """
        result = execute_query(query, (referral_id,), fetch="one")
        
        if result:
            return Referral(result)
            
        return None
        
    @staticmethod
    def get_by_referrer_id(referrer_id: int, limit: int = 20, offset: int = 0) -> List['Referral']:
        """
        Get referrals by referrer ID.
        
        Args:
            referrer_id (int): Referrer user ID
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            
        Returns:
            List[Referral]: List of referral objects
        """
        query = """
            SELECT r.*, 
                  u1.username as referrer_username, u1.first_name as referrer_first_name,
                  u2.username as referred_username, u2.first_name as referred_first_name
            FROM referrals r
            LEFT JOIN users u1 ON r.referrer_id = u1.id
            LEFT JOIN users u2 ON r.referred_id = u2.id
            WHERE r.referrer_id = %s
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        results = execute_query(query, (referrer_id, limit, offset))
        
        return [Referral(result) for result in results]
        
    @staticmethod
    def get_by_referred_id(referred_id: int) -> Optional['Referral']:
        """
        Get referral by referred user ID.
        
        Args:
            referred_id (int): Referred user ID
            
        Returns:
            Optional[Referral]: Referral object or None if not found
        """
        query = """
            SELECT r.*, 
                  u1.username as referrer_username, u1.first_name as referrer_first_name,
                  u2.username as referred_username, u2.first_name as referred_first_name
            FROM referrals r
            LEFT JOIN users u1 ON r.referrer_id = u1.id
            LEFT JOIN users u2 ON r.referred_id = u2.id
            WHERE r.referred_id = %s
        """
        result = execute_query(query, (referred_id,), fetch="one")
        
        if result:
            return Referral(result)
            
        return None
        
    @staticmethod
    def get_by_referral_code(referral_code: str) -> List['Referral']:
        """
        Get referrals by referral code.
        
        Args:
            referral_code (str): Referral code
            
        Returns:
            List[Referral]: List of referral objects
        """
        query = """
            SELECT r.*, 
                  u1.username as referrer_username, u1.first_name as referrer_first_name,
                  u2.username as referred_username, u2.first_name as referred_first_name
            FROM referrals r
            LEFT JOIN users u1 ON r.referrer_id = u1.id
            LEFT JOIN users u2 ON r.referred_id = u2.id
            WHERE r.referral_code = %s
            ORDER BY r.created_at DESC
        """
        results = execute_query(query, (referral_code,))
        
        return [Referral(result) for result in results]
        
    @staticmethod
    def create(referrer_id: int, referred_id: int, referral_code: str,
             reward_type: str = REWARD_WALLET_CREDIT, reward_amount: float = 0,
             reward_details: Optional[Dict] = None) -> Optional['Referral']:
        """
        Create a new referral.
        
        Args:
            referrer_id (int): Referrer user ID
            referred_id (int): Referred user ID
            referral_code (str): Referral code used
            reward_type (str, optional): Reward type. Defaults to REWARD_WALLET_CREDIT.
            reward_amount (float, optional): Reward amount. Defaults to 0.
            reward_details (Optional[Dict], optional): Additional reward details. Defaults to None.
            
        Returns:
            Optional[Referral]: Referral object or None if creation failed
        """
        # Check if referred user already has a referral
        existing = Referral.get_by_referred_id(referred_id)
        if existing:
            logger.error(f"User {referred_id} already has a referral")
            return None
            
        # Insert into database
        query = """
            INSERT INTO referrals (
                referrer_id, referred_id, referral_code, status,
                reward_type, reward_amount, reward_details
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        referral_id = execute_insert(query, (
            referrer_id, referred_id, referral_code, Referral.STATUS_PENDING,
            reward_type, reward_amount, reward_details
        ))
        
        if referral_id:
            # Return the created referral
            return Referral.get_by_id(referral_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save referral changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE referrals SET
                referrer_id = %s,
                referred_id = %s,
                referral_code = %s,
                status = %s,
                reward_type = %s,
                reward_amount = %s,
                reward_details = %s,
                completed_at = %s
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.referrer_id,
            self.referred_id,
            self.referral_code,
            self.status,
            self.reward_type,
            self.reward_amount,
            self.reward_details,
            self.completed_at,
            self.id
        ))
        
        return success
        
    def complete(self) -> bool:
        """
        Mark referral as completed and process reward.
        
        Returns:
            bool: True if completion was successful, False otherwise
        """
        if self.status == self.STATUS_COMPLETED:
            return True
            
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.now()
        
        # Process reward based on type
        if self.reward_type == self.REWARD_WALLET_CREDIT and self.reward_amount > 0:
            from models.user import User
            referrer = User.get_by_id(self.referrer_id)
            if referrer:
                referrer.add_to_wallet(
                    self.reward_amount,
                    f"Referral reward for inviting {self.referred_username or 'a user'}"
                )
                
        elif self.reward_type == self.REWARD_DISCOUNT_CODE:
            # Create a discount code for the referrer
            from models.discount import DiscountCode
            discount_value = self.reward_details.get('discount_value', 10)
            discount_type = self.reward_details.get('discount_type', DiscountCode.TYPE_PERCENTAGE)
            
            DiscountCode.create(
                code=f"REF{self.referrer_id}_{random.randint(1000, 9999)}",
                description=f"Referral reward for {self.referrer_username or 'user'}",
                discount_type=discount_type,
                discount_value=discount_value,
                max_uses=1,
                is_public=False,
                expiry_date=datetime.now().replace(
                    year=datetime.now().year + 1
                )  # Valid for 1 year
            )
            
        elif self.reward_type == self.REWARD_ACCOUNT_EXTENSION:
            # Extend the user's VPN account
            if 'account_id' in self.reward_details and 'days' in self.reward_details:
                from models.vpn_account import VPNAccount
                account = VPNAccount.get_by_id(self.reward_details['account_id'])
                if account:
                    account.extend(self.reward_details['days'])
        
        return self.save()
        
    def reject(self) -> bool:
        """
        Mark referral as rejected.
        
        Returns:
            bool: True if rejection was successful, False otherwise
        """
        if self.status == self.STATUS_REJECTED:
            return True
            
        self.status = self.STATUS_REJECTED
        
        return self.save()
        
    def get_referrer(self):
        """
        Get the referrer user.
        
        Returns:
            Optional[User]: Referrer user object or None if not found
        """
        if not self.referrer_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.referrer_id)
        
    def get_referred(self):
        """
        Get the referred user.
        
        Returns:
            Optional[User]: Referred user object or None if not found
        """
        if not self.referred_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.referred_id)
        
    @staticmethod
    def generate_referral_code(user_id: int, length: int = 8) -> str:
        """
        Generate a unique referral code for a user.
        
        Args:
            user_id (int): User ID
            length (int, optional): Code length. Defaults to 8.
            
        Returns:
            str: Generated referral code
        """
        prefix = f"MV{user_id}"
        chars = string.ascii_uppercase + string.digits
        suffix = ''.join(random.choice(chars) for _ in range(length - len(prefix)))
        
        return f"{prefix}{suffix}"
        
    @staticmethod
    def count_referrals_by_user(user_id: int) -> Dict[str, int]:
        """
        Count referrals by user ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Dict[str, int]: Dictionary with referral counts by status
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM referrals
            WHERE referrer_id = %s
            GROUP BY status
        """
        results = execute_query(query, (user_id,))
        
        counts = {
            Referral.STATUS_PENDING: 0,
            Referral.STATUS_COMPLETED: 0,
            Referral.STATUS_REJECTED: 0
        }
        
        for result in results:
            counts[result['status']] = result['count']
            
        return counts
        
    @staticmethod
    def get_top_referrers(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top referrers.
        
        Args:
            limit (int, optional): Limit results. Defaults to 10.
            
        Returns:
            List[Dict[str, Any]]: List of top referrers with counts
        """
        query = """
            SELECT 
                r.referrer_id,
                u.username as referrer_username,
                u.first_name as referrer_first_name,
                COUNT(*) as total_referrals,
                COUNT(CASE WHEN r.status = %s THEN 1 END) as completed_referrals,
                SUM(CASE WHEN r.status = %s THEN r.reward_amount ELSE 0 END) as total_rewards
            FROM referrals r
            JOIN users u ON r.referrer_id = u.id
            GROUP BY r.referrer_id, u.username, u.first_name
            ORDER BY completed_referrals DESC, total_referrals DESC
            LIMIT %s
        """
        
        return execute_query(query, (
            Referral.STATUS_COMPLETED,
            Referral.STATUS_COMPLETED,
            limit
        ))
        
    @staticmethod
    def get_referral_stats() -> Dict[str, Any]:
        """
        Get overall referral statistics.
        
        Returns:
            Dict[str, Any]: Dictionary with referral statistics
        """
        # Total referrals
        query1 = "SELECT COUNT(*) as count FROM referrals"
        result1 = execute_query(query1, fetch="one")
        
        # Completed referrals
        query2 = "SELECT COUNT(*) as count FROM referrals WHERE status = %s"
        result2 = execute_query(query2, (Referral.STATUS_COMPLETED,), fetch="one")
        
        # Total rewards
        query3 = """
            SELECT SUM(reward_amount) as total
            FROM referrals
            WHERE status = %s AND reward_type = %s
        """
        result3 = execute_query(query3, (
            Referral.STATUS_COMPLETED,
            Referral.REWARD_WALLET_CREDIT
        ), fetch="one")
        
        # Unique referrers
        query4 = "SELECT COUNT(DISTINCT referrer_id) as count FROM referrals"
        result4 = execute_query(query4, fetch="one")
        
        return {
            'total_referrals': result1.get('count', 0) if result1 else 0,
            'completed_referrals': result2.get('count', 0) if result2 else 0,
            'total_rewards': float(result3.get('total', 0)) if result3 and result3.get('total') else 0,
            'unique_referrers': result4.get('count', 0) if result4 else 0
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert referral to dictionary.
        
        Returns:
            Dict[str, Any]: Referral data as dictionary
        """
        return {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'referred_id': self.referred_id,
            'referral_code': self.referral_code,
            'status': self.status,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'reward_details': self.reward_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'referrer_username': self.referrer_username,
            'referrer_first_name': self.referrer_first_name,
            'referred_username': self.referred_username,
            'referred_first_name': self.referred_first_name
        } 