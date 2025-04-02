from fastapi import APIRouter

# Import endpoint modules
from app.api.v1.endpoints import items # Example endpoint
from app.api.v1.endpoints import users # Import the new users router
from app.api.v1.endpoints import plans # Import the new plans router
from app.api.v1.endpoints import panels # Import the new panels router
from app.api.v1.endpoints import locations # Import the new locations router
from app.api.v1.endpoints import auth # Import the new auth router
from app.api.v1.endpoints import roles # Import the roles router
from app.api.v1.endpoints import permissions # Import the permissions router
from app.api.v1.endpoints import orders # Import the orders router
from app.api.v1.endpoints import login # Import the login router
from app.api.v1.endpoints import inbounds # Import the inbounds router
from app.api.v1.endpoints import clients # Import the clients router
from app.api.v1.endpoints import subscriptions # Import the subscriptions router
from app.api.v1.endpoints import wallet # Import the wallet router
from app.api.v1.endpoints import bank_cards # Import the bank cards router
from app.api.v1.endpoints import payment_admins # Import the payment admins router
from app.api.v1.endpoints import payment_proofs # Import the payment proofs router
from app.api.v1.endpoints import payments # Import the payments router
from app.api.v1.endpoints import settings # Import the settings router
from app.api.v1.endpoints import panel # Import the panel router (deprecated endpoints)
from app.api.v1.endpoints import servers # Import the servers router
from app.api.v1.endpoints import financial_reporting # Import the financial reporting router
# Import other endpoint routers here as they are created
# from app.api.v1.endpoints import roles, permissions, ...

# Create the main API router for version 1
api_router = APIRouter()

# Include routers from endpoint modules
api_router.include_router(items.router, prefix="/items", tags=["Items"]) # Example
api_router.include_router(users.router, prefix="/users", tags=["Users"]) # Add users router
api_router.include_router(plans.router, prefix="/plans", tags=["Plans"]) # Add plans router
api_router.include_router(panels.router, prefix="/panels", tags=["Panels"]) # Add panels router
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"]) # Add locations router
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles Management"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions Management"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(login.router, tags=["login"])
api_router.include_router(inbounds.router, prefix="/inbounds", tags=["inbounds"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(bank_cards.router, prefix="/bank-cards", tags=["bank_cards"])
api_router.include_router(payment_admins.router, prefix="/payment-admins", tags=["payment_admins"])
api_router.include_router(payment_proofs.router, prefix="/payment-proofs", tags=["payment_proofs"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(panel.router, prefix="/panel", tags=["Panel"]) # Add panel router (deprecated endpoints)
api_router.include_router(servers.router, prefix="/servers", tags=["Servers"]) # Add servers router
api_router.include_router(financial_reporting.router, prefix="/financial-reporting", tags=["Financial Reports"]) # Add financial reporting router
# Include other routers here
# api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
# api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
