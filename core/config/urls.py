"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from api.views import monitoring_dashboard, health_check
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Swagger documentation settings
schema_view = get_schema_view(
    openapi.Info(
        title="moonvpn Bot API",
        default_version='v1',
        description="API documentation for moonvpn Bot",
        terms_of_service="https://www.moonvpn.com/terms/",
        contact=openapi.Contact(email="contact@moonvpn.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('main.urls')),
    path('api/v1/auth/', include('main.urls')),
    path('api/v1/services/', include('main.urls')),
    path('api/v1/payments/', include('payments.urls')),
    
    # MoonVPN API endpoints
    path('api/', include('api.urls')),
    
    # VPN API
    path('api/vpn/', include('vpn.api.urls')),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Authentication
    path('accounts/', include('allauth.urls')),
    
    # API documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Add monitoring dashboard
    path('admin/monitoring/', monitoring_dashboard, name='monitoring_dashboard'),

    # Add health check endpoint
    path('health-check/', health_check, name='health_check'),

    # Frontend (catch-all)
    # path('', include('frontend.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
