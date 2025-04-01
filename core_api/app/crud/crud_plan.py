# Import necessary components for CRUD operations
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union, List

# Import models and schemas
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate
from app.crud.base import CRUDBase

class CRUDPlan(CRUDBase[Plan, PlanCreate, PlanUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Plan]:
        """ Retrieves a single plan by its unique name. """
        return db.query(self.model).filter(self.model.name == name).first()

    # Override get_multi if filtering by active status is common
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False # Add custom filter parameter
    ) -> List[Plan]:
        query = db.query(self.model)
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.offset(skip).limit(limit).all()

    # Add any other plan-specific methods here

# Create a singleton instance
plan = CRUDPlan(Plan)

# --- Deprecated Individual Functions --- 
# def get_plan(...)
# def get_plan_by_name(...)
# def get_plans(...)
# def create_plan(...)
# def update_plan(...)
# def remove_plan(...) 