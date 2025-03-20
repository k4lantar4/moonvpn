"""
API Integration Service for managing API-to-API communication.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
import aiohttp
import json
from sqlalchemy.orm import Session

from ..database.models.enhancements.health import SystemHealth, HealthStatus
from ..core.config import settings

logger = logging.getLogger(__name__)

class APIIntegrationService:
    """Service for managing API-to-API integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.apis: Dict[str, Any] = {}
        self.api_status: Dict[str, bool] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1,
            "max_delay": 10
        }

    async def initialize(self):
        """Initialize all API integrations."""
        try:
            # Initialize HTTP session
            self.session = aiohttp.ClientSession()
            
            # Initialize core APIs
            await self._initialize_vpn_api()
            await self._initialize_bot_api()
            await self._initialize_payment_api()
            await self._initialize_monitoring_api()
            await self._initialize_security_api()
            
            logger.info("All API integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize API integrations: {str(e)}")
            raise

    async def _initialize_vpn_api(self):
        """Initialize VPN API integration."""
        try:
            from .vpn import VPNService
            self.apis['vpn'] = VPNService(self.db)
            await self.apis['vpn'].initialize()
            self.api_status['vpn'] = True
            logger.info("VPN API integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VPN API: {str(e)}")
            self.api_status['vpn'] = False
            raise

    async def _initialize_bot_api(self):
        """Initialize Bot API integration."""
        try:
            from .bot import BotService
            self.apis['bot'] = BotService(self.db)
            await self.apis['bot'].initialize()
            self.api_status['bot'] = True
            logger.info("Bot API integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bot API: {str(e)}")
            self.api_status['bot'] = False
            raise

    async def _initialize_payment_api(self):
        """Initialize Payment API integration."""
        try:
            from .payment import PaymentService
            self.apis['payment'] = PaymentService(self.db)
            await self.apis['payment'].initialize()
            self.api_status['payment'] = True
            logger.info("Payment API integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Payment API: {str(e)}")
            self.api_status['payment'] = False
            raise

    async def _initialize_monitoring_api(self):
        """Initialize Monitoring API integration."""
        try:
            from .monitoring import MonitoringService
            self.apis['monitoring'] = MonitoringService(self.db)
            await self.apis['monitoring'].initialize()
            self.api_status['monitoring'] = True
            logger.info("Monitoring API integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Monitoring API: {str(e)}")
            self.api_status['monitoring'] = False
            raise

    async def _initialize_security_api(self):
        """Initialize Security API integration."""
        try:
            from .security import SecurityService
            self.apis['security'] = SecurityService(self.db)
            await self.apis['security'].initialize()
            self.api_status['security'] = True
            logger.info("Security API integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Security API: {str(e)}")
            self.api_status['security'] = False
            raise

    async def make_api_request(self, api: str, method: str, endpoint: str, 
                             data: Optional[Dict[str, Any]] = None, 
                             headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make a request to an API."""
        if api not in self.apis:
            logger.error(f"API {api} not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    response = await self.apis[api].make_request(method, endpoint, data, headers)
                    return response
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to make request to API {api}: {str(e)}")
            return None

    async def make_external_request(self, url: str, method: str = "GET",
                                  data: Optional[Dict[str, Any]] = None,
                                  headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make a request to an external API."""
        if not self.session:
            logger.error("HTTP session not initialized")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    async with self.session.request(method, url, json=data, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"External API request failed with status {response.status}")
                            return None
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to make external API request: {str(e)}")
            return None

    async def get_api_status(self, api: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific API."""
        if api not in self.apis:
            return None
            
        try:
            status = await self.apis[api].get_status()
            return {
                "api": api,
                "status": status,
                "is_active": self.api_status.get(api, False),
                "last_check": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get status for API {api}: {str(e)}")
            return None

    async def get_all_api_status(self) -> List[Dict[str, Any]]:
        """Get the status of all APIs."""
        status_list = []
        for api in self.apis:
            status = await self.get_api_status(api)
            if status:
                status_list.append(status)
        return status_list

    async def shutdown(self):
        """Shutdown all API integrations."""
        if self.session:
            await self.session.close()
        for api in self.apis:
            try:
                await self.apis[api].shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown API {api}: {str(e)}")
        self.api_status.clear() 