from rest_framework import viewsets, permissions
from .models import Tenant, TenantMembership, AuditLog
from .serializers import TenantSerializer, TenantMembershipSerializer, AuditLogSerializer

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = 'slug'

class TenantMembershipViewSet(viewsets.ModelViewSet):
    queryset = TenantMembership.objects.select_related('user', 'tenant').all()
    serializer_class = TenantMembershipSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        return qs

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('actor', 'tenant').all()
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs
