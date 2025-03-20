"""
Health Check Service for monitoring system health and components.
"""
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.models.health import HealthCheck, HealthStatus
from app.core.schemas.health import HealthCheckCreate, HealthCheckUpdate
from app.core.utils.metrics import collect_system_metrics

class HealthCheckService:
    """Service for managing system health checks and monitoring."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_health_check(self, check: HealthCheckCreate) -> HealthCheck:
        """Create a new health check."""
        db_check = HealthCheck(
            component=check.component,
            status=check.status,
            message=check.message,
            metrics=check.metrics,
            last_check=datetime.utcnow()
        )
        self.db.add(db_check)
        await self.db.commit()
        await self.db.refresh(db_check)
        return db_check

    async def get_health_check(self, check_id: int) -> Optional[HealthCheck]:
        """Get a health check by ID."""
        result = await self.db.execute(
            select(HealthCheck).where(HealthCheck.id == check_id)
        )
        return result.scalar_one_or_none()

    async def update_health_check(self, check_id: int, check: HealthCheckUpdate) -> HealthCheck:
        """Update a health check."""
        db_check = await self.get_health_check(check_id)
        if not db_check:
            raise HTTPException(status_code=404, detail="Health check not found")

        for field, value in check.dict(exclude_unset=True).items():
            setattr(db_check, field, value)

        db_check.last_check = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(db_check)
        return db_check

    async def get_component_status(self, component: str) -> Optional[HealthCheck]:
        """Get the latest health check for a specific component."""
        result = await self.db.execute(
            select(HealthCheck)
            .where(HealthCheck.component == component)
            .order_by(HealthCheck.last_check.desc())
        )
        return result.scalar_one_or_none()

    async def get_system_status(self) -> Dict[str, HealthStatus]:
        """Get the current status of all system components."""
        components = [
            "server", "database", "api", "bot", 
            "system_resources", "network", "external_services"
        ]
        status = {}
        for component in components:
            check = await self.get_component_status(component)
            status[component] = check.status if check else HealthStatus.UNKNOWN
        return status

    async def perform_health_check(self, component: str) -> HealthCheck:
        """Perform a health check for a specific component."""
        metrics = await collect_system_metrics(component)
        status = self._determine_status(metrics)
        message = self._generate_status_message(component, status, metrics)

        check = HealthCheckCreate(
            component=component,
            status=status,
            message=message,
            metrics=metrics
        )
        return await self.create_health_check(check)

    def _determine_status(self, metrics: Dict) -> HealthStatus:
        """Determine the health status based on metrics."""
        # Implement status determination logic based on metrics
        if metrics.get("error_rate", 0) > 0.1:  # 10% error rate threshold
            return HealthStatus.ERROR
        elif metrics.get("response_time", 0) > 1.0:  # 1 second response time threshold
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY

    def _generate_status_message(self, component: str, status: HealthStatus, metrics: Dict) -> str:
        """Generate a human-readable status message."""
        if status == HealthStatus.HEALTHY:
            return f"{component} is healthy"
        elif status == HealthStatus.WARNING:
            return f"{component} is showing warning signs"
        else:
            return f"{component} is experiencing issues"

    async def get_health_history(self, component: str, limit: int = 100) -> List[HealthCheck]:
        """Get health check history for a component."""
        result = await self.db.execute(
            select(HealthCheck)
            .where(HealthCheck.component == component)
            .order_by(HealthCheck.last_check.desc())
            .limit(limit)
        )
        return result.scalars().all() 