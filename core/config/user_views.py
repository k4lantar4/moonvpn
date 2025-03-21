"""
User-related views for MoonVPN API v1.
"""

from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q

from main.models import User, UserActivity
from main.serializers import (
    UserSerializer, UserDetailSerializer,
    GroupSerializer, UserActivitySerializer
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for managing users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return UserDetailSerializer
        return UserSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all users
        if user.is_superuser:
            return User.objects.all()
            
        # Staff users can see all non-superusers
        if user.is_staff:
            return User.objects.filter(is_superuser=False)
            
        # Regular users can only see themselves
        return User.objects.filter(id=user.id)

class AdminGroupViewSet(viewsets.ModelViewSet):
    """API endpoint for managing admin groups."""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing user activity."""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all activity
        if user.is_superuser:
            return UserActivity.objects.all()
            
        # Staff users can see all non-superuser activity
        if user.is_staff:
            return UserActivity.objects.filter(user__is_superuser=False)
            
        # Regular users can only see their own activity
        return UserActivity.objects.filter(user=user)

class CurrentUserView(APIView):
    """API endpoint for getting current user info."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user info."""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

class UserSettingsView(APIView):
    """API endpoint for managing user settings."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get user settings."""
        user = request.user
        settings = {
            'notifications_enabled': user.notifications_enabled,
            'language': user.language,
            'theme': user.theme,
            'timezone': user.timezone
        }
        return Response(settings)

    def patch(self, request):
        """Update user settings."""
        user = request.user
        valid_fields = ['notifications_enabled', 'language', 'theme', 'timezone']
        
        for field in valid_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        user.save()
        return Response({
            'notifications_enabled': user.notifications_enabled,
            'language': user.language,
            'theme': user.theme,
            'timezone': user.timezone
        }) 