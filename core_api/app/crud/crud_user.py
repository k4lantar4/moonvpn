# Import necessary components for CRUD operations
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union, List

# Import models and schemas
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# Potentially import password hashing utilities if needed later
# from app.core.security import get_password_hash, verify_password

# --- User CRUD Operations ---

def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieves a single user by their primary key ID.

    Args:
        db: The database session.
        user_id: The ID of the user to retrieve.

    Returns:
        The User object if found, otherwise None.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    """
    Retrieves a single user by their Telegram ID.

    Args:
        db: The database session.
        telegram_id: The Telegram ID of the user to retrieve.

    Returns:
        The User object if found, otherwise None.
    """
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieves a list of users with pagination.

    Args:
        db: The database session.
        skip: The number of records to skip (for pagination).
        limit: The maximum number of records to return.

    Returns:
        A list of User objects.
    """
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, *, obj_in: UserCreate) -> User:
    """
    Creates a new user in the database.

    Args:
        db: The database session.
        obj_in: The Pydantic schema containing the user creation data.

    Returns:
        The newly created User object.
    """
    # Create a dictionary from the input schema
    # In a real scenario, hash the password here if applicable
    # hashed_password = get_password_hash(obj_in.password)
    # create_data = obj_in.model_dump()
    # create_data['hashed_password'] = hashed_password
    # del create_data['password'] # Don't store plain password

    # For now, directly use the model_dump without password hashing
    create_data = obj_in.model_dump()

    db_obj = User(**create_data) # Create SQLAlchemy model instance
    db.add(db_obj)              # Add to session
    db.commit()                 # Commit transaction
    db.refresh(db_obj)          # Refresh to get ID and defaults
    return db_obj

def update_user(db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    """
    Updates an existing user in the database.

    Args:
        db: The database session.
        db_obj: The existing User object to update.
        obj_in: The Pydantic schema or dictionary containing the update data.

    Returns:
        The updated User object.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        # Exclude unset fields to allow partial updates
        update_data = obj_in.model_dump(exclude_unset=True)

    # Update fields in the database object
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def remove_user(db: Session, *, user_id: int) -> Optional[User]:
    """
    Removes a user from the database by their ID.
    Note: Depending on requirements, this might perform a soft delete (e.g., setting an 'is_active' flag to False)
          instead of a hard delete. For now, it performs a hard delete.

    Args:
        db: The database session.
        user_id: The ID of the user to remove.

    Returns:
        The removed User object if found and deleted, otherwise None.
    """
    db_obj = db.query(User).get(user_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj # Return the object that was deleted, or None if not found 