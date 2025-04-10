"""Base for repository classes."""

from typing import TypeVar, Generic, Type, Optional, List, Any
from pydantic import BaseModel
from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Assuming Base is your SQLAlchemy declarative base
from core.database.session import Base

logger = logging.getLogger(__name__)

# Type Variables for Generic Repository
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic repository providing basic CRUD operations for SQLAlchemy models.
    Uses asynchronous session management.
    IMPORTANT: This repository does NOT commit transactions. Commit/Rollback
    should be handled by the caller (e.g., middleware or service layer).
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the repository with the SQLAlchemy model.

        Args:
            model: The SQLAlchemy model class.
        """
        self._model = model

    async def create(self, db_session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Adds a new record to the session.
        Flushes the session to get the ID, but does NOT commit.

        Args:
            db_session: The database session.
            obj_in: The Pydantic schema containing the data for the new object.

        Returns:
            The newly created database object (without final commit).
        """
        try:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
            db_obj = self._model(**obj_in_data)
            db_session.add(db_obj)
            await db_session.flush()  # Flush to get ID and check constraints
            await db_session.refresh(db_obj) # Refresh to load relationships if needed
            logger.debug(
                f"Added {self._model.__name__} record with ID {getattr(db_obj, 'id', '?')} to session (needs commit).")
            return db_obj
        except SQLAlchemyError as e:
            # No rollback here, handled by caller
            logger.error(
                f"Database error during add/flush of {self._model.__name__}: {e}", exc_info=True)
            raise # Re-raise for caller to handle rollback
        except Exception as e:
            # No rollback here, handled by caller
            logger.error(
                f"Unexpected error during add/flush of {self._model.__name__}: {e}", exc_info=True)
            raise

    async def get(self, db_session: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Retrieve a single record by its primary key.

        Args:
            db_session: The database session.
            id: The primary key of the record to retrieve.

        Returns:
            The database object if found, otherwise None.
        """
        try:
            statement = select(self._model).where(self._model.id == id)
            result = await db_session.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting {self._model.__name__} by ID {id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while getting {self._model.__name__} by ID {id}: {e}", exc_info=True)
            return None

    async def get_multi(
        self, db_session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieve multiple records with optional pagination.

        Args:
            db_session: The database session.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of database objects.
        """
        try:
            statement = select(self._model).offset(
                skip).limit(limit).order_by(self._model.id)
            result = await db_session.execute(statement)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting multiple {self._model.__name__}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error while getting multiple {self._model.__name__}: {e}", exc_info=True)
            return []

    async def get_by_attributes(self, db_session: AsyncSession, **kwargs: Any) -> Optional[ModelType]:
        """
        Retrieve a single record by matching attribute values.

        Args:
            db_session: The database session.
            **kwargs: Attribute names and values to filter by.

        Returns:
            The first matching database object if found, otherwise None.
        """
        try:
            statement = select(self._model)
            for key, value in kwargs.items():
                if hasattr(self._model, key):
                    statement = statement.where(getattr(self._model, key) == value)
                else:
                    logger.warning(
                        f"Attribute '{key}' not found on model {self._model.__name__}")
            result = await db_session.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting {self._model.__name__} by attributes {kwargs}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while getting {self._model.__name__} by attributes {kwargs}: {e}", exc_info=True)
            return None

    async def update(
        self, db_session: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        Marks an existing database record for update within the session.
        Flushes the session, but does NOT commit.

        Args:
            db_session: The database session.
            db_obj: The database object to update.
            obj_in: A Pydantic schema or dictionary containing the fields to update.

        Returns:
            The updated database object (without final commit).
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            if not update_data:
                logger.warning(
                    f"Update called for {self._model.__name__} ID {getattr(db_obj, 'id', '?')} with no data.")
                return db_obj

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
                else:
                    logger.warning(
                        f"Field '{field}' not found on model {self._model.__name__} during update.")

            db_session.add(db_obj)
            await db_session.flush() # Flush to apply changes within the session
            await db_session.refresh(db_obj) # Refresh to get updated state
            logger.debug(
                f"Marked {self._model.__name__} record with ID {getattr(db_obj, 'id', '?')} for update (needs commit).")
            return db_obj
        except SQLAlchemyError as e:
            # No rollback here, handled by caller
            logger.error(
                f"Database error during update/flush of {self._model.__name__} ID {getattr(db_obj, 'id', '?')}: {e}", exc_info=True)
            raise
        except Exception as e:
            # No rollback here, handled by caller
            logger.error(
                f"Unexpected error during update/flush of {self._model.__name__} ID {getattr(db_obj, 'id', '?')}: {e}", exc_info=True)
            raise

    async def delete(self, db_session: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Marks a record for deletion within the session by its primary key.
        Does NOT commit the transaction.

        Args:
            db_session: The database session.
            id: The primary key of the record to delete.

        Returns:
            The object marked for deletion if found, otherwise None.
        """
        try:
            obj = await self.get(db_session, id=id)
            if obj is None:
                logger.warning(
                    f"Attempted to delete non-existent {self._model.__name__} with ID {id}")
                return None

            await db_session.delete(obj)
            await db_session.flush() # Flush to confirm deletion within session context
            logger.debug(
                f"Marked {self._model.__name__} record with ID {id} for deletion (needs commit).")
            return obj
        except SQLAlchemyError as e:
            # No rollback here, handled by caller
            logger.error(
                f"Database error during delete/flush of {self._model.__name__} ID {id}: {e}", exc_info=True)
            raise
        except Exception as e:
            # No rollback here, handled by caller
            logger.error(
                f"Unexpected error during delete/flush of {self._model.__name__} ID {id}: {e}", exc_info=True)
            raise
