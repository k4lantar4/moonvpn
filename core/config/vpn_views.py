"""
VPN-related views for MoonVPN API v1.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone

from vpn.models import Server, Client
from main.models import SubscriptionPlan
from vpn.serializers import (
    ServerSerializer, ServerDetailSerializer,
    ClientSerializer, ClientDetailSerializer
)
from main.serializers import SubscriptionPlanSerializer
from vpn.services import VPNService

class ServerViewSet(viewsets.ModelViewSet):
    """API endpoint for managing VPN servers."""
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ServerDetailSerializer
        return ServerSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all servers
        if user.is_superuser:
            return Server.objects.all()
            
        # Staff users can see all active servers
        if user.is_staff:
            return Server.objects.filter(is_active=True)
            
        # Regular users can only see servers they have accounts on
        return Server.objects.filter(
            is_active=True,
            client__user=user,
            client__is_active=True
        ).distinct()

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing server locations."""
    queryset = Server.objects.values('location').distinct()
    serializer_class = ServerSerializer
    permission_classes = [permissions.IsAuthenticated]

class VPNAccountViewSet(viewsets.ModelViewSet):
    """API endpoint for managing VPN accounts."""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'config']:
            return ClientDetailSerializer
        return ClientSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all accounts
        if user.is_superuser:
            return Client.objects.all()
            
        # Staff users can see all accounts
        if user.is_staff:
            return Client.objects.all()
            
        # Regular users can only see their own accounts
        return Client.objects.filter(user=user)

    def perform_create(self, serializer):
        """Set user when creating account."""
        if not self.request.user.is_staff and 'user' not in serializer.validated_data:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for managing subscription plans."""
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAdminUser]

class ServerHealthCheckView(APIView):
    """API endpoint for checking server health."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, server_id):
        """Check server health."""
        vpn_service = VPNService()
        result = vpn_service.check_server_health(server_id)
        return Response(result)

class ServerSyncView(APIView):
    """API endpoint for syncing server data."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, server_id):
        """Sync server data."""
        vpn_service = VPNService()
        result = vpn_service.sync_server(server_id)
        return Response(result)

class RenewVPNAccountView(APIView):
    """API endpoint for renewing VPN accounts."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, account_id):
        """Renew VPN account."""
        vpn_service = VPNService()
        result = vpn_service.renew_account(account_id)
        return Response(result)

class ResetVPNAccountTrafficView(APIView):
    """API endpoint for resetting VPN account traffic."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, account_id):
        """Reset VPN account traffic."""
        vpn_service = VPNService()
        result = vpn_service.reset_account_traffic(account_id)
        return Response(result)

class ChangeVPNAccountServerView(APIView):
    """API endpoint for changing VPN account server."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, account_id):
        """Change VPN account server."""
        vpn_service = VPNService()
        result = vpn_service.change_account_server(account_id, request.data.get('server_id'))
        return Response(result)

class CurrentUserVPNAccountsView(APIView):
    """API endpoint for getting current user's VPN accounts."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user's VPN accounts."""
        accounts = Client.objects.filter(user=request.user)
        serializer = ClientSerializer(accounts, many=True)
        return Response(serializer.data) 