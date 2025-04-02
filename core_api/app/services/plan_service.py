from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.plan_category import PlanCategory
from app.schemas.plan import PlanCreate, PlanUpdate, Plan as PlanSchema
from app.crud.crud_plan import plan as plan_crud
from app.crud.crud_plan_category import plan_category as plan_category_crud


class PlanService:
    """
    Service for managing plans with business logic beyond basic CRUD operations.
    """

    @staticmethod
    def create_plan(
        db: Session, 
        plan_in: PlanCreate
    ) -> Plan:
        """
        Create a new plan with validation.
        """
        # Check if a plan with the same name already exists
        existing_plan = plan_crud.get_by_name(db, name=plan_in.name)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A plan with the name '{plan_in.name}' already exists."
            )
        
        # Validate category if provided
        if plan_in.category_id:
            category = plan_category_crud.get(db, id=plan_in.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {plan_in.category_id} does not exist."
                )
        
        # Create the plan
        return plan_crud.create(db=db, obj_in=plan_in)

    @staticmethod
    def update_plan(
        db: Session, 
        plan_id: int, 
        plan_in: PlanUpdate
    ) -> Plan:
        """
        Update an existing plan with validation.
        """
        # Get the existing plan
        plan = plan_crud.get(db, id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Check for name uniqueness if name is being updated
        if plan_in.name and plan_in.name != plan.name:
            existing_plan = plan_crud.get_by_name(db, name=plan_in.name)
            if existing_plan and existing_plan.id != plan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A plan with the name '{plan_in.name}' already exists."
                )
        
        # Validate category if provided
        if plan_in.category_id:
            category = plan_category_crud.get(db, id=plan_in.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {plan_in.category_id} does not exist."
                )
        
        # Update the plan
        return plan_crud.update(db=db, db_obj=plan, obj_in=plan_in)

    @staticmethod
    def get_plans_with_usage(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get plans with usage statistics and apply advanced filtering.
        """
        # Start with the base query
        query = db.query(Plan)
        
        # Apply filters if provided
        if filter_params:
            if filter_params.get("is_active") is not None:
                query = query.filter(Plan.is_active == filter_params["is_active"])
            
            if filter_params.get("is_featured") is not None:
                query = query.filter(Plan.is_featured == filter_params["is_featured"])
            
            if filter_params.get("category_id"):
                query = query.filter(Plan.category_id == filter_params["category_id"])
            
            if filter_params.get("search"):
                search_term = f"%{filter_params['search']}%"
                query = query.filter(
                    or_(
                        Plan.name.ilike(search_term),
                        Plan.description.ilike(search_term)
                    )
                )
            
            # Advanced filtering options
            if filter_params.get("min_price"):
                query = query.filter(Plan.price >= filter_params["min_price"])
                
            if filter_params.get("max_price"):
                query = query.filter(Plan.price <= filter_params["max_price"])
                
            if filter_params.get("min_duration"):
                query = query.filter(Plan.duration_days >= filter_params["min_duration"])
                
            if filter_params.get("max_duration"):
                query = query.filter(Plan.duration_days <= filter_params["max_duration"])
        
        # Apply sorting
        sort_by = "sort_order"
        if filter_params and filter_params.get("sort_by"):
            # Ensure the requested sort field exists in the model
            if hasattr(Plan, filter_params["sort_by"]):
                sort_by = filter_params["sort_by"]
        
        sort_order = getattr(Plan, sort_by)
        if filter_params and filter_params.get("sort_desc"):
            sort_order = sort_order.desc()
        else:
            sort_order = sort_order.asc()
            
        query = query.order_by(sort_order)
        
        # Execute query with pagination
        plans = query.offset(skip).limit(limit).all()
        
        # Enhance plans with usage statistics
        result = []
        for plan in plans:
            # Count active subscriptions for this plan
            active_subscriptions_count = db.query(func.count(Subscription.id))\
                .filter(Subscription.plan_id == plan.id)\
                .filter(Subscription.is_active == True)\
                .scalar() or 0
            
            # Check if max_users limit is reached
            is_full = False
            if plan.max_users is not None:
                is_full = active_subscriptions_count >= plan.max_users
            
            # Get category name if category exists
            category_name = None
            if plan.category_id:
                category = db.query(PlanCategory).filter(PlanCategory.id == plan.category_id).first()
                if category:
                    category_name = category.name
            
            # Create enhanced plan dict
            plan_dict = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "price": plan.price,
                "seller_price": plan.seller_price,
                "duration_days": plan.duration_days,
                "traffic_limit_gb": plan.traffic_limit_gb,
                "max_users": plan.max_users,
                "is_active": plan.is_active,
                "is_featured": plan.is_featured,
                "sort_order": plan.sort_order,
                "category_id": plan.category_id,
                "category_name": category_name,
                "active_subscriptions": active_subscriptions_count,
                "is_full": is_full,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at
            }
            result.append(plan_dict)
        
        return result

    @staticmethod
    def get_plan_with_usage(
        db: Session, 
        plan_id: int
    ) -> Dict[str, Any]:
        """
        Get a single plan with usage statistics.
        """
        # Get the plan
        plan = plan_crud.get(db, id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Count active subscriptions for this plan
        active_subscriptions_count = db.query(func.count(Subscription.id))\
            .filter(Subscription.plan_id == plan.id)\
            .filter(Subscription.is_active == True)\
            .scalar() or 0
        
        # Check if max_users limit is reached
        is_full = False
        if plan.max_users is not None:
            is_full = active_subscriptions_count >= plan.max_users
        
        # Get category name if category exists
        category_name = None
        if plan.category_id:
            category = db.query(PlanCategory).filter(PlanCategory.id == plan.category_id).first()
            if category:
                category_name = category.name
        
        # Create enhanced plan dict
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "price": plan.price,
            "seller_price": plan.seller_price,
            "duration_days": plan.duration_days,
            "traffic_limit_gb": plan.traffic_limit_gb,
            "max_users": plan.max_users,
            "is_active": plan.is_active,
            "is_featured": plan.is_featured,
            "sort_order": plan.sort_order,
            "category_id": plan.category_id,
            "category_name": category_name,
            "active_subscriptions": active_subscriptions_count,
            "is_full": is_full,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at
        }
        
        return plan_dict

    @staticmethod
    def toggle_plan_status(
        db: Session, 
        plan_id: int
    ) -> Plan:
        """
        Toggle the active status of a plan.
        """
        # Get the plan
        plan = plan_crud.get(db, id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Toggle the status
        update_data = {"is_active": not plan.is_active}
        return plan_crud.update(db=db, db_obj=plan, obj_in=update_data)

    @staticmethod
    def get_plan_categories(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        only_active: bool = False
    ) -> List[PlanCategory]:
        """
        Get plan categories with optional filtering.
        """
        query = db.query(PlanCategory)
        
        if only_active:
            query = query.filter(PlanCategory.is_active == True)
            
        query = query.order_by(PlanCategory.sort_order.asc())
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_plan_category(
        db: Session, 
        name: str, 
        description: Optional[str] = None,
        is_active: bool = True,
        sort_order: int = 100
    ) -> PlanCategory:
        """
        Create a new plan category.
        """
        # Check if category with same name exists
        existing_category = db.query(PlanCategory).filter(PlanCategory.name == name).first()
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A category with the name '{name}' already exists."
            )
        
        # Create category
        new_category = PlanCategory(
            name=name,
            description=description,
            is_active=is_active,
            sort_order=sort_order
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        return new_category
    
    @staticmethod
    def update_plan_category(
        db: Session, 
        category_id: int, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_order: Optional[int] = None
    ) -> PlanCategory:
        """
        Update an existing plan category.
        """
        # Get the category
        category = db.query(PlanCategory).filter(PlanCategory.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check for name uniqueness if name is provided
        if name and name != category.name:
            existing_category = db.query(PlanCategory).filter(PlanCategory.name == name).first()
            if existing_category and existing_category.id != category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A category with the name '{name}' already exists."
                )
            category.name = name
            
        # Update other fields if provided
        if description is not None:
            category.description = description
            
        if is_active is not None:
            category.is_active = is_active
            
        if sort_order is not None:
            category.sort_order = sort_order
            
        db.commit()
        db.refresh(category)
        
        return category
    
    @staticmethod
    def delete_plan_category(
        db: Session, 
        category_id: int
    ) -> PlanCategory:
        """
        Delete a plan category if it has no associated plans.
        """
        # Get the category
        category = db.query(PlanCategory).filter(PlanCategory.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if there are plans associated with this category
        plans_count = db.query(func.count(Plan.id))\
            .filter(Plan.category_id == category_id)\
            .scalar() or 0
            
        if plans_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category '{category.name}' because it has {plans_count} associated plans. Reassign or delete the plans first."
            )
        
        # Delete the category
        db.delete(category)
        db.commit()
        
        return category


# Create a singleton instance of the service
plan_service = PlanService() 