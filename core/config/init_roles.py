from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from roles.models import PermissionGroup, Permission, Role
import logging

logger = logging.getLogger(__name__)

# Define default permission groups
DEFAULT_PERMISSION_GROUPS = [
    {
        'name': 'server',
        'description': _('Server management permissions'),
        'permissions': [
            {'name': _('View Servers'), 'codename': 'view_servers', 'description': _('Can view server list and details')},
            {'name': _('Manage Servers'), 'codename': 'manage_servers', 'description': _('Can add, edit, and delete servers')},
            {'name': _('Monitor Servers'), 'codename': 'monitor_servers', 'description': _('Can view server metrics and status')},
            {'name': _('Sync Servers'), 'codename': 'sync_servers', 'description': _('Can sync servers with 3x-UI')},
        ]
    },
    {
        'name': 'user',
        'description': _('User management permissions'),
        'permissions': [
            {'name': _('View Users'), 'codename': 'view_users', 'description': _('Can view user list and details')},
            {'name': _('Manage Users'), 'codename': 'manage_users', 'description': _('Can edit user details')},
            {'name': _('Create Users'), 'codename': 'create_users', 'description': _('Can create new users')},
            {'name': _('Delete Users'), 'codename': 'delete_users', 'description': _('Can delete users')},
        ]
    },
    {
        'name': 'subscription',
        'description': _('Subscription management permissions'),
        'permissions': [
            {'name': _('View Subscriptions'), 'codename': 'view_subscriptions', 'description': _('Can view subscription list and details')},
            {'name': _('Manage Subscriptions'), 'codename': 'manage_subscriptions', 'description': _('Can edit subscription details')},
            {'name': _('Create Subscriptions'), 'codename': 'create_subscriptions', 'description': _('Can create new subscriptions')},
            {'name': _('Delete Subscriptions'), 'codename': 'delete_subscriptions', 'description': _('Can delete subscriptions')},
        ]
    },
    {
        'name': 'payment',
        'description': _('Payment management permissions'),
        'permissions': [
            {'name': _('View Payments'), 'codename': 'view_payments', 'description': _('Can view payment list and details')},
            {'name': _('Manage Payments'), 'codename': 'manage_payments', 'description': _('Can edit payment details')},
            {'name': _('Verify Payments'), 'codename': 'verify_payments', 'description': _('Can verify payments')},
            {'name': _('Refund Payments'), 'codename': 'refund_payments', 'description': _('Can process refunds')},
        ]
    },
    {
        'name': 'monitoring',
        'description': _('Monitoring and reporting permissions'),
        'permissions': [
            {'name': _('View Metrics'), 'codename': 'view_metrics', 'description': _('Can view system metrics')},
            {'name': _('View Logs'), 'codename': 'view_logs', 'description': _('Can view system logs')},
            {'name': _('Manage Alerts'), 'codename': 'manage_alerts', 'description': _('Can manage system alerts')},
        ]
    },
    {
        'name': 'admin',
        'description': _('Administrative permissions'),
        'permissions': [
            {'name': _('Manage Roles'), 'codename': 'manage_roles', 'description': _('Can manage user roles')},
            {'name': _('Manage Settings'), 'codename': 'manage_settings', 'description': _('Can manage system settings')},
            {'name': _('View Reports'), 'codename': 'view_reports', 'description': _('Can view system reports')},
        ]
    },
    {
        'name': 'seller',
        'description': _('Seller permissions'),
        'permissions': [
            {'name': _('Sell Subscriptions'), 'codename': 'sell_subscriptions', 'description': _('Can sell subscriptions')},
            {'name': _('View Commissions'), 'codename': 'view_commissions', 'description': _('Can view commission reports')},
            {'name': _('Manage Customers'), 'codename': 'manage_customers', 'description': _('Can manage assigned customers')},
        ]
    },
]

# Define default roles with permissions
DEFAULT_ROLES = [
    {
        'name': 'admin',
        'description': _('Administrator with full access'),
        'is_system_role': True,
        'permissions': [
            # Admin has all permissions
            'view_servers', 'manage_servers', 'monitor_servers', 'sync_servers',
            'view_users', 'manage_users', 'create_users', 'delete_users',
            'view_subscriptions', 'manage_subscriptions', 'create_subscriptions', 'delete_subscriptions',
            'view_payments', 'manage_payments', 'verify_payments', 'refund_payments',
            'view_metrics', 'view_logs', 'manage_alerts',
            'manage_roles', 'manage_settings', 'view_reports',
            'sell_subscriptions', 'view_commissions', 'manage_customers',
        ]
    },
    {
        'name': 'seller',
        'description': _('Seller with customer management access'),
        'is_system_role': True,
        'permissions': [
            'view_servers',
            'view_users',
            'view_subscriptions', 'create_subscriptions',
            'view_payments', 'verify_payments',
            'view_metrics',
            'sell_subscriptions', 'view_commissions', 'manage_customers',
        ]
    },
    {
        'name': 'vip',
        'description': _('VIP Customer with enhanced access'),
        'is_system_role': True,
        'permissions': [
            'view_servers',
            'view_subscriptions',
            'view_payments',
        ]
    },
    {
        'name': 'user',
        'description': _('Regular user with basic access'),
        'is_system_role': True,
        'permissions': [
            'view_servers',
            'view_subscriptions',
            'view_payments',
        ]
    },
]


class Command(BaseCommand):
    help = 'Initialize default permission groups, permissions, and roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing permissions and roles',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.NOTICE('Initializing permission groups and permissions...'))
        permissions_map = self._init_permissions(force)
        
        self.stdout.write(self.style.NOTICE('Initializing roles...'))
        self._init_roles(permissions_map, force)
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized roles and permissions.'))

    def _init_permissions(self, force):
        """Initialize permission groups and permissions."""
        permissions_map = {}
        
        for group_data in DEFAULT_PERMISSION_GROUPS:
            group, created = PermissionGroup.objects.get_or_create(
                name=group_data['name'],
                defaults={'description': group_data['description']}
            )
            
            if not created and force:
                group.description = group_data['description']
                group.save()
                self.stdout.write(self.style.WARNING(f'Updated permission group: {group.name}'))
            elif created:
                self.stdout.write(self.style.SUCCESS(f'Created permission group: {group.name}'))
            
            for perm_data in group_data['permissions']:
                perm, created = Permission.objects.get_or_create(
                    codename=perm_data['codename'],
                    defaults={
                        'name': perm_data['name'],
                        'description': perm_data['description'],
                        'group': group
                    }
                )
                
                if not created and force:
                    perm.name = perm_data['name']
                    perm.description = perm_data['description']
                    perm.group = group
                    perm.save()
                    self.stdout.write(self.style.WARNING(f'Updated permission: {perm.codename}'))
                elif created:
                    self.stdout.write(self.style.SUCCESS(f'Created permission: {perm.codename}'))
                
                permissions_map[perm.codename] = perm
        
        return permissions_map

    def _init_roles(self, permissions_map, force):
        """Initialize default roles with permissions."""
        for role_data in DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system_role': role_data['is_system_role'],
                }
            )
            
            if not created and force:
                role.description = role_data['description']
                role.is_system_role = role_data['is_system_role']
                role.save()
                self.stdout.write(self.style.WARNING(f'Updated role: {role.name}'))
            elif created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role.name}'))
            
            # Assign permissions
            perms_to_add = []
            for codename in role_data['permissions']:
                if codename in permissions_map:
                    perms_to_add.append(permissions_map[codename])
            
            if force:
                role.permissions.clear()
                self.stdout.write(self.style.WARNING(f'Cleared permissions for role: {role.name}'))
            
            if perms_to_add:
                role.permissions.add(*perms_to_add)
                self.stdout.write(self.style.SUCCESS(f'Added {len(perms_to_add)} permissions to role: {role.name}')) 