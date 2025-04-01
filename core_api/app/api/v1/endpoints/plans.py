# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Any, Optional
from sqlalchemy.orm import Session

# Import CRUD functions, schemas, models, and dependencies
from app import crud
from app import schemas
from app import models
from app.api import deps # Dependency injection for DB session

# Create a new FastAPI router for plan endpoints
router = APIRouter()

# --- Plan API Endpoints ---

@router.post("/", response_model=schemas.Plan, status_code=status.HTTP_201_CREATED)
def create_plan(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Superuser auth
) -> Any:
    """
    Create a new subscription plan.
    Requires appropriate permissions (e.g., superuser).
    Handles potential duplicate plan names.
    """
    # Check if a plan with the same name already exists
    existing_plan = crud.plan.get_plan_by_name(db, name=plan_in.name)
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A plan with the name '{plan_in.name}' already exists.",
        )
    # Create the plan using the CRUD function
    plan = crud.plan.create_plan(db=db, obj_in=plan_in)
    return plan

@router.get("/", response_model=List[schemas.Plan])
def read_plans(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active plans"),
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Any logged-in user
) -> Any:
    """
    Retrieve a list of subscription plans.
    Includes pagination (skip, limit).
    Allows filtering by active status.
    """
    # Use the only_active flag directly if provided, otherwise default behavior of crud function
    plans = crud.plan.get_plans(db, skip=skip, limit=limit, only_active=only_active or False)
    return plans

@router.get("/{plan_id}", response_model=schemas.Plan)
def read_plan(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int, # Path parameter for the plan ID
    # current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve a specific plan by its ID.
    Handles the case where the plan is not found.
    """
    plan = crud.plan.get_plan(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan

@router.put("/{plan_id}", response_model=schemas.Plan)
def update_plan(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int, # Path parameter
    plan_in: schemas.PlanUpdate, # Request body with update data
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Superuser auth
) -> Any:
    """
    Update an existing plan.
    Requires appropriate permissions.
    Handles not found errors and potential duplicate names if name is updated.
    """
    plan = crud.plan.get_plan(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Check for duplicate name if the name is being changed
    if plan_in.name is not None and plan_in.name != plan.name:
        existing_plan = crud.plan.get_plan_by_name(db, name=plan_in.name)
        if existing_plan and existing_plan.id != plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A plan with the name '{plan_in.name}' already exists.",
            )

    # Perform the update using the CRUD function
    updated_plan = crud.plan.update_plan(db=db, db_obj=plan, obj_in=plan_in)
    return updated_plan

@router.delete("/{plan_id}", response_model=schemas.Plan)
def delete_plan(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Superuser auth
) -> Any:
    """
    Delete a plan by ID.
    Requires appropriate permissions.
    Handles not found errors.
    Returns the deleted plan data as confirmation.
    """
    plan = crud.plan.get_plan(db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    # Perform the deletion using the CRUD function
    deleted_plan = crud.plan.remove_plan(db=db, plan_id=plan_id)
    # remove_plan returns the deleted object
    return deleted_plan 