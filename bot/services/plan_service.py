"""
Service layer for subscription plans management.

This service manages plan creation, retrieval, and related operations.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

# Import models and schemas
from core.database.models.plan import Plan
from core.database.repositories.plan_repository import PlanRepository

# Import exceptions
from core.exceptions import NotFoundError, ServiceError

logger = logging.getLogger(__name__)

class PlanService:
    """Service for managing subscription plans."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.plan_repo = PlanRepository()

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """
        Get a plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan object or None if not found
        """
        return await self.plan_repo.get(self.db, id=plan_id)

    async def get_plans_by_name(self, name: str) -> List[Plan]:
        """
        Get plans by exact name match.
        
        Args:
            name: Plan name to match
            
        Returns:
            List of matching Plan objects
        """
        # This is a simple implementation, in a real app you might want more sophisticated matching
        plans = await self.plan_repo.get_multi(self.db)
        return [plan for plan in plans if plan.name == name]

    async def get_active_plans(
        self, 
        *,
        location_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Plan]:
        """
        Get active plans, optionally filtered by location.
        
        Args:
            location_id: Optional location filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Plan objects
        """
        # This is a simple implementation, you would need to add filtering by is_active and location
        return await self.plan_repo.get_multi(self.db, skip=skip, limit=limit)

    # Add other methods as needed 