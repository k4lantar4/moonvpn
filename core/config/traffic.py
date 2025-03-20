"""
Traffic Management Service for V2Ray Telegram Bot.

This module handles traffic monitoring, limits, and notifications.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

class TrafficManager:
    def __init__(self, db_connection, notification_service):
        self.db = db_connection
        self.notifier = notification_service
        self.check_interval = 300  # 5 minutes
        self.warning_thresholds = {
            'traffic': [50, 75, 90, 95],  # Percentage of limit
            'bandwidth': [50, 75, 90, 95]  # Percentage of capacity
        }
        self.monitoring_task = None

    async def start_monitoring(self):
        """Start the traffic monitoring service"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self.monitor_traffic())

    async def stop_monitoring(self):
        """Stop the traffic monitoring service"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None

    async def monitor_traffic(self):
        """Monitor user traffic consumption"""
        while True:
            try:
                active_subscriptions = await self.db.subscriptions.find({
                    'status': 'active'
                })

                for sub in active_subscriptions:
                    await self._check_traffic_limits(sub)
                    await self._update_traffic_stats(sub)
                    await self._send_traffic_alerts(sub)

            except Exception as e:
                await self.notifier.notify_admin(f"Traffic monitoring error: {str(e)}")
            
            await asyncio.sleep(self.check_interval)

    async def _check_traffic_limits(self, subscription: dict):
        """Check if traffic limits are exceeded"""
        try:
            current_usage = await self._get_current_usage(subscription['id'])
            limit = subscription['traffic_limit']
            
            usage_percentage = (current_usage / limit) * 100
            
            if usage_percentage >= 100:
                await self._handle_traffic_exceeded(subscription)
            else:
                for threshold in self.warning_thresholds['traffic']:
                    if usage_percentage >= threshold:
                        await self._send_traffic_warning(
                            subscription, 
                            usage_percentage,
                            threshold
                        )
                        
        except Exception as e:
            await self.notifier.notify_admin(
                f"Traffic limit check error for sub {subscription['id']}: {str(e)}"
            )

    async def _get_current_usage(self, subscription_id: str) -> float:
        """Get current traffic usage for a subscription"""
        try:
            stats = await self.db.traffic_stats.find_one({'subscription_id': subscription_id})
            return float(stats.get('total_usage', 0))
        except Exception:
            return 0.0

    async def _handle_traffic_exceeded(self, subscription: dict):
        """Handle subscription that has exceeded traffic limit"""
        try:
            # Update subscription status
            await self.db.subscriptions.update_one(
                {'_id': subscription['_id']},
                {'$set': {'status': 'traffic_exceeded'}}
            )
            
            # Notify user
            await self._send_traffic_exceeded_notification(subscription)
            
            # Log event
            await self._log_traffic_event(
                subscription['id'],
                'traffic_exceeded',
                {'subscription_id': subscription['id']}
            )
            
        except Exception as e:
            await self.notifier.notify_admin(
                f"Error handling traffic exceeded for sub {subscription['id']}: {str(e)}"
            )

    async def _send_traffic_warning(self, subscription: dict, usage: float, threshold: int):
        """Send traffic warning notification"""
        user_id = subscription['user_id']
        remaining = subscription['traffic_limit'] - subscription['traffic_used']
        
        message = (
            f"⚠️ Traffic Warning\n\n"
            f"Your subscription has reached {threshold}% of its traffic limit.\n"
            f"Current Usage: {usage:.1f}%\n"
            f"Remaining Traffic: {self._format_traffic(remaining)}\n\n"
            f"Consider upgrading your plan or purchasing additional traffic."
        )
        
        await self.notifier.send_notification(
            user_id=user_id,
            notification_type='traffic_warning',
            data={'message': message},
            priority='high'
        )

    async def _send_traffic_exceeded_notification(self, subscription: dict):
        """Send notification when traffic is exceeded"""
        user_id = subscription['user_id']
        
        message = (
            f"🚫 Traffic Limit Exceeded\n\n"
            f"Your subscription has exceeded its traffic limit.\n"
            f"Service has been temporarily suspended.\n\n"
            f"To resume service, please:\n"
            f"1. Purchase additional traffic\n"
            f"2. Upgrade your plan\n"
            f"3. Wait for next billing cycle\n\n"
            f"Contact support if you need assistance."
        )
        
        await self.notifier.send_notification(
            user_id=user_id,
            notification_type='traffic_exceeded',
            data={'message': message},
            priority='high'
        )

    def _format_traffic(self, bytes_amount: float) -> str:
        """Format traffic amount in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_amount < 1024:
                return f"{bytes_amount:.2f} {unit}"
            bytes_amount /= 1024
        return f"{bytes_amount:.2f} PB"

    async def _update_traffic_stats(self, subscription: dict):
        """Update traffic statistics for subscription"""
        try:
            current_usage = await self._get_current_usage(subscription['id'])
            
            # Update subscription traffic usage
            await self.db.subscriptions.update_one(
                {'_id': subscription['_id']},
                {'$set': {'traffic_used': current_usage}}
            )
            
            # Update traffic stats
            await self.db.traffic_stats.update_one(
                {'subscription_id': subscription['id']},
                {
                    '$set': {
                        'last_updated': datetime.now(),
                        'total_usage': current_usage
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            await self.notifier.notify_admin(
                f"Error updating traffic stats for sub {subscription['id']}: {str(e)}"
            )

    async def _log_traffic_event(self, subscription_id: str, event_type: str, data: dict):
        """Log traffic-related events"""
        try:
            await self.db.traffic_events.insert_one({
                'subscription_id': subscription_id,
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.now()
            })
        except Exception as e:
            await self.notifier.notify_admin(
                f"Error logging traffic event: {str(e)}"
            ) 