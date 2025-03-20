"""
MoonVPN Telegram Bot - User Activity Model

This module provides the UserActivity model for tracking user actions and events.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class UserActivity:
    """User Activity model for tracking user actions and events."""
    
    # Activity types
    TYPE_LOGIN = 'login'
    TYPE_LOGOUT = 'logout'
    TYPE_REGISTRATION = 'registration'
    TYPE_ACCOUNT_PURCHASE = 'account_purchase'
    TYPE_ACCOUNT_RENEWAL = 'account_renewal'
    TYPE_PAYMENT = 'payment'
    TYPE_PROFILE_UPDATE = 'profile_update'
    TYPE_TICKET_CREATED = 'ticket_created'
    TYPE_TICKET_REPLIED = 'ticket_replied'
    TYPE_REFERRAL = 'referral'
    TYPE_PASSWORD_RESET = 'password_reset'
    TYPE_ADMIN_ACTION = 'admin_action'
    TYPE_BOT_COMMAND = 'bot_command'
    
    def __init__(self, activity_data: Dict[str, Any]):
        """
        Initialize a user activity object.
        
        Args:
            activity_data (Dict[str, Any]): Activity data from database
        """
        self.id = activity_data.get('id')
        self.user_id = activity_data.get('user_id')
        self.activity_type = activity_data.get('activity_type')
        self.description = activity_data.get('description')
        self.ip_address = activity_data.get('ip_address')
        self.user_agent = activity_data.get('user_agent')
        self.platform = activity_data.get('platform')
        self.related_id = activity_data.get('related_id')
        self.related_type = activity_data.get('related_type')
        self.details = activity_data.get('details', {})
        self.created_at = activity_data.get('created_at')
        
        # Additional data from joins
        self.user_telegram_id = activity_data.get('user_telegram_id')
        self.user_username = activity_data.get('user_username')
        
    @staticmethod
    def get_by_id(activity_id: int) -> Optional['UserActivity']:
        """
        Get a user activity by ID.
        
        Args:
            activity_id (int): Activity ID
            
        Returns:
            Optional[UserActivity]: Activity object or None if not found
        """
        query = """
            SELECT a.*, u.telegram_id as user_telegram_id, u.username as user_username
            FROM user_activities a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """
        result = execute_query(query, (activity_id,), fetch="one")
        
        if result:
            return UserActivity(result)
            
        return None
        
    @staticmethod
    def get_by_user_id(user_id: int, limit: int = 20, offset: int = 0,
                      activity_type: Optional[str] = None) -> List['UserActivity']:
        """
        Get user activities by user ID.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            activity_type (Optional[str], optional): Filter by activity type. Defaults to None.
            
        Returns:
            List[UserActivity]: List of activity objects
        """
        params = [user_id]
        query = """
            SELECT a.*, u.telegram_id as user_telegram_id, u.username as user_username
            FROM user_activities a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.user_id = %s
        """
        
        if activity_type:
            query += " AND a.activity_type = %s"
            params.append(activity_type)
            
        query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        results = execute_query(query, tuple(params))
        
        return [UserActivity(result) for result in results]
        
    @staticmethod
    def search(search_term: str, limit: int = 20, offset: int = 0) -> List['UserActivity']:
        """
        Search user activities.
        
        Args:
            search_term (str): Search term
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            
        Returns:
            List[UserActivity]: List of matching activity objects
        """
        search = f"%{search_term}%"
        query = """
            SELECT a.*, u.telegram_id as user_telegram_id, u.username as user_username
            FROM user_activities a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.description ILIKE %s OR u.username ILIKE %s OR u.first_name ILIKE %s
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """
        results = execute_query(query, (search, search, search, limit, offset))
        
        return [UserActivity(result) for result in results]
        
    @staticmethod
    def get_recent(limit: int = 100, activity_type: Optional[str] = None) -> List['UserActivity']:
        """
        Get recent user activities.
        
        Args:
            limit (int, optional): Limit results. Defaults to 100.
            activity_type (Optional[str], optional): Filter by activity type. Defaults to None.
            
        Returns:
            List[UserActivity]: List of recent activity objects
        """
        params = []
        query = """
            SELECT a.*, u.telegram_id as user_telegram_id, u.username as user_username
            FROM user_activities a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
        """
        
        if activity_type:
            query += " AND a.activity_type = %s"
            params.append(activity_type)
            
        query += " ORDER BY a.created_at DESC LIMIT %s"
        params.append(limit)
        
        results = execute_query(query, tuple(params) if params else (limit,))
        
        return [UserActivity(result) for result in results]
        
    @staticmethod
    def create(user_id: int, activity_type: str, description: str,
             ip_address: Optional[str] = None, user_agent: Optional[str] = None,
             platform: Optional[str] = None, related_id: Optional[int] = None,
             related_type: Optional[str] = None, details: Optional[Dict] = None) -> Optional['UserActivity']:
        """
        Create a new user activity.
        
        Args:
            user_id (int): User ID
            activity_type (str): Activity type
            description (str): Activity description
            ip_address (Optional[str], optional): IP address. Defaults to None.
            user_agent (Optional[str], optional): User agent. Defaults to None.
            platform (Optional[str], optional): Platform. Defaults to None.
            related_id (Optional[int], optional): Related object ID. Defaults to None.
            related_type (Optional[str], optional): Related object type. Defaults to None.
            details (Optional[Dict], optional): Additional details. Defaults to None.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        # Insert into database
        query = """
            INSERT INTO user_activities (
                user_id, activity_type, description, ip_address, user_agent,
                platform, related_id, related_type, details
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        activity_id = execute_insert(query, (
            user_id, activity_type, description, ip_address, user_agent,
            platform, related_id, related_type, json.dumps(details) if details else None
        ))
        
        if activity_id:
            # Return the created activity
            return UserActivity.get_by_id(activity_id)
            
        return None
        
    @staticmethod
    def log_login(user_id: int, ip_address: Optional[str] = None, 
                user_agent: Optional[str] = None, platform: Optional[str] = None,
                success: bool = True) -> Optional['UserActivity']:
        """
        Log a user login.
        
        Args:
            user_id (int): User ID
            ip_address (Optional[str], optional): IP address. Defaults to None.
            user_agent (Optional[str], optional): User agent. Defaults to None.
            platform (Optional[str], optional): Platform. Defaults to None.
            success (bool, optional): Login success. Defaults to True.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        description = "User logged in successfully"
        if not success:
            description = "Failed login attempt"
            
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_LOGIN,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            platform=platform,
            details={'success': success}
        )
        
    @staticmethod
    def log_registration(user_id: int, ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None, platform: Optional[str] = None,
                       referrer_id: Optional[int] = None) -> Optional['UserActivity']:
        """
        Log a user registration.
        
        Args:
            user_id (int): User ID
            ip_address (Optional[str], optional): IP address. Defaults to None.
            user_agent (Optional[str], optional): User agent. Defaults to None.
            platform (Optional[str], optional): Platform. Defaults to None.
            referrer_id (Optional[int], optional): Referrer user ID. Defaults to None.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        description = "User registered"
        details = {}
        
        if referrer_id:
            description = "User registered via referral"
            details = {'referrer_id': referrer_id}
            
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_REGISTRATION,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            platform=platform,
            details=details
        )
        
    @staticmethod
    def log_bot_command(user_id: int, command: str, params: Optional[str] = None) -> Optional['UserActivity']:
        """
        Log a bot command.
        
        Args:
            user_id (int): User ID
            command (str): Bot command
            params (Optional[str], optional): Command parameters. Defaults to None.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        description = f"Bot command: {command}"
        
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_BOT_COMMAND,
            description=description,
            platform="telegram",
            details={'command': command, 'params': params}
        )
        
    @staticmethod
    def log_account_purchase(user_id: int, account_id: int, package_id: int,
                          payment_id: Optional[int] = None) -> Optional['UserActivity']:
        """
        Log an account purchase.
        
        Args:
            user_id (int): User ID
            account_id (int): VPN account ID
            package_id (int): Subscription package ID
            payment_id (Optional[int], optional): Payment ID. Defaults to None.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        # Get package name
        query = "SELECT name FROM vpn_packages WHERE id = %s"
        result = execute_query(query, (package_id,), fetch="one")
        package_name = result.get('name', 'Unknown package') if result else 'Unknown package'
        
        description = f"Purchased VPN account: {package_name}"
        
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_ACCOUNT_PURCHASE,
            description=description,
            related_id=account_id,
            related_type='vpn_account',
            details={
                'package_id': package_id,
                'payment_id': payment_id
            }
        )
        
    @staticmethod
    def log_account_renewal(user_id: int, account_id: int,
                         payment_id: Optional[int] = None) -> Optional['UserActivity']:
        """
        Log an account renewal.
        
        Args:
            user_id (int): User ID
            account_id (int): VPN account ID
            payment_id (Optional[int], optional): Payment ID. Defaults to None.
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        description = "Renewed VPN account"
        
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_ACCOUNT_RENEWAL,
            description=description,
            related_id=account_id,
            related_type='vpn_account',
            details={'payment_id': payment_id}
        )
        
    @staticmethod
    def log_payment(user_id: int, payment_id: int, amount: float,
                  payment_method: str, payment_type: str) -> Optional['UserActivity']:
        """
        Log a payment.
        
        Args:
            user_id (int): User ID
            payment_id (int): Payment ID
            amount (float): Payment amount
            payment_method (str): Payment method
            payment_type (str): Payment type
            
        Returns:
            Optional[UserActivity]: Activity object or None if creation failed
        """
        description = f"Payment of {amount} via {payment_method} for {payment_type}"
        
        return UserActivity.create(
            user_id=user_id,
            activity_type=UserActivity.TYPE_PAYMENT,
            description=description,
            related_id=payment_id,
            related_type='payment',
            details={
                'amount': amount,
                'payment_method': payment_method,
                'payment_type': payment_type
            }
        )
        
    @staticmethod
    def get_activity_stats(days: int = 30) -> Dict[str, Any]:
        """
        Get activity statistics.
        
        Args:
            days (int, optional): Number of days to analyze. Defaults to 30.
            
        Returns:
            Dict[str, Any]: Activity statistics
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Total activities
        query1 = """
            SELECT COUNT(*) as count
            FROM user_activities
            WHERE created_at >= %s
        """
        result1 = execute_query(query1, (start_date,), fetch="one")
        
        # Activities by type
        query2 = """
            SELECT activity_type, COUNT(*) as count
            FROM user_activities
            WHERE created_at >= %s
            GROUP BY activity_type
            ORDER BY count DESC
        """
        result2 = execute_query(query2, (start_date,))
        
        # Activities by day
        query3 = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM user_activities
            WHERE created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        result3 = execute_query(query3, (start_date,))
        
        # Active users
        query4 = """
            SELECT COUNT(DISTINCT user_id) as count
            FROM user_activities
            WHERE created_at >= %s
        """
        result4 = execute_query(query4, (start_date,), fetch="one")
        
        # Most active users
        query5 = """
            SELECT a.user_id, u.username, u.first_name, COUNT(*) as activity_count
            FROM user_activities a
            JOIN users u ON a.user_id = u.id
            WHERE a.created_at >= %s
            GROUP BY a.user_id, u.username, u.first_name
            ORDER BY activity_count DESC
            LIMIT 10
        """
        result5 = execute_query(query5, (start_date,))
        
        return {
            'total_activities': result1.get('count', 0) if result1 else 0,
            'activities_by_type': result2,
            'activities_by_day': result3,
            'active_users': result4.get('count', 0) if result4 else 0,
            'most_active_users': result5
        }
        
    @staticmethod
    def clean_old_activities(days: int = 90) -> int:
        """
        Delete old activities.
        
        Args:
            days (int, optional): Days to keep. Defaults to 90.
            
        Returns:
            int: Number of activities deleted
        """
        query = """
            DELETE FROM user_activities
            WHERE created_at < NOW() - INTERVAL %s DAY
        """
        
        return execute_delete(query, (days,))
        
    def get_user(self):
        """
        Get the user for this activity.
        
        Returns:
            Optional[User]: User object or None if not found
        """
        if not self.user_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.user_id)
        
    def get_related_object(self):
        """
        Get the related object for this activity.
        
        Returns:
            Optional[Any]: Related object or None if not found
        """
        if not self.related_id or not self.related_type:
            return None
            
        if self.related_type == 'vpn_account':
            from models.vpn_account import VPNAccount
            return VPNAccount.get_by_id(self.related_id)
        elif self.related_type == 'payment':
            from models.payment import Payment
            return Payment.get_by_id(self.related_id)
        elif self.related_type == 'ticket':
            from models.ticket import Ticket
            return Ticket.get_by_id(self.related_id)
            
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert activity to dictionary.
        
        Returns:
            Dict[str, Any]: Activity data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'platform': self.platform,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_telegram_id': self.user_telegram_id,
            'user_username': self.user_username
        } 