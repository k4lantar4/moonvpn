from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from roles.models import Role, Permission

User = get_user_model()

DEFAULT_ROLES = [
    {
        'name': 'admin',
        'description': 'Administrator with full access',
        'permissions': [
            'manage_users',
            'manage_roles',
            'manage_permissions',
            'manage_vpn_accounts',
            'view_logs',
            'manage_settings',
            'manage_payments',
            'view_statistics',
        ]
    },
    {
        'name': 'manager',
        'description': 'Manager with access to user management and VPN accounts',
        'permissions': [
            'manage_users',
            'manage_vpn_accounts',
            'view_logs',
            'view_statistics',
        ]
    },
    {
        'name': 'support',
        'description': 'Support staff with limited access',
        'permissions': [
            'view_users',
            'view_vpn_accounts',
            'view_logs',
        ]
    },
    {
        'name': 'user',
        'description': 'Regular user with access to own VPN accounts',
        'permissions': [
            'view_own_vpn_accounts',
            'manage_own_vpn_accounts',
        ]
    },
]

DEFAULT_PERMISSIONS = [
    # User management
    {'codename': 'view_users', 'name': 'Can view users'},
    {'codename': 'manage_users', 'name': 'Can manage users'},
    
    # Role management
    {'codename': 'view_roles', 'name': 'Can view roles'},
    {'codename': 'manage_roles', 'name': 'Can manage roles'},
    
    # Permission management
    {'codename': 'view_permissions', 'name': 'Can view permissions'},
    {'codename': 'manage_permissions', 'name': 'Can manage permissions'},
    
    # VPN account management
    {'codename': 'view_vpn_accounts', 'name': 'Can view all VPN accounts'},
    {'codename': 'manage_vpn_accounts', 'name': 'Can manage all VPN accounts'},
    {'codename': 'view_own_vpn_accounts', 'name': 'Can view own VPN accounts'},
    {'codename': 'manage_own_vpn_accounts', 'name': 'Can manage own VPN accounts'},
    
    # Logs
    {'codename': 'view_logs', 'name': 'Can view logs'},
    
    # Settings
    {'codename': 'manage_settings', 'name': 'Can manage system settings'},
    
    # Payments
    {'codename': 'manage_payments', 'name': 'Can manage payments'},
    {'codename': 'view_payments', 'name': 'Can view payments'},
    
    # Statistics
    {'codename': 'view_statistics', 'name': 'Can view statistics'},
]


class Command(BaseCommand):
    help = 'Creates default roles and permissions for the application'
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Creating default permissions...')
        
        # Create default permissions
        created_permissions = 0
        for perm_data in DEFAULT_PERMISSIONS:
            perm, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults={'name': perm_data['name']}
            )
            if created:
                created_permissions += 1
        
        self.stdout.write(f'Created {created_permissions} new permissions')
        
        # Create default roles
        self.stdout.write('Creating default roles...')
        created_roles = 0
        
        for role_data in DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            
            if created:
                created_roles += 1
            
            # Add permissions to role
            for perm_codename in role_data['permissions']:
                try:
                    perm = Permission.objects.get(codename=perm_codename)
                    role.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'Permission {perm_codename} does not exist'
                    ))
        
        self.stdout.write(f'Created {created_roles} new roles')
        
        # Assign admin role to superusers
        admin_role = Role.objects.get(name='admin')
        superusers = User.objects.filter(is_superuser=True)
        
        for user in superusers:
            from roles.utils import assign_role_to_user
            user_role, created = assign_role_to_user(user, 'admin')
            if created:
                self.stdout.write(f'Assigned admin role to superuser {user.username}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created default roles and permissions')) 