"""
Usage Analytics Service for MoonVPN Telegram Bot

This module implements usage analytics functionality for tracking and analyzing
VPN usage patterns, traffic consumption, and performance metrics.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database.models import VPNAccount, UsageLog, UsageRecord, Server
from app.core.database.session import get_db
from app.bot.utils.logger import setup_logger
import logging

logger = logging.getLogger(__name__)

class UsageService:
    """Service for handling VPN usage analytics."""
    
    def __init__(self):
        """Initialize the usage service."""
        self.logger = setup_logger(__name__)
    
    async def get_usage_details(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed usage information for a user's VPN account.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict containing usage details
        """
        try:
            db = next(get_db())
            
            # Get account
            account = db.query(VPNAccount).filter(VPNAccount.user_id == user_id).first()
            if not account:
                raise ValueError("No active VPN account found")
            
            # Get today's usage
            today = datetime.utcnow().date()
            daily_usage = db.query(func.sum(UsageLog.traffic_used))\
                .filter(UsageLog.account_id == account.id)\
                .filter(func.date(UsageLog.timestamp) == today)\
                .scalar() or 0
            
            # Get total usage
            total_usage = db.query(func.sum(UsageLog.traffic_used))\
                .filter(UsageLog.account_id == account.id)\
                .scalar() or 0
            
            # Get usage history
            history = db.query(UsageLog)\
                .filter(UsageLog.account_id == account.id)\
                .order_by(UsageLog.timestamp.desc())\
                .limit(7)\
                .all()
            
            # Calculate average daily usage
            avg_daily = sum(log.traffic_used for log in history) / len(history) if history else 0
            
            return {
                "start_date": account.created_at.strftime("%Y-%m-%d"),
                "daily_usage": daily_usage / (1024 * 1024 * 1024),  # Convert to GB
                "total_usage": total_usage / (1024 * 1024 * 1024),  # Convert to GB
                "last_update": history[0].timestamp.strftime("%Y-%m-%d %H:%M") if history else "نامشخص",
                "average_daily": avg_daily / (1024 * 1024 * 1024),  # Convert to GB
                "traffic_limit": account.traffic_limit / (1024 * 1024 * 1024),  # Convert to GB
                "remaining_days": (account.expiry_date - datetime.utcnow()).days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage details: {str(e)}")
            raise
    
    async def get_usage_history(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get usage history for a user's VPN account.
        
        Args:
            user_id: Telegram user ID
            days: Number of days of history to retrieve
            
        Returns:
            List of daily usage records
        """
        try:
            db = next(get_db())
            
            # Get account
            account = db.query(VPNAccount).filter(VPNAccount.user_id == user_id).first()
            if not account:
                raise ValueError("No active VPN account found")
            
            # Get usage history
            start_date = datetime.utcnow() - timedelta(days=days)
            history = db.query(UsageLog)\
                .filter(UsageLog.account_id == account.id)\
                .filter(UsageLog.timestamp >= start_date)\
                .order_by(UsageLog.timestamp.desc())\
                .all()
            
            return [
                {
                    "date": log.timestamp.strftime("%Y-%m-%d"),
                    "usage": log.traffic_used / (1024 * 1024 * 1024),  # Convert to GB
                    "duration": log.duration_seconds / 3600,  # Convert to hours
                    "server": log.server_name
                }
                for log in history
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting usage history: {str(e)}")
            raise
    
    async def get_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a user's VPN account.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict containing usage statistics
        """
        try:
            db = next(get_db())
            
            # Get account
            account = db.query(VPNAccount).filter(VPNAccount.user_id == user_id).first()
            if not account:
                raise ValueError("No active VPN account found")
            
            # Get total usage
            total_usage = db.query(func.sum(UsageLog.traffic_used))\
                .filter(UsageLog.account_id == account.id)\
                .scalar() or 0
            
            # Get total duration
            total_duration = db.query(func.sum(UsageLog.duration_seconds))\
                .filter(UsageLog.account_id == account.id)\
                .scalar() or 0
            
            # Get average session duration
            avg_duration = db.query(func.avg(UsageLog.duration_seconds))\
                .filter(UsageLog.account_id == account.id)\
                .scalar() or 0
            
            # Get most used server
            most_used = db.query(
                UsageLog.server_name,
                func.sum(UsageLog.traffic_used).label('total_traffic')
            )\
                .filter(UsageLog.account_id == account.id)\
                .group_by(UsageLog.server_name)\
                .order_by(func.sum(UsageLog.traffic_used).desc())\
                .first()
            
            return {
                "total_usage": total_usage / (1024 * 1024 * 1024),  # Convert to GB
                "total_duration": total_duration / 3600,  # Convert to hours
                "average_session": avg_duration / 60,  # Convert to minutes
                "most_used_server": most_used[0] if most_used else "نامشخص",
                "server_usage": most_used[1] / (1024 * 1024 * 1024) if most_used else 0  # Convert to GB
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {str(e)}")
            raise
    
    async def get_server_usage_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed server usage statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            List of dictionaries containing server usage statistics
        """
        try:
            db = next(get_db())
            account = db.query(VPNAccount).filter(VPNAccount.user_id == user_id).first()
            
            if not account:
                raise ValueError("No active VPN account found")
            
            # Get usage history
            history = db.query(UsageLog)\
                .filter(UsageLog.account_id == account.id)\
                .order_by(UsageLog.timestamp.desc())\
                .all()
            
            # Group by server
            server_stats = {}
            for log in history:
                if log.server_id not in server_stats:
                    server_stats[log.server_id] = {
                        "usage": 0,
                        "duration": 0,
                        "connection_count": 0
                    }
                server_stats[log.server_id]["usage"] += log.traffic_used
                server_stats[log.server_id]["duration"] += log.duration_seconds
                server_stats[log.server_id]["connection_count"] += 1
            
            # Get server names and format results
            results = []
            for server_id, stats in server_stats.items():
                server = db.query(Server).filter(Server.id == server_id).first()
                if server:
                    results.append({
                        "name": server.name,
                        "total_usage": stats["usage"] / (1024 * 1024 * 1024),  # Convert to GB
                        "duration": stats["duration"] / 3600,  # Convert to hours
                        "connection_count": stats["connection_count"]
                    })
            
            return sorted(results, key=lambda x: x["total_usage"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting server usage stats: {str(e)}")
            raise
    
    async def get_timing_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get timing-based usage statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing timing statistics
        """
        try:
            db = next(get_db())
            account = db.query(VPNAccount).filter(VPNAccount.user_id == user_id).first()
            
            if not account:
                raise ValueError("No active VPN account found")
            
            # Get usage history
            history = db.query(UsageLog)\
                .filter(UsageLog.account_id == account.id)\
                .order_by(UsageLog.timestamp.desc())\
                .all()
            
            # Initialize timing categories
            timing_stats = {
                "morning_usage": 0,    # 6-12
                "afternoon_usage": 0,   # 12-18
                "evening_usage": 0,     # 18-24
                "night_usage": 0,       # 0-6
                "weekday_usage": 0,
                "weekend_usage": 0,
                "average_daily_duration": 0
            }
            
            # Calculate timing statistics
            total_duration = 0
            for log in history:
                hour = log.timestamp.hour
                weekday = log.timestamp.weekday()
                
                # Time of day
                if 6 <= hour < 12:
                    timing_stats["morning_usage"] += log.duration_seconds
                elif 12 <= hour < 18:
                    timing_stats["afternoon_usage"] += log.duration_seconds
                elif 18 <= hour < 24:
                    timing_stats["evening_usage"] += log.duration_seconds
                else:
                    timing_stats["night_usage"] += log.duration_seconds
                
                # Weekday vs weekend
                if weekday < 5:  # Monday to Friday
                    timing_stats["weekday_usage"] += log.duration_seconds
                else:
                    timing_stats["weekend_usage"] += log.duration_seconds
                
                total_duration += log.duration_seconds
            
            # Calculate average daily duration
            timing_stats["average_daily_duration"] = total_duration / len(history) if history else 0
            
            return timing_stats
            
        except Exception as e:
            self.logger.error(f"Error getting timing stats: {str(e)}")
            raise 