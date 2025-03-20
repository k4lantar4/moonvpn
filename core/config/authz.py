"""
Authorization service for handling role-based access control and permissions.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..database.models.user import User
from ..database.models.role import Role
from ..database.models.permission import Permission
from ..core.exceptions import SecurityError

class AuthorizationService:
    def __init__(self, db: Session):
        self.db = db

    async def check_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise SecurityError("User not found")

            # Get user's role
            role = self.db.query(Role).filter(Role.id == user.role_id).first()
            if not role:
                raise SecurityError("User role not found")

            # Check if role has permission
            return any(p.name == permission for p in role.permissions)

        except Exception as e:
            raise SecurityError(f"Permission check failed: {str(e)}")

    async def check_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise SecurityError("User not found")

            # Get user's role
            role = self.db.query(Role).filter(Role.id == user.role_id).first()
            if not role:
                raise SecurityError("User role not found")

            # Check if role has all permissions
            role_permissions = {p.name for p in role.permissions}
            return all(p in role_permissions for p in permissions)

        except Exception as e:
            raise SecurityError(f"Permissions check failed: {str(e)}")

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise SecurityError("User not found")

            # Get user's role
            role = self.db.query(Role).filter(Role.id == user.role_id).first()
            if not role:
                raise SecurityError("User role not found")

            # Get all permissions for role
            return [p.name for p in role.permissions]

        except Exception as e:
            raise SecurityError(f"Failed to get user permissions: {str(e)}")

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Assign a role to a user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise SecurityError("User not found")

            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise SecurityError("Role not found")

            user.role_id = role_id
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to assign role: {str(e)}")

    async def create_role(self, name: str, description: str, permissions: List[str]) -> Role:
        """Create a new role with permissions."""
        try:
            # Check if role already exists
            existing_role = self.db.query(Role).filter(Role.name == name).first()
            if existing_role:
                raise SecurityError("Role already exists")

            # Get permission objects
            permission_objects = []
            for perm_name in permissions:
                perm = self.db.query(Permission).filter(Permission.name == perm_name).first()
                if not perm:
                    raise SecurityError(f"Permission not found: {perm_name}")
                permission_objects.append(perm)

            # Create new role
            role = Role(
                name=name,
                description=description,
                permissions=permission_objects
            )
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)

            return role

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to create role: {str(e)}")

    async def update_role(self, role_id: int, name: Optional[str] = None,
                         description: Optional[str] = None,
                         permissions: Optional[List[str]] = None) -> Role:
        """Update an existing role."""
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise SecurityError("Role not found")

            # Update fields if provided
            if name:
                role.name = name
            if description:
                role.description = description
            if permissions:
                # Get permission objects
                permission_objects = []
                for perm_name in permissions:
                    perm = self.db.query(Permission).filter(Permission.name == perm_name).first()
                    if not perm:
                        raise SecurityError(f"Permission not found: {perm_name}")
                    permission_objects.append(perm)
                role.permissions = permission_objects

            self.db.commit()
            self.db.refresh(role)

            return role

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to update role: {str(e)}")

    async def delete_role(self, role_id: int) -> bool:
        """Delete a role."""
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise SecurityError("Role not found")

            # Check if role is assigned to any users
            users_with_role = self.db.query(User).filter(User.role_id == role_id).count()
            if users_with_role > 0:
                raise SecurityError("Cannot delete role that is assigned to users")

            self.db.delete(role)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to delete role: {str(e)}")

    async def create_permission(self, name: str, description: str) -> Permission:
        """Create a new permission."""
        try:
            # Check if permission already exists
            existing_perm = self.db.query(Permission).filter(Permission.name == name).first()
            if existing_perm:
                raise SecurityError("Permission already exists")

            # Create new permission
            permission = Permission(
                name=name,
                description=description
            )
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)

            return permission

        except Exception as e:
            self.db.rollback()
            raise SecurityError(f"Failed to create permission: {str(e)}")

    async def get_role_permissions(self, role_id: int) -> List[str]:
        """Get all permissions for a role."""
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise SecurityError("Role not found")

            return [p.name for p in role.permissions]

        except Exception as e:
            raise SecurityError(f"Failed to get role permissions: {str(e)}") 