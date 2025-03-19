"""
Serializers for VPN module
"""

from rest_framework import serializers
from .models import Server, Client, ServerStatus, ServerMetrics, Plan, Subscription, Transaction

class ServerSerializer(serializers.ModelSerializer):
    """Serializer for Server model"""
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'ip_address', 'port', 'location',
            'is_active', 'max_clients', 'created_at', 'updated_at'
        ]

class ServerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Server model"""
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'ip_address', 'port', 'username',
            'password', 'location', 'panel_path', 'is_active',
            'max_clients', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'username': {'write_only': True},
            'password': {'write_only': True}
        }

class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    server = ServerSerializer(read_only=True)
    server_id = serializers.PrimaryKeyRelatedField(
        queryset=Server.objects.all(),
        source='server',
        write_only=True
    )
    
    class Meta:
        model = Client
        fields = [
            'id', 'server', 'server_id', 'email', 'uuid',
            'traffic_limit', 'used_traffic', 'expire_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'used_traffic']

class ClientDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Client model"""
    server = ServerDetailSerializer(read_only=True)
    server_id = serializers.PrimaryKeyRelatedField(
        queryset=Server.objects.all(),
        source='server',
        write_only=True
    )
    traffic_limit_gb = serializers.FloatField(read_only=True)
    used_traffic_gb = serializers.FloatField(read_only=True)
    remaining_traffic_gb = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'server', 'server_id', 'email', 'uuid',
            'traffic_limit', 'used_traffic', 'expire_date',
            'is_active', 'created_at', 'updated_at',
            'traffic_limit_gb', 'used_traffic_gb',
            'remaining_traffic_gb'
        ]
        read_only_fields = ['uuid', 'used_traffic']

class ServerStatusSerializer(serializers.ModelSerializer):
    """Serializer for ServerStatus model"""
    server = ServerSerializer(read_only=True)
    
    class Meta:
        model = ServerStatus
        fields = [
            'id', 'server', 'cpu_usage', 'memory_usage',
            'disk_usage', 'network_in', 'network_out',
            'timestamp'
        ]

class ServerMetricsSerializer(serializers.ModelSerializer):
    """Serializer for ServerMetrics model"""
    server = ServerSerializer(read_only=True)
    
    class Meta:
        model = ServerMetrics
        fields = [
            'id', 'server', 'cpu_usage', 'memory_usage',
            'disk_usage', 'active_users', 'total_traffic',
            'timestamp'
        ]

class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model"""
    servers = ServerSerializer(many=True, read_only=True)
    server_ids = serializers.PrimaryKeyRelatedField(
        queryset=Server.objects.all(),
        source='servers',
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'duration_type',
            'duration_days', 'traffic_limit', 'price',
            'max_connections', 'status', 'features',
            'servers', 'server_ids', 'created_at', 'updated_at'
        ]

class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""
    user = serializers.StringRelatedField(read_only=True)
    plan = PlanSerializer(read_only=True)
    client = ClientSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'client', 'status',
            'start_date', 'end_date', 'last_renewal',
            'auto_renew', 'notes', 'created_at', 'updated_at'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    user = serializers.StringRelatedField(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'subscription', 'transaction_type',
            'status', 'amount', 'payment_method', 'payment_id',
            'notes', 'created_at', 'updated_at'
        ] 