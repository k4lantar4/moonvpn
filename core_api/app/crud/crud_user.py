# Import necessary components for CRUD operations
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union, List

# Import models and schemas
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase # Import the base CRUD class
# Potentially import password hashing utilities if needed later
# from app.core.security import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_telegram_id(self, db: Session, *, telegram_id: int) -> Optional[User]:
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    # Override create method if password hashing is needed
    # def create(self, db: Session, *, obj_in: UserCreate) -> User:
    #     create_data = obj_in.model_dump()
    #     create_data.pop("password") # Remove plain password
    #     db_obj = User(**create_data)
    #     db_obj.hashed_password = get_password_hash(obj_in.password)
    #     db.add(db_obj)
    #     db.commit()
    #     db.refresh(db_obj)
    #     return db_obj

    # Add any other user-specific CRUD methods here
    # For example:
    # def activate_user(self, db: Session, *, user: User) -> User:
    #     user.is_active = True
    #     db.add(user)
    #     db.commit()
    #     db.refresh(user)
    #     return user

# Create a singleton instance of the CRUDUser class
user = CRUDUser(User)

# --- Deprecated Individual Functions (kept for reference, can be removed later) ---
# These are now handled by the CRUDBase methods (user.get, user.get_multi, user.create, etc.)

# def get_user(db: Session, user_id: int) -> Optional[User]:
#     return db.query(User).filter(User.id == user_id).first()
#
# def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
#     return db.query(User).filter(User.telegram_id == telegram_id).first()
#
# def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
#     return db.query(User).offset(skip).limit(limit).all()
#
# def create_user(db: Session, *, obj_in: UserCreate) -> User:
#     create_data = obj_in.model_dump()
#     db_obj = User(**create_data)
#     db.add(db_obj)
#     db.commit()
#     db.refresh(db_obj)
#     return db_obj
#
# def update_user(db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
#     if isinstance(obj_in, dict):
#         update_data = obj_in
#     else:
#         update_data = obj_in.model_dump(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(db_obj, field, value)
#     db.add(db_obj)
#     db.commit()
#     db.refresh(db_obj)
#     return db_obj
#
# def remove_user(db: Session, *, user_id: int) -> Optional[User]:
#     db_obj = db.query(User).get(user_id)
#     if db_obj:
#         db.delete(db_obj)
#         db.commit()
#     return db_obj 