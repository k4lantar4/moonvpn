"""
Subscription-related views for MoonVPN API v1.
"""

from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from main.models import SubscriptionPlan, Subscription
from main.serializers import SubscriptionPlanSerializer, SubscriptionSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """API endpoint for managing subscription plans."""
    
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers and staff can see all plans
        if user.is_superuser or user.is_staff:
            return SubscriptionPlan.objects.all()
            
        # Regular users can only see active plans
        return SubscriptionPlan.objects.filter(is_active=True)
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class SubscriptionViewSet(viewsets.ModelViewSet):
    """API endpoint for managing subscriptions."""
    
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Superusers can see all subscriptions
        if user.is_superuser:
            return Subscription.objects.all()
            
        # Staff users can see all non-superuser subscriptions
        if user.is_staff:
            return Subscription.objects.filter(user__is_superuser=False)
            
        # Regular users can only see their own subscriptions
        return Subscription.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Create a new subscription for the current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription."""
        subscription = self.get_object()
        
        # Only allow cancelling active subscriptions
        if subscription.status != 'active':
            return Response({
                'success': False,
                'message': 'Only active subscriptions can be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update subscription status
        subscription.status = 'cancelled'
        subscription.auto_renew = False
        subscription.metadata.update({
            'cancelled_at': timezone.now().isoformat(),
            'cancelled_by': request.user.username
        })
        subscription.save()
        
        return Response({
            'success': True,
            'message': 'Subscription cancelled successfully'
        })
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a subscription."""
        subscription = self.get_object()
        
        # Only allow renewing active or expired subscriptions
        if subscription.status not in ['active', 'expired']:
            return Response({
                'success': False,
                'message': 'Only active or expired subscriptions can be renewed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate new dates based on plan duration
        now = timezone.now()
        if subscription.end_date > now:
            start_date = subscription.end_date
        else:
            start_date = now
        
        if subscription.plan.duration == 'monthly':
            end_date = start_date + timezone.timedelta(days=30)
        elif subscription.plan.duration == 'quarterly':
            end_date = start_date + timezone.timedelta(days=90)
        elif subscription.plan.duration == 'semi_annual':
            end_date = start_date + timezone.timedelta(days=180)
        else:  # annual
            end_date = start_date + timezone.timedelta(days=365)
        
        # Update subscription
        subscription.status = 'active'
        subscription.start_date = start_date
        subscription.end_date = end_date
        subscription.metadata.update({
            'renewed_at': timezone.now().isoformat(),
            'renewed_by': request.user.username
        })
        subscription.save()
        
        return Response({
            'success': True,
            'message': 'Subscription renewed successfully'
        })

class ActiveSubscriptionView(views.APIView):
    """API endpoint for getting current user's active subscription."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get current user's active subscription."""
        try:
            subscription = Subscription.objects.get(
                user=request.user,
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active subscription found'
            }, status=status.HTTP_404_NOT_FOUND) 