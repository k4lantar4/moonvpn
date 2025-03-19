from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from ..serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserStatsSerializer
)
from ...services.user_manager import UserManager
from ...models import User

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for managing users"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        queryset = User.objects.all()
        
        if user.is_admin:
            return queryset
        elif user.is_reseller:
            return queryset.filter(parent_reseller=user)
        else:
            return queryset.filter(id=user.id)
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user, error = UserManager.create_user(**serializer.validated_data)
        
        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def make_reseller(self, request, pk=None):
        """Convert user to reseller"""
        user = self.get_object()
        
        if not request.user.is_admin:
            return Response(
                {'error': _("Only admins can create resellers")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        commission_rate = request.data.get('commission_rate', 10)
        success, error = UserManager.create_reseller(
            user=user,
            commission_rate=commission_rate
        )
        
        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(UserSerializer(user).data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get user statistics"""
        user = self.get_object()
        stats = UserManager.get_user_stats(user)
        return Response(UserStatsSerializer(stats).data)
    
    @action(detail=True, methods=['post'])
    def update_settings(self, request, pk=None):
        """Update user settings"""
        user = self.get_object()
        
        if user != request.user and not request.user.is_admin:
            return Response(
                {'error': _("You can only update your own settings")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, error = UserManager.update_user_settings(
            user=user,
            **request.data
        )
        
        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(UserSerializer(user).data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user"""
        user = self.get_object()
        
        if user != request.user and not request.user.is_admin:
            return Response(
                {'error': _("You can only delete your own account")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success, error = UserManager.delete_user(user)
        
        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT) 