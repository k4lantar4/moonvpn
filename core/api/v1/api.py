"""
API router configuration.

This module contains the main FastAPI router configuration,
combining all endpoint routers.
"""

from fastapi import APIRouter

from core.api.v1.endpoints import (
    auth, users, vpn, payments, reports,
    notifications, maintenance, backup
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vpn.router, prefix="/vpn", tags=["vpn"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(backup.router, prefix="/backups", tags=["backups"]) 