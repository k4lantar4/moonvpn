"""
Template service for system health monitoring.

This module provides functionality for managing recovery action templates
and template categories.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.models.template import TemplateCategory, RecoveryTemplate
from app.core.models.recovery import RecoveryStrategy
from app.core.schemas.template import (
    TemplateCategoryCreate,
    TemplateCategoryUpdate,
    RecoveryTemplateCreate,
    RecoveryTemplateUpdate
)
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

class TemplateService:
    """Service for managing recovery action templates."""

    def __init__(self, db: Session):
        """Initialize the template service.
        
        Args:
            db: Database session for persistence operations
        """
        self.db = db

    def create_category(
        self,
        category: TemplateCategoryCreate
    ) -> TemplateCategory:
        """Create a new template category.
        
        Args:
            category: Category creation data
            
        Returns:
            TemplateCategory: Created category
        """
        try:
            db_category = TemplateCategory(**category.dict())
            self.db.add(db_category)
            self.db.commit()
            self.db.refresh(db_category)
            logger.info(f"Created template category: {db_category.name}")
            return db_category
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating template category: {str(e)}")
            raise

    def get_category(self, category_id: int) -> Optional[TemplateCategory]:
        """Get a template category by ID.
        
        Args:
            category_id: ID of the category
            
        Returns:
            Optional[TemplateCategory]: Category if found
        """
        return self.db.query(TemplateCategory).filter(
            TemplateCategory.id == category_id
        ).first()

    def get_categories(self) -> List[TemplateCategory]:
        """Get all template categories.
        
        Returns:
            List[TemplateCategory]: List of categories
        """
        return self.db.query(TemplateCategory).all()

    def update_category(
        self,
        category_id: int,
        category: TemplateCategoryUpdate
    ) -> Optional[TemplateCategory]:
        """Update a template category.
        
        Args:
            category_id: ID of the category
            category: Category update data
            
        Returns:
            Optional[TemplateCategory]: Updated category if found
        """
        try:
            db_category = self.get_category(category_id)
            if not db_category:
                return None

            update_data = category.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_category, field, value)

            self.db.commit()
            self.db.refresh(db_category)
            logger.info(f"Updated template category: {db_category.name}")
            return db_category
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating template category: {str(e)}")
            raise

    def delete_category(self, category_id: int) -> bool:
        """Delete a template category.
        
        Args:
            category_id: ID of the category
            
        Returns:
            bool: True if category was deleted
        """
        try:
            db_category = self.get_category(category_id)
            if not db_category:
                return False

            self.db.delete(db_category)
            self.db.commit()
            logger.info(f"Deleted template category: {db_category.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting template category: {str(e)}")
            raise

    def create_template(
        self,
        template: RecoveryTemplateCreate
    ) -> RecoveryTemplate:
        """Create a new recovery template.
        
        Args:
            template: Template creation data
            
        Returns:
            RecoveryTemplate: Created template
        """
        try:
            template_data = template.dict()
            template_data["strategy"] = RecoveryStrategy(template_data["strategy"])
            db_template = RecoveryTemplate(**template_data)
            self.db.add(db_template)
            self.db.commit()
            self.db.refresh(db_template)
            logger.info(f"Created recovery template: {db_template.name}")
            return db_template
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating recovery template: {str(e)}")
            raise

    def get_template(self, template_id: int) -> Optional[RecoveryTemplate]:
        """Get a recovery template by ID.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Optional[RecoveryTemplate]: Template if found
        """
        return self.db.query(RecoveryTemplate).filter(
            RecoveryTemplate.id == template_id
        ).first()

    def get_templates(
        self,
        category_id: Optional[int] = None,
        active_only: bool = False
    ) -> List[RecoveryTemplate]:
        """Get recovery templates with optional filtering.
        
        Args:
            category_id: Optional category ID filter
            active_only: Whether to return only active templates
            
        Returns:
            List[RecoveryTemplate]: List of templates
        """
        query = self.db.query(RecoveryTemplate)
        
        if category_id:
            query = query.filter(RecoveryTemplate.category_id == category_id)
        if active_only:
            query = query.filter(RecoveryTemplate.is_active == True)
            
        return query.all()

    def update_template(
        self,
        template_id: int,
        template: RecoveryTemplateUpdate
    ) -> Optional[RecoveryTemplate]:
        """Update a recovery template.
        
        Args:
            template_id: ID of the template
            template: Template update data
            
        Returns:
            Optional[RecoveryTemplate]: Updated template if found
        """
        try:
            db_template = self.get_template(template_id)
            if not db_template:
                return None

            update_data = template.dict(exclude_unset=True)
            if "strategy" in update_data:
                update_data["strategy"] = RecoveryStrategy(update_data["strategy"])
                
            for field, value in update_data.items():
                setattr(db_template, field, value)

            self.db.commit()
            self.db.refresh(db_template)
            logger.info(f"Updated recovery template: {db_template.name}")
            return db_template
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating recovery template: {str(e)}")
            raise

    def delete_template(self, template_id: int) -> bool:
        """Delete a recovery template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            bool: True if template was deleted
        """
        try:
            db_template = self.get_template(template_id)
            if not db_template:
                return False

            self.db.delete(db_template)
            self.db.commit()
            logger.info(f"Deleted recovery template: {db_template.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting recovery template: {str(e)}")
            raise

    def create_recovery_action_from_template(
        self,
        template_id: int,
        component: str,
        failure_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a recovery action from a template.
        
        Args:
            template_id: ID of the template
            component: Component to recover
            failure_type: Type of failure
            parameters: Optional override parameters
            
        Returns:
            Optional[Dict[str, Any]]: Created action data if successful
        """
        try:
            template = self.get_template(template_id)
            if not template or not template.is_active:
                return None

            # Use template parameters or override with provided ones
            action_params = parameters if parameters is not None else template.parameters

            return {
                "component": component,
                "failure_type": failure_type,
                "strategy": template.strategy,
                "parameters": action_params
            }
        except Exception as e:
            logger.error(f"Error creating action from template: {str(e)}")
            return None 