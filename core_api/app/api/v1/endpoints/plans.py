# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Any, Optional, Dict
from sqlalchemy.orm import Session
from decimal import Decimal

# Import CRUD functions, schemas, models, services, and dependencies
from app import crud, schemas, models
from app.api import deps  # Dependency injection for DB session
from app.services.plan_service import plan_service

# Create a new FastAPI router for plan endpoints
router = APIRouter()

# --- Plan API Endpoints ---

@router.post("/", response_model=schemas.Plan, status_code=status.HTTP_201_CREATED)
def create_plan(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create a new subscription plan.
    Requires superuser privileges.
    """
    # Use the plan service to create the plan
    plan = plan_service.create_plan(db=db, plan_in=plan_in)
    return plan


@router.get("/", response_model=List[Dict[str, Any]])
def read_plans(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price"),
    min_duration: Optional[int] = Query(None, description="Minimum duration in days"),
    max_duration: Optional[int] = Query(None, description="Maximum duration in days"),
    sort_by: Optional[str] = Query("sort_order", description="Field to sort by"),
    sort_desc: bool = Query(False, description="Sort in descending order"),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve plans with advanced filtering and usage statistics.
    """
    # Construct filter parameters
    filter_params = {
        "is_active": is_active,
        "is_featured": is_featured,
        "category_id": category_id,
        "search": search,
        "min_price": min_price,
        "max_price": max_price,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "sort_by": sort_by,
        "sort_desc": sort_desc
    }
    
    # Use the plan service to get plans with usage stats
    plans = plan_service.get_plans_with_usage(db, skip=skip, limit=limit, filter_params=filter_params)
    return plans


@router.get("/{plan_id}", response_model=Dict[str, Any])
def read_plan(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int = Path(..., gt=0, description="The ID of the plan to retrieve"),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve details for a specific plan, including usage statistics.
    """
    # Use the plan service to get the plan with usage stats
    plan = plan_service.get_plan_with_usage(db, plan_id=plan_id)
    return plan


@router.put("/{plan_id}", response_model=schemas.Plan)
def update_plan(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int = Path(..., gt=0, description="The ID of the plan to update"),
    plan_in: schemas.PlanUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Update an existing plan.
    Requires superuser privileges.
    """
    # Use the plan service to update the plan
    updated_plan = plan_service.update_plan(db=db, plan_id=plan_id, plan_in=plan_in)
    return updated_plan


@router.delete("/{plan_id}", response_model=schemas.Plan)
def delete_plan(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int = Path(..., gt=0, description="The ID of the plan to delete"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Delete a plan.
    Requires superuser privileges.
    """
    # Get the plan to check if it exists
    plan = crud.plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
    # Check if the plan has any subscriptions
    if plan.subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete plan '{plan.name}' because it has active subscriptions. Deactivate the plan instead."
        )
        
    # Delete the plan
    return crud.plan.remove(db=db, id=plan_id)


@router.patch("/{plan_id}/toggle", response_model=schemas.Plan)
def toggle_plan_status(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    plan_id: int = Path(..., gt=0, description="The ID of the plan to toggle"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Toggle the active status of a plan.
    Requires superuser privileges.
    """
    # Use the plan service to toggle the plan status
    plan = plan_service.toggle_plan_status(db=db, plan_id=plan_id)
    return plan


# --- Plan Categories API Endpoints ---

@router.get("/categories/", response_model=List[schemas.PlanCategory])
def read_plan_categories(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: bool = Query(False, description="Filter to return only active categories"),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve a list of plan categories.
    """
    # Use the plan service to get categories
    categories = plan_service.get_plan_categories(db, skip=skip, limit=limit, only_active=only_active)
    return categories


@router.post("/categories/", response_model=schemas.PlanCategory, status_code=status.HTTP_201_CREATED)
def create_plan_category(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    category_in: schemas.PlanCategoryCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Create a new plan category.
    Requires superuser privileges.
    """
    # Use the plan service to create a category
    category = plan_service.create_plan_category(
        db=db,
        name=category_in.name,
        description=category_in.description,
        is_active=category_in.is_active,
        sort_order=category_in.sort_order
    )
    return category


@router.put("/categories/{category_id}", response_model=schemas.PlanCategory)
def update_plan_category(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    category_in: schemas.PlanCategoryUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Update an existing plan category.
    Requires superuser privileges.
    """
    # Use the plan service to update a category
    category = plan_service.update_plan_category(
        db=db,
        category_id=category_id,
        name=category_in.name,
        description=category_in.description,
        is_active=category_in.is_active,
        sort_order=category_in.sort_order
    )
    return category


@router.delete("/categories/{category_id}", response_model=schemas.PlanCategory)
def delete_plan_category(
    *,  # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    category_id: int = Path(..., gt=0, description="The ID of the category to delete"),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Delete a plan category.
    Requires superuser privileges.
    Will fail if the category has associated plans.
    """
    # Use the plan service to delete a category
    category = plan_service.delete_plan_category(db=db, category_id=category_id)
    return category 