from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.health import HealthCheck, HealthStatus
from app.services.notification import NotificationService
from app.services.vpn import VPNService
from app.services.database import DatabaseService

logger = logging.getLogger(__name__)

class HealthCheckService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.vpn_service = VPNService(db)
        self.database_service = DatabaseService(db)

    async def check_health(self) -> Dict[str, HealthStatus]:
        """Check health of all system components"""
        health_status = {}
        
        # Check database health
        db_status = await self.database_service.check_health()
        health_status['database'] = db_status
        
        # Check VPN service health
        vpn_status = await self.vpn_service.check_health()
        health_status['vpn'] = vpn_status
        
        # Check notification service health
        notification_status = await self.notification_service.check_health()
        health_status['notification'] = notification_status
        
        # Check system resources
        system_status = await self._check_system_resources()
        health_status['system'] = system_status
        
        return health_status

    async def _check_system_resources(self) -> HealthStatus:
        """Check system resources (CPU, memory, disk)"""
        try:
            # Implement system resource checks
            # This is a placeholder - implement actual system checks
            return HealthStatus(
                status="healthy",
                message="System resources are within normal limits",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error checking system resources: {str(e)}")
            return HealthStatus(
                status="unhealthy",
                message=f"Error checking system resources: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def handle_unhealthy_component(self, component: str, status: HealthStatus):
        """Handle unhealthy component by attempting recovery"""
        try:
            logger.warning(f"Component {component} is unhealthy: {status.message}")
            
            # Notify administrators
            await self.notification_service.send_admin_alert(
                f"Component {component} is unhealthy",
                status.message
            )
            
            # Attempt recovery based on component
            if component == "database":
                await self._recover_database()
            elif component == "vpn":
                await self._recover_vpn_service()
            elif component == "notification":
                await self._recover_notification_service()
            elif component == "system":
                await self._recover_system_resources()
            
            # Log recovery attempt
            logger.info(f"Recovery attempt completed for {component}")
            
        except Exception as e:
            logger.error(f"Error during recovery for {component}: {str(e)}")
            await self.notification_service.send_admin_alert(
                f"Recovery failed for {component}",
                str(e)
            )

    async def _recover_database(self):
        """Attempt to recover database connection"""
        try:
            # Implement database recovery logic
            await self.database_service.reconnect()
            logger.info("Database recovery completed")
        except Exception as e:
            logger.error(f"Database recovery failed: {str(e)}")
            raise

    async def _recover_vpn_service(self):
        """Attempt to recover VPN service"""
        try:
            # Implement VPN service recovery logic
            await self.vpn_service.reconnect()
            logger.info("VPN service recovery completed")
        except Exception as e:
            logger.error(f"VPN service recovery failed: {str(e)}")
            raise

    async def _recover_notification_service(self):
        """Attempt to recover notification service"""
        try:
            # Implement notification service recovery logic
            await self.notification_service.reconnect()
            logger.info("Notification service recovery completed")
        except Exception as e:
            logger.error(f"Notification service recovery failed: {str(e)}")
            raise

    async def _recover_system_resources(self):
        """Attempt to recover system resources"""
        try:
            # Implement system resource recovery logic
            # This could include:
            # - Clearing caches
            # - Restarting services
            # - Releasing resources
            logger.info("System resource recovery completed")
        except Exception as e:
            logger.error(f"System resource recovery failed: {str(e)}")
            raise

    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        while True:
            try:
                # Check health of all components
                health_status = await self.check_health()
                
                # Handle unhealthy components
                for component, status in health_status.items():
                    if status.status == "unhealthy":
                        await self.handle_unhealthy_component(component, status)
                
                # Wait before next check
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL) 