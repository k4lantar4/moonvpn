"""
Log service for MoonVPN Telegram Bot.

This module provides functionality for managing detailed system logs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.core.database.models import Server, SystemLog, User, Order, Transaction
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class LogService:
    """Service for managing detailed system logs."""
    
    def __init__(self):
        self.log_levels = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
            "debug": "🔍"
        }
    
    async def create_log(
        self,
        db: Session,
        level: str,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        server_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new system log entry."""
        try:
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
            db.commit()
            
            return {
                "id": log.id,
                "level": level,
                "category": category,
                "message": message,
                "details": details or {},
                "server_id": server_id,
                "user_id": user_id,
                "created_at": log.created_at
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
        limit: int = 100
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
                    "created_at": log.created_at
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
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting log stats: {str(e)}")
            raise
    
    async def get_user_activity_logs(
        self,
        db: Session,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get detailed activity logs for a specific user."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get user info
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get system logs
            system_logs = db.query(SystemLog).filter(
                and_(
                    SystemLog.user_id == user_id,
                    SystemLog.created_at >= start_date
                )
            ).order_by(
                SystemLog.created_at.desc()
            ).all()
            
            # Get orders
            orders = db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= start_date
                )
            ).order_by(
                Order.created_at.desc()
            ).all()
            
            # Get transactions
            transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date
                )
            ).order_by(
                Transaction.created_at.desc()
            ).all()
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "created_at": user.created_at
                },
                "system_logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "category": log.category,
                        "message": log.message,
                        "details": log.details,
                        "created_at": log.created_at
                    }
                    for log in system_logs
                ],
                "orders": [
                    {
                        "id": order.id,
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
                        "created_at": transaction.created_at
                    }
                    for transaction in transactions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity logs: {str(e)}")
            raise
    
    async def get_server_logs(
        self,
        db: Session,
        server_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get detailed logs for a specific server."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get server info
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Get system logs
            system_logs = db.query(SystemLog).filter(
                and_(
                    SystemLog.server_id == server_id,
                    SystemLog.created_at >= start_date
                )
            ).order_by(
                SystemLog.created_at.desc()
            ).all()
            
            return {
                "server": {
                    "id": server.id,
                    "name": server.name,
                    "ip": server.ip,
                    "status": server.status
                },
                "logs": [
                    {
                        "id": log.id,
                        "level": log.level,
                        "category": log.category,
                        "message": log.message,
                        "details": log.details,
                        "created_at": log.created_at
                    }
                    for log in system_logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting server logs: {str(e)}")
            raise 