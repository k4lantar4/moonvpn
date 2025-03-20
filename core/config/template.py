"""
Template endpoints for system health monitoring.

This module provides API endpoints for managing recovery action templates
and template categories.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.services.template import TemplateService
from app.core.schemas.template import (
    TemplateCategory,
    TemplateCategoryCreate,
    TemplateCategoryUpdate,
    RecoveryTemplate,
    RecoveryTemplateCreate,
    RecoveryTemplateUpdate
)

router = APIRouter()

@router.post("/categories/", response_model=TemplateCategory, tags=["templates"])
async def create_category(
    category: TemplateCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new template category.
    
    Args:
        category: Category creation data
        db: Database session
        
    Returns:
        TemplateCategory: Created category
    """
    template_service = TemplateService(db)
    try:
        return template_service.create_category(category)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/categories/", response_model=List[TemplateCategory], tags=["templates"])
async def get_categories(db: Session = Depends(get_db)):
    """Get all template categories.
    
    Args:
        db: Database session
        
    Returns:
        List[TemplateCategory]: List of categories
    """
    template_service = TemplateService(db)
    return template_service.get_categories()

@router.get("/categories/{category_id}", response_model=TemplateCategory, tags=["templates"])
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get a template category by ID.
    
    Args:
        category_id: ID of the category
        db: Database session
        
    Returns:
        TemplateCategory: Category if found
        
    Raises:
        HTTPException: If category not found
    """
    template_service = TemplateService(db)
    category = template_service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=TemplateCategory, tags=["templates"])
async def update_category(
    category_id: int,
    category: TemplateCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a template category.
    
    Args:
        category_id: ID of the category
        category: Category update data
        db: Database session
        
    Returns:
        TemplateCategory: Updated category
        
    Raises:
        HTTPException: If category not found or update fails
    """
    template_service = TemplateService(db)
    updated_category = template_service.update_category(category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category

@router.delete("/categories/{category_id}", tags=["templates"])
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Delete a template category.
    
    Args:
        category_id: ID of the category
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If category not found or deletion fails
    """
    template_service = TemplateService(db)
    if not template_service.delete_category(category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

@router.post("/templates/", response_model=RecoveryTemplate, tags=["templates"])
async def create_template(
    template: RecoveryTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new recovery template.
    
    Args:
        template: Template creation data
        db: Database session
        
    Returns:
        RecoveryTemplate: Created template
    """
    template_service = TemplateService(db)
    try:
        return template_service.create_template(template)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/templates/", response_model=List[RecoveryTemplate], tags=["templates"])
async def get_templates(
    category_id: Optional[int] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get recovery templates with optional filtering.
    
    Args:
        category_id: Optional category ID filter
        active_only: Whether to return only active templates
        db: Database session
        
    Returns:
        List[RecoveryTemplate]: List of templates
    """
    template_service = TemplateService(db)
    return template_service.get_templates(category_id, active_only)

@router.get("/templates/{template_id}", response_model=RecoveryTemplate, tags=["templates"])
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get a recovery template by ID.
    
    Args:
        template_id: ID of the template
        db: Database session
        
    Returns:
        RecoveryTemplate: Template if found
        
    Raises:
        HTTPException: If template not found
    """
    template_service = TemplateService(db)
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/templates/{template_id}", response_model=RecoveryTemplate, tags=["templates"])
async def update_template(
    template_id: int,
    template: RecoveryTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a recovery template.
    
    Args:
        template_id: ID of the template
        template: Template update data
        db: Database session
        
    Returns:
        RecoveryTemplate: Updated template
        
    Raises:
        HTTPException: If template not found or update fails
    """
    template_service = TemplateService(db)
    updated_template = template_service.update_template(template_id, template)
    if not updated_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated_template

@router.delete("/templates/{template_id}", tags=["templates"])
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Delete a recovery template.
    
    Args:
        template_id: ID of the template
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If template not found or deletion fails
    """
    template_service = TemplateService(db)
    if not template_service.delete_template(template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"} 