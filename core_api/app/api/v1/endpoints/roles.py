# core_api/app/api/v1/endpoints/roles.py
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app import models
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Role, status_code=status.HTTP_201_CREATED)
def create_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_in: schemas.RoleCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Create a new role (Superuser only)."""
    existing_role = crud.role.get_role_by_name(db, name=role_in.name)
    if existing_role:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    role = crud.role.create(db=db, obj_in=role_in) # Use base create method
    return role

@router.get("/", response_model=List[schemas.Role])
def read_roles(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Retrieve all roles (Superuser only)."""
    roles = crud.role.get_multi(db, skip=skip, limit=limit) # Use base get_multi
    return roles

@router.get("/{role_id}", response_model=schemas.Role)
def read_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Get a specific role by ID (Superuser only)."""
    role = crud.role.get(db=db, id=role_id) # Use base get method
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put("/{role_id}", response_model=schemas.Role)
def update_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_id: int,
    role_in: schemas.RoleUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Update a role (Superuser only)."""
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # Check for name conflict if name is being changed
    if role_in.name and role_in.name != role.name:
        existing_role = crud.role.get_role_by_name(db, name=role_in.name)
        if existing_role and existing_role.id != role_id:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
    role = crud.role.update(db=db, db_obj=role, obj_in=role_in) # Use base update
    return role

@router.delete("/{role_id}", response_model=schemas.Role)
def delete_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Delete a role (Superuser only)."""
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # TODO: Add logic to handle users assigned to this role before deletion?
    # Maybe prevent deletion if users are assigned, or reassign them?
    role = crud.role.remove(db=db, id=role_id) # Use base remove
    return role

# --- Role Permissions Management --- #

@router.post("/{role_id}/permissions/{permission_id}", response_model=schemas.Role)
def add_permission_to_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_id: int,
    permission_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Add a permission to a specific role (Superuser only)."""
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    role = crud.role.add_permission_to_role(db=db, role=role, permission=permission)
    return role

@router.delete("/{role_id}/permissions/{permission_id}", response_model=schemas.Role)
def remove_permission_from_role(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    role_id: int,
    permission_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """Remove a permission from a specific role (Superuser only)."""
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    role = crud.role.remove_permission_from_role(db=db, role=role, permission=permission)
    return role 