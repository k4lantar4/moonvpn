"""
API router module that includes all API endpoints.
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    users,
    vpn_accounts,
    servers,
    locations,
    payments,
    admin,
)

api_router = APIRouter()

# Include all router modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vpn_accounts.router, prefix="/vpn-accounts", tags=["vpn-accounts"])
api_router.include_router(servers.router, prefix="/servers", tags=["servers"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 