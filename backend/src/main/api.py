from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
import secrets
from rest_framework import serializers, status
from .models import (
    User, Role, Server, SubscriptionPlan, Subscription,
    Payment, CardPayment, ZarinpalPayment, Discount,
    TelegramMessage, ServerMonitor, APIKey,
    UserUsagePattern, PlanSuggestion
)
from .permissions import Permission, PermissionGroup
from .services import (
    create_subscription, update_subscription,
    sync_server, verify_card_payment, process_zarinpal_payment,
    generate_discount_code, send_telegram_message,
    redeem_points
)
from points.models import PointsTransaction, PointsRedemptionRule, PointsRedemption
from points.serializers import PointsTransactionSerializer, PointsRedemptionRuleSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.db.models import Q
from .serializers import (
    UserSerializer,
    RoleSerializer,
    ServerSerializer,
    PlanSerializer,
    SubscriptionSerializer,
    PaymentSerializer,
    DiscountSerializer,
    UserUsagePatternSerializer,
    UserActivitySerializer,
    UserPreferenceSerializer,
    UserNotificationSerializer,
    UserDeviceSerializer,
    UserLocationSerializer,
    UserLoginHistorySerializer,
    UserAPIKeySerializer,
    UserWebhookSerializer,
    UserReferralSerializer,
    UserWalletSerializer,
    UserTransactionSerializer,
    UserInvitationSerializer,
    UserReportSerializer,
    UserFeedbackSerializer,
    UserSuggestionSerializer,
    UserTicketSerializer,
    UserTicketMessageSerializer,
    UserTicketAttachmentSerializer,
    UserTicketCategorySerializer,
    UserTicketPrioritySerializer,
    UserTicketStatusSerializer,
    UserTicketTypeSerializer,
)
from .permissions import (
    IsAdminUser,
    IsSellerUser,
    HasPermission,
    Permission,
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_points_balance(request):
    """Get user's points balance."""
    return Response({
        'points': request.user.points
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_points_history(request):
    """Get user's points transaction history."""
    transactions = request.user.get_points_history()
    serializer = PointsTransactionSerializer(transactions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_redemption_rules(request):
    """Get available points redemption rules."""
    rules = PointsRedemptionRule.objects.filter(is_active=True)
    serializer = PointsRedemptionRuleSerializer(rules, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def redeem_points(request):
    """Redeem points for a reward."""
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    rule_id = request.data.get('rule_id')
    if not rule_id:
        return Response({'error': 'Rule ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get user and rule
        user = request.user
        rule = PointsRedemptionRule.objects.get(id=rule_id, is_active=True)
        
        # Check if user has enough points
        if user.points < rule.points_required:
            return Response({'error': 'Insufficient points'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Apply the reward
        with transaction.atomic():
            # Deduct points
            user.points -= rule.points_required
            user.save()
            
            # Create points transaction
            PointsTransaction.objects.create(
                user=user,
                type="spend",
                points=rule.points_required,
                description=f"Redeemed for {rule.name}"
            )
            
            # Create redemption record
            redemption = PointsRedemption.objects.create(
                user=user,
                rule=rule,
                points_spent=rule.points_required,
                reward_value=rule.reward_value
            )
            
            # Apply the reward based on rule type
            if rule.reward_type == "discount":
                # Create discount code
                discount_code = secrets.token_urlsafe(8)
                Discount.objects.create(
                    code=discount_code,
                    percentage=rule.reward_value,
                    expiry_date=timezone.now() + timezone.timedelta(days=7)
                )
                reward_text = f"Discount code: {discount_code}"
            elif rule.reward_type == "days":
                # Find active subscription
                active_subscription = Subscription.objects.filter(
                    user=user,
                    is_active=True,
                    expiry_date__gt=timezone.now()
                ).first()
                
                if active_subscription:
                    # Extend subscription
                    active_subscription.expiry_date += timezone.timedelta(days=rule.reward_value)
                    active_subscription.save()
                    
                    # Update redemption with subscription
                    redemption.subscription = active_subscription
                    redemption.save()
                    
                    reward_text = f"{rule.reward_value} days extension"
                else:
                    return Response({'error': 'No active subscription found'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                reward_text = rule.name
        
        return Response({
            'success': True,
            'points_spent': rule.points_required,
            'reward': reward_text,
            'new_balance': user.points
        })
        
    except PointsRedemptionRule.DoesNotExist:
        return Response({'error': 'Invalid redemption rule'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_points_transactions(request):
    """Get user's points transactions."""
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    transactions = PointsTransaction.objects.filter(user=request.user).order_by('-created_at')
    serializer = PointsTransactionSerializer(transactions, many=True)
    
    return Response(serializer.data) 