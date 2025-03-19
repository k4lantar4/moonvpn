from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import PointsTransaction, PointsRedemptionRule, PointsRedemption

class PointsService:
    """Service class for handling points-related operations."""
    
    @staticmethod
    def get_user_points(user):
        """Get total points for a user."""
        return PointsTransaction.objects.filter(user=user).aggregate(
            total=models.Sum('points')
        )['total'] or 0
    
    @staticmethod
    def add_points(user, points, description, transaction_type=PointsTransaction.TransactionType.EARN):
        """Add points to a user's account."""
        if points <= 0:
            raise ValidationError(_('Points must be positive'))
            
        with transaction.atomic():
            PointsTransaction.objects.create(
                user=user,
                type=transaction_type,
                points=points,
                description=description
            )
            return PointsService.get_user_points(user)
    
    @staticmethod
    def spend_points(user, points, description):
        """Spend points from a user's account."""
        if points <= 0:
            raise ValidationError(_('Points must be positive'))
            
        current_points = PointsService.get_user_points(user)
        if current_points < points:
            raise ValidationError(_('Insufficient points'))
            
        with transaction.atomic():
            PointsTransaction.objects.create(
                user=user,
                type=PointsTransaction.TransactionType.SPEND,
                points=-points,
                description=description
            )
            return PointsService.get_user_points(user)
    
    @staticmethod
    def redeem_points(user, rule_id):
        """Redeem points for a reward."""
        try:
            rule = PointsRedemptionRule.objects.get(id=rule_id, is_active=True)
        except PointsRedemptionRule.DoesNotExist:
            raise ValidationError(_('Invalid redemption rule'))
            
        current_points = PointsService.get_user_points(user)
        if current_points < rule.points_required:
            raise ValidationError(_('Insufficient points for redemption'))
            
        with transaction.atomic():
            # Create redemption record
            redemption = PointsRedemption.objects.create(
                user=user,
                rule=rule,
                points_spent=rule.points_required,
                reward_value=rule.reward_value
            )
            
            # Deduct points
            PointsTransaction.objects.create(
                user=user,
                type=PointsTransaction.TransactionType.SPEND,
                points=-rule.points_required,
                description=f'Redeemed {rule.name}'
            )
            
            return redemption
    
    @staticmethod
    def get_available_rewards(user):
        """Get list of available rewards for a user."""
        current_points = PointsService.get_user_points(user)
        return PointsRedemptionRule.objects.filter(
            is_active=True,
            points_required__lte=current_points
        ).order_by('points_required')
    
    @staticmethod
    def get_user_transactions(user, limit=10):
        """Get recent transactions for a user."""
        return PointsTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_user_redemptions(user, limit=10):
        """Get recent redemptions for a user."""
        return PointsRedemption.objects.filter(
            user=user
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def expire_points(user, points, description):
        """Expire points from a user's account."""
        if points <= 0:
            raise ValidationError(_('Points must be positive'))
            
        current_points = PointsService.get_user_points(user)
        if current_points < points:
            raise ValidationError(_('Insufficient points'))
            
        with transaction.atomic():
            PointsTransaction.objects.create(
                user=user,
                type=PointsTransaction.TransactionType.EXPIRE,
                points=-points,
                description=description
            )
            return PointsService.get_user_points(user)
    
    @staticmethod
    def adjust_points(user, points, description):
        """Adjust points for a user (admin only)."""
        with transaction.atomic():
            PointsTransaction.objects.create(
                user=user,
                type=PointsTransaction.TransactionType.ADJUST,
                points=points,
                description=description
            )
            return PointsService.get_user_points(user) 