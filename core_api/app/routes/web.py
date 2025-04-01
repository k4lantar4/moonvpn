from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })

# Admin dashboard routes
@router.get("/admin/bank-cards", response_class=HTMLResponse)
async def admin_bank_cards(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("admin/bank_cards.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/payment-admins", response_class=HTMLResponse)
async def admin_payment_admins(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("admin/payment_admin.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/payment-verification", response_class=HTMLResponse)
async def admin_payment_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("admin/payment_verification.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/performance-reports", response_class=HTMLResponse)
async def admin_performance_reports(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("admin/admin_performance.html", {
        "request": request,
        "user": current_user
    }) 