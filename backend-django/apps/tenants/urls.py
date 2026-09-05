from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantMembershipViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'organizations', TenantViewSet, basename='tenant')
router.register(r'memberships', TenantMembershipViewSet, basename='membership')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
