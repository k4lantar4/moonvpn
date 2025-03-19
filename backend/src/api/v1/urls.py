"""
API v1 URLs for MoonVPN.

This module contains the URL patterns for the v1 API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from api.v1 import views

# Create a router for viewsets
router = DefaultRouter()

# User management
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'user-activities', views.UserActivityViewSet, basename='user-activity')

# Payment management
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'vouchers', views.VoucherViewSet, basename='voucher')

# VPN management
router.register(r'servers', views.ServerViewSet, basename='server')
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'vpn-accounts', views.VPNAccountViewSet, basename='vpn-account')
router.register(r'subscription-plans', views.SubscriptionPlanViewSet, basename='subscription-plan')

# Panel management
router.register(r'panels', views.PanelConfigViewSet, basename='panel')

urlpatterns = [
    # JWT Authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # User endpoints
    path('users/me/', views.CurrentUserView.as_view(), name='current-user'),
    path('wallets/me/', views.CurrentUserWalletView.as_view(), name='current-user-wallet'),
    path('vpn-accounts/me/', views.CurrentUserVPNAccountsView.as_view(), name='current-user-vpn-accounts'),
    path('orders/me/', views.CurrentUserOrdersView.as_view(), name='current-user-orders'),
    
    # VPN account management
    path('vpn-accounts/<int:pk>/renew/', views.RenewVPNAccountView.as_view(), name='vpn-account-renew'),
    path('vpn-accounts/<int:pk>/reset-traffic/', views.ResetVPNAccountTrafficView.as_view(), name='vpn-account-reset-traffic'),
    path('vpn-accounts/<int:pk>/change-server/', views.ChangeVPNAccountServerView.as_view(), name='vpn-account-change-server'),
    
    # Server management
    path('servers/<int:server_id>/health/', views.ServerHealthCheckView.as_view(), name='server-health'),
    path('servers/<int:server_id>/sync/', views.ServerSyncView.as_view(), name='server-sync'),
] 