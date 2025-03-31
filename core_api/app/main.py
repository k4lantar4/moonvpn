from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# TODO: Import routers later
# from app.api.v1 import api_router

# --- App Initialization ---
app = FastAPI(
    title="MoonVPN Core API",
    description="Backend API for MoonVPN Telegram Bot and Dashboard",
    version="0.1.0"
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
# app.include_router(api_router, prefix="/api/v1")

# --- Root API Endpoint --- (For basic testing)
@app.get("/api", tags=["API Root"])
async def read_api_root():
    """Basic API root endpoint to check if the API part is running."""
    return {"message": "Welcome to MoonVPN Core API!"}

# --- Health Check Endpoint --- (Useful for deployment checks)
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# --- Dashboard Test Endpoint --- #
@app.get("/dashboard", tags=["Dashboard"], include_in_schema=False)
async def read_dashboard_root(request: Request):
    """Renders the basic dashboard page using Tabler template."""
    return templates.TemplateResponse("base.html", {"request": request})
