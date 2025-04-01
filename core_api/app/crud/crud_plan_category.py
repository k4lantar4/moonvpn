from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.plan_category import PlanCategory
from app.schemas.plan_category import PlanCategoryCreate, PlanCategoryUpdate # Schemas need to be created
from app.crud.base import CRUDBase

class CRUDPlanCategory(CRUDBase[PlanCategory, PlanCategoryCreate, PlanCategoryUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[PlanCategory]:
        """ Retrieves a plan category by its unique name. """
        return db.query(self.model).filter(self.model.name == name).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False
    ) -> List[PlanCategory]:
        query = db.query(self.model)
        if only_active:
            query = query.filter(self.model.is_active == True)
        # Consider adding sorting by sort_order
        # query = query.order_by(self.model.sort_order)
        return query.offset(skip).limit(limit).all()

    # Add other category-specific methods if needed

# Create a singleton instance
plan_category = CRUDPlanCategory(PlanCategory) 