from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uvicorn

# Import routers
from app.api.v1 import api_router
from app.api.v1.endpoints import users, plans
from app.core.config import settings

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

# Only mount if directory exists (won't crash if static files are not downloaded yet)
if os.path.isdir(static_dir):
  app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Templates Mounting ---
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# --- CORS Middleware ---
# Adjust origins as needed for your dashboard frontend
origins = [
    "http://localhost",
    "http://localhost:3000", # Example for a React/Next frontend dev server
    # Add your production frontend domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include API Routers ---
# Include main routers
try:
    # Try to include the routers with fixed circular dependencies
    api_router.include_router(users.router, prefix="/users", tags=["Users"])
    api_router.include_router(plans.router, prefix="/plans", tags=["Plans"])
    
    # Mount the API router
    app.include_router(api_router, prefix="/api/v1")
    print("Successfully loaded API routers!")
except Exception as e:
    print(f"Error loading API routers: {e}")
    print("Fallback to basic endpoints activated")
    
    # --- Basic User Endpoints for Bot --- (Fallback if routers fail)
    @app.get("/api/v1/users/telegram/{telegram_id}", tags=["Users"])
    async def get_user_by_telegram_id(telegram_id: int):
        """Get user by Telegram ID (temporary mock endpoint)."""
        # Return a mock user for now
        if telegram_id in [1713374557]:  # Admin user ID for testing
            return {
                "id": 1,
                "telegram_id": telegram_id,
                "first_name": "Admin",
                "username": "admin",
                "phone_number": "+989123456789",
                "role_id": 1
            }
        return None  # 404 if not found

    @app.post("/api/v1/users/", tags=["Users"], status_code=201)
    async def register_user(user_data: dict):
        """Register a new user (temporary mock endpoint)."""
        # Just return the data back as if registered successfully
        return {
            "id": 1,
            "telegram_id": user_data.get("telegram_id"),
            "first_name": user_data.get("first_name"),
            "username": user_data.get("username"),
            "phone_number": user_data.get("phone_number"),
            "role_id": 2  # Default regular user role
        }

    @app.get("/api/v1/plans/active/", tags=["Plans"])
    async def get_active_plans():
        """Get list of active plans (temporary mock endpoint)."""
        # Return some mock plans
        return [
            {
                "id": 1,
                "name": "طرح یک ماهه",
                "description": "دسترسی به VPN با ترافیک نامحدود به مدت یک ماه",
                "price": 250000,
                "duration_days": 30,
                "is_active": True
            },
            {
                "id": 2,
                "name": "طرح سه ماهه",
                "description": "دسترسی به VPN با ترافیک نامحدود به مدت سه ماه",
                "price": 650000,
                "duration_days": 90,
                "is_active": True
            }
        ]

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

# Main entry point for running the app directly (e.g., without Uvicorn command)
if __name__ == "__main__":
    # Note: Uvicorn configuration here might override command-line args
    # It's usually better to run with 'uvicorn app.main:app --host ...'
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
