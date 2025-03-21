"""
Log service for MoonVPN Telegram Bot.

This module provides functionality for managing detailed system logs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from fastapi import HTTPException

from app.core.database.models import (
    SystemLog, User, Server, Order, Transaction,
    LogCategory, LogLevel, LogRetention
)
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class LogService:
    """Service for managing detailed system logs."""
    
    def __init__(self):
        # Log retention periods (days)
        self.retention_periods = {
            "debug": 7,
            "info": 30,
            "warning": 90,
            "error": 365,
            "critical": 365
        }
        
        # Log level emojis
        self.level_emojis = {
            "debug": "🔍",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
            "success": "✅"
        }
        
        # Log category emojis
        self.category_emojis = {
            "system": "⚙️",
            "security": "🔒",
            "performance": "⚡",
            "user": "👤",
            "payment": "💳",
            "network": "🌐",
            "database": "🗄️",
            "backup": "💾",
            "alert": "🚨",
            "other": "📝"
        }
        
        # Log level colors for UI
        self.level_colors = {
            "debug": "#808080",
            "info": "#0000FF",
            "warning": "#FFA500",
            "error": "#FF0000",
            "critical": "#800000",
            "success": "#008000"
        }
    
    async def create_log(
        self,
        db: Session,
        level: str,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        server_id: Optional[int] = None,
        user_id: Optional[int] = None,
        retention_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new system log entry."""
        try:
            # Validate log level and category
            if level not in self.retention_periods:
                raise ValueError(f"Invalid log level: {level}")
            if category not in self.category_emojis:
                raise ValueError(f"Invalid log category: {category}")
            
            # Create log entry
            log = SystemLog(
                level=level,
                category=category,
                message=message,
                details=details or {},
                server_id=server_id,
                user_id=user_id,
                created_at=datetime.now()
            )
            db.add(log)
            
            # Create retention record if specified
            if retention_days:
                retention = LogRetention(
                    log_id=log.id,
                    retention_days=retention_days,
                    expires_at=datetime.now() + timedelta(days=retention_days)
                )
                db.add(retention)
            
            db.commit()
            
            return {
                "id": log.id,
                "level": log.level,
                "category": log.category,
                "message": log.message,
                "details": log.details,
                "server_id": log.server_id,
                "user_id": log.user_id,
                "created_at": log.created_at,
                "level_emoji": self.level_emojis.get(log.level, "📝"),
                "category_emoji": self.category_emojis.get(log.category, "📝"),
                "level_color": self.level_colors.get(log.level, "#000000")
            }
            
        except Exception as e:
            logger.error(f"Error creating log: {str(e)}")
            raise
    
    async def get_logs(
        self,
        db: Session,
        level: Optional[str] = None,
        category: Optional[str] = None,
        server_id: Optional[int] = None,
        user_id: Optional[int] = None,
        days: int = 7,
        limit: int = 100,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """Get filtered system logs."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            query = db.query(SystemLog).filter(
                SystemLog.created_at >= start_date
            )
            
            if level:
                query = query.filter(SystemLog.level == level)
            if category:
                query = query.filter(SystemLog.category == category)
            if server_id:
                query = query.filter(SystemLog.server_id == server_id)
            if user_id:
                query = query.filter(SystemLog.user_id == user_id)
            
            if not include_expired:
                query = query.join(
                    LogRetention,
                    SystemLog.id == LogRetention.log_id,
                    isouter=True
                ).filter(
                    or_(
                        LogRetention.expires_at > datetime.now(),
                        LogRetention.id.is_(None)
                    )
                )
            
            logs = query.order_by(
                SystemLog.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": log.id,
                    "level": log.level,
                    "category": log.category,
                    "message": log.message,
                    "details": log.details,
                    "server_id": log.server_id,
                    "user_id": log.user_id,
                    "created_at": log.created_at,
                    "level_emoji": self.level_emojis.get(log.level, "📝"),
                    "category_emoji": self.category_emojis.get(log.category, "📝"),
                    "level_color": self.level_colors.get(log.level, "#000000")
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            raise
    
    async def get_log_stats(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Get log statistics for the specified period."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get total logs
            total_logs = db.query(SystemLog).filter(
                SystemLog.created_at >= start_date
            ).count()
            
            # Get logs by level
            logs_by_level = db.query(
                SystemLog.level,
                func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.created_at >= start_date
            ).group_by(
                SystemLog.level
            ).all()
            
            # Get logs by category
            logs_by_category = db.query(
                SystemLog.category,
                func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.created_at >= start_date
            ).group_by(
                SystemLog.category
            ).all()
            
            # Get logs by server
            logs_by_server = db.query(
                SystemLog.server_id,
                func.count(SystemLog.id).label('count')
            ).filter(
                and_(
                    SystemLog.created_at >= start_date,
                    SystemLog.server_id.isnot(None)
                )
            ).group_by(
                SystemLog.server_id
            ).all()
            
            # Get daily log counts
            daily_counts = db.query(
                func.date(SystemLog.created_at).label('date'),
                func.count(SystemLog.id).label('count'),
                func.count(case((SystemLog.level == 'error', 1), else_=None)).label('error_count'),
                func.count(case((SystemLog.level == 'critical', 1), else_=None)).label('critical_count')
            ).filter(
                SystemLog.created_at >= start_date
            ).group_by(
                func.date(SystemLog.created_at)
            ).all()
            
            return {
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_logs": total_logs,
                "logs_by_level": {
                    level: count
                    for level, count in logs_by_level
                },
                "logs_by_category": {
                    category: count
                    for category, count in logs_by_category
                },
                "logs_by_server": {
                    server_id: count
                    for server_id, count in logs_by_server
                },
                "daily_counts": [
                    {
                        "date": count.date,
                        "total": count.count,
                        "errors": count.error_count,
                        "critical": count.critical_count
                    }
                    for count in daily_counts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting log stats: {str(e)}")
            raise
    
    async def get_user_activity_logs(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get detailed activity logs for a specific user."""
        try:
            # Get user info
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get user's system logs
            system_logs = db.query(SystemLog).filter(
                and_(
                    SystemLog.user_id == user_id,
                    SystemLog.created_at >= start_date
                )
            ).order_by(
                SystemLog.created_at.desc()
            ).all()
            
            # Get user's orders
            orders = db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= start_date
                )
            ).order_by(
                Order.created_at.desc()
            ).all()
            
            # Get user's transactions
            transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date
                )
            ).order_by(
                Transaction.created_at.desc()
            ).all()
            
            # Calculate statistics
            total_orders = len(orders)
            total_transactions = len(transactions)
            total_amount = sum(t.amount for t in transactions if t.status == "success")
            
            # Get activity by hour
            activity_by_hour = db.query(
                func.extract('hour', SystemLog.created_at).label('hour'),
                func.count(SystemLog.id).label('count')
            ).filter(
                and_(
                    SystemLog.user_id == user_id,
                    SystemLog.created_at >= start_date
                )
            ).group_by(
                func.extract('hour', SystemLog.created_at)
            ).all()
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at
                },
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_orders": total_orders,
                "total_transactions": total_transactions,
                "total_amount": total_amount,
                "system_logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "category": log.category,
                        "message": log.message,
                        "details": log.details,
                        "created_at": log.created_at,
                        "level_emoji": self.level_emojis.get(log.level, "📝"),
                        "category_emoji": self.category_emojis.get(log.category, "📝"),
                        "level_color": self.level_colors.get(log.level, "#000000")
                    }
                    for log in system_logs
                ],
                "orders": [
                    {
                        "id": order.id,
                        "plan_id": order.plan_id,
                        "amount": order.amount,
                        "status": order.status,
                        "created_at": order.created_at
                    }
                    for order in orders
                ],
                "transactions": [
                    {
                        "id": transaction.id,
                        "amount": transaction.amount,
                        "status": transaction.status,
                        "payment_method": transaction.payment_method,
                        "created_at": transaction.created_at
                    }
                    for transaction in transactions
                ],
                "activity_by_hour": {
                    hour: count
                    for hour, count in activity_by_hour
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity logs: {str(e)}")
            raise
    
    async def get_server_logs(
        self,
        db: Session,
        server_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get detailed logs for a specific server."""
        try:
            # Get server info
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get server's system logs
            system_logs = db.query(SystemLog).filter(
                and_(
                    SystemLog.server_id == server_id,
                    SystemLog.created_at >= start_date
                )
            ).order_by(
                SystemLog.created_at.desc()
            ).all()
            
            # Calculate statistics
            total_logs = len(system_logs)
            error_logs = len([log for log in system_logs if log.level in ["error", "critical"]])
            warning_logs = len([log for log in system_logs if log.level == "warning"])
            
            # Get logs by level
            logs_by_level = db.query(
                SystemLog.level,
                func.count(SystemLog.id).label('count')
            ).filter(
                and_(
                    SystemLog.server_id == server_id,
                    SystemLog.created_at >= start_date
                )
            ).group_by(
                SystemLog.level
            ).all()
            
            # Get logs by category
            logs_by_category = db.query(
                SystemLog.category,
                func.count(SystemLog.id).label('count')
            ).filter(
                and_(
                    SystemLog.server_id == server_id,
                    SystemLog.created_at >= start_date
                )
            ).group_by(
                SystemLog.category
            ).all()
            
            # Get daily log counts
            daily_counts = db.query(
                func.date(SystemLog.created_at).label('date'),
                func.count(SystemLog.id).label('count'),
                func.count(case((SystemLog.level == 'error', 1), else_=None)).label('error_count'),
                func.count(case((SystemLog.level == 'critical', 1), else_=None)).label('critical_count')
            ).filter(
                and_(
                    SystemLog.server_id == server_id,
                    SystemLog.created_at >= start_date
                )
            ).group_by(
                func.date(SystemLog.created_at)
            ).all()
            
            return {
                "server": {
                    "id": server.id,
                    "name": server.name,
                    "ip": server.ip,
                    "status": server.status
                },
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_logs": total_logs,
                "error_logs": error_logs,
                "warning_logs": warning_logs,
                "logs_by_level": {
                    level: count
                    for level, count in logs_by_level
                },
                "logs_by_category": {
                    category: count
                    for category, count in logs_by_category
                },
                "system_logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "category": log.category,
                        "message": log.message,
                        "details": log.details,
                        "created_at": log.created_at,
                        "level_emoji": self.level_emojis.get(log.level, "📝"),
                        "category_emoji": self.category_emojis.get(log.category, "📝"),
                        "level_color": self.level_colors.get(log.level, "#000000")
                    }
                    for log in system_logs
                ],
                "daily_counts": [
                    {
                        "date": count.date,
                        "total": count.count,
                        "errors": count.error_count,
                        "critical": count.critical_count
                    }
                    for count in daily_counts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting server logs: {str(e)}")
            raise
    
    async def cleanup_expired_logs(self, db: Session) -> Dict[str, Any]:
        """Clean up expired logs based on retention periods."""
        try:
            removed_count = 0
            failed_deletions = []
            
            # Get expired retention records
            expired = db.query(LogRetention).filter(
                LogRetention.expires_at <= datetime.now()
            ).all()
            
            for retention in expired:
                try:
                    # Delete log
                    log = db.query(SystemLog).filter(
                        SystemLog.id == retention.log_id
                    ).first()
                    
                    if log:
                        db.delete(log)
                        removed_count += 1
                    
                    # Delete retention record
                    db.delete(retention)
                    
                except Exception as e:
                    logger.error(f"Error deleting expired log {retention.log_id}: {str(e)}")
                    failed_deletions.append({
                        "log_id": retention.log_id,
                        "error": str(e)
                    })
            
            # Clean up logs without retention records
            logs_without_retention = db.query(SystemLog).outerjoin(
                LogRetention,
                SystemLog.id == LogRetention.log_id
            ).filter(
                LogRetention.id.is_(None)
            ).all()
            
            for log in logs_without_retention:
                try:
                    # Check if log is older than default retention period
                    retention_days = self.retention_periods.get(log.level, 30)
                    if (datetime.now() - log.created_at).days > retention_days:
                        db.delete(log)
                        removed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error deleting old log {log.id}: {str(e)}")
                    failed_deletions.append({
                        "log_id": log.id,
                        "error": str(e)
                    })
            
            db.commit()
            
            return {
                "removed_count": removed_count,
                "failed_deletions": failed_deletions,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired logs: {str(e)}")
            raise 