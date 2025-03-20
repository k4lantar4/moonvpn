"""
Alert service for managing system alerts and alert rules.
"""
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.models.alert import Alert, AlertRule, AlertSeverity, AlertStatus
from app.core.schemas.alert import AlertCreate, AlertUpdate, AlertRuleCreate, AlertRuleUpdate
from app.core.utils.notifications import send_alert_notification

class AlertService:
    """Service for managing system alerts and alert rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(self, alert: AlertCreate) -> Alert:
        """Create a new alert."""
        db_alert = Alert(**alert.dict())
        self.db.add(db_alert)
        await self.db.commit()
        await self.db.refresh(db_alert)
        
        # Send notification for the new alert
        await send_alert_notification(db_alert)
        
        return db_alert

    async def get_alert(self, alert_id: int) -> Optional[Alert]:
        """Get an alert by ID."""
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def update_alert(self, alert_id: int, alert: AlertUpdate) -> Alert:
        """Update an alert."""
        db_alert = await self.get_alert(alert_id)
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        for field, value in alert.dict(exclude_unset=True).items():
            setattr(db_alert, field, value)

        await self.db.commit()
        await self.db.refresh(db_alert)
        return db_alert

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        result = await self.db.execute(
            select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        )
        return result.scalars().all()

    async def get_component_alerts(self, component: str) -> List[Alert]:
        """Get all alerts for a specific component."""
        result = await self.db.execute(
            select(Alert).where(Alert.component == component)
        )
        return result.scalars().all()

    async def create_alert_rule(self, rule: AlertRuleCreate) -> AlertRule:
        """Create a new alert rule."""
        db_rule = AlertRule(**rule.dict())
        self.db.add(db_rule)
        await self.db.commit()
        await self.db.refresh(db_rule)
        return db_rule

    async def get_alert_rule(self, rule_id: int) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def update_alert_rule(self, rule_id: int, rule: AlertRuleUpdate) -> AlertRule:
        """Update an alert rule."""
        db_rule = await self.get_alert_rule(rule_id)
        if not db_rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        for field, value in rule.dict(exclude_unset=True).items():
            setattr(db_rule, field, value)

        await self.db.commit()
        await self.db.refresh(db_rule)
        return db_rule

    async def get_active_rules(self) -> List[AlertRule]:
        """Get all active alert rules."""
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.is_active == True)
        )
        return result.scalars().all()

    async def get_component_rules(self, component: str) -> List[AlertRule]:
        """Get all alert rules for a specific component."""
        result = await self.db.execute(
            select(AlertRule).where(
                and_(
                    AlertRule.component == component,
                    AlertRule.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def evaluate_metrics(self, component: str, metrics: Dict) -> List[Alert]:
        """Evaluate metrics against alert rules and create alerts if needed."""
        rules = await self.get_component_rules(component)
        alerts = []

        for rule in rules:
            if self._check_condition(rule.condition, metrics):
                alert = AlertCreate(
                    component=component,
                    severity=rule.severity,
                    title=f"Alert: {rule.name}",
                    message=f"Alert rule '{rule.name}' triggered for {component}",
                    metrics=metrics
                )
                alerts.append(await self.create_alert(alert))

        return alerts

    def _check_condition(self, condition: Dict, metrics: Dict) -> bool:
        """Check if metrics meet the alert condition."""
        # Implement condition evaluation logic
        # This is a placeholder - implement actual condition evaluation
        return False 