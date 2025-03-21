from .utils import get_user_active_roles, get_user_permissions

class RoleMiddleware:
    """
    Middleware that adds role information to the request.
    
    This middleware adds the following attributes to the request:
    - user_roles: A list of UserRole objects for the current user
    - user_permissions: A set of permission codenames for the current user
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request before view is called
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Add user roles to request
            request.user_roles = get_user_active_roles(request.user)
            
            # Add user permissions to request
            request.user_permissions = get_user_permissions(request.user)
        
        # Get response
        response = self.get_response(request)
        
        # Process response
        return response 