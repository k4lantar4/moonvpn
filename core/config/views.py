from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from .models import SystemSettings
from .serializers import SystemSettingsSerializer
from .permissions import IsAdminUser

class SystemSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing system settings"""
    
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        # Only return the first instance since we only want one settings object
        return SystemSettings.objects.all()[:1]
    
    def create(self, request, *args, **kwargs):
        # Only allow one instance
        if SystemSettings.objects.exists():
            return Response(
                {'detail': 'System settings already exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current system settings"""
        settings = SystemSettings.get_settings()
        if not settings:
            return Response(
                {'detail': 'System settings not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Clear cache after updating
        cache.delete('system_settings') 