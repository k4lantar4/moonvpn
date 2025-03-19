from rest_framework import serializers
from .models import SystemSettings

class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings model"""
    
    class Meta:
        model = SystemSettings
        fields = [
            'id',
            'site_name',
            'site_description',
            'maintenance_mode',
            'session_timeout',
            'max_login_attempts',
            'enable_2fa',
            'enable_email_notifications',
            'enable_telegram_notifications',
            'telegram_bot_token',
            'zarinpal_merchant_id',
            'min_withdrawal_amount',
            'enable_card_payment',
            'default_language',
            'enable_rtl',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at'] 