"""
Celery tasks for V2Ray management.

This module contains Celery tasks for:
- Server monitoring and health checks
- Traffic usage tracking
- Server synchronization
- Notification sending
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import F
from django.db import transaction
from django.conf import settings

from main.models import Server, ServerMonitor, User, Subscription, PanelConfig
from v2ray.models import Inbound, Client, ServerMetrics, ServerHealthCheck, ServerRotationLog
from core.services.panel.api import XUIClient
from utils.notifications import send_telegram_notification
from utils.server_sync import sync_server, sync_all_servers, check_server_health
from v2ray.sync_manager import ServerSyncManager, sync_accounts, check_expirations, sync_panel, ThreeXUI_Connector

logger = logging.getLogger(__name__)

@shared_task
def sync_servers() -> None:
    """
    Synchronize all active servers.
    This task should be run every 5 minutes.
    """
    try:
        async with ServerSyncManager() as sync_manager:
            results = await sync_manager.sync_all_servers()
            
            if results['failed'] > 0:
                await send_telegram_notification(
                    f"⚠️ Server sync completed with {results['failed']} failures\n"
                    f"Total: {results['total']}, Success: {results['success']}"
                )
    except Exception as e:
        logger.error(f"Error in sync_servers task: {str(e)}")
        await send_telegram_notification(
            f"❌ Server sync failed: {str(e)}"
        )

@shared_task
def monitor_servers() -> None:
    """
    Monitor all active servers and record their status.
    This task should be run every 5 minutes.
    """
    try:
        async with ServerSyncManager() as sync_manager:
            servers = Server.objects.filter(is_active=True)
            
            for server in servers:
                try:
                    # Get server metrics
                    metrics = await sync_manager.get_server_metrics(server)
                    
                    # Record metrics
                    for metric in metrics:
                        ServerMetrics.objects.create(
                            server=server,
                            cpu_usage=metric['cpu_usage'],
                            memory_usage=metric['memory_usage'],
                            disk_usage=metric['disk_usage'],
                            network_in=metric['network_in'],
                            network_out=metric['network_out'],
                            active_connections=metric['active_connections']
                        )
                    
                    # Check for high resource usage
                    latest_metric = metrics[0] if metrics else None
                    if latest_metric:
                        if (
                            latest_metric['cpu_usage'] > 80 or
                            latest_metric['memory_usage'] > 80 or
                            latest_metric['disk_usage'] > 80
                        ):
                            await send_telegram_notification(
                                f"⚠️ High resource usage on server {server.name}\n"
                                f"CPU: {latest_metric['cpu_usage']}%\n"
                                f"Memory: {latest_metric['memory_usage']}%\n"
                                f"Disk: {latest_metric['disk_usage']}%"
                            )
                except Exception as e:
                    logger.error(f"Error monitoring server {server.name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in monitor_servers task: {str(e)}")

@shared_task
def check_server_health() -> None:
    """
    Check server health and perform automatic rotation if needed.
    This task should be run every 15 minutes.
    """
    try:
        async with ServerSyncManager() as sync_manager:
            servers = Server.objects.filter(is_active=True)
            
            for server in servers:
                try:
                    # Check server health
                    health = await sync_manager.check_server_health(server)
                    
                    # Record health check
                    ServerHealthCheck.objects.create(
                        server=server,
                        status=health['is_healthy'] and 'healthy' or 'offline',
                        cpu_usage=health['cpu_usage'],
                        memory_usage=health['memory_usage'],
                        disk_usage=health['disk_usage'],
                        uptime=health['uptime'],
                        error_message=health.get('error', '')
                    )
                    
                    # Rotate subscriptions if server is unhealthy
                    if not health['is_healthy']:
                        await sync_manager.rotate_subscriptions(server)
                        
                except Exception as e:
                    logger.error(f"Error checking health for server {server.name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in check_server_health task: {str(e)}")

@shared_task
def cleanup_old_monitoring_data() -> None:
    """
    Clean up old monitoring data to prevent database bloat.
    This task should be run daily.
    """
    try:
        # Keep only last 7 days of data
        cutoff_date = timezone.now() - timedelta(days=7)
        
        # Delete old metrics
        ServerMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # Delete old health checks
        ServerHealthCheck.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # Delete old rotation logs
        ServerRotationLog.objects.filter(timestamp__lt=cutoff_date).delete()
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_monitoring_data task: {str(e)}")

@shared_task
def update_seller_commissions() -> None:
    """
    Update seller commissions based on sales.
    This task should be run daily.
    """
    try:
        sellers = User.objects.filter(role__name='seller')
        
        for seller in sellers:
            try:
                # Calculate commission
                total_sales = seller.total_sales
                commission_rate = seller.commission_rate
                commission = total_sales * (commission_rate / 100)
                
                # Update seller's wallet
                seller.wallet_balance = F('wallet_balance') + commission
                seller.save()
                
                # Send notification
                if commission > 0:
                    await send_telegram_notification(
                        f"💰 Commission updated for seller {seller.username}\n"
                        f"Amount: {commission:.2f}"
                    )
            except Exception as e:
                logger.error(f"Error updating commission for seller {seller.username}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in update_seller_commissions task: {str(e)}")

@shared_task
def sync_accounts_task():
    """
    Synchronize all VPN accounts with the 3x-UI panel.
    This task updates account status, traffic usage, and expiration dates.
    """
    logger.info("Starting sync_accounts_task")
    try:
        # Get active subscriptions
        subscriptions = Subscription.objects.filter(status__in=['active', 'pending'])
        logger.info(f"Found {subscriptions.count()} active/pending subscriptions to sync")
        
        # Get panel credentials
        panel_url = os.environ.get('PANEL_URL', '')
        username = os.environ.get('PANEL_USERNAME', '')
        password = os.environ.get('PANEL_PASSWORD', '')
        
        if not all([panel_url, username, password]):
            logger.error("Missing panel credentials in environment variables")
            return False
        
        # Initialize connector
        connector = ThreeXUI_Connector(panel_url, username, password)
        if not connector.is_authenticated:
            logger.error("Failed to authenticate with 3x-UI panel")
            return False
        
        # Get all inbounds
        inbounds = connector.get_inbounds()
        if not inbounds:
            logger.error("Failed to get inbounds from panel")
            return False
        
        # Process each subscription
        for subscription in subscriptions:
            try:
                # Find client by email
                client_found = False
                client_data = None
                
                # Search in all inbounds
                for inbound in inbounds:
                    inbound_id = inbound.get('id')
                    clients = connector.get_clients(inbound_id)
                    
                    if not clients:
                        continue
                    
                    # Find client by email
                    for client in clients:
                        if client.get('email') == subscription.email:
                            client_found = True
                            client_data = client
                            
                            # Update subscription data
                            subscription.data_usage_gb = (client.get('up', 0) + client.get('down', 0)) / (1024 * 1024 * 1024)
                            
                            # Check expiration
                            expiry_time_ms = client.get('expiryTime', 0)
                            if expiry_time_ms > 0:
                                expiry_time = datetime.fromtimestamp(expiry_time_ms / 1000)
                                subscription.expiry_date = expiry_time
                                
                                # Update status if expired
                                if expiry_time < timezone.now():
                                    subscription.status = 'expired'
                            
                            subscription.save()
                            logger.info(f"Updated subscription for {subscription.email}")
                            break
                    
                    if client_found:
                        break
                
                if not client_found:
                    logger.warning(f"Client {subscription.email} not found in panel")
                    
                    # If subscription is active but client not found, create it
                    if subscription.status == 'active':
                        logger.info(f"Creating missing client for {subscription.email}")
                        # Find default inbound
                        default_inbound_id = None
                        for inbound in inbounds:
                            if inbound.get('protocol', '').lower() in ['vmess', 'vless', 'trojan']:
                                default_inbound_id = inbound.get('id')
                                break
                        
                        if default_inbound_id:
                            # Calculate expiry days
                            if subscription.expiry_date:
                                days_remaining = (subscription.expiry_date - timezone.now()).days
                                days_remaining = max(1, days_remaining)  # At least 1 day
                            else:
                                days_remaining = 30  # Default 30 days
                            
                            # Add client to panel
                            success = connector.add_client(
                                default_inbound_id,
                                subscription.email,
                                traffic_limit_gb=subscription.data_limit_gb or 0,
                                expire_days=days_remaining
                            )
                            
                            if success:
                                logger.info(f"Created client for {subscription.email}")
                            else:
                                logger.error(f"Failed to create client for {subscription.email}")
                
            except Exception as e:
                logger.error(f"Error processing subscription {subscription.email}: {str(e)}")
        
        logger.info("Completed sync_accounts_task successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in sync_accounts_task: {str(e)}")
        return False

@shared_task
def check_expirations_task():
    """
    Check for expired VPN accounts and update their status.
    This task also sends notifications for accounts about to expire.
    """
    logger.info("Starting check_expirations_task")
    try:
        # Get active subscriptions
        subscriptions = Subscription.objects.filter(status='active')
        logger.info(f"Checking {subscriptions.count()} active subscriptions for expiration")
        
        now = timezone.now()
        expiring_soon_count = 0
        expired_count = 0
        
        # Process each subscription
        for subscription in subscriptions:
            try:
                # Skip if no expiry date
                if not subscription.expiry_date:
                    continue
                
                # Check if expired
                if subscription.expiry_date <= now:
                    subscription.status = 'expired'
                    subscription.save()
                    expired_count += 1
                    logger.info(f"Marked subscription {subscription.email} as expired")
                    
                    # Notify user
                    user = subscription.user
                    if user:
                        # Send notification logic here
                        pass
                
                # Check if expiring soon (within 3 days)
                elif subscription.expiry_date <= now + timedelta(days=3):
                    expiring_soon_count += 1
                    logger.info(f"Subscription {subscription.email} expiring soon: {subscription.expiry_date}")
                    
                    # Notify user
                    user = subscription.user
                    if user:
                        # Send notification logic here
                        pass
                        
            except Exception as e:
                logger.error(f"Error checking expiration for {subscription.email}: {str(e)}")
        
        logger.info(f"Completed check_expirations_task: {expired_count} expired, {expiring_soon_count} expiring soon")
        return True
        
    except Exception as e:
        logger.error(f"Error in check_expirations_task: {str(e)}")
        return False

@shared_task
def sync_panel_data():
    """
    Celery task to sync data from all active panel configurations.
    """
    try:
        ThreeXUI_Connector.sync_all_panels()
        return True
    except Exception as e:
        logger.error(f"Error in sync_panel_data task: {str(e)}")
        return False

@shared_task
def check_panel_health():
    """
    Celery task to check health of all active panel configurations.
    """
    try:
        panels = PanelConfig.objects.filter(is_active=True, disable_check=False)
        
        for panel in panels:
            try:
                connector = ThreeXUI_Connector(
                    panel_url=panel.panel_url,
                    username=panel.username,
                    password=panel.password
                )
                
                if connector.authenticate():
                    status = connector.get_server_status()
                    if status:
                        # Update server status
                        server, _ = Server.objects.get_or_create(
                            sync_id=f"panel_{panel.server_id}",
                            defaults={
                                'name': f"3x-UI Panel ({panel.name})",
                                'host': panel.domain,
                                'port': panel.port,
                                'location': panel.location,
                                'type': 'xray',
                                'is_active': True
                            }
                        )
                        
                        server.cpu_usage = status.get('cpu', 0)
                        server.memory_usage = status.get('mem', 0)
                        server.disk_usage = status.get('disk', 0)
                        server.save()
                        
                        # Update panel last check time
                        panel.last_check = timezone.now()
                        panel.save()
                        
                        logger.info(f"Health check passed for panel {panel.name}")
                    else:
                        logger.error(f"Failed to get status from panel {panel.name}")
                else:
                    logger.error(f"Failed to authenticate with panel {panel.name}")
            
            except Exception as e:
                logger.error(f"Error checking panel {panel.name}: {str(e)}")
                continue
        
        return True
    
    except Exception as e:
        logger.error(f"Error in check_panel_health task: {str(e)}")
        return False 