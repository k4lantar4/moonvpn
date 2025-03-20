from django import template
from django.utils.safestring import mark_safe
from ..utils import user_has_permission, user_has_any_permission, user_has_all_permissions

register = template.Library()

@register.simple_tag
def has_permission(user, permission_codename):
    """
    Check if a user has a specific permission.
    
    Usage:
        {% load role_tags %}
        {% has_permission user "manage_users" as can_manage_users %}
        {% if can_manage_users %}
            <a href="{% url 'admin:users_user_changelist' %}">Manage Users</a>
        {% endif %}
    """
    return user_has_permission(user, permission_codename)

@register.simple_tag
def has_any_permission(user, *permission_codenames):
    """
    Check if a user has any of the specified permissions.
    
    Usage:
        {% load role_tags %}
        {% has_any_permission user "view_users" "manage_users" as can_access_users %}
        {% if can_access_users %}
            <a href="{% url 'admin:users_user_changelist' %}">Users</a>
        {% endif %}
    """
    return user_has_any_permission(user, permission_codenames)

@register.simple_tag
def has_all_permissions(user, *permission_codenames):
    """
    Check if a user has all of the specified permissions.
    
    Usage:
        {% load role_tags %}
        {% has_all_permissions user "view_users" "manage_users" as can_fully_manage_users %}
        {% if can_fully_manage_users %}
            <a href="{% url 'admin:users_user_changelist' %}">Manage Users</a>
        {% endif %}
    """
    return user_has_all_permissions(user, permission_codenames)

@register.filter
def user_roles(user):
    """
    Get a list of role names for a user.
    
    Usage:
        {% load role_tags %}
        <p>Roles: {{ user|user_roles|join:", " }}</p>
    """
    if not user or not user.is_authenticated:
        return []
    
    from ..utils import get_user_active_roles
    user_roles = get_user_active_roles(user)
    return [user_role.role.name for user_role in user_roles]

@register.filter
def role_badge(role_name):
    """
    Generate a badge for a role.
    
    Usage:
        {% load role_tags %}
        <div>{{ role.name|role_badge }}</div>
    """
    colors = {
        'admin': 'danger',
        'manager': 'warning',
        'support': 'info',
        'user': 'secondary',
    }
    
    color = colors.get(role_name.lower(), 'primary')
    return mark_safe(f'<span class="badge bg-{color}">{role_name}</span>')

@register.inclusion_tag('roles/user_roles_list.html')
def render_user_roles(user):
    """
    Render a list of user roles.
    
    Usage:
        {% load role_tags %}
        {% render_user_roles user %}
    """
    from ..utils import get_user_active_roles
    user_roles = get_user_active_roles(user)
    return {'user_roles': user_roles} 