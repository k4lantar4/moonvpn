from functools import wraps
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from .utils import user_has_permission, user_has_any_permission, user_has_all_permissions

# Django view decorators
def permission_required(permission_codename):
    """
    Decorator for views that checks whether a user has a particular permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden(_("Authentication required"))
            
            if user_has_permission(request.user, permission_codename):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(_("Permission denied"))
        return _wrapped_view
    return decorator

def any_permission_required(permission_codenames):
    """
    Decorator for views that checks whether a user has any of the given permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden(_("Authentication required"))
            
            if user_has_any_permission(request.user, permission_codenames):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(_("Permission denied"))
        return _wrapped_view
    return decorator

def all_permissions_required(permission_codenames):
    """
    Decorator for views that checks whether a user has all of the given permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden(_("Authentication required"))
            
            if user_has_all_permissions(request.user, permission_codenames):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(_("Permission denied"))
        return _wrapped_view
    return decorator

# DRF Permission classes
class HasRolePermission(BasePermission):
    """
    Permission class that checks if the user has a specific permission.
    """
    message = _("You do not have the required permission to perform this action.")
    
    def __init__(self, permission_codename):
        self.permission_codename = permission_codename
    
    def has_permission(self, request, view):
        return user_has_permission(request.user, self.permission_codename)

class HasAnyRolePermission(BasePermission):
    """
    Permission class that checks if the user has any of the specified permissions.
    """
    message = _("You do not have any of the required permissions to perform this action.")
    
    def __init__(self, permission_codenames):
        self.permission_codenames = permission_codenames
    
    def has_permission(self, request, view):
        return user_has_any_permission(request.user, self.permission_codenames)

class HasAllRolePermissions(BasePermission):
    """
    Permission class that checks if the user has all of the specified permissions.
    """
    message = _("You do not have all the required permissions to perform this action.")
    
    def __init__(self, permission_codenames):
        self.permission_codenames = permission_codenames
    
    def has_permission(self, request, view):
        return user_has_all_permissions(request.user, self.permission_codenames) 