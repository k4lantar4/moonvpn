"""
Permission constants for the MoonVPN system.

This module defines all permission constants used throughout the application.
When adding a new permission, add it here as a constant to ensure consistency.

Permissions are grouped by functional area for better organization.
"""

# User Management Permissions
USER_READ = "user:read"
USER_CREATE = "user:create"
USER_UPDATE = "user:update"
USER_DELETE = "user:delete"
USER_BLOCK = "user:block"
USER_CHANGE_ROLE = "user:change_role"

# Role Management Permissions
ROLE_READ = "role:read"
ROLE_CREATE = "role:create"
ROLE_UPDATE = "role:update"
ROLE_DELETE = "role:delete"
ROLE_ASSIGN_PERMISSION = "role:assign_permission"

# Plan Management Permissions
PLAN_READ = "plan:read"
PLAN_CREATE = "plan:create"
PLAN_UPDATE = "plan:update"
PLAN_DELETE = "plan:delete"
PLAN_CATEGORY_MANAGE = "plan:category_manage"

# Payment Management Permissions
PAYMENT_READ = "payment:read"
PAYMENT_VERIFY = "payment:verify"
PAYMENT_REFUND = "payment:refund"
PAYMENT_REPORT = "payment:report"
BANKCARD_MANAGE = "payment:bankcard_manage"

# Subscription Management Permissions
SUBSCRIPTION_READ = "subscription:read"
SUBSCRIPTION_CREATE = "subscription:create"
SUBSCRIPTION_UPDATE = "subscription:update"
SUBSCRIPTION_DELETE = "subscription:delete"
SUBSCRIPTION_FREEZE = "subscription:freeze"

# Server Management Permissions
SERVER_READ = "server:read"
SERVER_CREATE = "server:create"
SERVER_UPDATE = "server:update"
SERVER_DELETE = "server:delete"
SERVER_RESTART = "server:restart"
SERVER_EXECUTE_COMMAND = "server:execute_command"

# Panel Management Permissions
PANEL_READ = "panel:read"
PANEL_CREATE = "panel:create"
PANEL_UPDATE = "panel:update"
PANEL_DELETE = "panel:delete"

# Affiliate System Permissions
AFFILIATE_READ = "affiliate:read"
AFFILIATE_MANAGE = "affiliate:manage"
AFFILIATE_WITHDRAW_APPROVE = "affiliate:withdraw_approve"

# Financial Permissions
FINANCIAL_REPORT_VIEW = "financial:report_view"
FINANCIAL_REPORT_EXPORT = "financial:report_export"
WALLET_MANAGE = "financial:wallet_manage"

# System Settings Permissions
SETTINGS_READ = "settings:read"
SETTINGS_UPDATE = "settings:update"

# Permission Groups
# Group related permissions for convenience when assigning to roles

USER_MANAGEMENT_PERMISSIONS = [
    USER_READ, USER_CREATE, USER_UPDATE, USER_DELETE, USER_BLOCK, USER_CHANGE_ROLE
]

ROLE_MANAGEMENT_PERMISSIONS = [
    ROLE_READ, ROLE_CREATE, ROLE_UPDATE, ROLE_DELETE, ROLE_ASSIGN_PERMISSION
]

PLAN_MANAGEMENT_PERMISSIONS = [
    PLAN_READ, PLAN_CREATE, PLAN_UPDATE, PLAN_DELETE, PLAN_CATEGORY_MANAGE
]

PAYMENT_MANAGEMENT_PERMISSIONS = [
    PAYMENT_READ, PAYMENT_VERIFY, PAYMENT_REFUND, PAYMENT_REPORT, BANKCARD_MANAGE
]

SUBSCRIPTION_MANAGEMENT_PERMISSIONS = [
    SUBSCRIPTION_READ, SUBSCRIPTION_CREATE, SUBSCRIPTION_UPDATE, SUBSCRIPTION_DELETE, SUBSCRIPTION_FREEZE
]

SERVER_MANAGEMENT_PERMISSIONS = [
    SERVER_READ, SERVER_CREATE, SERVER_UPDATE, SERVER_DELETE, SERVER_RESTART, SERVER_EXECUTE_COMMAND
]

PANEL_MANAGEMENT_PERMISSIONS = [
    PANEL_READ, PANEL_CREATE, PANEL_UPDATE, PANEL_DELETE
]

AFFILIATE_MANAGEMENT_PERMISSIONS = [
    AFFILIATE_READ, AFFILIATE_MANAGE, AFFILIATE_WITHDRAW_APPROVE
]

FINANCIAL_MANAGEMENT_PERMISSIONS = [
    FINANCIAL_REPORT_VIEW, FINANCIAL_REPORT_EXPORT, WALLET_MANAGE
]

SETTINGS_MANAGEMENT_PERMISSIONS = [
    SETTINGS_READ, SETTINGS_UPDATE
]

# Predefined Role Templates
# These define standard permission sets for common roles

ADMIN_PERMISSIONS = (
    USER_MANAGEMENT_PERMISSIONS +
    ROLE_MANAGEMENT_PERMISSIONS +
    PLAN_MANAGEMENT_PERMISSIONS +
    PAYMENT_MANAGEMENT_PERMISSIONS +
    SUBSCRIPTION_MANAGEMENT_PERMISSIONS +
    SERVER_MANAGEMENT_PERMISSIONS +
    PANEL_MANAGEMENT_PERMISSIONS +
    AFFILIATE_MANAGEMENT_PERMISSIONS +
    FINANCIAL_MANAGEMENT_PERMISSIONS +
    SETTINGS_MANAGEMENT_PERMISSIONS
)

PAYMENT_ADMIN_PERMISSIONS = [
    USER_READ,
    PAYMENT_READ,
    PAYMENT_VERIFY,
    PAYMENT_REPORT,
    SUBSCRIPTION_READ,
    FINANCIAL_REPORT_VIEW
]

SUPPORT_PERMISSIONS = [
    USER_READ,
    PLAN_READ,
    PAYMENT_READ,
    SUBSCRIPTION_READ,
    SUBSCRIPTION_FREEZE,
    FINANCIAL_REPORT_VIEW,
    SERVER_READ,
    PANEL_READ,
    AFFILIATE_READ
]

SELLER_PERMISSIONS = [
    USER_READ,
    PLAN_READ,
    SUBSCRIPTION_READ,
    SUBSCRIPTION_CREATE
]

# Function to get all permissions as a list
def get_all_permissions():
    """Return a list of all defined permission constants."""
    return ADMIN_PERMISSIONS 