"""
Template test API endpoints for system health monitoring.

This module provides the API endpoints for template testing functionality.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core.schemas.template_test import TemplateTestCreate, TemplateTestResult
from app.core.services.template_test import TemplateTestService

router = APIRouter()

@router.post("/templates/{template_id}/test", response_model=TemplateTestResult)
def run_template_test(
    template_id: int,
    test_data: TemplateTestCreate,
    db: Session = Depends(deps.get_db)
) -> TemplateTestResult:
    """Run a test for a recovery template.
    
    Args:
        template_id: ID of the template to test
        test_data: Test configuration data
        db: Database session
        
    Returns:
        TemplateTestResult: Test result
        
    Raises:
        HTTPException: If template not found or test fails
    """
    service = TemplateTestService(db)
    result = service.run_test(template_id, test_data.parameters)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Template with ID {template_id} not found"
        )
    
    return result

@router.get("/templates/{template_id}/test-results", response_model=List[TemplateTestResult])
def get_template_test_results(
    template_id: int,
    limit: int = 10,
    db: Session = Depends(deps.get_db)
) -> List[TemplateTestResult]:
    """Get test results for a template.
    
    Args:
        template_id: ID of the template
        limit: Maximum number of results to return
        db: Database session
        
    Returns:
        List[TemplateTestResult]: List of test results
    """
    service = TemplateTestService(db)
    return service.get_test_results(template_id, limit) 