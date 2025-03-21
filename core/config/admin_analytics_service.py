"""
Admin analytics service for MoonVPN Telegram Bot.

This module provides analytics and reporting services for admin groups.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.core.database.models.admin import AdminGroup, AdminGroupType, AdminGroupMember
from app.core.exceptions import AdminGroupError

class AdminAnalyticsService:
    """Service for admin group analytics and reporting."""
    
    def __init__(self, db: Session):
        """Initialize the admin analytics service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_group_statistics(self, group_chat_id: int) -> Dict[str, Any]:
        """Get statistics for a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            
        Returns:
            Dictionary containing group statistics
            
        Raises:
            AdminGroupError: If group is not found
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == group_chat_id
        ).first()
        
        if not group:
            raise AdminGroupError(f"Admin group with chat ID {group_chat_id} not found")
        
        # Get member statistics
        total_members = self.db.query(func.count(AdminGroupMember.id)).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True
        ).scalar()
        
        role_distribution = self.db.query(
            AdminGroupMember.role,
            func.count(AdminGroupMember.id)
        ).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True
        ).group_by(AdminGroupMember.role).all()
        
        # Convert role distribution to dictionary
        roles = {role: count for role, count in role_distribution}
        
        return {
            'group_name': group.name,
            'group_type': group.type.value,
            'total_members': total_members,
            'role_distribution': roles,
            'is_active': group.is_active,
            'notification_level': group.notification_level.value,
            'notification_types': group.notification_types
        }
    
    def get_member_activity(
        self,
        group_chat_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get member activity for a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            days: Number of days to look back
            
        Returns:
            List of member activity data
            
        Raises:
            AdminGroupError: If group is not found
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == group_chat_id
        ).first()
        
        if not group:
            raise AdminGroupError(f"Admin group with chat ID {group_chat_id} not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get member activity (example query - adjust based on your activity tracking)
        activity = self.db.query(
            AdminGroupMember.user_id,
            AdminGroupMember.role,
            func.count('*').label('action_count')
        ).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True,
            # Add your activity tracking conditions here
        ).group_by(
            AdminGroupMember.user_id,
            AdminGroupMember.role
        ).all()
        
        return [
            {
                'user_id': user_id,
                'role': role,
                'action_count': count
            }
            for user_id, role, count in activity
        ]
    
    def get_notification_statistics(
        self,
        group_chat_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get notification statistics for a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            days: Number of days to look back
            
        Returns:
            Dictionary containing notification statistics
            
        Raises:
            AdminGroupError: If group is not found
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == group_chat_id
        ).first()
        
        if not group:
            raise AdminGroupError(f"Admin group with chat ID {group_chat_id} not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Example notification statistics (adjust based on your notification tracking)
        return {
            'total_notifications': len(group.notification_types),
            'notification_types': group.notification_types,
            'notification_level': group.notification_level.value,
            'time_period': f'Last {days} days',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    def get_group_health(self, group_chat_id: int) -> Dict[str, Any]:
        """Get health metrics for a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            
        Returns:
            Dictionary containing group health metrics
            
        Raises:
            AdminGroupError: If group is not found
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == group_chat_id
        ).first()
        
        if not group:
            raise AdminGroupError(f"Admin group with chat ID {group_chat_id} not found")
        
        # Get active members count
        active_members = self.db.query(func.count(AdminGroupMember.id)).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True
        ).scalar()
        
        # Get admin members count
        admin_members = self.db.query(func.count(AdminGroupMember.id)).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True,
            AdminGroupMember.role == 'admin'
        ).scalar()
        
        # Calculate health score (example)
        health_score = 100
        health_factors = []
        
        # Check if group has active members
        if active_members == 0:
            health_score -= 50
            health_factors.append("No active members")
        
        # Check if group has admin members
        if admin_members == 0:
            health_score -= 30
            health_factors.append("No admin members")
        
        # Check if group is active
        if not group.is_active:
            health_score -= 100
            health_factors.append("Group is inactive")
        
        # Check notification configuration
        if not group.notification_types:
            health_score -= 20
            health_factors.append("No notification types configured")
        
        return {
            'health_score': max(0, health_score),
            'status': 'healthy' if health_score >= 70 else 'warning' if health_score >= 40 else 'critical',
            'factors': health_factors,
            'active_members': active_members,
            'admin_members': admin_members,
            'is_active': group.is_active,
            'has_notifications': bool(group.notification_types)
        }
    
    def get_group_recommendations(self, group_chat_id: int) -> List[Dict[str, Any]]:
        """Get recommendations for improving a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            
        Returns:
            List of recommendations
            
        Raises:
            AdminGroupError: If group is not found
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == group_chat_id
        ).first()
        
        if not group:
            raise AdminGroupError(f"Admin group with chat ID {group_chat_id} not found")
        
        recommendations = []
        
        # Check active members
        active_members = self.db.query(func.count(AdminGroupMember.id)).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True
        ).scalar()
        
        if active_members < 2:
            recommendations.append({
                'type': 'members',
                'priority': 'high',
                'message': 'Add more active members to the group',
                'details': 'Groups should have at least 2 active members for redundancy'
            })
        
        # Check admin members
        admin_members = self.db.query(func.count(AdminGroupMember.id)).filter(
            AdminGroupMember.group_id == group.id,
            AdminGroupMember.is_active == True,
            AdminGroupMember.role == 'admin'
        ).scalar()
        
        if admin_members < 2:
            recommendations.append({
                'type': 'admins',
                'priority': 'high',
                'message': 'Add more admin members',
                'details': 'Groups should have at least 2 admin members for backup'
            })
        
        # Check notification types
        if not group.notification_types:
            recommendations.append({
                'type': 'notifications',
                'priority': 'medium',
                'message': 'Configure notification types',
                'details': 'Add relevant notification types based on group purpose'
            })
        
        # Check notification level
        if group.type in [AdminGroupType.MANAGE, AdminGroupType.OUTAGES] and \
           group.notification_level.value != 'high':
            recommendations.append({
                'type': 'notification_level',
                'priority': 'medium',
                'message': 'Increase notification level',
                'details': f'Consider setting notification level to HIGH for {group.type.value} group'
            })
        
        # Check group description
        if not group.description:
            recommendations.append({
                'type': 'description',
                'priority': 'low',
                'message': 'Add group description',
                'details': 'Add a clear description of group purpose and responsibilities'
            })
        
        return recommendations
    
    def generate_activity_report(
        self,
        group_chat_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate a comprehensive activity report for a specific admin group.
        
        Args:
            group_chat_id: Telegram chat ID of the group
            days: Number of days to include in the report
            
        Returns:
            Dictionary containing the activity report
            
        Raises:
            AdminGroupError: If group is not found
        """
        # Get group statistics
        statistics = self.get_group_statistics(group_chat_id)
        
        # Get member activity
        activity = self.get_member_activity(group_chat_id, days)
        
        # Get notification statistics
        notifications = self.get_notification_statistics(group_chat_id, days)
        
        # Get health metrics
        health = self.get_group_health(group_chat_id)
        
        # Get recommendations
        recommendations = self.get_group_recommendations(group_chat_id)
        
        return {
            'report_date': datetime.utcnow().isoformat(),
            'time_period': f'Last {days} days',
            'group_info': statistics,
            'member_activity': activity,
            'notifications': notifications,
            'health_metrics': health,
            'recommendations': recommendations
        } 