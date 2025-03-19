from rest_framework import serializers
from .models import (
    User, Role, Server, SubscriptionPlan, Subscription,
    Payment, CardPayment, ZarinpalPayment, Discount,
    TelegramMessage, ServerMonitor, APIKey,
    UserUsagePattern, PlanSuggestion, UserActivity,
    Wallet, Transaction, Order, Voucher, PanelConfig
)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'date_joined', 'last_login',
            'telegram_id', 'phone_number', 'language_code',
            'role', 'is_admin', 'wallet_balance', 'commission_rate',
            'total_sales', 'referral_code', 'points',
            'two_factor_enabled', 'notification_preferences',
            'created_at', 'updated_at', 'last_login_ip'
        ]
        read_only_fields = [
            'id', 'is_active', 'is_staff', 'date_joined', 'last_login',
            'wallet_balance', 'total_sales', 'points',
            'created_at', 'updated_at', 'last_login_ip'
        ]

class UserDetailSerializer(UserSerializer):
    """Detailed serializer for User model."""
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['traffic_limit', 'traffic_used', 'subscription_expires']
        read_only_fields = UserSerializer.Meta.read_only_fields + ['traffic_limit', 'traffic_used', 'subscription_expires']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = '__all__'
        read_only_fields = ['created_at']

class UserUsagePatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserUsagePattern
        fields = '__all__'
        read_only_fields = ['last_updated']

# Additional serializers for nested resources and related models
class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for UserActivity model."""
    
    user = UserSerializer(read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'description', 'ip_address', 'user_agent', 'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserPreferenceSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.JSONField()

class UserNotificationSerializer(serializers.Serializer):
    type = serializers.CharField()
    enabled = serializers.BooleanField()

class UserDeviceSerializer(serializers.Serializer):
    device_id = serializers.CharField()
    device_type = serializers.CharField()
    last_used = serializers.DateTimeField()

class UserLocationSerializer(serializers.Serializer):
    ip = serializers.IPAddressField()
    country = serializers.CharField()
    city = serializers.CharField()

class UserLoginHistorySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    ip = serializers.IPAddressField()
    device = serializers.CharField()

class UserAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'is_active', 'created_at', 'expires_at']
        read_only_fields = ['created_at']

class UserWebhookSerializer(serializers.Serializer):
    url = serializers.URLField()
    events = serializers.ListField(child=serializers.CharField())
    is_active = serializers.BooleanField()

class UserReferralSerializer(serializers.Serializer):
    code = serializers.CharField()
    referrals_count = serializers.IntegerField()
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2)

class UserWalletSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    transactions = serializers.ListField(child=serializers.JSONField())

class UserTransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    created_at = serializers.DateTimeField()

class UserInvitationSerializer(serializers.Serializer):
    code = serializers.CharField()
    expires_at = serializers.DateTimeField()
    max_uses = serializers.IntegerField()

class UserReportSerializer(serializers.Serializer):
    type = serializers.CharField()
    data = serializers.JSONField()
    period = serializers.CharField()

class UserFeedbackSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()

class UserSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanSuggestion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

# Support ticket related serializers
class UserTicketSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subject = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
    created_at = serializers.DateTimeField()

class UserTicketMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    content = serializers.CharField()
    sender = serializers.CharField()
    created_at = serializers.DateTimeField()

class UserTicketAttachmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    file_url = serializers.URLField()
    file_name = serializers.CharField()
    file_size = serializers.IntegerField()

class UserTicketCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()

class UserTicketPrioritySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()

class UserTicketStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()

class UserTicketTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()

class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model."""
    
    class Meta:
        model = Group
        fields = ['id', 'name']

class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'currency', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    user = UserSerializer(read_only=True)
    wallet = WalletSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'wallet', 'type', 'type_display',
            'amount', 'status', 'status_display', 'description',
            'reference_id', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    user = UserSerializer(read_only=True)
    subscription_plan = PlanSerializer(read_only=True)
    voucher = serializers.PrimaryKeyRelatedField(queryset=Voucher.objects.all(), required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'subscription_plan', 'amount',
            'status', 'status_display', 'payment_method',
            'payment_id', 'voucher', 'discount_amount',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class VoucherSerializer(serializers.ModelSerializer):
    """Serializer for Voucher model."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Voucher
        fields = [
            'id', 'code', 'type', 'type_display', 'value',
            'max_uses', 'used_count', 'min_order_amount',
            'max_discount_amount', 'start_date', 'end_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'used_count', 'created_at', 'updated_at']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model."""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description', 'price',
            'duration', 'traffic_limit', 'concurrent_connections',
            'is_active', 'features', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    user = UserSerializer(read_only=True)
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    voucher = VoucherSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'subscription_plan', 'amount',
            'status', 'payment_method', 'payment_id',
            'voucher', 'discount_amount', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status',
            'start_date', 'end_date', 'auto_renew',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PanelConfigSerializer(serializers.ModelSerializer):
    """Serializer for PanelConfig model."""
    
    panel_url = serializers.CharField(read_only=True)
    api_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = PanelConfig
        fields = [
            'id', 'name', 'server_id', 'domain', 'port',
            'username', 'password', 'location', 'base_path',
            'api_path', 'use_ssl', 'disable_check', 'is_active',
            'last_check', 'panel_url', 'api_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_check', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        } 