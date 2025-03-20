"""
Component Integration Service for managing system component integrations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session

from ..database.models.enhancements.health import SystemHealth, HealthStatus
from ..core.config import settings

logger = logging.getLogger(__name__)

class ComponentIntegrationService:
    """Service for managing component integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.components: Dict[str, Any] = {}
        self.integration_status: Dict[str, bool] = {}

    async def initialize(self):
        """Initialize all component integrations."""
        try:
            # Initialize core components
            await self._initialize_vpn_component()
            await self._initialize_bot_component()
            await self._initialize_payment_component()
            await self._initialize_monitoring_component()
            await self._initialize_security_component()
            
            logger.info("All component integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize component integrations: {str(e)}")
            raise

    async def _initialize_vpn_component(self):
        """Initialize VPN component integration."""
        try:
            from .vpn import VPNService
            self.components['vpn'] = VPNService(self.db)
            await self.components['vpn'].initialize()
            self.integration_status['vpn'] = True
            logger.info("VPN component integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VPN component: {str(e)}")
            self.integration_status['vpn'] = False
            raise

    async def _initialize_bot_component(self):
        """Initialize Bot component integration."""
        try:
            from .bot import BotService
            self.components['bot'] = BotService(self.db)
            await self.components['bot'].initialize()
            self.integration_status['bot'] = True
            logger.info("Bot component integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bot component: {str(e)}")
            self.integration_status['bot'] = False
            raise

    async def _initialize_payment_component(self):
        """Initialize Payment component integration."""
        try:
            from .payment import PaymentService
            self.components['payment'] = PaymentService(self.db)
            await self.components['payment'].initialize()
            self.integration_status['payment'] = True
            logger.info("Payment component integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Payment component: {str(e)}")
            self.integration_status['payment'] = False
            raise

    async def _initialize_monitoring_component(self):
        """Initialize Monitoring component integration."""
        try:
            from .monitoring import MonitoringService
            self.components['monitoring'] = MonitoringService(self.db)
            await self.components['monitoring'].initialize()
            self.integration_status['monitoring'] = True
            logger.info("Monitoring component integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Monitoring component: {str(e)}")
            self.integration_status['monitoring'] = False
            raise

    async def _initialize_security_component(self):
        """Initialize Security component integration."""
        try:
            from .security import SecurityService
            self.components['security'] = SecurityService(self.db)
            await self.components['security'].initialize()
            self.integration_status['security'] = True
            logger.info("Security component integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Security component: {str(e)}")
            self.integration_status['security'] = False
            raise

    async def get_component_status(self, component: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific component."""
        if component not in self.components:
            return None
            
        try:
            status = await self.components[component].get_status()
            return {
                "component": component,
                "status": status,
                "is_integrated": self.integration_status.get(component, False),
                "last_check": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get status for component {component}: {str(e)}")
            return None

    async def get_all_component_status(self) -> List[Dict[str, Any]]:
        """Get the status of all components."""
        status_list = []
        for component in self.components:
            status = await self.get_component_status(component)
            if status:
                status_list.append(status)
        return status_list

    async def check_component_health(self, component: str) -> bool:
        """Check if a component is healthy."""
        if component not in self.components:
            return False
            
        try:
            status = await self.get_component_status(component)
            if not status:
                return False
                
            return status["status"] == "healthy"
        except Exception as e:
            logger.error(f"Failed to check health for component {component}: {str(e)}")
            return False

    async def restart_component(self, component: str) -> bool:
        """Restart a specific component."""
        if component not in self.components:
            return False
            
        try:
            await self.components[component].shutdown()
            await asyncio.sleep(1)  # Wait for shutdown
            await self.components[component].initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to restart component {component}: {str(e)}")
            return False

    async def shutdown(self):
        """Shutdown all component integrations."""
        for component in self.components:
            try:
                await self.components[component].shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown component {component}: {str(e)}")
        self.integration_status.clear() 