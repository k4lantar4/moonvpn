"""
Serializers for V2Ray management.

This module contains serializers for:
- Server monitoring data
- Health status
- Statistics
"""

from rest_framework import serializers
from main.models import ServerMonitor
from .models import V2RayServer, V2RayInbound, V2RayTraffic

class ServerMonitorSerializer(serializers.ModelSerializer):
    """Serializer for server monitoring data."""
    network_usage_gb = serializers.SerializerMethodField()
    network_speed_mbps = serializers.SerializerMethodField()
    io_speed_mbps = serializers.SerializerMethodField()
    uptime_days = serializers.SerializerMethodField()
    
    class Meta:
        model = ServerMonitor
        fields = [
            'id', 'server', 'health_status', 'cpu_usage', 'memory_usage',
            'disk_usage', 'uptime_seconds', 'active_connections',
            'network_in', 'network_out', 'network_speed_in', 'network_speed_out',
            'load_average_1min', 'load_average_5min', 'load_average_15min',
            'swap_usage', 'io_read', 'io_write', 'io_speed_read', 'io_speed_write',
            'timestamp', 'network_usage_gb', 'network_speed_mbps',
            'io_speed_mbps', 'uptime_days'
        ]
        read_only_fields = fields
    
    def get_network_usage_gb(self, obj):
        return obj.get_network_usage_gb()
    
    def get_network_speed_mbps(self, obj):
        return obj.get_network_speed_mbps()
    
    def get_io_speed_mbps(self, obj):
        return obj.get_io_speed_mbps()
    
    def get_uptime_days(self, obj):
        return obj.get_uptime_days()

class ServerHealthSerializer(serializers.ModelSerializer):
    """Serializer for server health status."""
    network_usage_gb = serializers.SerializerMethodField()
    network_speed_mbps = serializers.SerializerMethodField()
    io_speed_mbps = serializers.SerializerMethodField()
    uptime_days = serializers.SerializerMethodField()
    
    class Meta:
        model = ServerMonitor
        fields = [
            'id', 'server', 'health_status', 'cpu_usage', 'memory_usage',
            'disk_usage', 'uptime_seconds', 'active_connections',
            'network_usage_gb', 'network_speed_mbps', 'io_speed_mbps',
            'uptime_days', 'timestamp'
        ]
        read_only_fields = fields
    
    def get_network_usage_gb(self, obj):
        return obj.get_network_usage_gb()
    
    def get_network_speed_mbps(self, obj):
        return obj.get_network_speed_mbps()
    
    def get_io_speed_mbps(self, obj):
        return obj.get_io_speed_mbps()
    
    def get_uptime_days(self, obj):
        return obj.get_uptime_days()

class ServerStatsSerializer(serializers.Serializer):
    """Serializer for server statistics."""
    cpu = serializers.DictField()
    memory = serializers.DictField()
    disk = serializers.DictField()
    network = serializers.DictField()
    io = serializers.DictField()
    connections = serializers.DictField()
    load = serializers.DictField()

class V2RayServerSerializer(serializers.ModelSerializer):
    """Serializer for V2Ray server model."""
    
    load_percentage = serializers.FloatField(read_only=True)
    total_traffic = serializers.SerializerMethodField()
    health_status = serializers.SerializerMethodField()
    
    class Meta:
        model = V2RayServer
        fields = [
            'id', 'name', 'host', 'port', 'is_active',
            'max_users', 'current_users', 'load_percentage',
            'last_check', 'is_healthy', 'health_check_failures',
            'total_upload', 'total_download', 'total_traffic',
            'health_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_upload', 'total_download', 'health_check_failures',
            'last_check', 'is_healthy'
        ]
    
    def get_total_traffic(self, obj):
        """Calculate total traffic (upload + download)."""
        return obj.total_upload + obj.total_download
    
    def get_health_status(self, obj):
        """Get server health status."""
        if not obj.is_active:
            return "inactive"
        if not obj.is_healthy:
            return "unhealthy"
        if obj.health_check_failures > 0:
            return "warning"
        return "healthy"

class V2RayInboundSerializer(serializers.ModelSerializer):
    """Serializer for V2Ray inbound model."""
    
    server_name = serializers.CharField(source='server.name', read_only=True)
    
    class Meta:
        model = V2RayInbound
        fields = [
            'id', 'server', 'server_name', 'inbound_id', 'tag',
            'protocol', 'port', 'settings', 'stream_settings',
            'sniffing_enabled', 'sniffing_dest_override',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['server', 'inbound_id']

class V2RayTrafficSerializer(serializers.ModelSerializer):
    """Serializer for V2Ray traffic model."""
    
    server_name = serializers.CharField(source='server.name', read_only=True)
    inbound_tag = serializers.CharField(source='inbound.tag', read_only=True)
    total_traffic = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = V2RayTraffic
        fields = [
            'id', 'user', 'server', 'server_name', 'inbound',
            'inbound_tag', 'upload', 'download', 'total_traffic',
            'recorded_at'
        ]
        read_only_fields = ['user', 'server', 'inbound']

class V2RayTrafficStatsSerializer(serializers.Serializer):
    """Serializer for traffic statistics."""
    
    server_id = serializers.IntegerField()
    server_name = serializers.CharField()
    total_upload = serializers.IntegerField()
    total_download = serializers.IntegerField()
    total_traffic = serializers.IntegerField()
    client_count = serializers.IntegerField()
    inbound_count = serializers.IntegerField()
    last_updated = serializers.DateTimeField()

class V2RayServerHealthSerializer(serializers.Serializer):
    """Serializer for server health data."""
    
    server_id = serializers.IntegerField()
    server_name = serializers.CharField()
    status = serializers.CharField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    load_percentage = serializers.FloatField()
    uptime = serializers.IntegerField()
    last_check = serializers.DateTimeField()
    error_message = serializers.CharField(allow_blank=True) 