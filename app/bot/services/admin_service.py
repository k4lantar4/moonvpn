"""
Admin group management and monitoring service for MoonVPN Telegram Bot.

This module provides functionality for managing admin groups and monitoring system status
using the 3x-ui panel API.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.database.models import Server, ServerStatus
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
    
    def __init__(self, panel_client: PanelClient):
        self.panel_client = panel_client
    
    async def is_admin_group(self, chat_id: int) -> bool:
        """Check if the chat is an admin group."""
        admin_groups = [
            self.MANAGE_GROUP_ID,
            self.REPORTS_GROUP_ID,
            self.LOGS_GROUP_ID,
            self.TRANSACTIONS_GROUP_ID,
            self.OUTAGES_GROUP_ID,
            self.SELLERS_GROUP_ID,
            self.BACKUPS_GROUP_ID
        ]
        return chat_id in admin_groups
    
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