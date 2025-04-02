from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    users,
    login,
    roles,
    permissions,
    orders,
    transactions,
    subscriptions,
    payments,
    plans,
    logs,
    affiliate
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(affiliate.router, prefix="/affiliate", tags=["affiliate"]) 