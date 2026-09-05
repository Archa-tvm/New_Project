from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tenant, TenantMembership, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TenantSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'contact_email', 'plan', 'is_active', 'settings', 'members_count', 'created_at']

    def get_members_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

class TenantMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = TenantMembership
        fields = ['id', 'tenant', 'user', 'user_id', 'role', 'is_active', 'joined_at']

class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'tenant', 'actor', 'actor_username', 'action', 'resource_type', 'resource_id', 'details', 'timestamp']
