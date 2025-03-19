"""
API serializers for VPN module
"""

from rest_framework import serializers
from vpn.models import Server, Client, ServerMetrics, Plan, Subscription, Transaction


class ServerSerializer(serializers.ModelSerializer):
    """Serializer for Server model"""
    
    active_users_count = serializers.SerializerMethodField()
    total_traffic_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'description', 'type', 'host', 'location', 'country',
            'country_code', 'protocols', 'default_protocol', 'status', 'is_active',
            'cpu_usage', 'memory_usage', 'disk_usage', 'active_users_count',
            'total_traffic_gb', 'last_sync', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'active_users_count',
            'total_traffic_gb', 'last_sync', 'created_at', 'updated_at'
        ]
    
    def get_active_users_count(self, obj):
        """Get count of active users on this server"""
        return obj.get_active_users_count()
    
    def get_total_traffic_gb(self, obj):
        """Get total traffic used on this server in GB"""
        total_bytes = obj.get_total_traffic()
        return round(total_bytes / (1024 * 1024 * 1024), 2)


class ServerDetailSerializer(ServerSerializer):
    """Detailed serializer for Server model"""
    
    class Meta(ServerSerializer.Meta):
        fields = ServerSerializer.Meta.fields + ['url', 'bandwidth_limit', 'config']
        read_only_fields = ServerSerializer.Meta.read_only_fields
        extra_kwargs = {
            'url': {'write_only': True},
            'username': {'write_only': True},
            'password': {'write_only': True},
            'config': {'write_only': True}
        }


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    
    server_name = serializers.CharField(source='server.name', read_only=True)
    server_location = serializers.CharField(source='server.location', read_only=True)
    traffic_used_gb = serializers.SerializerMethodField()
    traffic_limit_gb = serializers.SerializerMethodField()
    traffic_percentage = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_traffic_exceeded = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'user', 'server', 'server_name', 'server_location', 'email',
            'protocol', 'uuid', 'is_active', 'upload', 'download', 'total_traffic',
            'traffic_limit', 'traffic_used_gb', 'traffic_limit_gb', 'traffic_percentage',
            'expiry_date', 'remaining_days', 'is_expired', 'is_traffic_exceeded',
            'created_at', 'updated_at', 'last_sync'
        ]
        read_only_fields = [
            'uuid', 'upload', 'download', 'total_traffic', 'traffic_used_gb',
            'traffic_limit_gb', 'traffic_percentage', 'remaining_days', 'is_expired',
            'is_traffic_exceeded', 'created_at', 'updated_at', 'last_sync'
        ]
    
    def get_traffic_used_gb(self, obj):
        """Get traffic used in GB"""
        return obj.get_traffic_used_gb()
    
    def get_traffic_limit_gb(self, obj):
        """Get traffic limit in GB"""
        return obj.get_traffic_limit_gb()
    
    def get_traffic_percentage(self, obj):
        """Get percentage of traffic used"""
        return obj.get_traffic_percentage()
    
    def get_remaining_days(self, obj):
        """Get remaining days until expiry"""
        return obj.get_remaining_days()
    
    def get_is_expired(self, obj):
        """Check if account is expired"""
        return obj.is_expired()
    
    def get_is_traffic_exceeded(self, obj):
        """Check if traffic limit is exceeded"""
        return obj.is_traffic_exceeded()


class ClientDetailSerializer(ClientSerializer):
    """Detailed serializer for Client model"""
    
    config = serializers.SerializerMethodField()
    
    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + ['config']
    
    def get_config(self, obj):
        """Get VPN configuration for this account"""
        from vpn.factory import VPNConnectorFactory
        
        try:
            # Create connector for the server
            connector = VPNConnectorFactory.create_connector(obj.server)
            
            # Authenticate with the server
            if not connector.authenticate():
                return {'error': 'Failed to authenticate with server'}
                
            # Get user configuration
            return connector.get_user_config(obj.email)
        except Exception as e:
            return {'error': str(e)}


class ServerMetricsSerializer(serializers.ModelSerializer):
    """Serializer for ServerMetrics model"""
    
    server_name = serializers.CharField(source='server.name', read_only=True)
    total_traffic_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = ServerMetrics
        fields = [
            'id', 'server', 'server_name', 'cpu_usage', 'memory_usage', 'disk_usage',
            'active_users', 'total_traffic', 'total_traffic_gb', 'timestamp'
        ]
        read_only_fields = fields
    
    def get_total_traffic_gb(self, obj):
        """Get total traffic in GB"""
        return round(obj.total_traffic / (1024 * 1024 * 1024), 2)


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for VPN service plans"""
    traffic_limit_gb = serializers.FloatField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'duration_type',
            'duration_days', 'traffic_limit', 'traffic_limit_gb',
            'price', 'max_connections', 'status', 'features',
            'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for VPN subscriptions"""
    plan = PlanSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_renew = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status', 'start_date',
            'end_date', 'last_renewal', 'auto_renew', 'notes',
            'days_remaining', 'is_active', 'can_renew',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'plan', 'status', 'start_date', 'end_date',
            'last_renewal', 'created_at', 'updated_at'
        ]


class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating new subscriptions"""
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(status='active'))
    payment_method = serializers.CharField(max_length=50)
    auto_renew = serializers.BooleanField(default=False)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for subscription transactions"""
    subscription = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'subscription', 'transaction_type',
            'status', 'amount', 'payment_method', 'payment_id',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'subscription', 'transaction_type', 'status',
            'amount', 'payment_method', 'payment_id', 'created_at',
            'updated_at'
        ] 