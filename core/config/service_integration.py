"""
Service Integration Service for managing service-to-service communication.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
import json
from sqlalchemy.orm import Session

from ..database.models.enhancements.health import SystemHealth, HealthStatus
from ..core.config import settings

logger = logging.getLogger(__name__)

class ServiceIntegrationService:
    """Service for managing service-to-service integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.services: Dict[str, Any] = {}
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.service_status: Dict[str, bool] = {}
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1,
            "max_delay": 10
        }

    async def initialize(self):
        """Initialize all service integrations."""
        try:
            # Initialize core services
            await self._initialize_vpn_service()
            await self._initialize_bot_service()
            await self._initialize_payment_service()
            await self._initialize_monitoring_service()
            await self._initialize_security_service()
            
            # Initialize message queues
            for service in self.services:
                self.message_queues[service] = asyncio.Queue()
            
            logger.info("All service integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize service integrations: {str(e)}")
            raise

    async def _initialize_vpn_service(self):
        """Initialize VPN service integration."""
        try:
            from .vpn import VPNService
            self.services['vpn'] = VPNService(self.db)
            await self.services['vpn'].initialize()
            self.service_status['vpn'] = True
            logger.info("VPN service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VPN service: {str(e)}")
            self.service_status['vpn'] = False
            raise

    async def _initialize_bot_service(self):
        """Initialize Bot service integration."""
        try:
            from .bot import BotService
            self.services['bot'] = BotService(self.db)
            await self.services['bot'].initialize()
            self.service_status['bot'] = True
            logger.info("Bot service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bot service: {str(e)}")
            self.service_status['bot'] = False
            raise

    async def _initialize_payment_service(self):
        """Initialize Payment service integration."""
        try:
            from .payment import PaymentService
            self.services['payment'] = PaymentService(self.db)
            await self.services['payment'].initialize()
            self.service_status['payment'] = True
            logger.info("Payment service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Payment service: {str(e)}")
            self.service_status['payment'] = False
            raise

    async def _initialize_monitoring_service(self):
        """Initialize Monitoring service integration."""
        try:
            from .monitoring import MonitoringService
            self.services['monitoring'] = MonitoringService(self.db)
            await self.services['monitoring'].initialize()
            self.service_status['monitoring'] = True
            logger.info("Monitoring service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Monitoring service: {str(e)}")
            self.service_status['monitoring'] = False
            raise

    async def _initialize_security_service(self):
        """Initialize Security service integration."""
        try:
            from .security import SecurityService
            self.services['security'] = SecurityService(self.db)
            await self.services['security'].initialize()
            self.service_status['security'] = True
            logger.info("Security service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Security service: {str(e)}")
            self.service_status['security'] = False
            raise

    async def send_message(self, from_service: str, to_service: str, message: Dict[str, Any]) -> bool:
        """Send a message from one service to another."""
        if to_service not in self.message_queues:
            logger.error(f"Service {to_service} not found")
            return False
            
        try:
            message_data = {
                "from": from_service,
                "to": to_service,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.message_queues[to_service].put(message_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send message from {from_service} to {to_service}: {str(e)}")
            return False

    async def receive_message(self, service: str) -> Optional[Dict[str, Any]]:
        """Receive a message for a specific service."""
        if service not in self.message_queues:
            logger.error(f"Service {service} not found")
            return None
            
        try:
            message = await self.message_queues[service].get()
            return message
        except Exception as e:
            logger.error(f"Failed to receive message for service {service}: {str(e)}")
            return None

    async def make_service_request(self, from_service: str, to_service: str, 
                                 method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make a request from one service to another."""
        if to_service not in self.services:
            logger.error(f"Service {to_service} not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    response = await self.services[to_service].handle_request(method, endpoint, data)
                    return response
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to make request from {from_service} to {to_service}: {str(e)}")
            return None

    async def get_service_status(self, service: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific service."""
        if service not in self.services:
            return None
            
        try:
            status = await self.services[service].get_status()
            return {
                "service": service,
                "status": status,
                "is_active": self.service_status.get(service, False),
                "last_check": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get status for service {service}: {str(e)}")
            return None

    async def get_all_service_status(self) -> List[Dict[str, Any]]:
        """Get the status of all services."""
        status_list = []
        for service in self.services:
            status = await self.get_service_status(service)
            if status:
                status_list.append(status)
        return status_list

    async def shutdown(self):
        """Shutdown all service integrations."""
        for service in self.services:
            try:
                await self.services[service].shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown service {service}: {str(e)}")
        self.service_status.clear()
        self.message_queues.clear() 