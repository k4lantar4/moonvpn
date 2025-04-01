from typing import List, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app import models
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Permission])
def read_permissions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    # Require authentication, even if just listing predefined permissions
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Retrieve all available permissions.
    (Requires authenticated superuser - adjust if needed)
    """
    permissions = crud.permission.get_multi(db, skip=skip, limit=limit)
    return permissions

# Note: We assume permissions are predefined and don't need POST/PUT/DELETE endpoints.
# If dynamic permission creation is needed, add those endpoints here. 