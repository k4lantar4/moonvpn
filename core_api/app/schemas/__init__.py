# Import individual types to facilitate easier imports elsewhere
# e.g. from app.schemas import User, Plan, etc.

# First import models that don't depend on others
from .plan_category import PlanCategory, PlanCategoryCreate, PlanCategoryUpdate, PlanCategoryBase, PlanCategoryInDB
from .location import Location, LocationCreate, LocationUpdate, LocationBase, LocationInDB, LocationDetail
from .server import Server, ServerCreate, ServerUpdate, ServerBase, ServerInDB, ServerDetail
from .plan import Plan, PlanCreate, PlanUpdate, PlanBase, PlanInDB, PlanWithCategory, PlanDetail
from .panel import Panel, PanelCreate, PanelUpdate, PanelBase, PanelInDB, PanelDetail

# Import both Role and Permission - now they use string type hints to avoid circular references
from .role import Role, RoleCreate, RoleUpdate, RoleBase, RoleInDB, RoleList, RoleDetail, RoleWithPermissions
from .permission import Permission, PermissionCreate, PermissionUpdate, PermissionBase, PermissionInDB, PermissionList, PermissionDetail

# Import user which might depend on role
from .user import User, UserCreate, UserUpdate, UserInDB, UserPasswordUpdate, AdminUserUpdate, UserList, UserDetail, UserIds, UserWithRole

# Import Token schemas
from .token import Token, TokenPayload

# Import order and transaction schemas
from .order import Order, OrderCreate, OrderUpdate, OrderInDB, OrderDetail, OrderStatusList, OrderIds, OrderStatus, OrderType
from .transaction import (
    Transaction, TransactionCreate, TransactionUpdate, TransactionInDB,
    DepositRequest, WithdrawRequest, AdminAdjustment, TransactionType, TransactionStatus
)

# Import subscription and client schemas
from .subscription import Subscription, SubscriptionCreate, SubscriptionInDB, SubscriptionUpdate, SubscriptionStatus, SubscriptionType
from .client import Client, ClientCreate, ClientInDB, ClientUpdate, ClientStatus
from .billing import BillingInfo, BillingInfoCreate, BillingInfoInDB, BillingInfoUpdate

# Import wallet schemas  
from .wallet import DepositRequest, WithdrawRequest, AdminAdjustment, TransactionSummary, PaymentMethod

# Import bank card schemas
from .bank_card import (
    BankCard, BankCardCreate, BankCardUpdate, BankCardBase, 
    BankCardInDB, BankCardList, BankCardDetail
)

# All imports should be explicitly listed for better code maintainability
__all__ = [
    # User related
    "User", "UserCreate", "UserUpdate", "UserInDB", "UserPasswordUpdate", "AdminUserUpdate", 
    "UserList", "UserDetail", "UserIds", "UserWithRole",
    
    # Role and Permission related
    "Role", "RoleCreate", "RoleUpdate", "RoleInDB", "RoleList", "RoleDetail", "RoleWithPermissions",
    "Permission", "PermissionCreate", "PermissionUpdate", "PermissionInDB", "PermissionList", "PermissionDetail",
    
    # Panel and Location related
    "Panel", "PanelCreate", "PanelUpdate", "PanelInDB", "PanelDetail",
    "Location", "LocationCreate", "LocationUpdate", "LocationInDB", "LocationDetail",
    
    # Plan related
    "Plan", "PlanCreate", "PlanUpdate", "PlanInDB", "PlanWithCategory", "PlanDetail",
    "PlanCategory", "PlanCategoryCreate", "PlanCategoryUpdate", "PlanCategoryInDB",
    
    # Server related
    "Server", "ServerCreate", "ServerUpdate", "ServerInDB", "ServerDetail",
    
    # Authentication related
    "Token", "TokenPayload",
    
    # Order and Transaction related 
    "Order", "OrderCreate", "OrderUpdate", "OrderInDB", "OrderDetail", "OrderStatusList", "OrderIds", "OrderStatus", "OrderType",
    "Transaction", "TransactionCreate", "TransactionUpdate", "TransactionInDB", "TransactionType", "TransactionStatus",
    
    # Wallet related
    "DepositRequest", "WithdrawRequest", "AdminAdjustment", "TransactionSummary", "PaymentMethod",
    
    # Subscription and Client related
    "Subscription", "SubscriptionCreate", "SubscriptionInDB", "SubscriptionUpdate", "SubscriptionStatus", "SubscriptionType",
    "Client", "ClientCreate", "ClientInDB", "ClientUpdate", "ClientStatus",
    "BillingInfo", "BillingInfoCreate", "BillingInfoInDB", "BillingInfoUpdate",
    
    # Bank Card related
    "BankCard", "BankCardCreate", "BankCardUpdate", "BankCardBase", 
    "BankCardInDB", "BankCardList", "BankCardDetail"
]
