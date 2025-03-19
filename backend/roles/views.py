from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import Role, Permission, UserRole, RoleLog
from .serializers import (
    RoleSerializer, PermissionSerializer, UserRoleSerializer,
    RoleLogSerializer, UserRoleAssignmentSerializer
)
from .permissions import HasRolePermission
from .utils import assign_role_to_user, revoke_role_from_user

User = get_user_model()


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing permissions."""
    
    queryset = Permission.objects.all().order_by('codename')
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasRolePermission('view_permissions')]
    
    def get_queryset(self):
        """Filter permissions based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by codename
        codename = self.request.query_params.get('codename', None)
        if codename:
            queryset = queryset.filter(codename__icontains=codename)
        
        # Filter by name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        return queryset


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles."""
    
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated, HasRolePermission('view_roles')]
        else:
            permission_classes = [IsAuthenticated, HasRolePermission('manage_roles')]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter roles based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get users with this role."""
        role = self.get_object()
        user_roles = UserRole.objects.filter(role=role, is_active=True)
        
        # Filter by username
        username = request.query_params.get('username', None)
        if username:
            user_roles = user_roles.filter(user__username__icontains=username)
        
        # Filter by expiration
        expired = request.query_params.get('expired', None)
        if expired == 'true':
            now = timezone.now()
            user_roles = user_roles.filter(expires_at__lt=now)
        elif expired == 'false':
            now = timezone.now()
            user_roles = user_roles.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now)
            )
        
        page = self.paginate_queryset(user_roles)
        serializer = UserRoleSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for this role."""
        role = self.get_object()
        logs = RoleLog.objects.filter(role=role).order_by('-timestamp')
        
        page = self.paginate_queryset(logs)
        serializer = RoleLogSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_permission(self, request, pk=None):
        """Add a permission to this role."""
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        
        try:
            permission = Permission.objects.get(pk=permission_id)
            role.permissions.add(permission)
            
            # Log the change
            RoleLog.objects.create(
                role=role,
                action='permission_added',
                user=request.user,
                details=f"Added permission: {permission.codename}"
            )
            
            return Response({'status': 'permission added'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_permission(self, request, pk=None):
        """Remove a permission from this role."""
        role = self.get_object()
        permission_id = request.data.get('permission_id')
        
        try:
            permission = Permission.objects.get(pk=permission_id)
            role.permissions.remove(permission)
            
            # Log the change
            RoleLog.objects.create(
                role=role,
                action='permission_removed',
                user=request.user,
                details=f"Removed permission: {permission.codename}"
            )
            
            return Response({'status': 'permission removed'})
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user roles."""
    
    queryset = UserRole.objects.all().select_related('user', 'role', 'assigned_by')
    serializer_class = UserRoleSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated, HasRolePermission('view_roles')]
        else:
            permission_classes = [IsAuthenticated, HasRolePermission('manage_roles')]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter user roles based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by role
        role_id = self.request.query_params.get('role_id', None)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by expiration
        expired = self.request.query_params.get('expired', None)
        if expired == 'true':
            now = timezone.now()
            queryset = queryset.filter(expires_at__lt=now)
        elif expired == 'false':
            now = timezone.now()
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=now)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the assigned_by field to the current user."""
        serializer.save(assigned_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def assign_bulk(self, request):
        """Assign a role to multiple users."""
        serializer = UserRoleAssignmentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response({
            'status': 'roles assigned',
            'count': result['count']
        })
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """Assign a role to a user."""
        user_id = request.data.get('user_id')
        role_name = request.data.get('role_name')
        expires_at = request.data.get('expires_at')
        notes = request.data.get('notes', '')
        
        try:
            user = User.objects.get(pk=user_id)
            user_role, created = assign_role_to_user(
                user=user,
                role_name=role_name,
                assigned_by=request.user,
                expires_at=expires_at,
                notes=notes
            )
            
            if user_role:
                serializer = UserRoleSerializer(user_role)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Role not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def revoke(self, request):
        """Revoke a role from a user."""
        user_id = request.data.get('user_id')
        role_name = request.data.get('role_name')
        
        try:
            user = User.objects.get(pk=user_id)
            success = revoke_role_from_user(user, role_name)
            
            if success:
                return Response({'status': 'role revoked'})
            else:
                return Response(
                    {'error': 'Role not found or not assigned to user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RoleLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing role logs."""
    
    queryset = RoleLog.objects.all().order_by('-timestamp')
    serializer_class = RoleLogSerializer
    permission_classes = [IsAuthenticated, HasRolePermission('view_logs')]
    
    def get_queryset(self):
        """Filter logs based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by role
        role_id = self.request.query_params.get('role_id', None)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # Filter by action
        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset 