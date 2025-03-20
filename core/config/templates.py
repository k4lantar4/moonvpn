from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.validation_rule import ValidationRule, ValidationRuleCreate, ValidationRuleUpdate
from app.utils.template_validator import TemplateValidator
from app.database.session import get_db
from app.crud.template import TemplateCrud

router = APIRouter()

@router.get("/{template_id}/validation-rules", response_model=List[ValidationRule])
async def get_template_validation_rules(
    template_id: int,
    db: Session = Depends(get_db)
):
    """Get all validation rules for a template."""
    template = TemplateCrud.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.validation_rules

@router.post("/{template_id}/validation-rules", response_model=ValidationRule)
async def create_template_validation_rule(
    template_id: int,
    rule: ValidationRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new validation rule for a template."""
    template = TemplateCrud.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_rule = ValidationRule(**rule.dict())
    template.validation_rules.append(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.put("/{template_id}/validation-rules/{rule_id}", response_model=ValidationRule)
async def update_template_validation_rule(
    template_id: int,
    rule_id: int,
    rule: ValidationRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update a validation rule for a template."""
    template = TemplateCrud.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_rule = next((r for r in template.validation_rules if r.id == rule_id), None)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Validation rule not found")
    
    for field, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.delete("/{template_id}/validation-rules/{rule_id}")
async def delete_template_validation_rule(
    template_id: int,
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Delete a validation rule from a template."""
    template = TemplateCrud.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db_rule = next((r for r in template.validation_rules if r.id == rule_id), None)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Validation rule not found")
    
    db.delete(db_rule)
    db.commit()
    return {"message": "Validation rule deleted successfully"}

@router.post("/{template_id}/validate", response_model=Dict[str, Any])
async def validate_template_data(
    template_id: int,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Validate template data against validation rules."""
    template = TemplateCrud.get(db, id=template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    errors = TemplateValidator.validate_template(data, template.validation_rules)
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    } 