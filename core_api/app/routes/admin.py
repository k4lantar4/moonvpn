from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import json

from app.api import deps
from app.models import User
from app.services.plan_service import plan_service
from app.services.panel_service import panel_service
from app.services.server_service import server_service

# Main router for authenticated routes
router = APIRouter()
# Public router for routes that don't require authentication
public_router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@public_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login page.
    """
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )

@router.get("/plans", response_class=HTMLResponse)
async def plans_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None
):
    """
    Render the plans management page.
    """
    # Calculate skip for pagination
    skip = (page - 1) * limit
    
    # Prepare filter parameters
    filter_params = {
        "search": search,
        "category_id": category_id,
        "is_active": is_active
    }
    
    # Get plans with usage statistics
    plans = plan_service.get_plans_with_usage(db, skip=skip, limit=limit, filter_params=filter_params)
    
    # Get plan categories for the dropdown
    categories = plan_service.get_plan_categories(db)
    
    # Determine if there are more pages
    has_more = len(plans) == limit
    
    return templates.TemplateResponse(
        "admin/plans.html",
        {
            "request": request,
            "plans": plans,
            "categories": categories,
            "current_page": page,
            "has_more": has_more,
            "search": search or "",
            "category_id": category_id,
            "is_active": is_active
        }
    )

@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def plan_detail_page(
    request: Request,
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the plan detail page.
    """
    # Get the plan with usage statistics
    plan = plan_service.get_plan_with_usage(db, plan_id=plan_id)
    
    # Get categories for the dropdown
    categories = plan_service.get_plan_categories(db)
    
    return templates.TemplateResponse(
        "admin/plan_detail.html",
        {
            "request": request,
            "plan": plan,
            "categories": categories
        }
    )

@router.get("/plan/new", response_class=HTMLResponse)
async def new_plan_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the new plan creation page.
    """
    # Get categories for the dropdown
    categories = plan_service.get_plan_categories(db)
    
    return templates.TemplateResponse(
        "admin/plan_create.html",
        {
            "request": request,
            "categories": categories
        }
    )

@router.get("/plan-categories", response_class=HTMLResponse)
async def plan_categories_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the plan categories management page.
    """
    # Get all categories
    categories = plan_service.get_plan_categories(db)
    
    return templates.TemplateResponse(
        "admin/plan_categories.html",
        {
            "request": request,
            "categories": categories
        }
    )

@router.get("/panels", response_class=HTMLResponse)
async def panels_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the panel management page.
    """
    return templates.TemplateResponse(
        "admin/panels.html",
        {
            "request": request
        }
    )

@router.get("/servers", response_class=HTMLResponse)
async def servers_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the server management page.
    """
    return templates.TemplateResponse(
        "admin/servers.html",
        {
            "request": request
        }
    )

@router.get("/financial-reports", response_class=HTMLResponse)
async def financial_reports_page(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Render the financial reports page.
    """
    return templates.TemplateResponse(
        "admin/financial_reports/index.html",
        {
            "request": request
        }
    ) 