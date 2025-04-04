from fastapi import FastAPI, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
import os
import uvicorn
import logging

# Import routers
from app.api.v1 import api_router
from app.api.v1.endpoints import users, plans, panel, subscriptions
from app.routes import admin as admin_routes
from app.core.config import settings
from app.services.wallet_service import WalletException, InsufficientFundsException, InvalidAmountException
from app.api.deps import get_current_active_user, get_current_active_superuser, get_current_user_optional
from sqlalchemy.orm import Session
from app.api import deps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Print the database URI at startup for debugging
print(f"---> Database URI: {settings.SQLALCHEMY_DATABASE_URI}")

# --- App Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for MoonVPN Telegram Bot and Dashboard",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- Static Files Mounting ---
# Construct the path relative to the current file (main.py)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.isdir(static_dir):
    # Fallback if running from project root (e.g., tests)
    static_dir_alt = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
    if os.path.isdir(static_dir_alt):
        static_dir = static_dir_alt
    else:
        print(f"Warning: Static directory not found at {static_dir} or {static_dir_alt}")
        
# Check for uploads directory in the root core_api
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static/uploads")
if os.path.isdir(uploads_dir):
    print(f"Found uploads directory at {uploads_dir}")
    app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="static_uploads")
    
    # Ensure payment proofs directory exists
    payment_proofs_dir = os.path.join(uploads_dir, "payment_proofs")
    if not os.path.isdir(payment_proofs_dir):
        os.makedirs(payment_proofs_dir, exist_ok=True)
        print(f"Created payment proofs directory at {payment_proofs_dir}")

# Only mount if directory exists (won't crash if static files are not downloaded yet)
if os.path.isdir(static_dir):
  app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Templates Mounting ---
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# --- CORS Middleware ---
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Include API Routers ---
# Include all routers
try:
    # Include the individual routers
    api_router.include_router(users.router, prefix="/users", tags=["Users"])
    api_router.include_router(plans.router, prefix="/plans", tags=["Plans"])
    
    # Mount the API router
    app.include_router(api_router, prefix="/api/v1")
    print("Successfully loaded API routers!")
except Exception as e:
    print(f"Error loading API routers: {e}")
    logger.error(f"Failed to load API routers: {e}")
    raise  # Re-raise the exception to fail fast - circular imports should now be fixed

# Include panel router directly
app.include_router(
    panel.router,
    prefix=f"{settings.API_V1_STR}/panel",
    tags=["panel"],
    dependencies=[Depends(get_current_active_user)]
)

# Include subscriptions router
app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_STR}/subscriptions",
    tags=["subscriptions"],
    dependencies=[Depends(get_current_active_user)]
)

# --- Include Public Admin Routes (no auth required) ---
app.include_router(
    admin_routes.public_router,
    prefix="/admin",
    tags=["admin-public"],
)

# --- Include Protected Admin Dashboard Routes ---
app.include_router(
    admin_routes.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_active_superuser)]
)

# --- Root Route ---
@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request, 
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user_optional)
):
    """Render the dashboard if logged in, otherwise redirect to login."""
    if not current_user:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Dashboard Route ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_active_user)
):
    """Render the dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- Health Check Endpoint --- (Useful for deployment checks)
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# --- Root API Endpoint --- (For basic testing)
@app.get("/api", tags=["API Root"])
async def read_api_root():
    """Basic API root endpoint to check if the API part is running."""
    return {"message": "Welcome to MoonVPN Core API!"}

# Add custom exception handlers
@app.exception_handler(WalletException)
async def wallet_exception_handler(request: Request, exc: WalletException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(InsufficientFundsException)
async def insufficient_funds_exception_handler(request: Request, exc: InsufficientFundsException):
    return JSONResponse(
        status_code=402,  # Payment Required
        content={"detail": str(exc)},
    )

@app.exception_handler(InvalidAmountException)
async def invalid_amount_exception_handler(request: Request, exc: InvalidAmountException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

# Main entry point for running the app directly (e.g., without Uvicorn command)
if __name__ == "__main__":
    # Note: Uvicorn configuration here might override command-line args
    # It's usually better to run with 'uvicorn app.main:app --host ...'
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
