"""
Panel configuration views for MoonVPN API v1.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
import requests

from main.models import PanelConfig
from main.serializers import PanelConfigSerializer
from v2ray.sync_manager import ThreeXUI_Connector

class PanelConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for managing 3x-UI panel configurations."""
    
    queryset = PanelConfig.objects.all()
    serializer_class = PanelConfigSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def check_connection(self, request, pk=None):
        """Test connection to the panel."""
        panel = self.get_object()
        
        try:
            connector = ThreeXUI_Connector(
                panel_url=panel.panel_url,
                username=panel.username,
                password=panel.password
            )
            
            if connector.authenticate():
                status_data = connector.get_server_status()
                if status_data:
                    panel.last_check = timezone.now()
                    panel.save()
                    
                    return Response({
                        'status': 'success',
                        'message': 'Successfully connected to panel',
                        'data': status_data
                    })
            
            return Response({
                'status': 'error',
                'message': 'Failed to authenticate with panel'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync data from the panel."""
        panel = self.get_object()
        
        try:
            connector = ThreeXUI_Connector(
                panel_url=panel.panel_url,
                username=panel.username,
                password=panel.password
            )
            
            if not connector.authenticate():
                return Response({
                    'status': 'error',
                    'message': 'Failed to authenticate with panel'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get server status
            status_data = connector.get_server_status()
            if not status_data:
                return Response({
                    'status': 'error',
                    'message': 'Failed to get server status'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get inbounds
            inbounds = connector.get_inbounds()
            if not inbounds:
                return Response({
                    'status': 'error',
                    'message': 'Failed to get inbounds'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update last check time
            panel.last_check = timezone.now()
            panel.save()
            
            return Response({
                'status': 'success',
                'message': 'Successfully synced panel data',
                'data': {
                    'server_status': status_data,
                    'inbounds_count': len(inbounds)
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle panel active status."""
        panel = self.get_object()
        panel.is_active = not panel.is_active
        panel.save()
        
        return Response({
            'status': 'success',
            'message': f"Panel {'activated' if panel.is_active else 'deactivated'} successfully",
            'is_active': panel.is_active
        })
    
    @action(detail=False, methods=['get'])
    def active_panels(self, request):
        """Get list of active panels."""
        panels = PanelConfig.objects.filter(is_active=True)
        serializer = self.get_serializer(panels, many=True)
        return Response(serializer.data) 