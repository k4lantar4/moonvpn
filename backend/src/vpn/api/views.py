"""
API views for VPN module
"""

import logging
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.conf import settings

from vpn.models import Server, Client, ServerMetrics, Plan, Subscription, Transaction
from vpn.api.serializers import (
    ServerSerializer, ServerDetailSerializer,
    ClientSerializer, ClientDetailSerializer,
    ServerMetricsSerializer,
    PlanSerializer,
    SubscriptionSerializer,
    TransactionSerializer,
    CreateSubscriptionSerializer
)
from vpn.tasks import (
    sync_server, add_user_to_server, remove_user_from_server,
    move_user, check_expired_accounts, check_traffic_limits
)
from vpn.factory import VPNConnectorFactory
from vpn.manager import VPNManager
from vpn.services.subscription_manager import SubscriptionManager
from vpn.services.payment_manager import PaymentManager

logger = logging.getLogger(__name__)


class ServerViewSet(viewsets.ModelViewSet):
    """API endpoint for VPN servers"""
    
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow any access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'is_active', 'location', 'country']
    search_fields = ['name', 'host', 'location', 'country']
    ordering_fields = ['name', 'location', 'cpu_usage', 'memory_usage', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return ServerDetailSerializer
        return ServerSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
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
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync a server"""
        server = self.get_object()
        
        # Schedule sync task
        sync_server.delay(server.id)
        
        return Response({'status': 'sync scheduled'})
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get server metrics"""
        server = self.get_object()
        
        # Get metrics from database
        metrics = ServerMetrics.objects.filter(server=server).order_by('-timestamp')[:24]
        serializer = ServerMetricsSerializer(metrics, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get real-time server status"""
        server = self.get_object()
        
        try:
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(server)
            
            # Authenticate with the server
            if not connector.authenticate():
                return Response(
                    {'error': 'Failed to authenticate with server'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            # Get server status
            server_status = connector.get_server_status()
            
            # Get online users
            online_users = connector.get_online_users()
            
            # Prepare response
            response = {
                'server_id': server.id,
                'server_name': server.name,
                'status': 'online' if server_status.get('xray_state') == 'running' else 'error',
                'cpu_usage': server_status.get('cpu', 0),
                'memory_usage': server_status.get('mem', 0),
                'disk_usage': server_status.get('disk', 0),
                'xray_state': server_status.get('xray_state', 'unknown'),
                'xray_version': server_status.get('xray_version', 'unknown'),
                'online_users_count': len(online_users) if online_users else 0,
                'online_users': online_users if online_users else [],
                'timestamp': timezone.now().isoformat()
            }
            
            return Response(response)
            
        except Exception as e:
            logger.exception(f"Error getting server status: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def protocols(self, request):
        """Get list of supported protocols"""
        from vpn.base import VPNProtocolRegistry
        
        protocols = VPNProtocolRegistry.list_protocols()
        
        # Get protocol info for each protocol
        protocol_info = {}
        for protocol_id in protocols:
            try:
                protocol_class = VPNProtocolRegistry.get_protocol(protocol_id)
                if protocol_class:
                    protocol = protocol_class()
                    protocol_info[protocol_id] = protocol.get_protocol_info()
            except Exception as e:
                logger.exception(f"Error getting protocol info for {protocol_id}: {str(e)}")
                protocol_info[protocol_id] = {'id': protocol_id, 'error': str(e)}
        
        return Response(protocol_info)
    
    @action(detail=False, methods=['get'])
    def best_server(self, request):
        """Get best server based on load and filters"""
        # Get filter parameters
        location = request.query_params.get('location')
        protocol = request.query_params.get('protocol')
        min_uptime = request.query_params.get('min_uptime')
        
        if min_uptime:
            try:
                min_uptime = int(min_uptime)
            except ValueError:
                min_uptime = None
        
        # Get best server
        manager = VPNManager()
        best_server_id = manager.get_best_server(
            location=location,
            protocol=protocol,
            min_uptime=min_uptime
        )
        
        if best_server_id:
            server = Server.objects.get(id=best_server_id)
            serializer = self.get_serializer(server)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No suitable server found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClientViewSet(viewsets.ModelViewSet):
    """API endpoint for VPN clients"""
    
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow any access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'protocol', 'server']
    search_fields = ['email', 'server__name']
    ordering_fields = ['created_at', 'expiry_date', 'total_traffic']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action in ['retrieve', 'config']:
            return ClientDetailSerializer
        return ClientSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
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
        """Set user when creating account"""
        # If no user specified and not admin, use current user
        if not self.request.user.is_staff and 'user' not in serializer.validated_data:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['get'])
    def config(self, request, pk=None):
        """Get VPN configuration for an account"""
        account = self.get_object()
        
        # Check if user has permission to access this account
        if not request.user.is_staff and account.user != request.user:
            return Response(
                {'error': 'You do not have permission to access this account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ClientDetailSerializer(account)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_traffic(self, request, pk=None):
        """Reset traffic counters for an account"""
        account = self.get_object()
        
        # Check if user has permission to reset traffic
        if not request.user.is_staff and account.user != request.user:
            return Response(
                {'error': 'You do not have permission to reset traffic for this account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(account.server)
            
            # Authenticate with the server
            if not connector.authenticate():
                return Response(
                    {'error': 'Failed to authenticate with server'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            # Reset traffic
            success = connector.reset_user_traffic(account.email)
            
            if success:
                # Update account in database
                account.upload = 0
                account.download = 0
                account.total_traffic = 0
                account.last_sync = timezone.now()
                account.save(update_fields=['upload', 'download', 'total_traffic', 'last_sync'])
                
                return Response({'status': 'traffic reset successfully'})
            else:
                return Response(
                    {'error': 'Failed to reset traffic on server'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.exception(f"Error resetting traffic: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """Extend account expiry"""
        account = self.get_object()
        
        # Check if user has permission to extend account
        if not request.user.is_staff and account.user != request.user:
            return Response(
                {'error': 'You do not have permission to extend this account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get days to extend
        days = request.data.get('days', 30)
        try:
            days = int(days)
            if days <= 0:
                return Response(
                    {'error': 'Days must be a positive integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Days must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update expiry date
            if account.expiry_date:
                account.expiry_date = account.expiry_date + timezone.timedelta(days=days)
            else:
                account.expiry_date = timezone.now() + timezone.timedelta(days=days)
                
            # Update account on server
            connector = VPNConnectorFactory.create_connector(account.server)
            
            # Authenticate with the server
            if not connector.authenticate():
                return Response(
                    {'error': 'Failed to authenticate with server'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
            # Update user on server
            success = connector.update_user(
                account.email,
                expire_days=account.get_remaining_days()
            )
            
            if success:
                # Save account in database
                account.save(update_fields=['expiry_date'])
                
                return Response({
                    'status': 'account extended successfully',
                    'expiry_date': account.expiry_date.isoformat(),
                    'remaining_days': account.get_remaining_days()
                })
            else:
                return Response(
                    {'error': 'Failed to update account on server'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.exception(f"Error extending account: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move account to another server"""
        account = self.get_object()
        
        # Check if user has permission to move account
        if not request.user.is_staff and account.user != request.user:
            return Response(
                {'error': 'You do not have permission to move this account'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get target server
        target_server_id = request.data.get('server_id')
        if not target_server_id:
            return Response(
                {'error': 'Target server ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            target_server = Server.objects.get(id=target_server_id, is_active=True)
        except Server.DoesNotExist:
            return Response(
                {'error': 'Target server not found or not active'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if target server is different from current server
        if account.server.id == target_server.id:
            return Response(
                {'error': 'Target server is the same as current server'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Move account
            if account.user:
                # Schedule task to move user
                task = move_user.delay(
                    account.user.id,
                    account.server.id,
                    target_server.id
                )
                
                return Response({
                    'status': 'account move scheduled',
                    'task_id': task.id
                })
            else:
                return Response(
                    {'error': 'Account has no associated user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.exception(f"Error moving account: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ServerMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for server metrics"""
    
    queryset = ServerMetrics.objects.all()
    serializer_class = ServerMetricsSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow any access for testing
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['server']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Superusers can see all metrics
        if user.is_superuser:
            return ServerMetrics.objects.all()
            
        # Staff users can see all metrics
        if user.is_staff:
            return ServerMetrics.objects.all()
            
        # Regular users can only see metrics for servers they have accounts on
        return ServerMetrics.objects.filter(
            server__is_active=True,
            server__client__user=user,
            server__client__is_active=True
        ).distinct()


class PlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing VPN plans
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Filter plans based on status and availability"""
        queryset = Plan.objects.all()
        
        # Filter by status if specified
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        # Only show active plans for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='active')
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check plan availability and server status"""
        plan = self.get_object()
        return Response({
            'is_available': plan.is_available(),
            'active_servers': plan.servers.filter(is_active=True).count(),
            'features': plan.features
        })


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing VPN subscriptions
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter subscriptions based on user and status"""
        user = self.request.user
        queryset = Subscription.objects.filter(user=user)
        
        # Filter by status if specified
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new subscription"""
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        plan = serializer.validated_data['plan']
        payment_method = serializer.validated_data['payment_method']
        auto_renew = serializer.validated_data.get('auto_renew', False)
        
        # Create subscription
        subscription, error = SubscriptionManager.create_subscription(
            user=request.user,
            plan=plan,
            payment_method=payment_method,
            auto_renew=auto_renew
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew an existing subscription"""
        subscription = self.get_object()
        payment_method = request.data.get('payment_method')
        
        if not payment_method:
            return Response(
                {'error': 'Payment method is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, error = SubscriptionManager.renew_subscription(
            subscription=subscription,
            payment_method=payment_method
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription"""
        subscription = self.get_object()
        reason = request.data.get('reason', '')
        
        success, error = SubscriptionManager.cancel_subscription(
            subscription=subscription,
            reason=reason
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a subscription"""
        subscription = self.get_object()
        reason = request.data.get('reason', '')
        
        success, error = SubscriptionManager.suspend_subscription(
            subscription=subscription,
            reason=reason
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a suspended subscription"""
        subscription = self.get_object()
        
        success, error = SubscriptionManager.reactivate_subscription(
            subscription=subscription
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(SubscriptionSerializer(subscription).data)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get detailed subscription status"""
        subscription = self.get_object()
        status_data = SubscriptionManager.get_subscription_status(subscription)
        return Response(status_data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing transaction history
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter transactions based on user"""
        return Transaction.objects.filter(user=self.request.user)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def payment_callback(request):
    """Handle payment gateway callbacks"""
    payment_id = request.GET.get('Authority') or request.POST.get('Authority')
    status = request.GET.get('Status') or request.POST.get('Status')
    
    if not payment_id:
        return Response({'error': 'Payment ID not provided'}, status=400)
    
    # Verify payment
    transaction, error = PaymentManager.verify_payment(
        payment_id=payment_id,
        payment_method='zarinpal'  # Currently only supporting ZarinPal
    )
    
    if error:
        return Response({'error': error}, status=400)
    
    # Redirect to frontend with status
    redirect_url = settings.PAYMENT_SUCCESS_URL if transaction else settings.PAYMENT_FAILURE_URL
    return HttpResponseRedirect(f"{redirect_url}?payment_id={payment_id}") 