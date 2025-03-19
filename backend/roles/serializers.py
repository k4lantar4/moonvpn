from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PermissionGroup, Permission, Role, UserRole, RoleChangeLog, RoleLog

User = get_user_model()


class PermissionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionGroup
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for the Permission model."""
    
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name']
        read_only_fields = ['id']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""
    
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='permissions'
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new role with permissions."""
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        
        if permissions:
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        """Update a role with permissions."""
        permissions = validated_data.pop('permissions', None)
        
        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permissions is not None:
            old_permissions = set(instance.permissions.all())
            new_permissions = set(permissions)
            
            # Log changes to permissions
            added = new_permissions - old_permissions
            removed = old_permissions - new_permissions
            
            if added or removed:
                # Set the new permissions
                instance.permissions.set(permissions)
                
                # Log the changes
                request = self.context.get('request')
                user = request.user if request else None
                
                if added:
                    RoleLog.objects.create(
                        role=instance,
                        action='permissions_added',
                        user=user,
                        details=f"Added permissions: {', '.join(p.codename for p in added)}"
                    )
                
                if removed:
                    RoleLog.objects.create(
                        role=instance,
                        action='permissions_removed',
                        user=user,
                        details=f"Removed permissions: {', '.join(p.codename for p in removed)}"
                    )
        
        return instance


class RoleDetailSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permissions_count = serializers.IntegerField(source='permissions.count', read_only=True)
    users_count = serializers.IntegerField(source='user_roles.count', read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions', 'permissions_count',
            'users_count', 'is_system_role', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system_role', 'created_at', 'updated_at']


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'permission_ids', 'is_active'
        ]
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        # Add permissions
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        # Log role creation
        user = self.context.get('request').user
        RoleChangeLog.objects.create(
            action='create',
            role=role,
            performed_by=user,
            details={'permissions': [p.id for p in role.permissions.all()]}
        )
        
        return role
    
    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update role attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
        
        # Log role update
        user = self.context.get('request').user
        RoleChangeLog.objects.create(
            action='update',
            role=instance,
            performed_by=user,
            details={'permissions': [p.id for p in instance.permissions.all()]}
        )
        
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for the UserRole model."""
    
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        source='role'
    )
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    username = serializers.CharField(source='user.username', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'username', 'role', 'role_id', 
            'assigned_by', 'assigned_by_username', 'assigned_at', 
            'expires_at', 'is_active', 'notes'
        ]
        read_only_fields = ['id', 'assigned_at']
    
    def create(self, validated_data):
        """Create a new user role."""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and not validated_data.get('assigned_by'):
            validated_data['assigned_by'] = request.user
        
        return super().create(validated_data)


class UserRoleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'expires_at', 'is_active', 'notes']
    
    def create(self, validated_data):
        # Set the assigned_by field to the current user
        user = self.context.get('request').user
        validated_data['assigned_by'] = user
        
        user_role = UserRole.objects.create(**validated_data)
        
        # Log role assignment
        RoleChangeLog.objects.create(
            action='assign',
            role=user_role.role,
            user=user_role.user,
            performed_by=user,
            details={
                'expires_at': user_role.expires_at.isoformat() if user_role.expires_at else None,
                'is_active': user_role.is_active,
                'notes': user_role.notes
            }
        )
        
        return user_role
    
    def update(self, instance, validated_data):
        # Update user role attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Log role update
        user = self.context.get('request').user
        RoleChangeLog.objects.create(
            action='update',
            role=instance.role,
            user=instance.user,
            performed_by=user,
            details={
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'is_active': instance.is_active,
                'notes': instance.notes
            }
        )
        
        return instance


class RoleChangeLogSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True, allow_null=True)
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = RoleChangeLog
        fields = [
            'id', 'action', 'action_display', 'role', 'role_name', 'user', 'user_username',
            'performed_by', 'performed_by_username', 'timestamp', 'details'
        ]
        read_only_fields = fields 


class RoleLogSerializer(serializers.ModelSerializer):
    """Serializer for the RoleLog model."""
    
    role_name = serializers.CharField(source='role.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = RoleLog
        fields = ['id', 'role', 'role_name', 'action', 'user', 'username', 'timestamp', 'details']
        read_only_fields = ['id', 'timestamp']


class UserRoleAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning roles to users in bulk."""
    
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    user_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all()),
        min_length=1
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=255)
    
    def create(self, validated_data):
        """Assign a role to multiple users."""
        role = validated_data.get('role_id')
        users = validated_data.get('user_ids')
        expires_at = validated_data.get('expires_at')
        notes = validated_data.get('notes', '')
        
        request = self.context.get('request')
        assigned_by = request.user if request and hasattr(request, 'user') else None
        
        user_roles = []
        for user in users:
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
            user_roles.append(user_role)
        
        return {'user_roles': user_roles, 'count': len(user_roles)} 