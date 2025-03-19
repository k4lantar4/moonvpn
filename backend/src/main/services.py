from django.utils import timezone
from django.db import transaction, models
import secrets
import json
import uuid
import requests
from datetime import timedelta
from django.db.models import Sum, Count, Q, F
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import logging
import telegram
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple

# Import needed at the top
from .models import (
    User, Role, Server, SubscriptionPlan, Subscription,
    Payment, CardPayment, ZarinpalPayment, Discount,
    TelegramMessage, ServerMonitor, APIKey,
    UserUsagePattern, PlanSuggestion, Wallet, Transaction, Order, Voucher
)
from chat.models import (
    LiveChatSession,
    LiveChatMessage,
    LiveChatOperator,
    LiveChatRating,
)
from .permissions import Permission, PermissionGroup
from points.models import PointsTransaction, PointsRedemptionRule, PointsRedemption

logger = logging.getLogger(__name__)

class UsagePatternAnalyzer:
    """Service for analyzing user usage patterns and generating plan suggestions."""
    
    @staticmethod
    def analyze_usage(user):
        """Analyze user's usage patterns."""
        subscriptions = user.subscriptions.filter(status='active')
        if not subscriptions:
            return None
            
        total_usage = sum(sub.data_usage_gb for sub in subscriptions)
        days_active = (timezone.now() - subscriptions.first().start_date).days
        
        if days_active == 0:
            return None
            
        average_daily = total_usage / days_active
        
        # Analyze peak hours from usage logs
        peak_hours = UsagePatternAnalyzer._get_peak_hours(user)
        
        # Get preferred protocols
        preferred_protocols = UsagePatternAnalyzer._get_preferred_protocols(user)
        
        return {
            'average_daily_usage_gb': average_daily,
            'peak_hours': peak_hours,
            'preferred_protocols': preferred_protocols
        }
    
    @staticmethod
    def _get_peak_hours(user):
        """Get hours with highest usage."""
        # Implementation for analyzing peak usage hours
        # This would typically query usage logs and aggregate by hour
        return []
    
    @staticmethod
    def _get_preferred_protocols(user):
        """Get user's preferred protocols."""
        # Implementation for analyzing protocol preferences
        # This would typically query connection logs and count protocol usage
        return []

class PlanSuggestionService:
    """Service for generating and managing plan suggestions."""
    
    @staticmethod
    def generate_suggestion(user):
        """Generate a plan suggestion based on usage patterns."""
        usage_pattern = user.usage_pattern
        if not usage_pattern:
            return None
            
        current_plan = user.subscriptions.filter(status='active').first()
        if not current_plan:
            return None
            
        # Find suitable plans based on usage
        suitable_plans = SubscriptionPlan.objects.filter(
            data_limit_gb__gte=usage_pattern.average_daily_usage_gb * 30  # Monthly usage
        ).exclude(id=current_plan.plan.id)
        
        if not suitable_plans:
            return None
            
        # Select the most suitable plan
        suggested_plan = suitable_plans.first()
        
        # Generate reason for suggestion
        reason = PlanSuggestionService._generate_reason(
            current_plan,
            suggested_plan,
            usage_pattern
        )
        
        # Create suggestion
        return PlanSuggestion.objects.create(
            user=user,
            suggested_plan=suggested_plan,
            reason=reason
        )
    
    @staticmethod
    def _generate_reason(current_plan, suggested_plan, usage_pattern):
        """Generate a reason for the plan suggestion."""
        current_daily = current_plan.data_limit_gb / 30
        suggested_daily = suggested_plan.data_limit_gb / 30
        
        if suggested_daily > current_daily:
            return f"با توجه به مصرف روزانه شما ({usage_pattern.average_daily_usage_gb:.1f}GB)، پلن {suggested_plan.name} با {suggested_plan.data_limit_gb}GB ترافیک ماهانه برای شما مناسب‌تر است."
        else:
            return f"با توجه به مصرف روزانه شما ({usage_pattern.average_daily_usage_gb:.1f}GB)، پلن {suggested_plan.name} با {suggested_plan.data_limit_gb}GB ترافیک ماهانه برای شما مقرون به صرفه‌تر است."

# Add missing service functions

def create_subscription(user, plan, server, duration_days=None, data_limit=None):
    """Create a new subscription for a user."""
    if duration_days is None:
        duration_days = plan.duration_days
    
    if data_limit is None:
        data_limit = plan.data_limit_gb
    
    start_date = timezone.now()
    end_date = start_date + timedelta(days=duration_days)
    
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        server=server,
        data_limit_gb=data_limit,
        start_date=start_date,
        end_date=end_date,
        status='active'
    )
    
    # Give points to user for subscription purchase
    points_to_award = int(plan.price * 0.1)  # 10% of price as points
    if points_to_award > 0:
        user.add_points(points_to_award, f"خرید اشتراک {plan.name}")
    
    return subscription

def update_subscription(subscription, days_to_add=0, data_to_add=0):
    """Update an existing subscription."""
    if days_to_add > 0:
        subscription.end_date = subscription.end_date + timedelta(days=days_to_add)
    
    if data_to_add > 0:
        subscription.data_limit_gb += data_to_add
    
    subscription.save()
    return subscription

def sync_server(server):
    """Sync server with API."""
    # Implementation for syncing server with external system
    server.last_sync = timezone.now()
    server.is_synced = True
    server.save()
    return True

def verify_card_payment(payment):
    """Verify a card-to-card payment."""
    if not hasattr(payment, 'card_payment'):
        return False
    
    card_payment = payment.card_payment
    card_payment.status = 'verified'
    card_payment.verified_at = timezone.now()
    card_payment.save()
    
    payment.status = 'completed'
    payment.save()
    
    return True

def process_zarinpal_payment(payment, authority, status):
    """Process a Zarinpal payment callback."""
    if not hasattr(payment, 'zarinpal_payment'):
        return False
    
    zarinpal_payment = payment.zarinpal_payment
    
    if status == 'OK':
        # Verify with Zarinpal API (simplified here)
        zarinpal_payment.status = 'verified'
        zarinpal_payment.ref_id = str(uuid.uuid4())  # In real implementation, get from API
        payment.status = 'completed'
    else:
        zarinpal_payment.status = 'failed'
        payment.status = 'failed'
    
    zarinpal_payment.save()
    payment.save()
    
    return payment.status == 'completed'

def generate_discount_code(percentage=10, days_valid=7, max_uses=1):
    """Generate a new discount code."""
    code = f"DISCOUNT-{secrets.token_hex(4).upper()}"
    expiry = timezone.now() + timedelta(days=days_valid)
    
    discount = Discount.objects.create(
        code=code,
        type='percentage',
        value=percentage,
        valid_from=timezone.now(),
        valid_until=expiry,
        max_uses=max_uses,
        is_active=True
    )
    
    return discount

def send_telegram_message(user_id, message_name, context=None):
    """Send a message to a user via Telegram."""
    if context is None:
        context = {}
    
    try:
        template = TelegramMessage.objects.get(name=message_name)
        content = template.content
        
        # Simple template rendering
        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        # In real implementation, this would call the Telegram API
        return {
            'success': True,
            'message_id': str(uuid.uuid4())
        }
    except TelegramMessage.DoesNotExist:
        return {
            'success': False,
            'error': f"Message template '{message_name}' not found"
        }

def update_server_monitor(server, metrics):
    """Update server monitoring data."""
    health_status = 'healthy'
    
    if metrics.get('cpu_usage', 0) > 90 or metrics.get('memory_usage', 0) > 90:
        health_status = 'critical'
    elif metrics.get('cpu_usage', 0) > 70 or metrics.get('memory_usage', 0) > 70:
        health_status = 'warning'
    
    monitor = ServerMonitor.objects.create(
        server=server,
        health_status=health_status,
        cpu_usage=metrics.get('cpu_usage'),
        memory_usage=metrics.get('memory_usage'),
        disk_usage=metrics.get('disk_usage'),
        uptime_seconds=metrics.get('uptime'),
        active_connections=metrics.get('connections'),
        network_in=metrics.get('network_in'),
        network_out=metrics.get('network_out')
    )
    
    return monitor

def validate_api_key(key):
    """Validate an API key."""
    try:
        api_key = APIKey.objects.get(key=key, is_active=True)
        return api_key.is_valid()
    except APIKey.DoesNotExist:
        return False

def create_chat_session(user, subject, priority='medium'):
    """Create a new live chat session."""
    session = LiveChatSession.objects.create(
        user=user,
        subject=subject,
        priority=priority,
        status='active'
    )
    
    # Create a welcome message
    LiveChatMessage.objects.create(
        session=session,
        sender=User.objects.filter(is_staff=True).first(),  # Default system user
        type='system',
        content='سلام! چطور می‌توانم به شما کمک کنم؟'
    )
    
    # Assign to an available operator
    available_operator = LiveChatOperator.objects.filter(
        status='online',
        current_sessions__lt=models.F('max_sessions')
    ).first()
    
    if available_operator:
        session.operator = available_operator.user
        session.save()
        
        available_operator.current_sessions += 1
        available_operator.save()
    
    return session

def send_chat_message(session, sender, content, message_type='text', file_url=None):
    """Send a message in a chat session."""
    message = LiveChatMessage.objects.create(
        session=session,
        sender=sender,
        type=message_type,
        content=content,
        file_url=file_url
    )
    
    # Update session last message time
    session.last_message_at = timezone.now()
    session.save()
    
    return message

def update_operator_status(operator, status):
    """Update a chat operator's status."""
    if status not in ['online', 'busy', 'offline']:
        return False
    
    operator_profile = operator.operator_profile
    operator_profile.status = status
    operator_profile.last_active = timezone.now()
    operator_profile.save()
    
    return True

def rate_chat_session(session, rating, comment=''):
    """Rate a chat session."""
    if not session.operator:
        return False
    
    chat_rating = LiveChatRating.objects.create(
        session=session,
        user=session.user,
        operator=session.operator,
        rating=rating,
        comment=comment
    )
    
    return chat_rating

def update_usage_patterns(user, usage_data):
    """Update a user's usage patterns."""
    pattern, created = UserUsagePattern.objects.get_or_create(user=user)
    pattern.update_patterns(usage_data)
    return pattern

def suggest_plan(user):
    """Generate a plan suggestion for a user."""
    return PlanSuggestionService.generate_suggestion(user)

def redeem_points(user, rule_id):
    """Redeem points for a reward based on a rule."""
    try:
        rule = PointsRedemptionRule.objects.get(id=rule_id, is_active=True)
        
        # Check if user has enough points
        if user.points < rule.points_required:
            return {
                'success': False,
                'error': 'Insufficient points'
            }
        
        # Get active subscription
        subscription = user.v2ray_subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if not subscription and rule.reward_type == 'days':
            return {
                'success': False,
                'error': 'No active subscription found'
            }
        
        # Process the redemption
        with transaction.atomic():
            # Deduct points
            user.spend_points(rule.points_required, f"Redeemed for {rule.name}")
            
            redemption = PointsRedemption.objects.create(
                user=user,
                rule=rule,
                points_spent=rule.points_required,
                reward_value=rule.reward_value,
                subscription=subscription if rule.reward_type == 'days' else None
            )
            
            # Apply the reward
            if rule.reward_type == 'discount':
                # Create discount code
                discount = generate_discount_code(
                    percentage=rule.reward_value,
                    days_valid=7,
                    max_uses=1
                )
                result = {
                    'reward_type': 'discount',
                    'code': discount.code,
                    'value': f"{rule.reward_value}%",
                    'expires': discount.valid_until
                }
            elif rule.reward_type == 'days':
                # Extend subscription
                update_subscription(subscription, days_to_add=rule.reward_value)
                result = {
                    'reward_type': 'days',
                    'days': rule.reward_value,
                    'new_expiry': subscription.end_date
                }
            else:
                result = {
                    'reward_type': 'other',
                    'description': rule.name
                }
            
            return {
                'success': True,
                'points_spent': rule.points_required,
                'new_balance': user.points,
                'reward': result
            }
            
    except PointsRedemptionRule.DoesNotExist:
        return {
            'success': False,
            'error': 'Invalid redemption rule'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

class PaymentService:
    """Service for handling payments."""
    
    def handle_callback(self, data: dict) -> dict:
        """Handle payment gateway callback."""
        try:
            # Get order from payment ID
            order = Order.objects.get(payment_id=data.get('payment_id'))
            
            # Check payment status
            if data.get('status') == 'success':
                # Update order status
                order.status = 'paid'
                order.metadata.update({
                    'payment_data': data,
                    'paid_at': timezone.now().isoformat()
                })
                order.save()
                
                # Create transaction
                transaction = Transaction.objects.create(
                    user=order.user,
                    wallet=order.user.wallet,
                    type='subscription',
                    amount=order.amount,
                    status='completed',
                    description=f'Payment for {order.subscription_plan.name}',
                    reference_id=order.payment_id,
                    metadata={
                        'order_id': order.id,
                        'payment_data': data
                    }
                )
                
                # Update user wallet
                wallet = order.user.wallet
                wallet.balance += order.amount
                wallet.save()
                
                return {
                    'success': True,
                    'message': 'Payment processed successfully',
                    'order_id': order.id,
                    'transaction_id': transaction.id
                }
            else:
                # Update order status
                order.status = 'failed'
                order.metadata.update({
                    'payment_data': data,
                    'failed_at': timezone.now().isoformat()
                })
                order.save()
                
                return {
                    'success': False,
                    'message': 'Payment failed',
                    'order_id': order.id
                }
        except Order.DoesNotExist:
            return {
                'success': False,
                'message': 'Invalid payment ID'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def verify_payment(self, data: dict) -> dict:
        """Verify a payment."""
        try:
            # Get order from payment ID
            order = Order.objects.get(payment_id=data.get('payment_id'))
            
            # Check payment status
            if order.status == 'paid':
                return {
                    'success': True,
                    'message': 'Payment already verified',
                    'order_id': order.id
                }
            
            # Verify payment with gateway
            # TODO: Implement payment gateway verification
            
            return {
                'success': True,
                'message': 'Payment verified successfully',
                'order_id': order.id
            }
        except Order.DoesNotExist:
            return {
                'success': False,
                'message': 'Invalid payment ID'
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            } 