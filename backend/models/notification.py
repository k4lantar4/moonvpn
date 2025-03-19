"""
MoonVPN Telegram Bot - Notification Model

This module provides the Notification model for managing system and user notifications.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class Notification:
    """Notification model for managing system and user notifications."""
    
    # Notification types
    TYPE_ACCOUNT_EXPIRY = 'account_expiry'
    TYPE_PAYMENT_RECEIVED = 'payment_received'
    TYPE_PAYMENT_PENDING = 'payment_pending'
    TYPE_SYSTEM_MESSAGE = 'system_message'
    TYPE_ADMIN_ALERT = 'admin_alert'
    TYPE_TICKET_REPLY = 'ticket_reply'
    TYPE_REFERRAL_COMPLETED = 'referral_completed'
    TYPE_ACCOUNT_TRAFFIC = 'account_traffic'
    TYPE_ACCOUNT_CREATED = 'account_created'
    TYPE_ACCOUNT_RENEWED = 'account_renewed'
    
    # Notification priorities
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    # Notification status
    STATUS_UNREAD = 'unread'
    STATUS_READ = 'read'
    STATUS_DISMISSED = 'dismissed'
    
    def __init__(self, notification_data: Dict[str, Any]):
        """
        Initialize a notification object.
        
        Args:
            notification_data (Dict[str, Any]): Notification data from database
        """
        self.id = notification_data.get('id')
        self.user_id = notification_data.get('user_id')
        self.title = notification_data.get('title')
        self.message = notification_data.get('message')
        self.notification_type = notification_data.get('notification_type')
        self.priority = notification_data.get('priority', self.PRIORITY_MEDIUM)
        self.status = notification_data.get('status', self.STATUS_UNREAD)
        self.related_id = notification_data.get('related_id')
        self.related_type = notification_data.get('related_type')
        self.action_url = notification_data.get('action_url')
        self.sent_at = notification_data.get('sent_at')
        self.read_at = notification_data.get('read_at')
        self.created_at = notification_data.get('created_at')
        self.created_by = notification_data.get('created_by')
        
        # Additional data from joins
        self.user_telegram_id = notification_data.get('user_telegram_id')
        self.user_username = notification_data.get('user_username')
        self.admin_username = notification_data.get('admin_username')
        
    @staticmethod
    def get_by_id(notification_id: int) -> Optional['Notification']:
        """
        Get a notification by ID.
        
        Args:
            notification_id (int): Notification ID
            
        Returns:
            Optional[Notification]: Notification object or None if not found
        """
        query = """
            SELECT n.*, 
                  u.telegram_id as user_telegram_id, u.username as user_username,
                  a.username as admin_username
            FROM notifications n
            LEFT JOIN users u ON n.user_id = u.id
            LEFT JOIN users a ON n.created_by = a.id
            WHERE n.id = %s
        """
        result = execute_query(query, (notification_id,), fetch="one")
        
        if result:
            return Notification(result)
            
        return None
        
    @staticmethod
    def get_by_user_id(user_id: int, limit: int = 20, offset: int = 0, 
                      include_read: bool = True) -> List['Notification']:
        """
        Get notifications by user ID.
        
        Args:
            user_id (int): User ID
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            include_read (bool, optional): Include read notifications. Defaults to True.
            
        Returns:
            List[Notification]: List of notification objects
        """
        params = [user_id]
        query = """
            SELECT n.*, 
                  u.telegram_id as user_telegram_id, u.username as user_username,
                  a.username as admin_username
            FROM notifications n
            LEFT JOIN users u ON n.user_id = u.id
            LEFT JOIN users a ON n.created_by = a.id
            WHERE n.user_id = %s
        """
        
        if not include_read:
            query += " AND n.status = %s"
            params.append(Notification.STATUS_UNREAD)
            
        query += " ORDER BY n.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        results = execute_query(query, tuple(params))
        
        return [Notification(result) for result in results]
        
    @staticmethod
    def count_unread_by_user(user_id: int) -> int:
        """
        Count unread notifications by user ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            int: Number of unread notifications
        """
        # Try to get from cache first
        cached_count = cache_get(f"notification_count:user:{user_id}")
        if cached_count is not None:
            return int(cached_count)
        
        query = """
            SELECT COUNT(*) as count
            FROM notifications
            WHERE user_id = %s AND status = %s
        """
        result = execute_query(query, (user_id, Notification.STATUS_UNREAD), fetch="one")
        
        count = result.get('count', 0) if result else 0
        
        # Cache result
        cache_set(f"notification_count:user:{user_id}", count, 300)  # Cache for 5 minutes
        
        return count
        
    @staticmethod
    def get_admin_alerts(limit: int = 20, offset: int = 0) -> List['Notification']:
        """
        Get admin alerts.
        
        Args:
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            
        Returns:
            List[Notification]: List of admin alert objects
        """
        query = """
            SELECT n.*, 
                  u.telegram_id as user_telegram_id, u.username as user_username,
                  a.username as admin_username
            FROM notifications n
            LEFT JOIN users u ON n.user_id = u.id
            LEFT JOIN users a ON n.created_by = a.id
            WHERE n.notification_type = %s
            ORDER BY n.created_at DESC
            LIMIT %s OFFSET %s
        """
        results = execute_query(query, (Notification.TYPE_ADMIN_ALERT, limit, offset))
        
        return [Notification(result) for result in results]
        
    @staticmethod
    def create(user_id: int, title: str, message: str, notification_type: str,
             priority: str = PRIORITY_MEDIUM, related_id: Optional[int] = None,
             related_type: Optional[str] = None, action_url: Optional[str] = None,
             created_by: Optional[int] = None) -> Optional['Notification']:
        """
        Create a new notification.
        
        Args:
            user_id (int): User ID
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Notification type
            priority (str, optional): Priority. Defaults to PRIORITY_MEDIUM.
            related_id (Optional[int], optional): Related object ID. Defaults to None.
            related_type (Optional[str], optional): Related object type. Defaults to None.
            action_url (Optional[str], optional): Action URL. Defaults to None.
            created_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            Optional[Notification]: Notification object or None if creation failed
        """
        # Insert into database
        query = """
            INSERT INTO notifications (
                user_id, title, message, notification_type, priority,
                related_id, related_type, action_url, status, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        notification_id = execute_insert(query, (
            user_id, title, message, notification_type, priority,
            related_id, related_type, action_url, Notification.STATUS_UNREAD, created_by
        ))
        
        if notification_id:
            # Clear notification count cache
            cache_delete(f"notification_count:user:{user_id}")
            
            # Return the created notification
            return Notification.get_by_id(notification_id)
            
        return None
        
    @staticmethod
    def create_for_all_admins(title: str, message: str, priority: str = PRIORITY_MEDIUM,
                            related_id: Optional[int] = None, related_type: Optional[str] = None,
                            action_url: Optional[str] = None, created_by: Optional[int] = None) -> int:
        """
        Create a notification for all admin users.
        
        Args:
            title (str): Notification title
            message (str): Notification message
            priority (str, optional): Priority. Defaults to PRIORITY_MEDIUM.
            related_id (Optional[int], optional): Related object ID. Defaults to None.
            related_type (Optional[str], optional): Related object type. Defaults to None.
            action_url (Optional[str], optional): Action URL. Defaults to None.
            created_by (Optional[int], optional): Admin user ID. Defaults to None.
            
        Returns:
            int: Number of notifications created
        """
        from models.user import User
        admins = User.get_all_admins()
        
        count = 0
        for admin in admins:
            notification = Notification.create(
                user_id=admin.id,
                title=title,
                message=message,
                notification_type=Notification.TYPE_ADMIN_ALERT,
                priority=priority,
                related_id=related_id,
                related_type=related_type,
                action_url=action_url,
                created_by=created_by
            )
            if notification:
                count += 1
                
        return count
        
    @staticmethod
    def create_system_alert(title: str, message: str, priority: str = PRIORITY_HIGH,
                         related_id: Optional[int] = None, related_type: Optional[str] = None) -> Optional['Notification']:
        """
        Create a system alert (sent to the first super admin).
        
        Args:
            title (str): Alert title
            message (str): Alert message
            priority (str, optional): Priority. Defaults to PRIORITY_HIGH.
            related_id (Optional[int], optional): Related object ID. Defaults to None.
            related_type (Optional[str], optional): Related object type. Defaults to None.
            
        Returns:
            Optional[Notification]: Notification object or None if creation failed
        """
        from models.user import User
        superadmin = User.get_superadmin()
        
        if not superadmin:
            logger.error("No superadmin found for system alert")
            return None
            
        return Notification.create(
            user_id=superadmin.id,
            title=title,
            message=message,
            notification_type=Notification.TYPE_ADMIN_ALERT,
            priority=priority,
            related_id=related_id,
            related_type=related_type
        )
        
    def save(self) -> bool:
        """
        Save notification changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE notifications SET
                user_id = %s,
                title = %s,
                message = %s,
                notification_type = %s,
                priority = %s,
                status = %s,
                related_id = %s,
                related_type = %s,
                action_url = %s,
                read_at = %s
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.user_id,
            self.title,
            self.message,
            self.notification_type,
            self.priority,
            self.status,
            self.related_id,
            self.related_type,
            self.action_url,
            self.read_at,
            self.id
        ))
        
        if success and (self.status == self.STATUS_READ or self.status == self.STATUS_DISMISSED):
            # Clear notification count cache
            cache_delete(f"notification_count:user:{self.user_id}")
            
        return success
        
    def mark_as_read(self) -> bool:
        """
        Mark notification as read.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.status = self.STATUS_READ
        self.read_at = datetime.now()
        
        return self.save()
        
    def dismiss(self) -> bool:
        """
        Dismiss notification.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        self.status = self.STATUS_DISMISSED
        
        return self.save()
        
    def delete(self) -> bool:
        """
        Delete notification from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Delete from database
        query = "DELETE FROM notifications WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        if success:
            # Clear notification count cache
            cache_delete(f"notification_count:user:{self.user_id}")
            
        return success
        
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            int: Number of notifications marked as read
        """
        query = """
            UPDATE notifications
            SET status = %s, read_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND status = %s
        """
        
        count = execute_update(query, (
            Notification.STATUS_READ, 
            user_id, 
            Notification.STATUS_UNREAD
        ))
        
        if count > 0:
            # Clear notification count cache
            cache_delete(f"notification_count:user:{user_id}")
            
        return count
        
    @staticmethod
    def delete_all_read(user_id: int) -> int:
        """
        Delete all read notifications for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            int: Number of notifications deleted
        """
        query = """
            DELETE FROM notifications
            WHERE user_id = %s AND status = %s
        """
        
        return execute_delete(query, (user_id, Notification.STATUS_READ))
        
    @staticmethod
    def delete_old_notifications(days: int = 30) -> int:
        """
        Delete old read notifications.
        
        Args:
            days (int, optional): Days to keep. Defaults to 30.
            
        Returns:
            int: Number of notifications deleted
        """
        query = """
            DELETE FROM notifications
            WHERE status != %s AND created_at < NOW() - INTERVAL %s DAY
        """
        
        return execute_delete(query, (Notification.STATUS_UNREAD, days))
        
    def get_user(self):
        """
        Get the user for this notification.
        
        Returns:
            Optional[User]: User object or None if not found
        """
        if not self.user_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.user_id)
        
    def get_creator(self):
        """
        Get the admin who created this notification.
        
        Returns:
            Optional[User]: Admin user object or None if not found
        """
        if not self.created_by:
            return None
            
        from models.user import User
        return User.get_by_id(self.created_by)
        
    def get_related_object(self):
        """
        Get the related object for this notification.
        
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
        elif self.related_type == 'user':
            from models.user import User
            return User.get_by_id(self.related_id)
            
        return None
        
    @staticmethod
    def notify_expiring_accounts(days_before: int = 3) -> int:
        """
        Send notifications for accounts expiring soon.
        
        Args:
            days_before (int, optional): Days before expiry. Defaults to 3.
            
        Returns:
            int: Number of notifications sent
        """
        from models.vpn_account import VPNAccount
        accounts = VPNAccount.get_accounts_expiring_soon(days_before)
        
        count = 0
        for account in accounts:
            user = account.get_user()
            if user:
                notification = Notification.create(
                    user_id=user.id,
                    title=f"Your VPN account will expire soon",
                    message=f"Your VPN account will expire in {days_before} days. Please renew it to avoid service interruption.",
                    notification_type=Notification.TYPE_ACCOUNT_EXPIRY,
                    priority=Notification.PRIORITY_HIGH,
                    related_id=account.id,
                    related_type='vpn_account',
                    action_url=f"/account/renew/{account.id}"
                )
                if notification:
                    count += 1
                    
        return count
        
    @staticmethod
    def notify_low_traffic(percentage: int = 10) -> int:
        """
        Send notifications for accounts with low traffic remaining.
        
        Args:
            percentage (int, optional): Percentage threshold. Defaults to 10.
            
        Returns:
            int: Number of notifications sent
        """
        from models.vpn_account import VPNAccount
        query = """
            SELECT id 
            FROM vpn_accounts 
            WHERE status = 'active' AND traffic_used > 0 
            AND traffic_limit > 0
            AND (traffic_used / traffic_limit) * 100 >= %s
        """
        results = execute_query(query, (100 - percentage,))
        
        count = 0
        for result in results:
            account = VPNAccount.get_by_id(result['id'])
            if account:
                user = account.get_user()
                if user:
                    used, total = account.get_traffic_usage()
                    used_gb = round(used / (1024 * 1024 * 1024), 2)
                    total_gb = round(total / (1024 * 1024 * 1024), 2)
                    
                    notification = Notification.create(
                        user_id=user.id,
                        title=f"Low traffic remaining",
                        message=f"Your VPN account has less than {percentage}% traffic remaining. Used: {used_gb} GB of {total_gb} GB.",
                        notification_type=Notification.TYPE_ACCOUNT_TRAFFIC,
                        priority=Notification.PRIORITY_MEDIUM,
                        related_id=account.id,
                        related_type='vpn_account'
                    )
                    if notification:
                        count += 1
                        
        return count
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert notification to dictionary.
        
        Returns:
            Dict[str, Any]: Notification data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'status': self.status,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'action_url': self.action_url,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'user_telegram_id': self.user_telegram_id,
            'user_username': self.user_username,
            'admin_username': self.admin_username
        } 