from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from api.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    CRUD repository base class with default methods to Create, Read, Update, Delete (CRUD).
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with the model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Get a single model instance by id.

        Args:
            db: Database session
            id: Primary key ID

        Returns:
            ModelType: The model instance or None if not found
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_by(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """
        Get a single model instance by given filters.

        Args:
            db: Database session
            **kwargs: Filter conditions

        Returns:
            ModelType: The model instance or None if not found
        """
        stmt = select(self.model)
        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, **kwargs
    ) -> List[ModelType]:
        """
        Get multiple model instances with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            **kwargs: Filter conditions

        Returns:
            List[ModelType]: List of model instances
        """
        stmt = select(self.model).offset(skip).limit(limit)
        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new model instance.

        Args:
            db: Database session
            obj_in: Dict of model values

        Returns:
            ModelType: The created model instance
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Dict[str, Any]
    ) -> ModelType:
        """
        Update a model instance.

        Args:
            db: Database session
            db_obj: Model instance to update
            obj_in: Dict of values to update

        Returns:
            ModelType: The updated model instance
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """
        Delete a model instance.

        Args:
            db: Database session
            id: Primary key ID

        Returns:
            ModelType: The deleted model instance or None if not found
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def count(self, db: AsyncSession, **kwargs) -> int:
        """
        Count model instances with given filters.

        Args:
            db: Database session
            **kwargs: Filter conditions

        Returns:
            int: Count of model instances
        """
        stmt = select(self.model)
        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await db.execute(select([db.func.count()]).select_from(stmt.subquery()))
        return result.scalar_one() 