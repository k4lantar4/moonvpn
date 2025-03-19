from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from main.models import Server, SubscriptionPlan, Subscription, PlanSuggestion
from v2ray.models import Inbound, Client, SyncLog, ClientConfig
from payments.models import Transaction, CardPayment, ZarinpalPayment, PaymentMethod, DiscountCode as Discount
from telegrambot.models import TelegramMessage, TelegramNotification
from points.models import PointsRedemptionRule, PointsRedemption

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'telegram_id', 'phone_number', 
                  'language_code', 'is_admin', 'wallet_balance', 'date_joined', 
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class ServerSerializer(serializers.ModelSerializer):
    """
    Serializer for Server model.
    Used for managing VPN server panel entries.
    """
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'host', 'port', 'url', 'username', 'password', 
            'location', 'country_code', 'type', 'protocol', 'is_active',
            'cpu_usage', 'memory_usage', 'disk_usage', 'is_synced', 'last_sync',
            'created_at', 'updated_at', 'status'
        ]
        read_only_fields = ['id', 'is_synced', 'last_sync', 'cpu_usage', 'memory_usage', 'disk_usage', 'created_at', 'updated_at']
    
    def get_status(self, obj):
        """
        Get server status indicator
        """
        if not obj.is_active:
            return "inactive"
        
        if not obj.is_synced:
            return "not_synced"
        
        if obj.last_sync:
            # Check if last sync is within the last hour
            one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
            if obj.last_sync < one_hour_ago:
                return "sync_outdated"
        
        return "ok"
    
    def to_representation(self, instance):
        """
        Transform the output to hide sensitive information
        """
        ret = super().to_representation(instance)
        # Mask password and add sync time info
        if 'password' in ret:
            del ret['password']
        
        # Add formatted dates for readability
        if instance.last_sync:
            ret['last_sync_ago'] = self._get_time_ago(instance.last_sync)
        
        if instance.created_at:
            ret['created_at_formatted'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        return ret
    
    def _get_time_ago(self, timestamp):
        """
        Convert timestamp to 'time ago' format
        """
        if not timestamp:
            return None
            
        now = timezone.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)} minute{'s' if int(minutes) != 1 else ''} ago"
        
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)} hour{'s' if int(hours) != 1 else ''} ago"
        
        days = hours / 24
        if days < 30:
            return f"{int(days)} day{'s' if int(days) != 1 else ''} ago"
        
        months = days / 30
        if months < 12:
            return f"{int(months)} month{'s' if int(months) != 1 else ''} ago"
        
        years = days / 365
        return f"{int(years)} year{'s' if int(years) != 1 else ''} ago"


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for the SubscriptionPlan model"""
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'description', 'type', 'data_limit_gb', 
                  'duration_days', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for the Subscription model"""
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    server = ServerSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'server', 'inbound_id', 'client_email',
                  'status', 'data_usage_gb', 'data_limit_gb', 'start_date', 
                  'end_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class InboundSerializer(serializers.ModelSerializer):
    """Serializer for the Inbound model"""
    server = ServerSerializer(read_only=True)
    
    class Meta:
        model = Inbound
        fields = ['id', 'server', 'inbound_id', 'protocol', 'tag', 'port', 
                  'network', 'enable', 'expiry_time', 'listen', 'total', 
                  'remark', 'up', 'down', 'last_sync']
        read_only_fields = ['id', 'last_sync']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for the Client model"""
    inbound = InboundSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = ['id', 'inbound', 'client_id', 'email', 'enable', 'expiry_time',
                  'total', 'up', 'down', 'subscription_id', 'last_sync']
        read_only_fields = ['id', 'last_sync']


class ClientConfigSerializer(serializers.ModelSerializer):
    """Serializer for the ClientConfig model"""
    client = ClientSerializer(read_only=True)
    
    class Meta:
        model = ClientConfig
        fields = ['id', 'client', 'vmess_link', 'vless_link', 'trojan_link',
                  'shadowsocks_link', 'subscription_url', 'qrcode_data', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyncLogSerializer(serializers.ModelSerializer):
    """Serializer for the SyncLog model"""
    server = ServerSerializer(read_only=True)
    
    class Meta:
        model = SyncLog
        fields = ['id', 'server', 'status', 'message', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for the Transaction model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'status', 'type', 'description',
                  'reference_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'reference_id', 'created_at', 'updated_at']


class CardPaymentSerializer(serializers.ModelSerializer):
    """Serializer for the CardPayment model"""
    transaction = TransactionSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CardPayment
        fields = ['id', 'transaction', 'card_number', 'reference_number',
                  'transfer_time', 'verification_code', 'expires_at', 'status',
                  'admin_note', 'verified_by', 'verified_at']
        read_only_fields = ['id', 'verification_code', 'expires_at', 'verified_at']


class ZarinpalPaymentSerializer(serializers.ModelSerializer):
    """Serializer for the ZarinpalPayment model"""
    transaction = TransactionSerializer(read_only=True)
    
    class Meta:
        model = ZarinpalPayment
        fields = ['id', 'transaction', 'authority', 'ref_id', 'status', 'payment_url']
        read_only_fields = ['id', 'authority', 'ref_id', 'payment_url']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for the PaymentMethod model"""
    
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'type', 'is_active', 'description', 'instructions']
        read_only_fields = ['id']


class DiscountSerializer(serializers.ModelSerializer):
    """Serializer for the Discount model"""
    
    class Meta:
        model = Discount
        fields = ['id', 'code', 'description', 'type', 'value', 'valid_from',
                  'valid_until', 'max_uses', 'times_used', 'is_active', 'created_at']
        read_only_fields = ['id', 'times_used', 'created_at']


class TelegramMessageSerializer(serializers.ModelSerializer):
    """Serializer for the TelegramMessage model"""
    
    class Meta:
        model = TelegramMessage
        fields = ['id', 'name', 'content', 'language_code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TelegramNotificationSerializer(serializers.ModelSerializer):
    """Serializer for the TelegramNotification model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TelegramNotification
        fields = ['id', 'user', 'type', 'message', 'status', 'error_message',
                  'created_at', 'sent_at']
        read_only_fields = ['id', 'created_at', 'sent_at']


class PlanSuggestionSerializer(serializers.ModelSerializer):
    """Serializer for plan suggestions."""
    suggested_plan_name = serializers.CharField(source='suggested_plan.name', read_only=True)
    
    class Meta:
        model = PlanSuggestion
        fields = [
            'id', 'suggested_plan', 'suggested_plan_name',
            'reason', 'created_at', 'is_accepted'
        ]
        read_only_fields = ['created_at', 'is_accepted']


class PointsRedemptionRuleSerializer(serializers.ModelSerializer):
    """Serializer for points redemption rules."""
    
    class Meta:
        model = PointsRedemptionRule
        fields = [
            'id', 'name', 'description', 'points_cost',
            'reward_type', 'reward_value', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PointsRedemptionSerializer(serializers.ModelSerializer):
    """Serializer for points redemption transactions."""
    rule = PointsRedemptionRuleSerializer(read_only=True)
    rule_id = serializers.IntegerField(write_only=True)
    applied_to_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = PointsRedemption
        fields = [
            'id', 'user', 'rule', 'rule_id', 'status',
            'points_spent', 'reward_value', 'applied_to',
            'applied_to_id', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'points_spent', 'reward_value', 'created_at', 'completed_at'] 