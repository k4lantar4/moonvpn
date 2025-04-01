# core_api/app/crud/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete

from app.db.base_class import Base # Assuming your SQLAlchemy models inherit from Base defined here

# Define Type Variables for Pydantic models and SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single object by ID."""
        # return db.query(self.model).filter(self.model.id == id).first()
        # Using SQLAlchemy 2.0 style select:
        stmt = select(self.model).where(self.model.id == id)
        return db.scalars(stmt).first()


    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple objects with pagination."""
        # return db.query(self.model).offset(skip).limit(limit).all()
        # Using SQLAlchemy 2.0 style select:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new object.

        Args:
            db: Database session.
            obj_in: Pydantic schema for creation.

        Returns:
            The created SQLAlchemy model instance.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing object.

        Args:
            db: Database session.
            db_obj: SQLAlchemy model instance to update.
            obj_in: Pydantic schema or dict with update data.

        Returns:
            The updated SQLAlchemy model instance.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Use exclude_unset=True to only update fields that are explicitly set
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Remove an object by ID.

        Args:
            db: Database session.
            id: ID of the object to remove.

        Returns:
            The removed SQLAlchemy model instance, or None if not found.
        """
        obj = self.get(db=db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    # Note: Assumes your models inherit from a Base defined in app.db.base_class
    # Adjust the import `from app.db.base_class import Base` if needed. 