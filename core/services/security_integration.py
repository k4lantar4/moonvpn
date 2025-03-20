"""
Security Integration Service for managing security-related integrations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session

from ..database.models.enhancements.health import SystemHealth, HealthStatus
from ..core.config import settings

logger = logging.getLogger(__name__)

class SecurityIntegrationService:
    """Service for managing security-related integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.security_services: Dict[str, Any] = {}
        self.security_status: Dict[str, bool] = {}
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1,
            "max_delay": 10
        }

    async def initialize(self):
        """Initialize all security integrations."""
        try:
            # Initialize core security services
            await self._initialize_authentication_service()
            await self._initialize_authorization_service()
            await self._initialize_encryption_service()
            await self._initialize_monitoring_service()
            await self._initialize_audit_service()
            
            logger.info("All security integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize security integrations: {str(e)}")
            raise

    async def _initialize_authentication_service(self):
        """Initialize authentication service integration."""
        try:
            from .auth import AuthenticationService
            self.security_services['auth'] = AuthenticationService(self.db)
            await self.security_services['auth'].initialize()
            self.security_status['auth'] = True
            logger.info("Authentication service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize authentication service: {str(e)}")
            self.security_status['auth'] = False
            raise

    async def _initialize_authorization_service(self):
        """Initialize authorization service integration."""
        try:
            from .authz import AuthorizationService
            self.security_services['authz'] = AuthorizationService(self.db)
            await self.security_services['authz'].initialize()
            self.security_status['authz'] = True
            logger.info("Authorization service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize authorization service: {str(e)}")
            self.security_status['authz'] = False
            raise

    async def _initialize_encryption_service(self):
        """Initialize encryption service integration."""
        try:
            from .encryption import EncryptionService
            self.security_services['encryption'] = EncryptionService(self.db)
            await self.security_services['encryption'].initialize()
            self.security_status['encryption'] = True
            logger.info("Encryption service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            self.security_status['encryption'] = False
            raise

    async def _initialize_monitoring_service(self):
        """Initialize security monitoring service integration."""
        try:
            from .monitoring import SecurityMonitoringService
            self.security_services['monitoring'] = SecurityMonitoringService(self.db)
            await self.security_services['monitoring'].initialize()
            self.security_status['monitoring'] = True
            logger.info("Security monitoring service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize security monitoring service: {str(e)}")
            self.security_status['monitoring'] = False
            raise

    async def _initialize_audit_service(self):
        """Initialize audit service integration."""
        try:
            from .audit import AuditService
            self.security_services['audit'] = AuditService(self.db)
            await self.security_services['audit'].initialize()
            self.security_status['audit'] = True
            logger.info("Audit service integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audit service: {str(e)}")
            self.security_status['audit'] = False
            raise

    async def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate a user using the authentication service."""
        if 'auth' not in self.security_services:
            logger.error("Authentication service not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    return await self.security_services['auth'].authenticate(credentials)
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to authenticate user: {str(e)}")
            return None

    async def authorize_access(self, user_id: int, resource: str) -> bool:
        """Authorize user access to a resource."""
        if 'authz' not in self.security_services:
            logger.error("Authorization service not found")
            return False
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    return await self.security_services['authz'].check_access(user_id, resource)
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to authorize access: {str(e)}")
            return False

    async def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt data using the encryption service."""
        if 'encryption' not in self.security_services:
            logger.error("Encryption service not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    return await self.security_services['encryption'].encrypt(data)
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            return None

    async def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data using the encryption service."""
        if 'encryption' not in self.security_services:
            logger.error("Encryption service not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    return await self.security_services['encryption'].decrypt(encrypted_data)
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            return None

    async def log_security_event(self, event: Dict[str, Any]) -> bool:
        """Log a security event using the audit service."""
        if 'audit' not in self.security_services:
            logger.error("Audit service not found")
            return False
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    return await self.security_services['audit'].log_event(event)
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            return False

    async def get_security_status(self, service: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific security service."""
        if service not in self.security_services:
            return None
            
        try:
            status = await self.security_services[service].get_status()
            return {
                "service": service,
                "status": status,
                "is_active": self.security_status.get(service, False),
                "last_check": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get status for security service {service}: {str(e)}")
            return None

    async def get_all_security_status(self) -> List[Dict[str, Any]]:
        """Get the status of all security services."""
        status_list = []
        for service in self.security_services:
            status = await self.get_security_status(service)
            if status:
                status_list.append(status)
        return status_list

    async def shutdown(self):
        """Shutdown all security integrations."""
        for service in self.security_services:
            try:
                await self.security_services[service].shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown security service {service}: {str(e)}")
        self.security_status.clear() 