"""
Audit logging service for tracking security events and maintaining audit trails.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database.models.security import SecurityEvent
from ..core.config import settings
from ..core.exceptions import SecurityError

class AuditService:
    def __init__(self, db: Session):
        self.db = db

    async def log_event(self, event_type: str, severity: str, description: str,
                       user_id: Optional[int] = None, ip_address: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> SecurityEvent:
        """Log a security event."""
        try:
            # Create security event
            event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                description=description,
                user_id=user_id,
                ip_address=ip_address,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            
            return event

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to log security event: {str(e)}")

    async def get_events(self, event_type: Optional[str] = None,
                        severity: Optional[str] = None,
                        user_id: Optional[int] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[SecurityEvent]:
        """Get security events with optional filters."""
        try:
            query = self.db.query(SecurityEvent)
            
            # Apply filters
            if event_type:
                query = query.filter(SecurityEvent.event_type == event_type)
            if severity:
                query = query.filter(SecurityEvent.severity == severity)
            if user_id:
                query = query.filter(SecurityEvent.user_id == user_id)
            if start_date:
                query = query.filter(SecurityEvent.created_at >= start_date)
            if end_date:
                query = query.filter(SecurityEvent.created_at <= end_date)
            
            # Order by creation date and limit results
            query = query.order_by(desc(SecurityEvent.created_at)).limit(limit)
            
            return query.all()

        except Exception as e:
            raise SecurityError(f"Failed to get security events: {str(e)}")

    async def get_user_events(self, user_id: int, limit: int = 50) -> List[SecurityEvent]:
        """Get security events for a specific user."""
        try:
            return self.db.query(SecurityEvent)\
                .filter(SecurityEvent.user_id == user_id)\
                .order_by(desc(SecurityEvent.created_at))\
                .limit(limit)\
                .all()

        except Exception as e:
            raise SecurityError(f"Failed to get user security events: {str(e)}")

    async def get_ip_events(self, ip_address: str, limit: int = 50) -> List[SecurityEvent]:
        """Get security events for a specific IP address."""
        try:
            return self.db.query(SecurityEvent)\
                .filter(SecurityEvent.ip_address == ip_address)\
                .order_by(desc(SecurityEvent.created_at))\
                .limit(limit)\
                .all()

        except Exception as e:
            raise SecurityError(f"Failed to get IP security events: {str(e)}")

    async def get_critical_events(self, limit: int = 50) -> List[SecurityEvent]:
        """Get critical security events."""
        try:
            return self.db.query(SecurityEvent)\
                .filter(SecurityEvent.severity == "critical")\
                .order_by(desc(SecurityEvent.created_at))\
                .limit(limit)\
                .all()

        except Exception as e:
            raise SecurityError(f"Failed to get critical security events: {str(e)}")

    async def get_recent_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get security events from the last N hours."""
        try:
            start_date = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(SecurityEvent)\
                .filter(SecurityEvent.created_at >= start_date)\
                .order_by(desc(SecurityEvent.created_at))\
                .all()

        except Exception as e:
            raise SecurityError(f"Failed to get recent security events: {str(e)}")

    async def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up security events older than N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = self.db.query(SecurityEvent)\
                .filter(SecurityEvent.created_at < cutoff_date)\
                .delete()
            
            self.db.commit()
            return deleted

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to cleanup old security events: {str(e)}")

    async def get_event_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get security event statistics for the last N days."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get total events
            total_events = self.db.query(SecurityEvent)\
                .filter(SecurityEvent.created_at >= start_date)\
                .count()
            
            # Get events by severity
            severity_counts = self.db.query(
                SecurityEvent.severity,
                func.count(SecurityEvent.id)
            ).filter(
                SecurityEvent.created_at >= start_date
            ).group_by(
                SecurityEvent.severity
            ).all()
            
            # Get events by type
            type_counts = self.db.query(
                SecurityEvent.event_type,
                func.count(SecurityEvent.id)
            ).filter(
                SecurityEvent.created_at >= start_date
            ).group_by(
                SecurityEvent.event_type
            ).all()
            
            return {
                "total_events": total_events,
                "severity_counts": dict(severity_counts),
                "type_counts": dict(type_counts)
            }

        except Exception as e:
            raise SecurityError(f"Failed to get security event stats: {str(e)}")

    async def export_events(self, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> str:
        """Export security events to a JSON file."""
        try:
            query = self.db.query(SecurityEvent)
            
            if start_date:
                query = query.filter(SecurityEvent.created_at >= start_date)
            if end_date:
                query = query.filter(SecurityEvent.created_at <= end_date)
            
            events = query.order_by(desc(SecurityEvent.created_at)).all()
            
            # Convert events to JSON
            events_json = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "description": event.description,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "metadata": json.loads(event.metadata) if event.metadata else None,
                    "created_at": event.created_at.isoformat()
                }
                events_json.append(event_dict)
            
            # Save to file
            filename = f"security_events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(events_json, f, indent=2)
            
            return filename

        except Exception as e:
            raise SecurityError(f"Failed to export security events: {str(e)}") 