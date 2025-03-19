"""
Points and rewards management service.

This module handles:
- Points earning and expiry
- Reward redemption
- VIP status management
- Points history
"""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VIPLevel(Enum):
    """VIP level enumeration."""
    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

@dataclass
class PointsTransaction:
    """Points transaction data class."""
    id: str
    user_id: str
    amount: int
    type: str  # earned, spent, expired
    source: str  # purchase, referral, reward, etc.
    description: str
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class UserPoints:
    """User points information data class."""
    user_id: str
    total_points: int
    available_points: int
    vip_level: VIPLevel
    points_history: List[PointsTransaction]
    last_activity: datetime
    referral_code: str
    referred_by: Optional[str]
    referral_count: int
    total_earned: int
    total_spent: int
    total_expired: int

class PointsManager:
    """Manages user points and rewards system."""
    
    def __init__(self):
        self.users: Dict[str, UserPoints] = {}
        self.referral_codes: Dict[str, str] = {}  # code -> user_id
        self.points_rules = {
            "purchase": 10,  # 10 points per 1000 toman
            "referral": 100,  # 100 points per referral
            "daily_login": 5,  # 5 points per daily login
            "vip_bonus": {
                VIPLevel.BRONZE: 1.1,  # 10% bonus
                VIPLevel.SILVER: 1.2,  # 20% bonus
                VIPLevel.GOLD: 1.3,    # 30% bonus
                VIPLevel.PLATINUM: 1.5  # 50% bonus
            }
        }
        self.points_expiry = {
            "purchase": 365,  # 1 year
            "referral": 180,  # 6 months
            "daily_login": 30  # 30 days
        }
    
    async def create_user(self, user_id: str) -> UserPoints:
        """Create a new user points account."""
        if user_id in self.users:
            return self.users[user_id]
        
        referral_code = str(uuid.uuid4())[:8]
        while referral_code in self.referral_codes:
            referral_code = str(uuid.uuid4())[:8]
        
        self.referral_codes[referral_code] = user_id
        
        user = UserPoints(
            user_id=user_id,
            total_points=0,
            available_points=0,
            vip_level=VIPLevel.NONE,
            points_history=[],
            last_activity=datetime.now(),
            referral_code=referral_code,
            referred_by=None,
            referral_count=0,
            total_earned=0,
            total_spent=0,
            total_expired=0
        )
        
        self.users[user_id] = user
        return user
    
    async def get_user(self, user_id: str) -> Optional[UserPoints]:
        """Get user points information."""
        return self.users.get(user_id)
    
    async def add_points(
        self,
        user_id: str,
        amount: int,
        source: str,
        description: str,
        expires_in_days: Optional[int] = None
    ) -> bool:
        """Add points to a user's account."""
        user = await self.get_user(user_id)
        if not user:
            user = await self.create_user(user_id)
        
        # Apply VIP bonus if applicable
        if source in self.points_rules["vip_bonus"]:
            bonus = self.points_rules["vip_bonus"][user.vip_level]
            amount = int(amount * bonus)
        
        transaction = PointsTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=amount,
            type="earned",
            source=source,
            description=description,
            created_at=datetime.now(),
            expires_at=(
                datetime.now() + timedelta(days=expires_in_days)
                if expires_in_days
                else None
            )
        )
        
        user.points_history.append(transaction)
        user.total_points += amount
        user.available_points += amount
        user.total_earned += amount
        user.last_activity = datetime.now()
        
        return True
    
    async def spend_points(
        self,
        user_id: str,
        amount: int,
        description: str
    ) -> bool:
        """Spend points from a user's account."""
        user = await self.get_user(user_id)
        if not user or user.available_points < amount:
            return False
        
        transaction = PointsTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            amount=-amount,
            type="spent",
            source="reward",
            description=description,
            created_at=datetime.now(),
            expires_at=None
        )
        
        user.points_history.append(transaction)
        user.available_points -= amount
        user.total_spent += amount
        user.last_activity = datetime.now()
        
        return True
    
    async def check_expired_points(self, user_id: str) -> int:
        """Check and remove expired points."""
        user = await self.get_user(user_id)
        if not user:
            return 0
        
        now = datetime.now()
        expired_amount = 0
        
        # Remove expired points
        for transaction in user.points_history:
            if (
                transaction.type == "earned"
                and transaction.expires_at
                and transaction.expires_at < now
                and transaction.amount > 0
            ):
                expired_amount += transaction.amount
                transaction.amount = 0
                transaction.type = "expired"
        
        if expired_amount > 0:
            user.available_points -= expired_amount
            user.total_expired += expired_amount
            user.last_activity = now
        
        return expired_amount
    
    async def update_vip_level(self, user_id: str) -> VIPLevel:
        """Update user's VIP level based on points and activity."""
        user = await self.get_user(user_id)
        if not user:
            return VIPLevel.NONE
        
        # Calculate VIP level based on total points and activity
        if user.total_points >= 10000 and user.referral_count >= 5:
            new_level = VIPLevel.PLATINUM
        elif user.total_points >= 5000 and user.referral_count >= 3:
            new_level = VIPLevel.GOLD
        elif user.total_points >= 2000 and user.referral_count >= 2:
            new_level = VIPLevel.SILVER
        elif user.total_points >= 500:
            new_level = VIPLevel.BRONZE
        else:
            new_level = VIPLevel.NONE
        
        if new_level != user.vip_level:
            user.vip_level = new_level
            user.last_activity = datetime.now()
        
        return new_level
    
    async def add_referral(
        self,
        user_id: str,
        referral_code: str
    ) -> bool:
        """Add a referral to a user's account."""
        referrer_id = self.referral_codes.get(referral_code)
        if not referrer_id or referrer_id == user_id:
            return False
        
        referrer = await self.get_user(referrer_id)
        if not referrer:
            return False
        
        referrer.referral_count += 1
        referrer.last_activity = datetime.now()
        
        # Add referral points
        await self.add_points(
            referrer_id,
            self.points_rules["referral"],
            "referral",
            f"Referral bonus for user {user_id}",
            self.points_expiry["referral"]
        )
        
        # Update referred user
        user = await self.get_user(user_id)
        if user:
            user.referred_by = referrer_id
        
        return True
    
    async def get_points_stats(self, user_id: str) -> Dict:
        """Get detailed points statistics for a user."""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Check for expired points
        expired = await self.check_expired_points(user_id)
        
        # Update VIP level
        vip_level = await self.update_vip_level(user_id)
        
        return {
            "user": {
                "id": user.user_id,
                "vip_level": vip_level.value,
                "referral_code": user.referral_code,
                "referred_by": user.referred_by,
                "referral_count": user.referral_count,
                "last_activity": user.last_activity.isoformat()
            },
            "points": {
                "total": user.total_points,
                "available": user.available_points,
                "expired": expired,
                "earned": user.total_earned,
                "spent": user.total_spent,
                "total_expired": user.total_expired
            },
            "history": [
                {
                    "id": t.id,
                    "amount": t.amount,
                    "type": t.type,
                    "source": t.source,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                    "expires_at": t.expires_at.isoformat() if t.expires_at else None
                }
                for t in user.points_history[-10:]  # Last 10 transactions
            ]
        } 