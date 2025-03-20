"""
Main application module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.config import settings
from core.database.session import engine
from core.database import models
from api.v1.endpoints import auth, users, vpn, payments, monitoring
from core.config.logging_config import setup_logging
from core.middleware.logging_middleware import LoggingMiddleware
from core.middleware.monitoring_middleware import MonitoringMiddleware
from core.utils.logger import log_info

# Set up logging
setup_logging()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(MonitoringMiddleware)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(vpn.router, prefix=f"{settings.API_V1_STR}/vpn", tags=["vpn"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(monitoring.router, prefix=f"{settings.API_V1_STR}/monitoring", tags=["monitoring"])

# Handle validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to MoonVPN API"}

@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    log_info("Application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown."""
    log_info("Application shutting down") 