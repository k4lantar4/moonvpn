from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from .models import Role, UserRole

User = get_user_model()

def get_user_active_roles(user):
    """Get all active roles for a user."""
    if not user or not user.is_authenticated:
        return []
    
    now = timezone.now()
    return UserRole.objects.filter(
        user=user,
        is_active=True
    ).filter(
        # Either no expiration, or not expired yet
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    ).select_related('role')

def get_user_permissions(user):
    """Get all permissions for a user across all active roles."""
    if not user or not user.is_authenticated:
        return set()
    
    # Get active user roles
    user_roles = get_user_active_roles(user)
    
    # Collect all permissions
    permissions = set()
    for user_role in user_roles:
        role_permissions = user_role.role.permissions.all()
        permissions.update(perm.codename for perm in role_permissions)
    
    return permissions

def user_has_permission(user, permission_codename):
    """Check if user has a specific permission."""
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Get active user roles
    user_roles = get_user_active_roles(user)
    
    # Check if any role has the permission
    for user_role in user_roles:
        if user_role.role.has_permission(permission_codename):
            return True
    
    return False

def user_has_any_permission(user, permission_codenames):
    """Check if user has any of the specified permissions."""
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Get active user roles
    user_roles = get_user_active_roles(user)
    
    # Check if any role has any of the permissions
    for user_role in user_roles:
        for codename in permission_codenames:
            if user_role.role.has_permission(codename):
                return True
    
    return False

def user_has_all_permissions(user, permission_codenames):
    """Check if user has all of the specified permissions."""
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Get all user permissions
    user_permissions = get_user_permissions(user)
    
    # Check if all permissions are in user permissions
    return all(codename in user_permissions for codename in permission_codenames)

def assign_role_to_user(user, role_name, assigned_by=None, expires_at=None, notes=''):
    """Assign a role to a user."""
    try:
        role = Role.objects.get(name=role_name)
        user_role, created = UserRole.objects.update_or_create(
            user=user,
            role=role,
            defaults={
                'assigned_by': assigned_by,
                'expires_at': expires_at,
                'is_active': True,
                'notes': notes
            }
        )
        return user_role, created
    except Role.DoesNotExist:
        return None, False

def revoke_role_from_user(user, role_name):
    """Revoke a role from a user."""
    try:
        role = Role.objects.get(name=role_name)
        user_role = UserRole.objects.filter(user=user, role=role).first()
        if user_role:
            user_role.delete()
            return True
    except Role.DoesNotExist:
        pass
    return False 