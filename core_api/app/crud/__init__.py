from .crud_user import user
from .crud_role import role
from .crud_permission import permission
from .crud_plan import plan
from .crud_panel import panel
from .crud_location import location
from .crud_server import server
from .crud_plan_category import plan_category
from .crud_order import order
from .crud_transaction import transaction
from .crud_subscription import subscription
from .crud_client import client
from .crud_billing import billing
from .crud_bank_card import bank_card
from . import (
    token,
    payment,
    log,
    affiliate
)

# Import base CRUD class for inheritance when creating new CRUD operations
from .base import CRUDBase

# Make all the CRUD operations available directly when importing the crud package
__all__ = [
    "user", "role", "permission", "plan", "plan_category", 
    "panel", "location", "server", "order", "transaction", "CRUDBase",
    "subscription",
    "client",
    "billing",
    "bank_card",
    "token",
    "payment",
    "log",
    "affiliate"
]

# You can optionally define a base CRUD class or utility functions here if needed
