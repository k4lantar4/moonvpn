"""
Subscription management service
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from ..models import Plan, Subscription, Transaction, Client, Server
from .server_manager import ServerManager
from .panel_manager import PanelManager

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Service class for managing VPN subscriptions"""
    
    def create_subscription(self, user, plan_id, server_id=None):
        """
        Create a new subscription
        
        Args:
            user: User object
            plan_id: ID of the subscription plan
            server_id: Optional ID of the server to use
            
        Returns:
            dict: Creation results
        """
        try:
            with transaction.atomic():
                plan = Plan.objects.get(id=plan_id)
                
                # If no server specified, get least loaded active server
                if not server_id:
                    server = Server.objects.filter(
                        is_active=True,
                        available_plans=plan
                    ).order_by('client__count').first()
                    if not server:
                        return {
                            'status': 'error',
                            'message': 'No available servers for this plan'
                        }
                else:
                    server = Server.objects.get(id=server_id)
                    if not server.is_active or plan not in server.available_plans.all():
                        return {
                            'status': 'error',
                            'message': 'Selected server not available for this plan'
                        }
                
                # Check if server is at capacity
                if server.is_at_capacity():
                    return {
                        'status': 'error',
                        'message': 'Selected server is at capacity'
                    }
                
                # Create client
                client = Client.objects.create(
                    server=server,
                    email=user.email,
                    traffic_limit=plan.traffic_limit,
                    expire_date=timezone.now() + timezone.timedelta(days=plan.duration_days)
                )
                
                # Create subscription
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    client=client,
                    start_date=timezone.now(),
                    end_date=client.expire_date
                )
                
                # Create transaction
                transaction = Transaction.objects.create(
                    user=user,
                    subscription=subscription,
                    transaction_type='new',
                    amount=plan.price,
                    payment_method='wallet',  # TODO: Make configurable
                    status='completed'
                )
                
                return {
                    'status': 'success',
                    'subscription': subscription,
                    'transaction': transaction
                }
                
        except Plan.DoesNotExist:
            logger.error(f"Plan {plan_id} not found")
            return {'status': 'error', 'message': 'Plan not found'}
        except Server.DoesNotExist:
            logger.error(f"Server {server_id} not found")
            return {'status': 'error', 'message': 'Server not found'}
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def renew_subscription(self, subscription_id):
        """
        Renew an existing subscription
        
        Args:
            subscription_id: ID of the subscription to renew
            
        Returns:
            dict: Renewal results
        """
        try:
            with transaction.atomic():
                subscription = Subscription.objects.get(id=subscription_id)
                
                # Check if subscription can be renewed
                if not subscription.can_renew():
                    return {
                        'status': 'error',
                        'message': 'Subscription cannot be renewed'
                    }
                
                # Update client expiry
                subscription.client.expire_date = timezone.now() + timezone.timedelta(days=subscription.plan.duration_days)
                subscription.client.save()
                
                # Update subscription
                subscription.end_date = subscription.client.expire_date
                subscription.last_renewal = timezone.now()
                subscription.status = 'active'
                subscription.save()
                
                # Create transaction
                transaction = Transaction.objects.create(
                    user=subscription.user,
                    subscription=subscription,
                    transaction_type='renewal',
                    amount=subscription.plan.price,
                    payment_method='wallet',  # TODO: Make configurable
                    status='completed'
                )
                
                return {
                    'status': 'success',
                    'subscription': subscription,
                    'transaction': transaction
                }
                
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found")
            return {'status': 'error', 'message': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Error renewing subscription: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def cancel_subscription(self, subscription_id):
        """
        Cancel a subscription
        
        Args:
            subscription_id: ID of the subscription to cancel
            
        Returns:
            dict: Cancellation results
        """
        try:
            with transaction.atomic():
                subscription = Subscription.objects.get(id=subscription_id)
                
                # Update subscription
                subscription.status = 'cancelled'
                subscription.auto_renew = False
                subscription.save()
                
                # Update client
                subscription.client.is_active = False
                subscription.client.save()
                
                return {
                    'status': 'success',
                    'subscription': subscription
                }
                
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found")
            return {'status': 'error', 'message': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def suspend_subscription(self, subscription_id, reason=''):
        """
        Suspend a subscription
        
        Args:
            subscription_id: ID of the subscription to suspend
            reason: Optional reason for suspension
            
        Returns:
            dict: Suspension results
        """
        try:
            with transaction.atomic():
                subscription = Subscription.objects.get(id=subscription_id)
                
                # Update subscription
                subscription.status = 'suspended'
                subscription.notes = f"Suspended: {reason}" if reason else "Suspended"
                subscription.save()
                
                # Update client
                subscription.client.is_active = False
                subscription.client.save()
                
                return {
                    'status': 'success',
                    'subscription': subscription
                }
                
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found")
            return {'status': 'error', 'message': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Error suspending subscription: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def reactivate_subscription(self, subscription_id):
        """
        Reactivate a suspended subscription
        
        Args:
            subscription_id: ID of the subscription to reactivate
            
        Returns:
            dict: Reactivation results
        """
        try:
            with transaction.atomic():
                subscription = Subscription.objects.get(id=subscription_id)
                
                # Check if subscription can be reactivated
                if subscription.status not in ['suspended', 'cancelled']:
                    return {
                        'status': 'error',
                        'message': 'Subscription cannot be reactivated'
                    }
                
                # Update subscription
                subscription.status = 'active'
                subscription.save()
                
                # Update client
                subscription.client.is_active = True
                subscription.client.save()
                
                return {
                    'status': 'success',
                    'subscription': subscription
                }
                
        except Subscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found")
            return {'status': 'error', 'message': 'Subscription not found'}
        except Exception as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def process_expired_subscriptions():
        """Process all expired subscriptions"""
        now = timezone.now()
        expired = Subscription.objects.filter(
            status='active',
            end_date__lt=now
        )
        
        results = {
            'processed': 0,
            'errors': 0
        }
        
        for subscription in expired:
            try:
                with transaction.atomic():
                    # Update panel
                    panel = PanelManager(subscription.client.server)
                    panel.update_client(
                        email=subscription.user.email,
                        enable=False
                    )
                    
                    # Update subscription
                    subscription.status = 'expired'
                    subscription.save()
                    
                    # Update client
                    subscription.client.is_active = False
                    subscription.client.save()
                    
                    results['processed'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing expired subscription {subscription.id}: {str(e)}")
                results['errors'] += 1
        
        return results
    
    @staticmethod
    def get_subscription_status(subscription: Subscription) -> Dict:
        """Get detailed status of a subscription"""
        try:
            panel = PanelManager(subscription.client.server)
            traffic_data = panel.get_client_traffic(subscription.user.email)
            
            if not traffic_data:
                return {
                    'status': subscription.status,
                    'error': 'Failed to get traffic data'
                }
            
            return {
                'status': subscription.status,
                'days_remaining': subscription.days_remaining(),
                'is_active': subscription.is_active(),
                'traffic_used': traffic_data.get('used', 0),
                'traffic_remaining': max(0, subscription.client.traffic_limit - traffic_data.get('used', 0)),
                'last_connection': traffic_data.get('last_seen'),
                'can_renew': subscription.can_renew()
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            return {
                'status': subscription.status,
                'error': str(e)
            } 