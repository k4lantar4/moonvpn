from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Role, UserRole, RoleChangeLog

User = get_user_model()

@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    """Assign default role to new users."""
    if created:
        try:
            default_role = Role.objects.get(name='user')
            UserRole.objects.create(
                user=instance,
                role=default_role,
                is_active=True
            )
        except Role.DoesNotExist:
            # If default role doesn't exist, log error
            pass

@receiver(post_delete, sender=UserRole)
def log_role_revocation(sender, instance, **kwargs):
    """Log when a user role is deleted."""
    # We don't create a log entry here because it's handled in the viewset
    pass

@receiver(m2m_changed, sender=Role.permissions.through)
def log_role_permissions_change(sender, instance, action, pk_set, **kwargs):
    """Log when permissions are added or removed from a role."""
    if action in ['post_add', 'post_remove']:
        # Skip logging here as it's handled in the serializer/viewset
        pass 