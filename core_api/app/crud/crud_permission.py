from typing import List

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase # Assuming you have a base CRUD class
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate # Although we might not use Create/Update

class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    # Permissions are likely predefined and not created/updated/deleted via API
    # So we primarily need a way to list them.
    pass # Inherits get, get_multi from CRUDBase

# Instantiate the CRUD object for Permission
permission = CRUDPermission(Permission) 