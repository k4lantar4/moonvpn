from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...models import ReferralCode

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model"""
    
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )
    referral_code = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone',
            'telegram_id', 'role', 'role_display',
            'wallet_balance', 'commission_rate',
            'language', 'notifications_enabled',
            'auto_renew_enabled', 'referral_code',
            'joined_at'
        ]
        read_only_fields = [
            'wallet_balance', 'commission_rate',
            'role', 'joined_at'
        ]
    
    def get_referral_code(self, obj):
        """Get user's referral code if they are a reseller"""
        if obj.is_reseller:
            try:
                return obj.referral_code.code
            except ReferralCode.DoesNotExist:
                return None
        return None

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'password', 'email',
            'phone', 'telegram_id', 'language',
            'referral_code'
        ]
    
    def validate_username(self, value):
        """Validate username"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Validate email"""
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'language',
            'notifications_enabled', 'auto_renew_enabled'
        ]
    
    def validate_email(self, value):
        """Validate email"""
        if value and User.objects.exclude(
            id=self.instance.id
        ).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    
    total_spent = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    wallet_balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    total_traffic_used = serializers.IntegerField()
    total_traffic_limit = serializers.IntegerField()
    remaining_traffic = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    
    # Reseller stats (optional)
    referral_code = serializers.CharField(required=False)
    total_referrals = serializers.IntegerField(required=False)
    total_earnings = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    sub_resellers = serializers.IntegerField(required=False)

class ResellerSerializer(UserSerializer):
    """Serializer for reseller users"""
    
    total_referrals = serializers.IntegerField(
        source='referral_code.total_uses'
    )
    total_earnings = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='referral_code.total_earnings'
    )
    sub_resellers_count = serializers.IntegerField(
        source='sub_resellers.count'
    )
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'total_referrals',
            'total_earnings',
            'sub_resellers_count'
        ] 