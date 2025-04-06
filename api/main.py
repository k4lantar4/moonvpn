import logging
import json
from fastapi import FastAPI, Response
from core.config import get_settings
from core.logging import setup_logging
from core.database import check_db_connection, check_redis_connection

# Setup logging before anything else
setup_logging()

# Get settings instance
settings = get_settings()

# Create FastAPI app instance
# Add title, description, version from settings or directly later
app = FastAPI(
    title="MoonVPN API",
    description="API for managing MoonVPN services, clients, and payments.",
    version="0.1.0"
)

# --- Database Setup (Optional: Create tables if not using Alembic) ---
# from core.database import engine, Base
# from api import models # Make sure all models are imported
# Base.metadata.create_all(bind=engine) # Creates tables if they don't exist
# --------------------------------------------------------------------

# --- Event Handlers (Optional) ---
@app.on_event("startup")
async def startup_event():
    logging.info("API Startup complete.")
    # Connect to Redis, etc.

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("API Shutdown.")
    # Disconnect from Redis, etc.
# --------------------------------

# --- Middleware (Optional) ---
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # Adjust in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# --------------------------

# --- Routers ---
from api.routes import panels
app.include_router(panels.router, prefix="/api/v1/panels", tags=["Panels"])
# Other routers will be included here when implemented
# -----------------------------

# --- Health Check Endpoints ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint.
    
    Checks:
    - Database connection
    - Redis connection
    
    Returns:
        dict: Health status of all components
    """
    db_status = "healthy" if check_db_connection() else "unhealthy"
    redis_status = "healthy" if check_redis_connection() else "unhealthy"
    
    status = "healthy" if all([
        db_status == "healthy",
        redis_status == "healthy"
    ]) else "unhealthy"
    
    response = {
        "status": status,
        "database": db_status,
        "redis": redis_status
    }
    
    return Response(
        content=json.dumps(response),
        media_type="application/json",
        headers={"X-Health-Check": "true"}
    )

@app.get("/ping", tags=["Health"])
async def pong():
    """Simple health check endpoint.

    Returns:
        dict: A status message indicating the API is running.
    """
    logging.info("Ping endpoint called")
    return {"status": "ok", "message": "Pong!"}
# ----------------------------------

# Add more routes and logic later...
