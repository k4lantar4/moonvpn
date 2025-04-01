from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase # Assuming you have a base CRUD class
from app.models.role import Role
from app.models.permission import Permission
from app.schemas.role import RoleCreate, RoleUpdate

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_role_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """Get a role by its name."""
        return db.query(Role).filter(Role.name == name).first()

    def add_permission_to_role(self, db: Session, *, role: Role, permission: Permission) -> Role:
        """Adds a permission to a role's permission list."""
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role

    def remove_permission_from_role(self, db: Session, *, role: Role, permission: Permission) -> Role:
        """Removes a permission from a role's permission list."""
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role

# Instantiate the CRUD object for Role
role = CRUDRole(Role) 