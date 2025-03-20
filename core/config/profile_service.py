"""
User profile management service for MoonVPN Telegram Bot.

This module provides functionality for managing user profiles,
including profile information, settings, preferences, and history.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.database.models import User, Subscription, Transaction, Point
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class ProfileService:
    """Service for managing user profiles and related data."""
    
    async def get_profile(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get active subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            ).first()
            
            # Get points balance
            points = db.query(Point).filter(Point.user_id == user_id).first()
            
            return {
                "id": user.id,
                "phone": user.phone,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "is_active": user.is_active,
                "subscription": {
                    "plan": subscription.plan.name if subscription else None,
                    "expires_at": subscription.expires_at if subscription else None,
                    "status": subscription.status if subscription else None
                },
                "points": points.balance if points else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {str(e)}")
            raise
    
    async def update_profile(self, user_id: int, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Update user profile information."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update allowed fields
            allowed_fields = ["notification_preferences", "language", "auto_renewal"]
            for field, value in data.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            db.commit()
            return await self.get_profile(user_id, db)
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")
            raise
    
    async def get_subscription_history(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get user's subscription history."""
        try:
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).order_by(Subscription.created_at.desc()).all()
            
            return [{
                "id": sub.id,
                "plan": sub.plan.name,
                "status": sub.status,
                "created_at": sub.created_at,
                "expires_at": sub.expires_at,
                "amount": sub.amount
            } for sub in subscriptions]
            
        except Exception as e:
            logger.error(f"Error getting subscription history for user {user_id}: {str(e)}")
            raise
    
    async def get_transaction_history(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get user's transaction history."""
        try:
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(Transaction.created_at.desc()).all()
            
            return [{
                "id": trans.id,
                "type": trans.type,
                "amount": trans.amount,
                "status": trans.status,
                "created_at": trans.created_at,
                "description": trans.description
            } for trans in transactions]
            
        except Exception as e:
            logger.error(f"Error getting transaction history for user {user_id}: {str(e)}")
            raise
    
    async def get_points_history(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get user's points history."""
        try:
            points = db.query(Point).filter(Point.user_id == user_id).first()
            if not points:
                return []
            
            return [{
                "id": record.id,
                "amount": record.amount,
                "type": record.type,
                "description": record.description,
                "created_at": record.created_at
            } for record in points.history]
            
        except Exception as e:
            logger.error(f"Error getting points history for user {user_id}: {str(e)}")
            raise
    
    async def get_referral_info(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user's referral information."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get referral code
            referral_code = user.referral_code
            
            # Get referred users
            referred_users = db.query(User).filter(
                User.referred_by == referral_code
            ).all()
            
            # Get referral rewards
            referral_rewards = db.query(Point).filter(
                Point.user_id == user_id,
                Point.type == "referral"
            ).all()
            
            return {
                "referral_code": referral_code,
                "referred_count": len(referred_users),
                "total_rewards": sum(reward.amount for reward in referral_rewards)
            }
            
        except Exception as e:
            logger.error(f"Error getting referral info for user {user_id}: {str(e)}")
            raise 