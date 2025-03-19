"""
Transaction service for MoonVPN Telegram Bot.

This module provides functionality for monitoring transactions and generating statistics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.core.database.models import Transaction, Order, User
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class TransactionService:
    """Service for managing transactions and generating statistics."""
    
    def __init__(self):
        pass
    
    async def get_transaction_stats(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get transaction statistics for the specified period."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get total transactions and amount
            total_stats = db.query(
                func.count(Transaction.id).label('total_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.created_at >= start_date
            ).first()
            
            # Get successful transactions
            success_stats = db.query(
                func.count(Transaction.id).label('success_count'),
                func.sum(Transaction.amount).label('success_amount')
            ).filter(
                and_(
                    Transaction.created_at >= start_date,
                    Transaction.status == 'success'
                )
            ).first()
            
            # Get failed transactions
            failed_stats = db.query(
                func.count(Transaction.id).label('failed_count'),
                func.sum(Transaction.amount).label('failed_amount')
            ).filter(
                and_(
                    Transaction.created_at >= start_date,
                    Transaction.status == 'failed'
                )
            ).first()
            
            # Get daily transaction counts
            daily_counts = db.query(
                func.date(Transaction.created_at).label('date'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.created_at >= start_date
            ).group_by(
                func.date(Transaction.created_at)
            ).all()
            
            return {
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_transactions": total_stats.total_count or 0,
                "total_amount": total_stats.total_amount or 0,
                "successful_transactions": success_stats.success_count or 0,
                "successful_amount": success_stats.success_amount or 0,
                "failed_transactions": failed_stats.failed_count or 0,
                "failed_amount": failed_stats.failed_amount or 0,
                "daily_counts": [
                    {"date": count.date, "count": count.count}
                    for count in daily_counts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction stats: {str(e)}")
            raise
    
    async def get_recent_transactions(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions with user details."""
        try:
            transactions = db.query(
                Transaction,
                User.username,
                User.phone_number
            ).join(
                User,
                Transaction.user_id == User.id
            ).order_by(
                Transaction.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": t.Transaction.id,
                    "amount": t.Transaction.amount,
                    "status": t.Transaction.status,
                    "method": t.Transaction.method,
                    "created_at": t.Transaction.created_at,
                    "username": t.username,
                    "phone_number": t.phone_number
                }
                for t in transactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent transactions: {str(e)}")
            raise
    
    async def get_failed_transactions(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failed transactions with error details."""
        try:
            transactions = db.query(
                Transaction,
                User.username,
                User.phone_number
            ).join(
                User,
                Transaction.user_id == User.id
            ).filter(
                Transaction.status == 'failed'
            ).order_by(
                Transaction.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": t.Transaction.id,
                    "amount": t.Transaction.amount,
                    "method": t.Transaction.method,
                    "error": t.Transaction.error_message,
                    "created_at": t.Transaction.created_at,
                    "username": t.username,
                    "phone_number": t.phone_number
                }
                for t in transactions
            ]
            
        except Exception as e:
            logger.error(f"Error getting failed transactions: {str(e)}")
            raise
    
    async def get_payment_method_stats(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get statistics by payment method."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get stats for each payment method
            method_stats = db.query(
                Transaction.method,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(case((Transaction.status == 'success', 1), else_=0)).label('success_count')
            ).filter(
                Transaction.created_at >= start_date
            ).group_by(
                Transaction.method
            ).all()
            
            return {
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "methods": [
                    {
                        "method": stat.method,
                        "total_count": stat.count,
                        "total_amount": stat.total_amount,
                        "success_count": stat.success_count,
                        "success_rate": (stat.success_count / stat.count * 100) if stat.count > 0 else 0
                    }
                    for stat in method_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting payment method stats: {str(e)}")
            raise 