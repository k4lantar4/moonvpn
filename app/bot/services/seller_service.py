"""
Seller service for MoonVPN Telegram Bot.

This module provides functionality for managing resellers and their commissions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.core.database.models import User, Transaction, Order
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class SellerService:
    """Service for managing resellers and their commissions."""
    
    def __init__(self):
        self.commission_rate = 0.1  # 10% commission rate
    
    async def get_seller_stats(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get seller statistics for the specified period."""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get total sellers
            total_sellers = db.query(User).filter(User.is_seller == True).count()
            
            # Get active sellers (with sales in the period)
            active_sellers = db.query(User).join(
                Order,
                User.id == Order.seller_id
            ).filter(
                and_(
                    User.is_seller == True,
                    Order.created_at >= start_date
                )
            ).distinct().count()
            
            # Get total sales and commission
            sales_stats = db.query(
                func.count(Order.id).label('total_sales'),
                func.sum(Order.amount).label('total_amount'),
                func.sum(Order.commission).label('total_commission')
            ).filter(
                Order.created_at >= start_date
            ).first()
            
            # Get top sellers
            top_sellers = db.query(
                User.username,
                User.phone_number,
                func.count(Order.id).label('sales_count'),
                func.sum(Order.amount).label('total_amount'),
                func.sum(Order.commission).label('total_commission')
            ).join(
                Order,
                User.id == Order.seller_id
            ).filter(
                and_(
                    User.is_seller == True,
                    Order.created_at >= start_date
                )
            ).group_by(
                User.id,
                User.username,
                User.phone_number
            ).order_by(
                func.sum(Order.amount).desc()
            ).limit(5).all()
            
            return {
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_sellers": total_sellers,
                "active_sellers": active_sellers,
                "total_sales": sales_stats.total_sales or 0,
                "total_amount": sales_stats.total_amount or 0,
                "total_commission": sales_stats.total_commission or 0,
                "top_sellers": [
                    {
                        "username": seller.username,
                        "phone_number": seller.phone_number,
                        "sales_count": seller.sales_count,
                        "total_amount": seller.total_amount,
                        "total_commission": seller.total_commission
                    }
                    for seller in top_sellers
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting seller stats: {str(e)}")
            raise
    
    async def get_seller_details(self, seller_id: int, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get detailed statistics for a specific seller."""
        try:
            seller = db.query(User).filter(
                and_(
                    User.id == seller_id,
                    User.is_seller == True
                )
            ).first()
            
            if not seller:
                raise HTTPException(status_code=404, detail="Seller not found")
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get sales statistics
            sales_stats = db.query(
                func.count(Order.id).label('total_sales'),
                func.sum(Order.amount).label('total_amount'),
                func.sum(Order.commission).label('total_commission')
            ).filter(
                and_(
                    Order.seller_id == seller_id,
                    Order.created_at >= start_date
                )
            ).first()
            
            # Get recent sales
            recent_sales = db.query(Order).filter(
                and_(
                    Order.seller_id == seller_id,
                    Order.created_at >= start_date
                )
            ).order_by(
                Order.created_at.desc()
            ).limit(10).all()
            
            return {
                "seller_id": seller_id,
                "username": seller.username,
                "phone_number": seller.phone_number,
                "created_at": seller.created_at,
                "period_days": days,
                "start_date": start_date,
                "end_date": datetime.now(),
                "total_sales": sales_stats.total_sales or 0,
                "total_amount": sales_stats.total_amount or 0,
                "total_commission": sales_stats.total_commission or 0,
                "recent_sales": [
                    {
                        "id": sale.id,
                        "amount": sale.amount,
                        "commission": sale.commission,
                        "created_at": sale.created_at,
                        "status": sale.status
                    }
                    for sale in recent_sales
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting seller details: {str(e)}")
            raise
    
    async def get_seller_balance(self, seller_id: int, db: Session) -> Dict[str, Any]:
        """Get current balance and pending commissions for a seller."""
        try:
            seller = db.query(User).filter(
                and_(
                    User.id == seller_id,
                    User.is_seller == True
                )
            ).first()
            
            if not seller:
                raise HTTPException(status_code=404, detail="Seller not found")
            
            # Get pending commissions
            pending_commissions = db.query(
                func.sum(Order.commission).label('total_pending')
            ).filter(
                and_(
                    Order.seller_id == seller_id,
                    Order.commission_paid == False
                )
            ).first()
            
            # Get paid commissions
            paid_commissions = db.query(
                func.sum(Order.commission).label('total_paid')
            ).filter(
                and_(
                    Order.seller_id == seller_id,
                    Order.commission_paid == True
                )
            ).first()
            
            return {
                "seller_id": seller_id,
                "username": seller.username,
                "phone_number": seller.phone_number,
                "pending_commission": pending_commissions.total_pending or 0,
                "paid_commission": paid_commissions.total_paid or 0,
                "total_commission": (pending_commissions.total_pending or 0) + (paid_commissions.total_paid or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting seller balance: {str(e)}")
            raise
    
    async def mark_commission_paid(self, seller_id: int, db: Session) -> Dict[str, Any]:
        """Mark all pending commissions as paid for a seller."""
        try:
            seller = db.query(User).filter(
                and_(
                    User.id == seller_id,
                    User.is_seller == True
                )
            ).first()
            
            if not seller:
                raise HTTPException(status_code=404, detail="Seller not found")
            
            # Update pending commissions
            result = db.query(Order).filter(
                and_(
                    Order.seller_id == seller_id,
                    Order.commission_paid == False
                )
            ).update(
                {
                    "commission_paid": True,
                    "commission_paid_at": datetime.now()
                }
            )
            
            db.commit()
            
            return {
                "seller_id": seller_id,
                "username": seller.username,
                "phone_number": seller.phone_number,
                "updated_count": result,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error marking commission as paid: {str(e)}")
            raise 