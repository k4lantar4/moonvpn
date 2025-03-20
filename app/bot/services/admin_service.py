"""
Admin group management and monitoring service for MoonVPN Telegram Bot.

This module provides functionality for managing admin groups and monitoring system status
using the 3x-ui panel API.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.database.models import Server, ServerStatus, AdminGroup, AdminGroupMember
from app.bot.utils.logger import setup_logger
from app.bot.services.panel_client import PanelClient

# Initialize logger
logger = setup_logger(__name__)

class AdminService:
    """Service for managing admin groups and system monitoring."""
    
    # Admin group IDs
    MANAGE_GROUP_ID = -1001234567890  # Replace with actual group ID
    REPORTS_GROUP_ID = -1001234567891
    LOGS_GROUP_ID = -1001234567892
    TRANSACTIONS_GROUP_ID = -1001234567893
    OUTAGES_GROUP_ID = -1001234567894
    SELLERS_GROUP_ID = -1001234567895
    BACKUPS_GROUP_ID = -1001234567896
    
    def __init__(self, db: Session, panel_client: PanelClient):
        """Initialize the admin service.
        
        Args:
            db: Database session
            panel_client: 3x-ui panel client
        """
        self.db = db
        self.panel_client = panel_client
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is an admin, False otherwise
        """
        member = self.db.query(AdminGroupMember).filter(
            AdminGroupMember.user_id == user_id,
            AdminGroupMember.is_active == True
        ).first()
        
        return member is not None and member.role == "admin"
    
    async def is_admin_group(self, chat_id: int) -> bool:
        """Check if a chat is an admin group.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            True if chat is an admin group, False otherwise
        """
        group = self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == chat_id,
            AdminGroup.is_active == True
        ).first()
        
        return group is not None
    
    async def get_group(self, chat_id: int) -> Optional[AdminGroup]:
        """Get an admin group by chat ID.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Admin group if found, None otherwise
        """
        return self.db.query(AdminGroup).filter(
            AdminGroup.chat_id == chat_id,
            AdminGroup.is_active == True
        ).first()
    
    async def get_group_type(self, chat_id: int) -> Optional[str]:
        """Get the type of admin group based on chat ID."""
        group_mapping = {
            self.MANAGE_GROUP_ID: "manage",
            self.REPORTS_GROUP_ID: "reports",
            self.LOGS_GROUP_ID: "logs",
            self.TRANSACTIONS_GROUP_ID: "transactions",
            self.OUTAGES_GROUP_ID: "outages",
            self.SELLERS_GROUP_ID: "sellers",
            self.BACKUPS_GROUP_ID: "backups"
        }
        return group_mapping.get(chat_id)
    
    async def get_server_status(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Get server status from 3x-ui panel."""
        try:
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Get status from panel
            status = await self.panel_client.get_server_status(server.panel_id)
            
            # Update server status in database
            server_status = db.query(ServerStatus).filter(
                ServerStatus.server_id == server_id
            ).first()
            
            if not server_status:
                server_status = ServerStatus(server_id=server_id)
                db.add(server_status)
            
            server_status.cpu_usage = status.get("cpu_usage", 0)
            server_status.memory_usage = status.get("memory_usage", 0)
            server_status.disk_usage = status.get("disk_usage", 0)
            server_status.network_in = status.get("network_in", 0)
            server_status.network_out = status.get("network_out", 0)
            server_status.uptime = status.get("uptime", 0)
            server_status.last_check = datetime.utcnow()
            
            db.commit()
            
            return {
                "server_id": server_id,
                "name": server.name,
                "location": server.location.name,
                "status": "online" if status.get("online", False) else "offline",
                "cpu_usage": status.get("cpu_usage", 0),
                "memory_usage": status.get("memory_usage", 0),
                "disk_usage": status.get("disk_usage", 0),
                "network_in": status.get("network_in", 0),
                "network_out": status.get("network_out", 0),
                "uptime": status.get("uptime", 0),
                "last_check": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting server status for server {server_id}: {str(e)}")
            raise
    
    async def get_system_status(self, db: Session) -> Dict[str, Any]:
        """Get overall system status from all servers."""
        try:
            servers = db.query(Server).filter(Server.is_active == True).all()
            total_users = 0
            total_traffic = 0
            online_servers = 0
            
            for server in servers:
                status = await self.get_server_status(server.id, db)
                if status["status"] == "online":
                    online_servers += 1
                    total_users += status.get("active_users", 0)
                    total_traffic += status.get("network_in", 0) + status.get("network_out", 0)
            
            return {
                "total_servers": len(servers),
                "online_servers": online_servers,
                "total_users": total_users,
                "total_traffic": total_traffic,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            raise
    
    async def check_server_health(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Check server health and generate alerts if needed."""
        try:
            status = await self.get_server_status(server_id, db)
            alerts = []
            
            # Check CPU usage
            if status["cpu_usage"] > 90:
                alerts.append({
                    "type": "cpu",
                    "message": f"High CPU usage on server {status['name']}: {status['cpu_usage']}%",
                    "severity": "warning"
                })
            
            # Check memory usage
            if status["memory_usage"] > 90:
                alerts.append({
                    "type": "memory",
                    "message": f"High memory usage on server {status['name']}: {status['memory_usage']}%",
                    "severity": "warning"
                })
            
            # Check disk usage
            if status["disk_usage"] > 90:
                alerts.append({
                    "type": "disk",
                    "message": f"High disk usage on server {status['name']}: {status['disk_usage']}%",
                    "severity": "warning"
                })
            
            # Check if server is offline
            if status["status"] == "offline":
                alerts.append({
                    "type": "offline",
                    "message": f"Server {status['name']} is offline",
                    "severity": "critical"
                })
            
            return {
                "server_id": server_id,
                "status": status,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Error checking server health for server {server_id}: {str(e)}")
            raise
    
    async def get_group_stats(self, group_type: str, db: Session) -> Dict[str, Any]:
        """Get statistics for specific admin group."""
        try:
            if group_type == "reports":
                return await self.get_system_status(db)
            elif group_type == "transactions":
                # Get transaction statistics
                return {
                    "total_transactions": 0,  # Implement transaction stats
                    "total_amount": 0,
                    "successful_transactions": 0,
                    "failed_transactions": 0
                }
            elif group_type == "sellers":
                # Get reseller statistics
                return {
                    "total_sellers": 0,  # Implement seller stats
                    "active_sellers": 0,
                    "total_commission": 0
                }
            else:
                raise HTTPException(status_code=400, detail="Invalid group type")
                
        except Exception as e:
            logger.error(f"Error getting stats for group {group_type}: {str(e)}")
            raise
    
    async def get_current_server_status(self) -> Dict[str, Any]:
        """Get current server status.
        
        Returns:
            Dictionary containing server status information
        """
        try:
            status = await self.panel_client.get_status()
            return {
                'cpu_usage': status.get('cpu_usage', 0),
                'memory_usage': status.get('memory_usage', 0),
                'disk_usage': status.get('disk_usage', 0),
                'network_status': status.get('network_status', 'unknown'),
                'uptime': status.get('uptime', 'unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get server status: {str(e)}")
            raise
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information.
        
        Returns:
            Dictionary containing system health information
        """
        try:
            health = await self.panel_client.get_health()
            return {
                'status': health.get('status', 'unknown'),
                'database_status': health.get('database_status', 'unknown'),
                'api_status': health.get('api_status', 'unknown'),
                'bot_status': health.get('bot_status', 'unknown'),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system health: {str(e)}")
            raise
    
    async def get_admin_statistics(self) -> Dict[str, Any]:
        """Get admin statistics.
        
        Returns:
            Dictionary containing admin statistics
        """
        try:
            total_admins = self.db.query(AdminGroupMember).filter(
                AdminGroupMember.role == "admin",
                AdminGroupMember.is_active == True
            ).count()
            
            active_admins = self.db.query(AdminGroupMember).filter(
                AdminGroupMember.role == "admin",
                AdminGroupMember.is_active == True,
                AdminGroupMember.last_active >= datetime.now() - timedelta(hours=24)
            ).count()
            
            return {
                'total_admins': total_admins,
                'active_admins': active_admins,
                'admin_actions': 0,  # TODO: Implement action tracking
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get admin statistics: {str(e)}")
            raise
    
    async def get_daily_report(self) -> Dict[str, Any]:
        """Get daily system report.
        
        Returns:
            Dictionary containing daily report information
        """
        try:
            # TODO: Implement actual report generation
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'new_users': 0,
                'active_users': 0,
                'total_revenue': 0,
                'system_uptime': '0h'
            }
        except Exception as e:
            logger.error(f"Failed to get daily report: {str(e)}")
            raise
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get system performance report.
        
        Returns:
            Dictionary containing performance metrics
        """
        try:
            status = await self.panel_client.get_status()
            return {
                'response_time': status.get('response_time', 0),
                'error_rate': status.get('error_rate', 0),
                'cpu_usage': status.get('cpu_usage', 0),
                'memory_usage': status.get('memory_usage', 0),
                'network_load': status.get('network_load', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get performance report: {str(e)}")
            raise
    
    async def get_usage_report(self) -> Dict[str, Any]:
        """Get system usage report.
        
        Returns:
            Dictionary containing usage metrics
        """
        try:
            # TODO: Implement actual usage tracking
            return {
                'total_users': 0,
                'active_sessions': 0,
                'bandwidth_usage': '0 GB',
                'peak_hours': '00:00-00:00',
                'avg_session': '0h'
            }
        except Exception as e:
            logger.error(f"Failed to get usage report: {str(e)}")
            raise
    
    async def get_error_logs(self) -> List[Dict[str, Any]]:
        """Get system error logs.
        
        Returns:
            List of error log entries
        """
        try:
            # TODO: Implement actual error logging
            return []
        except Exception as e:
            logger.error(f"Failed to get error logs: {str(e)}")
            raise
    
    async def get_user_logs(self) -> List[Dict[str, Any]]:
        """Get user activity logs.
        
        Returns:
            List of user log entries
        """
        try:
            # TODO: Implement actual user logging
            return []
        except Exception as e:
            logger.error(f"Failed to get user logs: {str(e)}")
            raise
    
    async def get_system_logs(self) -> List[Dict[str, Any]]:
        """Get system event logs.
        
        Returns:
            List of system log entries
        """
        try:
            # TODO: Implement actual system logging
            return []
        except Exception as e:
            logger.error(f"Failed to get system logs: {str(e)}")
            raise
    
    async def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get transaction statistics.
        
        Returns:
            Dictionary containing transaction metrics
        """
        try:
            # TODO: Implement actual transaction tracking
            return {
                'total_transactions': 0,
                'total_revenue': 0,
                'success_rate': 0,
                'avg_amount': 0,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get transaction statistics: {str(e)}")
            raise
    
    async def get_payment_report(self) -> Dict[str, Any]:
        """Get payment processing report.
        
        Returns:
            Dictionary containing payment metrics
        """
        try:
            # TODO: Implement actual payment tracking
            return {
                'total_payments': 0,
                'total_amount': 0,
                'payment_methods': [],
                'success_rate': 0,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get payment report: {str(e)}")
            raise
    
    async def get_refund_requests(self) -> List[Dict[str, Any]]:
        """Get refund requests.
        
        Returns:
            List of refund request entries
        """
        try:
            # TODO: Implement actual refund tracking
            return []
        except Exception as e:
            logger.error(f"Failed to get refund requests: {str(e)}")
            raise
    
    async def get_outage_status(self) -> Dict[str, Any]:
        """Get current outage status.
        
        Returns:
            Dictionary containing outage information
        """
        try:
            # TODO: Implement actual outage tracking
            return {
                'current_status': 'operational',
                'affected_services': [],
                'start_time': None,
                'estimated_resolution': None,
                'impact_level': 'none'
            }
        except Exception as e:
            logger.error(f"Failed to get outage status: {str(e)}")
            raise
    
    async def get_maintenance_schedule(self) -> List[Dict[str, Any]]:
        """Get maintenance schedule.
        
        Returns:
            List of maintenance windows
        """
        try:
            # TODO: Implement actual maintenance scheduling
            return []
        except Exception as e:
            logger.error(f"Failed to get maintenance schedule: {str(e)}")
            raise
    
    async def get_incident_report(self) -> Dict[str, Any]:
        """Get incident report.
        
        Returns:
            Dictionary containing incident metrics
        """
        try:
            # TODO: Implement actual incident tracking
            return {
                'total_incidents': 0,
                'resolved': 0,
                'active': 0,
                'avg_resolution_time': '0h',
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get incident report: {str(e)}")
            raise
    
    async def get_seller_statistics(self) -> Dict[str, Any]:
        """Get seller statistics.
        
        Returns:
            Dictionary containing seller metrics
        """
        try:
            # TODO: Implement actual seller tracking
            return {
                'total_sellers': 0,
                'active_sellers': 0,
                'total_sales': 0,
                'total_commission': 0,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get seller statistics: {str(e)}")
            raise
    
    async def get_commission_report(self) -> Dict[str, Any]:
        """Get commission report.
        
        Returns:
            Dictionary containing commission metrics
        """
        try:
            # TODO: Implement actual commission tracking
            return {
                'total_commission': 0,
                'paid_commission': 0,
                'pending_commission': 0,
                'commission_rate': 0,
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get commission report: {str(e)}")
            raise
    
    async def get_partner_status(self) -> List[Dict[str, Any]]:
        """Get partner status information.
        
        Returns:
            List of partner status entries
        """
        try:
            # TODO: Implement actual partner tracking
            return []
        except Exception as e:
            logger.error(f"Failed to get partner status: {str(e)}")
            raise
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """Get backup status information.
        
        Returns:
            Dictionary containing backup status
        """
        try:
            # TODO: Implement actual backup tracking
            return {
                'last_backup': None,
                'backup_size': '0 GB',
                'status': 'unknown',
                'next_backup': None,
                'storage_used': '0 GB'
            }
        except Exception as e:
            logger.error(f"Failed to get backup status: {str(e)}")
            raise
    
    async def get_backup_schedule(self) -> List[Dict[str, Any]]:
        """Get backup schedule.
        
        Returns:
            List of backup windows
        """
        try:
            # TODO: Implement actual backup scheduling
            return []
        except Exception as e:
            logger.error(f"Failed to get backup schedule: {str(e)}")
            raise
    
    async def get_restore_points(self) -> List[Dict[str, Any]]:
        """Get system restore points.
        
        Returns:
            List of restore point entries
        """
        try:
            # TODO: Implement actual restore point tracking
            return []
        except Exception as e:
            logger.error(f"Failed to get restore points: {str(e)}")
            raise 