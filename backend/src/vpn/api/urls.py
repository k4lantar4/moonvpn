"""
API URLs for VPN module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from vpn.api.views import ServerViewSet, ClientViewSet, ServerMetricsViewSet, PlanViewSet, SubscriptionViewSet, TransactionViewSet, payment_callback

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'servers', ServerViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'metrics', ServerMetricsViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'transactions', TransactionViewSet, basename='transaction')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('payment/callback/', payment_callback, name='payment-callback'),
] 