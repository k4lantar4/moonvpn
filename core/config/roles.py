from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class PermissionGroup(models.Model):
    """Model for organizing permissions into logical groups."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Permission Group')
        verbose_name_plural = _('Permission Groups')

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Model for granular permissions in the system."""
    name = models.CharField(max_length=50, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group__name', 'name']
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')
        unique_together = ['group', 'codename']

    def __str__(self):
        return f"{self.group.name} - {self.name}"


class Role(models.Model):
    """Model for user roles with dynamic permissions."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True
    )
    is_system_role = models.BooleanField(
        default=False,
        help_text=_('System roles cannot be deleted and have special behaviors')
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return self.name
    
    def has_permission(self, permission_codename):
        """Check if role has a specific permission by codename."""
        return self.permissions.filter(codename=permission_codename).exists()
    
    def has_group_permissions(self, group_name):
        """Check if role has all permissions in a group."""
        try:
            group = PermissionGroup.objects.get(name=group_name)
            group_permissions = Permission.objects.filter(group=group)
            return all(self.permissions.filter(id=perm.id).exists() for perm in group_permissions)
        except PermissionGroup.DoesNotExist:
            return False


class UserRole(models.Model):
    """Model for assigning roles to users with additional data."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-assigned_at']
        verbose_name = _('User Role')
        verbose_name_plural = _('User Roles')
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class RoleChangeLog(models.Model):
    """Audit log for role-related changes."""
    ACTION_CHOICES = (
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('assign', _('Assign')),
        ('revoke', _('Revoke')),
    )
    
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='change_logs'
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='role_changes'
    )
    performed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='performed_role_changes'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Role Change Log')
        verbose_name_plural = _('Role Change Logs')
        
    def __str__(self):
        return f"{self.get_action_display()} - {self.role} - {self.timestamp}" # Merged from backend/roles/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class PermissionGroup(models.Model):
    """Model for organizing permissions into logical groups."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Permission Group')
        verbose_name_plural = _('Permission Groups')

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Model for granular permissions in the system."""
    name = models.CharField(max_length=50, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    group = models.ForeignKey(
        PermissionGroup,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group__name', 'name']
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')
        unique_together = ['group', 'codename']

    def __str__(self):
        return f"{self.group.name} - {self.name}"


class Role(models.Model):
    """Model for user roles with dynamic permissions."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True
    )
    is_system_role = models.BooleanField(
        default=False,
        help_text=_('System roles cannot be deleted and have special behaviors')
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return self.name
    
    def has_permission(self, permission_codename):
        """Check if role has a specific permission by codename."""
        return self.permissions.filter(codename=permission_codename).exists()
    
    def has_group_permissions(self, group_name):
        """Check if role has all permissions in a group."""
        try:
            group = PermissionGroup.objects.get(name=group_name)
            group_permissions = Permission.objects.filter(group=group)
            return all(self.permissions.filter(id=perm.id).exists() for perm in group_permissions)
        except PermissionGroup.DoesNotExist:
            return False


class UserRole(models.Model):
    """Model for assigning roles to users with additional data."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-assigned_at']
        verbose_name = _('User Role')
        verbose_name_plural = _('User Roles')
        unique_together = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class RoleChangeLog(models.Model):
    """Audit log for role-related changes."""
    ACTION_CHOICES = (
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('assign', _('Assign')),
        ('revoke', _('Revoke')),
    )
    
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='change_logs'
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='role_changes'
    )
    performed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='performed_role_changes'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Role Change Log')
        verbose_name_plural = _('Role Change Logs')
        
    def __str__(self):
        return f"{self.get_action_display()} - {self.role} - {self.timestamp}" 