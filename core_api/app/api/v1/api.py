from fastapi import APIRouter

# Import endpoint modules
from app.api.v1.endpoints import items # Example endpoint
from app.api.v1.endpoints import users # Import the new users router
# Import other endpoint routers here as they are created
# from app.api.v1.endpoints import roles, permissions, ...

# Create the main API router for version 1
api_router = APIRouter()

# Include routers from endpoint modules
api_router.include_router(items.router, prefix="/items", tags=["Items"]) # Example
api_router.include_router(users.router, prefix="/users", tags=["Users"]) # Add users router
# Include other routers here
# api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
# api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"]) 