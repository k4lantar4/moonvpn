"""
MoonVPN Telegram Bot - Support Ticket Model

This module provides the Ticket and TicketReply models for managing support tickets.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from core.database import execute_query, execute_insert, execute_update, execute_delete, cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

class TicketReply:
    """Ticket Reply model for managing support ticket replies."""
    
    def __init__(self, reply_data: Dict[str, Any]):
        """
        Initialize a ticket reply object.
        
        Args:
            reply_data (Dict[str, Any]): Reply data from database
        """
        self.id = reply_data.get('id')
        self.ticket_id = reply_data.get('ticket_id')
        self.user_id = reply_data.get('user_id')
        self.message = reply_data.get('message')
        self.is_from_admin = reply_data.get('is_from_admin', False)
        self.attachment_path = reply_data.get('attachment_path')
        self.created_at = reply_data.get('created_at')
        
        # Additional data from joins
        self.username = reply_data.get('username')
        self.first_name = reply_data.get('first_name')
        self.is_read = reply_data.get('is_read', False)
        
    @staticmethod
    def get_by_id(reply_id: int) -> Optional['TicketReply']:
        """
        Get a ticket reply by ID.
        
        Args:
            reply_id (int): Reply ID
            
        Returns:
            Optional[TicketReply]: Ticket reply object or None if not found
        """
        query = """
            SELECT r.*, u.username, u.first_name
            FROM ticket_replies r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """
        result = execute_query(query, (reply_id,), fetch="one")
        
        if result:
            return TicketReply(result)
            
        return None
        
    @staticmethod
    def get_by_ticket_id(ticket_id: int) -> List['TicketReply']:
        """
        Get all replies for a ticket.
        
        Args:
            ticket_id (int): Ticket ID
            
        Returns:
            List[TicketReply]: List of ticket reply objects
        """
        query = """
            SELECT r.*, u.username, u.first_name
            FROM ticket_replies r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.ticket_id = %s
            ORDER BY r.created_at ASC
        """
        results = execute_query(query, (ticket_id,))
        
        return [TicketReply(result) for result in results]
        
    @staticmethod
    def create(ticket_id: int, user_id: int, message: str, 
              is_from_admin: bool = False, attachment_path: Optional[str] = None) -> Optional['TicketReply']:
        """
        Create a new ticket reply.
        
        Args:
            ticket_id (int): Ticket ID
            user_id (int): User ID
            message (str): Reply message
            is_from_admin (bool, optional): Whether the reply is from an admin. Defaults to False.
            attachment_path (Optional[str], optional): Path to attachment. Defaults to None.
            
        Returns:
            Optional[TicketReply]: Ticket reply object or None if creation failed
        """
        # Insert into database
        query = """
            INSERT INTO ticket_replies (
                ticket_id, user_id, message, is_from_admin, attachment_path
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """
        
        reply_id = execute_insert(query, (
            ticket_id, user_id, message, is_from_admin, attachment_path
        ))
        
        if reply_id:
            # Update ticket updated_at
            from models.ticket import Ticket
            ticket = Ticket.get_by_id(ticket_id)
            if ticket:
                # Mark as unread for the other party
                if is_from_admin:
                    ticket.user_has_unread = True
                else:
                    ticket.admin_has_unread = True
                    
                # Update ticket status if closed
                if ticket.status == Ticket.STATUS_CLOSED:
                    ticket.status = Ticket.STATUS_OPEN
                
                ticket.save()
                
            # Return the created reply
            return TicketReply.get_by_id(reply_id)
            
        return None
        
    def delete(self) -> bool:
        """
        Delete reply from database.
        
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not self.id:
            return False
            
        # Delete attachment if exists
        if self.attachment_path:
            try:
                import os
                if os.path.exists(self.attachment_path):
                    os.remove(self.attachment_path)
            except Exception as e:
                logger.error(f"Error deleting attachment: {e}")
            
        # Delete from database
        query = "DELETE FROM ticket_replies WHERE id = %s"
        success = execute_delete(query, (self.id,))
        
        return success
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ticket reply to dictionary.
        
        Returns:
            Dict[str, Any]: Ticket reply data as dictionary
        """
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'message': self.message,
            'is_from_admin': self.is_from_admin,
            'attachment_path': self.attachment_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'username': self.username,
            'first_name': self.first_name,
            'is_read': self.is_read
        }


class Ticket:
    """Ticket model for managing support tickets."""
    
    # Ticket status constants
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    
    # Ticket priority constants
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    # Ticket category constants
    CATEGORY_GENERAL = 'general'
    CATEGORY_TECHNICAL = 'technical'
    CATEGORY_BILLING = 'billing'
    CATEGORY_ACCOUNT = 'account'
    
    def __init__(self, ticket_data: Dict[str, Any]):
        """
        Initialize a ticket object.
        
        Args:
            ticket_data (Dict[str, Any]): Ticket data from database
        """
        self.id = ticket_data.get('id')
        self.user_id = ticket_data.get('user_id')
        self.subject = ticket_data.get('subject')
        self.status = ticket_data.get('status', self.STATUS_OPEN)
        self.priority = ticket_data.get('priority', self.PRIORITY_MEDIUM)
        self.category = ticket_data.get('category', self.CATEGORY_GENERAL)
        self.assigned_to = ticket_data.get('assigned_to')
        self.user_has_unread = ticket_data.get('user_has_unread', False)
        self.admin_has_unread = ticket_data.get('admin_has_unread', False)
        self.vpn_account_id = ticket_data.get('vpn_account_id')
        self.created_at = ticket_data.get('created_at')
        self.updated_at = ticket_data.get('updated_at')
        self.closed_at = ticket_data.get('closed_at')
        
        # Additional data from joins
        self.username = ticket_data.get('username')
        self.first_name = ticket_data.get('first_name')
        self.telegram_id = ticket_data.get('telegram_id')
        self.assigned_username = ticket_data.get('assigned_username')
        self.vpn_account_uuid = ticket_data.get('vpn_account_uuid')
    
    @staticmethod
    def get_by_id(ticket_id: int) -> Optional['Ticket']:
        """
        Get a ticket by ID.
        
        Args:
            ticket_id (int): Ticket ID
            
        Returns:
            Optional[Ticket]: Ticket object or None if not found
        """
        # Try to get from cache first
        cached_ticket = cache_get(f"ticket:id:{ticket_id}")
        if cached_ticket:
            return Ticket(cached_ticket)
        
        # Get from database with user info
        query = """
            SELECT t.*, u.username, u.first_name, u.telegram_id,
                  a.username as assigned_username,
                  v.uuid as vpn_account_uuid
            FROM support_tickets t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
            WHERE t.id = %s
        """
        result = execute_query(query, (ticket_id,), fetch="one")
        
        if result:
            # Cache ticket data
            cache_set(f"ticket:id:{ticket_id}", dict(result), 300)  # Cache for 5 minutes
            return Ticket(result)
            
            return None
                
    @staticmethod
    def get_by_user_id(user_id: int, include_closed: bool = False,
                      limit: int = 10, offset: int = 0) -> List['Ticket']:
        """
        Get tickets by user ID.
        
        Args:
            user_id (int): User ID
            include_closed (bool, optional): Include closed tickets. Defaults to False.
            limit (int, optional): Limit results. Defaults to 10.
            offset (int, optional): Offset results. Defaults to 0.
            
        Returns:
            List[Ticket]: List of ticket objects
        """
        if include_closed:
            query = """
                SELECT t.*, u.username, u.first_name, u.telegram_id,
                      a.username as assigned_username,
                      v.uuid as vpn_account_uuid
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
                WHERE t.user_id = %s
                ORDER BY t.updated_at DESC
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (user_id, limit, offset))
        else:
            query = """
                SELECT t.*, u.username, u.first_name, u.telegram_id,
                      a.username as assigned_username,
                      v.uuid as vpn_account_uuid
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
                WHERE t.user_id = %s AND t.status != %s
                ORDER BY t.updated_at DESC
                LIMIT %s OFFSET %s
            """
            results = execute_query(query, (user_id, Ticket.STATUS_CLOSED, limit, offset))
        
        return [Ticket(result) for result in results]
        
    @staticmethod
    def get_active_ticket_for_user(user_id: int) -> Optional['Ticket']:
        """
        Get the most recent active ticket for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[Ticket]: Ticket object or None if not found
        """
        query = """
            SELECT t.*, u.username, u.first_name, u.telegram_id,
                  a.username as assigned_username,
                  v.uuid as vpn_account_uuid
            FROM support_tickets t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
            WHERE t.user_id = %s AND t.status = %s
            ORDER BY t.updated_at DESC
            LIMIT 1
        """
        result = execute_query(query, (user_id, Ticket.STATUS_OPEN), fetch="one")
        
        if result:
            return Ticket(result)
            
        return None
        
    @staticmethod
    def get_all_open(assigned_to: Optional[int] = None,
                    limit: int = 20, offset: int = 0) -> List['Ticket']:
        """
        Get all open tickets.
        
        Args:
            assigned_to (Optional[int], optional): Admin ID to filter by. Defaults to None.
            limit (int, optional): Limit results. Defaults to 20.
            offset (int, optional): Offset results. Defaults to 0.
            
        Returns:
            List[Ticket]: List of ticket objects
        """
        if assigned_to is not None:
            query = """
                SELECT t.*, u.username, u.first_name, u.telegram_id,
                      a.username as assigned_username,
                      v.uuid as vpn_account_uuid
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
                WHERE t.status = %s AND t.assigned_to = %s
                ORDER BY t.priority DESC, t.updated_at ASC
                    LIMIT %s OFFSET %s
            """
            results = execute_query(query, (Ticket.STATUS_OPEN, assigned_to, limit, offset))
            query = """
                SELECT t.*, u.username, u.first_name, u.telegram_id,
                      a.username as assigned_username,
                      v.uuid as vpn_account_uuid
                FROM support_tickets t
                LEFT JOIN users u ON t.user_id = u.id
                LEFT JOIN users a ON t.assigned_to = a.id
                LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
                WHERE t.status = %s
                ORDER BY t.priority DESC, t.updated_at ASC
                    LIMIT %s OFFSET %s
            """
            results = execute_query(query, (Ticket.STATUS_OPEN, limit, offset))
        
        return [Ticket(result) for result in results]
        
    @staticmethod
    def get_unassigned() -> List['Ticket']:
        """
        Get all unassigned open tickets.
        
        Returns:
            List[Ticket]: List of ticket objects
        """
        query = """
            SELECT t.*, u.username, u.first_name, u.telegram_id,
                  a.username as assigned_username,
                  v.uuid as vpn_account_uuid
            FROM support_tickets t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN users a ON t.assigned_to = a.id
            LEFT JOIN vpn_accounts v ON t.vpn_account_id = v.id
            WHERE t.status = %s AND t.assigned_to IS NULL
            ORDER BY t.priority DESC, t.created_at ASC
        """
        results = execute_query(query, (Ticket.STATUS_OPEN,))
        
        return [Ticket(result) for result in results]
        
    @staticmethod
    def create(user_id: int, subject: str, first_message: str,
             category: str = CATEGORY_GENERAL, priority: str = PRIORITY_MEDIUM,
             vpn_account_id: Optional[int] = None, attachment_path: Optional[str] = None) -> Optional['Ticket']:
        """
        Create a new ticket.
        
        Args:
            user_id (int): User ID
            subject (str): Ticket subject
            first_message (str): First message content
            category (str, optional): Ticket category. Defaults to CATEGORY_GENERAL.
            priority (str, optional): Ticket priority. Defaults to PRIORITY_MEDIUM.
            vpn_account_id (Optional[int], optional): VPN account ID. Defaults to None.
            attachment_path (Optional[str], optional): Path to attachment. Defaults to None.
            
        Returns:
            Optional[Ticket]: Ticket object or None if creation failed
        """
        # Insert into database
        query = """
            INSERT INTO support_tickets (
                user_id, subject, status, priority, category,
                vpn_account_id, admin_has_unread
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        ticket_id = execute_insert(query, (
            user_id, subject, Ticket.STATUS_OPEN, priority, category,
            vpn_account_id, True
        ))
        
        if ticket_id:
            # Add first message
            TicketReply.create(
                ticket_id=ticket_id,
                user_id=user_id,
                message=first_message,
                is_from_admin=False,
                attachment_path=attachment_path
            )
            
            # Return the created ticket
            return Ticket.get_by_id(ticket_id)
            
        return None
        
    def save(self) -> bool:
        """
        Save ticket changes to the database.
        
        Returns:
            bool: True if changes were saved, False otherwise
        """
        if not self.id:
            return False
            
        query = """
            UPDATE support_tickets SET
                user_id = %s,
                subject = %s,
                status = %s,
                priority = %s,
                category = %s,
                assigned_to = %s,
                user_has_unread = %s,
                admin_has_unread = %s,
                vpn_account_id = %s,
                closed_at = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        success = execute_update(query, (
            self.user_id,
            self.subject,
            self.status,
            self.priority,
            self.category,
            self.assigned_to,
            self.user_has_unread,
            self.admin_has_unread,
            self.vpn_account_id,
            self.closed_at,
            self.id
        ))
        
        if success:
            # Clear cache
            cache_delete(f"ticket:id:{self.id}")
            
        return success
        
    def close(self, closed_by_user_id: int, close_message: Optional[str] = None) -> bool:
        """
        Close a ticket.
        
        Args:
            closed_by_user_id (int): User ID who closed the ticket
            close_message (Optional[str], optional): Close message. Defaults to None.
            
        Returns:
            bool: True if closure was successful, False otherwise
        """
        if self.status == self.STATUS_CLOSED:
            return True
            
        self.status = self.STATUS_CLOSED
        self.closed_at = datetime.now()
        
        # Add close message if provided
        if close_message:
            from models.user import User
            user = User.get_by_id(closed_by_user_id)
            is_admin = user and (user.is_admin() or user.is_superadmin())
            
            TicketReply.create(
                ticket_id=self.id,
                user_id=closed_by_user_id,
                message=close_message,
                is_from_admin=is_admin
            )
            
        return self.save()
        
    def reopen(self, reopened_by_user_id: int, reopen_message: Optional[str] = None) -> bool:
        """
        Reopen a closed ticket.
        
        Args:
            reopened_by_user_id (int): User ID who reopened the ticket
            reopen_message (Optional[str], optional): Reopen message. Defaults to None.
            
        Returns:
            bool: True if reopening was successful, False otherwise
        """
        if self.status == self.STATUS_OPEN:
            return True
            
        self.status = self.STATUS_OPEN
        self.closed_at = None
        
        # Add reopen message if provided
        if reopen_message:
            from models.user import User
            user = User.get_by_id(reopened_by_user_id)
            is_admin = user and (user.is_admin() or user.is_superadmin())
            
            TicketReply.create(
                ticket_id=self.id,
                user_id=reopened_by_user_id,
                message=reopen_message,
                is_from_admin=is_admin
            )
            
        return self.save()
        
    def assign(self, admin_id: int) -> bool:
        """
        Assign ticket to an admin.
        
        Args:
            admin_id (int): Admin user ID
            
        Returns:
            bool: True if assignment was successful, False otherwise
        """
        # Check if admin exists
        from models.user import User
        admin = User.get_by_id(admin_id)
        if not admin or not (admin.is_admin() or admin.is_superadmin()):
            logger.error(f"Cannot assign ticket to non-admin user {admin_id}")
            return False
            
        self.assigned_to = admin_id
        return self.save()
        
    def unassign(self) -> bool:
        """
        Unassign ticket.
        
        Returns:
            bool: True if unassignment was successful, False otherwise
        """
        self.assigned_to = None
        return self.save()
        
    def update_priority(self, priority: str) -> bool:
        """
        Update ticket priority.
        
        Args:
            priority (str): New priority (low, medium, high)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if priority not in [self.PRIORITY_LOW, self.PRIORITY_MEDIUM, self.PRIORITY_HIGH]:
            logger.error(f"Invalid priority: {priority}")
            return False
            
        self.priority = priority
        return self.save()
        
    def update_category(self, category: str) -> bool:
        """
        Update ticket category.
        
        Args:
            category (str): New category
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if category not in [self.CATEGORY_GENERAL, self.CATEGORY_TECHNICAL, 
                           self.CATEGORY_BILLING, self.CATEGORY_ACCOUNT]:
            logger.error(f"Invalid category: {category}")
            return False
    
        self.category = category
        return self.save()
        
    def mark_read_for_user(self) -> bool:
        """
        Mark ticket as read for user.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.user_has_unread:
            return True
            
        self.user_has_unread = False
        return self.save()
        
    def mark_read_for_admin(self) -> bool:
        """
        Mark ticket as read for admin.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.admin_has_unread:
            return True
            
        self.admin_has_unread = False
        return self.save()
        
    def add_reply(self, user_id: int, message: str, is_from_admin: bool = False,
                attachment_path: Optional[str] = None) -> Optional[TicketReply]:
        """
        Add a reply to the ticket.
        
        Args:
            user_id (int): User ID
            message (str): Reply message
            is_from_admin (bool, optional): Whether the reply is from an admin. Defaults to False.
            attachment_path (Optional[str], optional): Path to attachment. Defaults to None.
            
        Returns:
            Optional[TicketReply]: Ticket reply object or None if creation failed
        """
        return TicketReply.create(
            ticket_id=self.id,
            user_id=user_id,
            message=message,
            is_from_admin=is_from_admin,
            attachment_path=attachment_path
        )
        
    def get_replies(self) -> List[TicketReply]:
        """
        Get all replies for this ticket.
        
        Returns:
            List[TicketReply]: List of ticket reply objects
        """
        return TicketReply.get_by_ticket_id(self.id)
        
    def get_user(self):
        """
        Get the user who created this ticket.
        
        Returns:
            Optional[User]: User object or None if not found
        """
        if not self.user_id:
            return None
            
        from models.user import User
        return User.get_by_id(self.user_id)
        
    def get_assigned_admin(self):
        """
        Get the admin assigned to this ticket.
        
        Returns:
            Optional[User]: Admin user object or None if not found
        """
        if not self.assigned_to:
            return None
            
        from models.user import User
        return User.get_by_id(self.assigned_to)
        
    def get_vpn_account(self):
        """
        Get the VPN account associated with this ticket.
        
        Returns:
            Optional[VPNAccount]: VPN account object or None if not found
        """
        if not self.vpn_account_id:
            return None
    
        from models.vpn_account import VPNAccount
        return VPNAccount.get_by_id(self.vpn_account_id)
        
    @staticmethod
    def count_by_status() -> Dict[str, int]:
        """
        Count tickets by status.
        
        Returns:
            Dict[str, int]: Dictionary with ticket counts by status
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM support_tickets
            GROUP BY status
        """
        results = execute_query(query)
        
        counts = {
            Ticket.STATUS_OPEN: 0,
            Ticket.STATUS_CLOSED: 0
        }
        
        for result in results:
            counts[result['status']] = result['count']
            
        return counts
        
    @staticmethod
    def count_unassigned() -> int:
        """
        Count unassigned open tickets.
        
        Returns:
            int: Number of unassigned open tickets
        """
        query = """
            SELECT COUNT(*) as count
            FROM support_tickets
            WHERE status = %s AND assigned_to IS NULL
        """
        result = execute_query(query, (Ticket.STATUS_OPEN,), fetch="one")
        
        return result.get('count', 0) if result else 0
        
    @staticmethod
    def get_response_times() -> Dict[str, float]:
        """
        Get average response times.
        
        Returns:
            Dict[str, float]: Dictionary with average response times
        """
        # First response time
        query1 = """
            SELECT AVG(EXTRACT(EPOCH FROM (MIN(r.created_at) - t.created_at))/3600) as avg_hours
            FROM support_tickets t
            JOIN ticket_replies r ON t.id = r.ticket_id
            WHERE r.is_from_admin = TRUE
            GROUP BY t.id
        """
        result1 = execute_query(query1, fetch="one")
        
        # Response time between user and admin messages
        query2 = """
            WITH user_msgs AS (
                SELECT ticket_id, created_at
                FROM ticket_replies
                WHERE is_from_admin = FALSE
                ORDER BY created_at
            ),
            admin_responses AS (
                SELECT r.ticket_id, r.created_at, 
                       (SELECT MAX(created_at) FROM user_msgs um 
                        WHERE um.ticket_id = r.ticket_id AND um.created_at < r.created_at) as prev_user_msg
                FROM ticket_replies r
                WHERE r.is_from_admin = TRUE
                AND EXISTS (SELECT 1 FROM user_msgs um 
                           WHERE um.ticket_id = r.ticket_id AND um.created_at < r.created_at)
            )
            SELECT AVG(EXTRACT(EPOCH FROM (created_at - prev_user_msg))/3600) as avg_hours
            FROM admin_responses
        """
        result2 = execute_query(query2, fetch="one")
        
        # Resolution time (ticket created to ticket closed)
        query3 = """
            SELECT AVG(EXTRACT(EPOCH FROM (closed_at - created_at))/3600) as avg_hours
            FROM support_tickets
            WHERE status = %s AND closed_at IS NOT NULL
        """
        result3 = execute_query(query3, (Ticket.STATUS_CLOSED,), fetch="one")
        
        return {
            'first_response_hours': float(result1.get('avg_hours', 0)) if result1 and result1.get('avg_hours') else 0,
            'avg_response_hours': float(result2.get('avg_hours', 0)) if result2 and result2.get('avg_hours') else 0,
            'resolution_hours': float(result3.get('avg_hours', 0)) if result3 and result3.get('avg_hours') else 0
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ticket to dictionary.
        
        Returns:
            Dict[str, Any]: Ticket data as dictionary
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'user_has_unread': self.user_has_unread,
            'admin_has_unread': self.admin_has_unread,
            'vpn_account_id': self.vpn_account_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'username': self.username,
            'first_name': self.first_name,
            'telegram_id': self.telegram_id,
            'assigned_username': self.assigned_username,
            'vpn_account_uuid': self.vpn_account_uuid
        } 