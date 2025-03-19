from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PermissionViewSet, RoleViewSet, UserRoleViewSet, RoleLogViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'permissions', PermissionViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'user-roles', UserRoleViewSet)
router.register(r'logs', RoleLogViewSet)

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
] 