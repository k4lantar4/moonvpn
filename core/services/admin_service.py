"""
Admin service for MoonVPN.

This module provides functionality for managing admin operations,
including system monitoring, notifications, and configuration.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.models.admin_config import AdminConfig
from app.core.models.user import User
from app.core.models.transaction import Transaction
from app.core.models.server import Server
from app.core.services.notification_service import NotificationService
from app.core.exceptions import AdminError

logger = logging.getLogger(__name__)

class AdminService:
    """Service for managing admin operations."""
    
    def __init__(self, db: Session):
        """Initialize admin service."""
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            # Get server health
            servers = self.db.query(Server).all()
            online_servers = len([s for s in servers if s.is_online])
            
            # Get user stats
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Get transaction stats
            pending_transactions = self.db.query(Transaction).filter(
                Transaction.status == 'pending'
            ).count()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'servers': {
                    'total': len(servers),
                    'online': online_servers,
                    'status': 'healthy' if online_servers == len(servers) else 'degraded'
                },
                'users': {
                    'total': total_users,
                    'active': active_users
                },
                'transactions': {
                    'pending': pending_transactions
                }
            }
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            raise AdminError(f"Failed to get system health: {str(e)}")
    
    async def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin statistics."""
        try:
            # Get admin users
            admins = self.db.query(User).filter(User.is_admin == True).all()
            active_admins = [a for a in admins if a.last_active and 
                           a.last_active >= datetime.utcnow() - timedelta(hours=24)]
            
            return {
                'total_admins': len(admins),
                'active_admins': len(active_admins),
                'last_update': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting admin stats: {str(e)}")
            raise AdminError(f"Failed to get admin stats: {str(e)}")
    
    async def get_daily_report(self) -> Dict[str, Any]:
        """Get daily system report."""
        try:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            # Get new users
            new_users = self.db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            # Get active users
            active_users = self.db.query(User).filter(
                User.last_active >= yesterday
            ).count()
            
            # Get revenue
            revenue = self.db.query(func.sum(Transaction.amount)).filter(
                func.date(Transaction.created_at) == today,
                Transaction.status == 'completed'
            ).scalar() or 0
            
            return {
                'date': today.isoformat(),
                'new_users': new_users,
                'active_users': active_users,
                'total_revenue': float(revenue),
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting daily report: {str(e)}")
            raise AdminError(f"Failed to get daily report: {str(e)}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            # Get server performance
            servers = self.db.query(Server).all()
            server_metrics = []
            
            for server in servers:
                metrics = {
                    'server_id': server.id,
                    'cpu_usage': server.get_cpu_usage(),
                    'memory_usage': server.get_memory_usage(),
                    'network_load': server.get_network_load(),
                    'active_connections': server.get_active_connections()
                }
                server_metrics.append(metrics)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'servers': server_metrics,
                'average_response_time': self._calculate_avg_response_time(),
                'error_rate': self._calculate_error_rate()
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            raise AdminError(f"Failed to get performance metrics: {str(e)}")
    
    async def update_admin_setting(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None
    ) -> None:
        """Update an admin configuration setting."""
        try:
            AdminConfig.set_setting(self.db, key, value, description)
            logger.info(f"Updated admin setting: {key}")
        except Exception as e:
            logger.error(f"Error updating admin setting: {str(e)}")
            raise AdminError(f"Failed to update admin setting: {str(e)}")
    
    async def get_admin_setting(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get an admin configuration setting."""
        try:
            return AdminConfig.get_setting(self.db, key, default)
        except Exception as e:
            logger.error(f"Error getting admin setting: {str(e)}")
            raise AdminError(f"Failed to get admin setting: {str(e)}")
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average API response time."""
        # TODO: Implement actual response time calculation
        return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate system error rate."""
        # TODO: Implement actual error rate calculation
        return 0.0 