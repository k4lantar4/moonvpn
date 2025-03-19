from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import PointsTransaction, PointsRedemptionRule, PointsRedemption

class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions."""
    
    class Meta:
        model = PointsTransaction
        fields = ('id', 'type', 'points', 'description', 'created_at')
        read_only_fields = ('created_at',)

class PointsRedemptionRuleSerializer(serializers.ModelSerializer):
    """Serializer for points redemption rules."""
    
    class Meta:
        model = PointsRedemptionRule
        fields = ('id', 'name', 'description', 'points_required', 'reward_type', 'reward_value', 'is_active')
        read_only_fields = ('is_active',)

class PointsRedemptionSerializer(serializers.ModelSerializer):
    """Serializer for points redemptions."""
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_description = serializers.CharField(source='rule.description', read_only=True)
    
    class Meta:
        model = PointsRedemption
        fields = ('id', 'rule', 'rule_name', 'rule_description', 'points_spent', 'reward_value', 'created_at')
        read_only_fields = ('created_at',) 