"""
Broadcast service for managing mass messages and notifications.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from core.config import settings
from core.database import get_db

logger = logging.getLogger(__name__)

class BroadcastService:
    """Service for managing broadcast messages."""
    
    def __init__(self):
        """Initialize broadcast service."""
        self.db = get_db()
    
    async def create_broadcast(
        self,
        sender_id: int,
        message: str,
        target: str = 'all',
        schedule_time: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Any]:
        """Create a new broadcast message."""
        try:
            # Create broadcast data
            broadcast_data = {
                'sender_id': sender_id,
                'message': message,
                'target': target,
                'schedule_time': schedule_time,
                'filters': filters or {},
                'status': 'pending',
                'created_at': datetime.now(),
                'sent_count': 0,
                'failed_count': 0,
                'completed_at': None
            }
            
            result = await self.db.broadcasts.insert_one(broadcast_data)
            broadcast_data['_id'] = result.inserted_id
            
            return True, broadcast_data
            
        except Exception as e:
            logger.error("Error creating broadcast: %s", str(e))
            return False, "خطا در ایجاد پیام گروهی"
    
    async def get_broadcast(self, broadcast_id: str) -> Optional[Dict[str, Any]]:
        """Get broadcast by ID."""
        try:
            broadcast = await self.db.broadcasts.find_one({'_id': broadcast_id})
            return broadcast
        except Exception as e:
            logger.error("Error getting broadcast: %s", str(e))
            return None
    
    async def get_pending_broadcasts(self) -> List[Dict[str, Any]]:
        """Get list of pending broadcasts."""
        try:
            now = datetime.now()
            broadcasts = await self.db.broadcasts.find({
                'status': 'pending',
                '$or': [
                    {'schedule_time': None},
                    {'schedule_time': {'$lte': now}}
                ]
            }).to_list(length=None)
            return broadcasts
        except Exception as e:
            logger.error("Error getting pending broadcasts: %s", str(e))
            return []
    
    async def update_broadcast_status(
        self,
        broadcast_id: str,
        status: str,
        sent_count: int = 0,
        failed_count: int = 0
    ) -> bool:
        """Update broadcast status."""
        try:
            update_data = {
                'status': status,
                'sent_count': sent_count,
                'failed_count': failed_count
            }
            
            if status in ['completed', 'failed']:
                update_data['completed_at'] = datetime.now()
            
            result = await self.db.broadcasts.update_one(
                {'_id': broadcast_id},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error("Error updating broadcast status: %s", str(e))
            return False
    
    async def get_target_users(
        self,
        target: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get list of users matching target and filters."""
        try:
            query = {}
            
            # Apply target filter
            if target == 'active':
                cutoff_date = datetime.now() - timedelta(days=7)
                query['last_active'] = {'$gte': cutoff_date}
            elif target == 'inactive':
                cutoff_date = datetime.now() - timedelta(days=30)
                query['last_active'] = {'$lt': cutoff_date}
            elif target == 'premium':
                query['role'] = {'$in': ['admin', 'seller']}
            
            # Apply additional filters
            if filters:
                if 'min_traffic' in filters:
                    query['total_traffic'] = {'$gte': filters['min_traffic']}
                if 'min_spent' in filters:
                    query['total_spent'] = {'$gte': filters['min_spent']}
                if 'has_active_account' in filters and filters['has_active_account']:
                    now = datetime.now()
                    query['vpn_accounts'] = {
                        '$elemMatch': {
                            'expiry_date': {'$gt': now.strftime('%Y-%m-%d')}
                        }
                    }
            
            users = await self.db.users.find(query).to_list(length=None)
            return users
            
        except Exception as e:
            logger.error("Error getting target users: %s", str(e))
            return []
    
    async def get_broadcast_stats(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get broadcast statistics for the last N days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get broadcasts in date range
            broadcasts = await self.db.broadcasts.find({
                'created_at': {'$gte': cutoff_date}
            }).to_list(length=None)
            
            # Calculate stats
            total_broadcasts = len(broadcasts)
            total_sent = sum(b.get('sent_count', 0) for b in broadcasts)
            total_failed = sum(b.get('failed_count', 0) for b in broadcasts)
            
            # Group by status
            status_counts = {}
            for b in broadcasts:
                status = b.get('status', 'unknown')
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
            
            # Group by target
            target_counts = {}
            for b in broadcasts:
                target = b.get('target', 'unknown')
                if target not in target_counts:
                    target_counts[target] = 0
                target_counts[target] += 1
            
            return {
                'total_broadcasts': total_broadcasts,
                'total_sent': total_sent,
                'total_failed': total_failed,
                'status_breakdown': status_counts,
                'target_breakdown': target_counts
            }
            
        except Exception as e:
            logger.error("Error getting broadcast stats: %s", str(e))
            return {
                'total_broadcasts': 0,
                'total_sent': 0,
                'total_failed': 0,
                'status_breakdown': {},
                'target_breakdown': {}
            }
    
    async def cancel_broadcast(self, broadcast_id: str) -> bool:
        """Cancel a pending broadcast."""
        try:
            result = await self.db.broadcasts.update_one(
                {
                    '_id': broadcast_id,
                    'status': 'pending'
                },
                {'$set': {'status': 'cancelled'}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error("Error cancelling broadcast: %s", str(e))
            return False
    
    async def retry_failed_broadcast(self, broadcast_id: str) -> Tuple[bool, Any]:
        """Create a new broadcast from a failed one."""
        try:
            # Get original broadcast
            broadcast = await self.get_broadcast(broadcast_id)
            if not broadcast:
                return False, "پیام گروهی یافت نشد"
            
            # Create new broadcast with same data
            new_broadcast = {
                'sender_id': broadcast['sender_id'],
                'message': broadcast['message'],
                'target': broadcast['target'],
                'filters': broadcast['filters'],
                'status': 'pending',
                'created_at': datetime.now(),
                'sent_count': 0,
                'failed_count': 0,
                'completed_at': None,
                'original_broadcast_id': broadcast_id
            }
            
            result = await self.db.broadcasts.insert_one(new_broadcast)
            new_broadcast['_id'] = result.inserted_id
            
            return True, new_broadcast
            
        except Exception as e:
            logger.error("Error retrying broadcast: %s", str(e))
            return False, "خطا در تلاش مجدد پیام گروهی" 