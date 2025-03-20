"""
FastAPI application for system health monitoring and recovery.

This module provides the main FastAPI application with endpoints for
health monitoring, metrics, recovery actions, and templates.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import health, metrics, recovery, template

app = FastAPI(
    title="MoonVPN Health Monitor",
    description="API for monitoring system health and managing recovery actions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(recovery.router, prefix="/api/v1/recovery", tags=["recovery"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["templates"])

@app.get("/")
async def root():
    """Root endpoint returning basic API information.
    
    Returns:
        dict: API information
    """
    return {
        "name": "MoonVPN Health Monitor",
        "version": "1.0.0",
        "status": "operational"
    } 