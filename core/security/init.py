"""
Security initialization script for setting up security services.
"""
from typing import Optional
from fastapi import FastAPI
from sqlalchemy.orm import Session
import logging
import asyncio

from ..services.security_monitoring import SecurityMonitoringService
from ..services.notification import NotificationService
from ..middleware.security_middleware import SecurityMiddleware
from ..core.config.security_config import security_settings
from ..database.session import SessionLocal

logger = logging.getLogger(__name__)

class SecurityInitializer:
    def __init__(self, app: FastAPI):
        self.app = app
        self.monitoring_service: Optional[SecurityMonitoringService] = None
        self.notification_service: Optional[NotificationService] = None
        self.cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize security services."""
        try:
            # Initialize database session
            db = SessionLocal()

            # Initialize services
            self.monitoring_service = SecurityMonitoringService(db)
            self.notification_service = NotificationService()

            # Start monitoring service
            await self.monitoring_service.start_monitoring()

            # Add security middleware
            self.app.add_middleware(
                SecurityMiddleware,
                monitoring_service=self.monitoring_service,
                notification_service=self.notification_service
            )

            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_task())

            logger.info("Security services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize security services: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown security services."""
        try:
            # Stop monitoring service
            if self.monitoring_service:
                await self.monitoring_service.stop_monitoring()

            # Cancel cleanup task
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            logger.info("Security services shutdown successfully")

        except Exception as e:
            logger.error(f"Error during security services shutdown: {str(e)}")
            raise

    async def _cleanup_task(self):
        """Background task for cleaning up security-related data."""
        while True:
            try:
                # Get middleware instance
                middleware = next(
                    (m for m in self.app.user_middleware if isinstance(m, SecurityMiddleware)),
                    None
                )

                if middleware:
                    # Run cleanup
                    await middleware.cleanup()

                # Wait for next cleanup interval
                await asyncio.sleep(security_settings.RATE_LIMIT_WINDOW)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during security cleanup: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

def init_security(app: FastAPI):
    """Initialize security for the FastAPI application."""
    initializer = SecurityInitializer(app)

    @app.on_event("startup")
    async def startup_event():
        await initializer.initialize()

    @app.on_event("shutdown")
    async def shutdown_event():
        await initializer.shutdown()

    return initializer 