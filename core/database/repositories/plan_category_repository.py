"""Repository for PlanCategory model operations."""

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, Sequence, List, Any
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
import logging

from core.database.models.plan_category import PlanCategory
from core.database.repositories.base_repo import BaseRepository
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class PlanCategoryRepository(BaseRepository[PlanCategory, Any, Any]):
    """
    Repository for PlanCategory model operations.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    def __init__(self):
        super().__init__(model=PlanCategory)

    async def get_by_name(self, db_session: AsyncSession, *, name: str) -> Optional[PlanCategory]:
        """
        Retrieve a plan category by name.
        
        Args:
            db_session: The database session
            name: Name of the category to find
            
        Returns:
            The PlanCategory if found, None otherwise
        """
        try:
            statement = select(self._model).where(self._model.name == name)
            result = await db_session.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving plan category by name '{name}': {e}", exc_info=True)
            raise ServiceError(f"Database error while retrieving plan category '{name}'")
    
    async def get_active_categories(
        self, 
        db_session: AsyncSession, 
        *, 
        eager_load_plans: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[PlanCategory]:
        """
        Retrieve all active plan categories with optional pagination.
        
        Args:
            db_session: The database session
            eager_load_plans: Whether to load associated plans
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to retrieve
            
        Returns:
            A sequence of PlanCategory objects
        """
        try:
            stmt = select(self._model).where(self._model.is_active == True).order_by(self._model.sorting_order, self._model.name)
            
            if eager_load_plans:
                stmt = stmt.options(selectinload(self._model.plans))
            
            if skip > 0:
                stmt = stmt.offset(skip)
            
            if limit > 0:
                stmt = stmt.limit(limit)
                
            result = await db_session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving active plan categories: {e}", exc_info=True)
            raise ServiceError("Database error while retrieving active plan categories")
    
    async def update_sorting_order(self, db_session: AsyncSession, *, category_id: int, sorting_order: int) -> None:
        """
        Update the sorting order of a specific plan category.
        
        Args:
            db_session: The database session
            category_id: ID of the category to update
            sorting_order: New sorting order value
        """
        try:
            stmt = (
                update(self._model)
                .where(self._model.id == category_id)
                .values(sorting_order=sorting_order, updated_at=func.now())
            )
            await db_session.execute(stmt)
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating sorting order for category {category_id}: {e}", exc_info=True)
            raise ServiceError(f"Database error while updating category sorting order")
