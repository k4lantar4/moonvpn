"""
Panel Selector Service

This module provides a service for selecting the most appropriate panel
for client creation based on various criteria including load, health status,
priority, and location.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from core.database import get_db
from api.models import Panel, PanelHealthCheck, Location, Client

logger = logging.getLogger(__name__)


class SelectionStrategy(str, Enum):
    """Strategy for panel selection."""
    LEAST_LOAD = "LEAST_LOAD"  # Select panel with lowest client count
    ROUND_ROBIN = "ROUND_ROBIN"  # Select panels in rotation
    BEST_HEALTH = "BEST_HEALTH"  # Select panel with best health score
    PRIORITY = "PRIORITY"  # Select panel with highest priority
    BALANCED = "BALANCED"  # Balanced selection considering multiple factors


class PanelSelector:
    """Service for selecting the optimal panel for new clients.
    
    This service provides methods for:
    - Finding the best panel for a given location
    - Panel selection using various strategies
    - Load balancing across multiple panels
    """
    
    def __init__(self, db: AsyncSession = None):
        """Initialize panel selector.
        
        Args:
            db: Database session (optional, will be created if needed)
        """
        self.db = db
    
    async def _get_db(self) -> AsyncSession:
        """Get database session, creating one if not provided in constructor.
        
        Returns:
            AsyncSession: Database session
        """
        if self.db is None:
            self.db = await anext(get_db())
        return self.db
    
    async def select_panel(
        self, 
        location_id: int,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        protocol: Optional[str] = None,
        premium_only: bool = False,
        exclude_panel_ids: List[int] = None
    ) -> Optional[Panel]:
        """Select the best panel for a new client.
        
        Args:
            location_id: Location ID
            strategy: Selection strategy
            protocol: Required protocol (if specific protocol needed)
            premium_only: Whether to select only premium panels
            exclude_panel_ids: Panel IDs to exclude
            
        Returns:
            Optional[Panel]: Selected panel or None if no suitable panel found
        """
        db = await self._get_db()
        
        # Get all active panels for the location
        query = (
            select(Panel)
            .options(selectinload(Panel.health_checks))
            .filter(Panel.location_id == location_id)
            .filter(Panel.is_active == True)
        )
        
        # Apply additional filters
        if premium_only:
            query = query.filter(Panel.is_premium == True)
        
        if exclude_panel_ids:
            query = query.filter(Panel.id.notin_(exclude_panel_ids))
        
        # Get all eligible panels
        result = await db.execute(query)
        panels = result.scalars().all()
        
        if not panels:
            logger.warning(f"No active panels found for location ID {location_id}")
            return None
        
        # Filter by protocol support if needed
        if protocol:
            panels = [p for p in panels if self._supports_protocol(p, protocol)]
            
            if not panels:
                logger.warning(f"No panels supporting protocol {protocol} found for location ID {location_id}")
                return None
        
        # Select panel using the specified strategy
        if strategy == SelectionStrategy.LEAST_LOAD:
            return await self._select_by_least_load(panels)
        elif strategy == SelectionStrategy.ROUND_ROBIN:
            return await self._select_by_round_robin(panels, location_id)
        elif strategy == SelectionStrategy.BEST_HEALTH:
            return await self._select_by_health(panels)
        elif strategy == SelectionStrategy.PRIORITY:
            return await self._select_by_priority(panels)
        else:  # BALANCED strategy (default)
            return await self._select_balanced(panels)
    
    async def _select_by_least_load(self, panels: List[Panel]) -> Panel:
        """Select panel with the lowest current client count.
        
        Args:
            panels: List of panels to choose from
            
        Returns:
            Panel: Selected panel
        """
        db = await self._get_db()
        
        panel_loads = {}
        for panel in panels:
            # Count active clients on this panel
            client_count = await db.execute(
                select(func.count(Client.id))
                .filter(Client.panel_id == panel.id)
                .filter(Client.status == "ACTIVE")
            )
            panel_loads[panel.id] = client_count.scalar() or 0
        
        # Select panel with lowest load
        if not panel_loads:
            return panels[0]  # Fallback to first panel if no load data
        
        selected_panel_id = min(panel_loads, key=panel_loads.get)
        return next(p for p in panels if p.id == selected_panel_id)
    
    async def _select_by_round_robin(self, panels: List[Panel], location_id: int) -> Panel:
        """Select panel using round-robin strategy.
        
        Args:
            panels: List of panels to choose from
            location_id: Location ID for tracking last selected panel
            
        Returns:
            Panel: Selected panel
        """
        db = await self._get_db()
        
        # Get last selected panel for this location from settings
        from api.models import Settings
        setting_key = f"last_panel_for_location_{location_id}"
        
        result = await db.execute(
            select(Settings).filter(Settings.key == setting_key)
        )
        setting = result.scalars().first()
        
        last_panel_id = None
        if setting:
            try:
                last_panel_id = int(setting.value)
            except (ValueError, TypeError):
                last_panel_id = None
        
        # Find the panel that was used last time
        last_index = -1
        for i, panel in enumerate(panels):
            if panel.id == last_panel_id:
                last_index = i
                break
        
        # Select next panel in rotation
        next_index = (last_index + 1) % len(panels)
        selected_panel = panels[next_index]
        
        # Update the setting for next selection
        if setting:
            setting.value = str(selected_panel.id)
            db.add(setting)
        else:
            new_setting = Settings(
                key=setting_key,
                value=str(selected_panel.id),
                description=f"Last selected panel for location {location_id}",
                is_public=False,
                group="panel_selection"
            )
            db.add(new_setting)
        
        await db.commit()
        return selected_panel
    
    async def _select_by_health(self, panels: List[Panel]) -> Panel:
        """Select panel with the best health status.
        
        Args:
            panels: List of panels to choose from
            
        Returns:
            Panel: Selected panel
        """
        # Score panels based on health checks
        panel_scores = {}
        
        for panel in panels:
            # Default score for panels without health checks
            score = 0
            
            # Add score based on is_healthy flag
            if panel.is_healthy:
                score += 10
            
            # Add score based on recent health checks
            recent_checks = [
                check for check in panel.health_checks
                if check.checked_at > datetime.utcnow() - timedelta(hours=1)
            ]
            
            if recent_checks:
                # Calculate percentage of successful checks
                success_count = sum(1 for check in recent_checks if check.status == "OK")
                success_rate = success_count / len(recent_checks)
                score += success_rate * 5
                
                # Add score based on response times (lower is better)
                avg_response_time = sum(
                    check.response_time_ms for check in recent_checks 
                    if check.response_time_ms is not None
                ) / len(recent_checks) if recent_checks else 1000
                
                # Convert response time to score (1-5)
                # 0-100ms: 5, 100-200ms: 4, 200-500ms: 3, 500-1000ms: 2, >1000ms: 1
                time_score = 0
                if avg_response_time < 100:
                    time_score = 5
                elif avg_response_time < 200:
                    time_score = 4
                elif avg_response_time < 500:
                    time_score = 3
                elif avg_response_time < 1000:
                    time_score = 2
                else:
                    time_score = 1
                
                score += time_score
            
            panel_scores[panel.id] = score
        
        # Select panel with highest health score
        if not panel_scores:
            return panels[0]  # Fallback to first panel if no health data
        
        selected_panel_id = max(panel_scores, key=panel_scores.get)
        return next(p for p in panels if p.id == selected_panel_id)
    
    async def _select_by_priority(self, panels: List[Panel]) -> Panel:
        """Select panel with the highest priority setting.
        
        Args:
            panels: List of panels to choose from
            
        Returns:
            Panel: Selected panel
        """
        # Sort panels by priority (higher is better)
        sorted_panels = sorted(
            panels, 
            key=lambda p: p.priority if p.priority is not None else 0,
            reverse=True
        )
        
        return sorted_panels[0]
    
    async def _select_balanced(self, panels: List[Panel]) -> Panel:
        """Select panel using a balanced approach considering multiple factors.
        
        Args:
            panels: List of panels to choose from
            
        Returns:
            Panel: Selected panel
        """
        db = await self._get_db()
        
        # Calculate comprehensive score for each panel
        panel_scores = {}
        
        for panel in panels:
            score = 0
            
            # 1. Load score (lower client count is better)
            client_count = await db.execute(
                select(func.count(Client.id))
                .filter(Client.panel_id == panel.id)
                .filter(Client.status == "ACTIVE")
            )
            clients = client_count.scalar() or 0
            
            # Calculate load score (0-40 points, inversely proportional to load)
            max_clients = panel.max_clients or 1000
            load_percentage = min(100, (clients / max_clients) * 100)
            load_score = 40 * (1 - (load_percentage / 100))
            score += load_score
            
            # 2. Health score (0-30 points)
            health_score = 0
            if panel.is_healthy:
                health_score += 15
                
            recent_checks = [
                check for check in panel.health_checks
                if check.checked_at > datetime.utcnow() - timedelta(hours=1)
            ]
            
            if recent_checks:
                success_count = sum(1 for check in recent_checks if check.status == "OK")
                success_rate = success_count / len(recent_checks)
                health_score += success_rate * 15
            
            score += health_score
            
            # 3. Priority score (0-20 points)
            priority_score = min(20, panel.priority or 0)
            score += priority_score
            
            # 4. Premium bonus (0-10 points)
            if panel.is_premium:
                score += 10
                
            panel_scores[panel.id] = score
        
        # Select panel with highest balanced score
        if not panel_scores:
            return panels[0]  # Fallback to first panel
        
        selected_panel_id = max(panel_scores, key=panel_scores.get)
        return next(p for p in panels if p.id == selected_panel_id)
    
    def _supports_protocol(self, panel: Panel, protocol: str) -> bool:
        """Check if panel supports the specified protocol.
        
        Args:
            panel: Panel to check
            protocol: Required protocol
            
        Returns:
            bool: True if panel supports the protocol, False otherwise
        """
        # Check if panel has protocol constraints
        # For now, assume all panels support all protocols
        # In the future, this could be enhanced to check panel configuration
        return True 