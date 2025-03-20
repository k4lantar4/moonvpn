"""
Integration Manager Service for coordinating all integration services.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session

from .component_integration import ComponentIntegrationService
from .service_integration import ServiceIntegrationService
from .api_integration import APIIntegrationService
from .database_integration import DatabaseIntegrationService
from .security_integration import SecurityIntegrationService

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Manager service for coordinating all integration services."""

    def __init__(self, db: Session):
        self.db = db
        self.component_service = ComponentIntegrationService(db)
        self.service_service = ServiceIntegrationService(db)
        self.api_service = APIIntegrationService(db)
        self.database_service = DatabaseIntegrationService(db)
        self.security_service = SecurityIntegrationService(db)
        self.is_initialized = False

    async def initialize(self):
        """Initialize all integration services."""
        try:
            # Initialize all services in parallel
            await asyncio.gather(
                self.component_service.initialize(),
                self.service_service.initialize(),
                self.api_service.initialize(),
                self.database_service.initialize(),
                self.security_service.initialize()
            )
            
            self.is_initialized = True
            logger.info("All integration services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integration services: {str(e)}")
            raise

    async def get_system_status(self) -> Dict[str, Any]:
        """Get the overall status of the system."""
        if not self.is_initialized:
            return {"status": "not_initialized"}
            
        try:
            # Get status from all services in parallel
            component_status, service_status, api_status, db_status, security_status = await asyncio.gather(
                self.component_service.get_all_component_status(),
                self.service_service.get_all_service_status(),
                self.api_service.get_all_api_status(),
                self.database_service.get_all_database_status(),
                self.security_service.get_all_security_status()
            )
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": component_status,
                "services": service_status,
                "apis": api_status,
                "databases": db_status,
                "security": security_status
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def check_system_health(self) -> bool:
        """Check if the entire system is healthy."""
        if not self.is_initialized:
            return False
            
        try:
            status = await self.get_system_status()
            if status["status"] != "healthy":
                return False
                
            # Check each component's health
            for component in status["components"]:
                if not component.get("is_integrated", False):
                    return False
                    
            # Check each service's health
            for service in status["services"]:
                if not service.get("is_active", False):
                    return False
                    
            # Check each API's health
            for api in status["apis"]:
                if not api.get("is_active", False):
                    return False
                    
            # Check each database's health
            for db in status["databases"]:
                if db.get("status") != "healthy":
                    return False
                    
            # Check each security service's health
            for security in status["security"]:
                if not security.get("is_active", False):
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Failed to check system health: {str(e)}")
            return False

    async def restart_component(self, component: str) -> bool:
        """Restart a specific component."""
        if not self.is_initialized:
            return False
            
        try:
            return await self.component_service.restart_component(component)
        except Exception as e:
            logger.error(f"Failed to restart component {component}: {str(e)}")
            return False

    async def backup_database(self, source_db: str, target_db: str) -> bool:
        """Backup data from one database to another."""
        if not self.is_initialized:
            return False
            
        try:
            return await self.database_service.backup_database(source_db, target_db)
        except Exception as e:
            logger.error(f"Failed to backup database from {source_db} to {target_db}: {str(e)}")
            return False

    async def sync_databases(self, source_db: str, target_db: str) -> bool:
        """Synchronize data between two databases."""
        if not self.is_initialized:
            return False
            
        try:
            return await self.database_service.sync_databases(source_db, target_db)
        except Exception as e:
            logger.error(f"Failed to sync databases {source_db} and {target_db}: {str(e)}")
            return False

    async def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate a user using the security service."""
        if not self.is_initialized:
            return None
            
        try:
            return await self.security_service.authenticate_user(credentials)
        except Exception as e:
            logger.error(f"Failed to authenticate user: {str(e)}")
            return None

    async def authorize_access(self, user_id: int, resource: str) -> bool:
        """Authorize user access to a resource."""
        if not self.is_initialized:
            return False
            
        try:
            return await self.security_service.authorize_access(user_id, resource)
        except Exception as e:
            logger.error(f"Failed to authorize access: {str(e)}")
            return False

    async def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt data using the security service."""
        if not self.is_initialized:
            return None
            
        try:
            return await self.security_service.encrypt_data(data)
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            return None

    async def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data using the security service."""
        if not self.is_initialized:
            return None
            
        try:
            return await self.security_service.decrypt_data(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            return None

    async def log_security_event(self, event: Dict[str, Any]) -> bool:
        """Log a security event using the security service."""
        if not self.is_initialized:
            return False
            
        try:
            return await self.security_service.log_security_event(event)
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            return False

    async def shutdown(self):
        """Shutdown all integration services."""
        if not self.is_initialized:
            return
            
        try:
            # Shutdown all services in parallel
            await asyncio.gather(
                self.component_service.shutdown(),
                self.service_service.shutdown(),
                self.api_service.shutdown(),
                self.database_service.shutdown(),
                self.security_service.shutdown()
            )
            
            self.is_initialized = False
            logger.info("All integration services shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown integration services: {str(e)}")
            raise 