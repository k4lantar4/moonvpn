"""
Permission definitions for the V2Ray management system.
"""

from enum import Enum
from typing import List, Dict
from rest_framework import permissions

class PermissionGroup(str, Enum):
    """Permission groups for organizing permissions."""
    SERVER = "server"
    USER = "user"
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"
    MONITORING = "monitoring"
    ADMIN = "admin"
    SELLER = "seller"

class Permission(str, Enum):
    """Granular permissions for the system."""
    # Server permissions
    VIEW_SERVERS = "view_servers"
    MANAGE_SERVERS = "manage_servers"
    MONITOR_SERVERS = "monitor_servers"
    SYNC_SERVERS = "sync_servers"
    
    # User permissions
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"
    
    # Subscription permissions
    VIEW_SUBSCRIPTIONS = "view_subscriptions"
    MANAGE_SUBSCRIPTIONS = "manage_subscriptions"
    CREATE_SUBSCRIPTIONS = "create_subscriptions"
    DELETE_SUBSCRIPTIONS = "delete_subscriptions"
    
    # Payment permissions
    VIEW_PAYMENTS = "view_payments"
    MANAGE_PAYMENTS = "manage_payments"
    VERIFY_PAYMENTS = "verify_payments"
    REFUND_PAYMENTS = "refund_payments"
    
    # Monitoring permissions
    VIEW_METRICS = "view_metrics"
    VIEW_LOGS = "view_logs"
    MANAGE_ALERTS = "manage_alerts"
    
    # Admin permissions
    MANAGE_ROLES = "manage_roles"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_REPORTS = "view_reports"
    
    # Seller permissions
    SELL_SUBSCRIPTIONS = "sell_subscriptions"
    VIEW_COMMISSIONS = "view_commissions"
    MANAGE_CUSTOMERS = "manage_customers"

# Permission groups mapping
PERMISSION_GROUPS: Dict[PermissionGroup, List[Permission]] = {
    PermissionGroup.SERVER: [
        Permission.VIEW_SERVERS,
        Permission.MANAGE_SERVERS,
        Permission.MONITOR_SERVERS,
        Permission.SYNC_SERVERS,
    ],
    PermissionGroup.USER: [
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.CREATE_USERS,
        Permission.DELETE_USERS,
    ],
    PermissionGroup.SUBSCRIPTION: [
        Permission.VIEW_SUBSCRIPTIONS,
        Permission.MANAGE_SUBSCRIPTIONS,
        Permission.CREATE_SUBSCRIPTIONS,
        Permission.DELETE_SUBSCRIPTIONS,
    ],
    PermissionGroup.PAYMENT: [
        Permission.VIEW_PAYMENTS,
        Permission.MANAGE_PAYMENTS,
        Permission.VERIFY_PAYMENTS,
        Permission.REFUND_PAYMENTS,
    ],
    PermissionGroup.MONITORING: [
        Permission.VIEW_METRICS,
        Permission.VIEW_LOGS,
        Permission.MANAGE_ALERTS,
    ],
    PermissionGroup.ADMIN: [
        Permission.MANAGE_ROLES,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_REPORTS,
    ],
    PermissionGroup.SELLER: [
        Permission.SELL_SUBSCRIPTIONS,
        Permission.VIEW_COMMISSIONS,
        Permission.MANAGE_CUSTOMERS,
    ],
}

# Role permissions mapping
ROLE_PERMISSIONS: Dict[str, List[Permission]] = {
    "admin": [p for group in PERMISSION_GROUPS.values() for p in group],
    "seller": [
        Permission.VIEW_SERVERS,
        Permission.VIEW_USERS,
        Permission.SELL_SUBSCRIPTIONS,
        Permission.VIEW_COMMISSIONS,
        Permission.MANAGE_CUSTOMERS,
        Permission.VIEW_METRICS,
    ],
    "vip": [
        Permission.VIEW_SERVERS,
        Permission.VIEW_SUBSCRIPTIONS,
        Permission.VIEW_PAYMENTS,
    ],
    "user": [
        Permission.VIEW_SERVERS,
        Permission.VIEW_SUBSCRIPTIONS,
        Permission.VIEW_PAYMENTS,
    ],
}

def get_role_permissions(role_name: str) -> List[Permission]:
    """Get permissions for a specific role."""
    return ROLE_PERMISSIONS.get(role_name, [])

def get_group_permissions(group: PermissionGroup) -> List[Permission]:
    """Get permissions for a specific group."""
    return PERMISSION_GROUPS.get(group, [])

def has_permission(user_permissions: List[Permission], required_permission: Permission) -> bool:
    """Check if user has a specific permission."""
    return required_permission in user_permissions

def has_any_permission(user_permissions: List[Permission], required_permissions: List[Permission]) -> bool:
    """Check if user has any of the required permissions."""
    return any(p in user_permissions for p in required_permissions)

def has_all_permissions(user_permissions: List[Permission], required_permissions: List[Permission]) -> bool:
    """Check if user has all of the required permissions."""
    return all(p in user_permissions for p in required_permissions)

class HasPermission(permissions.BasePermission):
    """Custom permission class for checking specific permissions."""
    
    def __init__(self, required_permission: Permission):
        self.required_permission = required_permission
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_permission(self.required_permission)

class HasGroupPermissions(permissions.BasePermission):
    """Custom permission class for checking group permissions."""
    
    def __init__(self, required_group: PermissionGroup):
        self.required_group = required_group
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_group_permissions(self.required_group)

class HasAnyPermission(permissions.BasePermission):
    """Custom permission class for checking any of the required permissions."""
    
    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return any(request.user.has_permission(p) for p in self.required_permissions)

class HasAllPermissions(permissions.BasePermission):
    """Custom permission class for checking all required permissions."""
    
    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return all(request.user.has_permission(p) for p in self.required_permissions)

class IsAdminUser(permissions.BasePermission):
    """Custom permission class for admin users."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

class IsSellerUser(permissions.BasePermission):
    """Custom permission class for seller users."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'seller'
        )

class IsVIPUser(permissions.BasePermission):
    """Custom permission class for VIP users."""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'vip'
        ) 