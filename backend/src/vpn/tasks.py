"""
Celery tasks for VPN module
"""

import logging
from django.utils import timezone
from datetime import timedelta
from celery_app import app

logger = logging.getLogger(__name__)

@app.task
def sync_all_servers():
    """
    Synchronize all active VPN servers
    """
    from vpn.manager import VPNManager
    
    logger.info("Starting sync of all VPN servers")
    manager = VPNManager()
    results = manager.sync_all_servers()
    
    logger.info(f"VPN server sync completed: {results['success']} succeeded, {results['failed']} failed")
    return results


@app.task
def sync_server(server_id):
    """
    Synchronize a specific VPN server
    
    Args:
        server_id: ID of the server to sync
    """
    from vpn.manager import VPNManager
    
    logger.info(f"Starting sync of VPN server {server_id}")
    manager = VPNManager()
    success = manager.sync_server(server_id)
    
    if success:
        logger.info(f"VPN server {server_id} sync completed successfully")
    else:
        logger.error(f"VPN server {server_id} sync failed")
        
    return success


@app.task
def check_expired_accounts():
    """
    Check for expired VPN accounts and deactivate them
    """
    from vpn.models import VPNAccount
    
    logger.info("Checking for expired VPN accounts")
    now = timezone.now()
    
    # Find expired accounts that are still active
    expired_accounts = VPNAccount.objects.filter(
        is_active=True,
        expiry_date__lt=now
    )
    
    count = expired_accounts.count()
    if count > 0:
        # Deactivate expired accounts
        expired_accounts.update(is_active=False)
        logger.info(f"Deactivated {count} expired VPN accounts")
    else:
        logger.info("No expired VPN accounts found")
        
    return count


@app.task
def check_traffic_limits():
    """
    Check for VPN accounts that have exceeded their traffic limits
    """
    from vpn.models import VPNAccount
    
    logger.info("Checking for VPN accounts exceeding traffic limits")
    
    # Find accounts that have exceeded their traffic limits and are still active
    exceeded_accounts = VPNAccount.objects.filter(
        is_active=True,
        traffic_limit__gt=0,  # Only check accounts with a limit
        total_traffic__gte=models.F('traffic_limit')
    )
    
    count = exceeded_accounts.count()
    if count > 0:
        # Deactivate accounts that exceeded their limits
        exceeded_accounts.update(is_active=False)
        logger.info(f"Deactivated {count} VPN accounts that exceeded traffic limits")
    else:
        logger.info("No VPN accounts exceeding traffic limits found")
        
    return count


@app.task
def collect_server_metrics():
    """
    Collect metrics from all active servers and store in database
    """
    from vpn.models import Server, ServerMetrics
    
    logger.info("Collecting metrics from all active VPN servers")
    
    # Get all active servers
    servers = Server.objects.filter(is_active=True)
    
    metrics_count = 0
    for server in servers:
        try:
            # Create metrics record
            ServerMetrics.objects.create(
                server=server,
                cpu_usage=server.cpu_usage,
                memory_usage=server.memory_usage,
                disk_usage=server.disk_usage,
                active_users=server.get_active_users_count(),
                total_traffic=server.get_total_traffic()
            )
            metrics_count += 1
        except Exception as e:
            logger.error(f"Error collecting metrics for server {server.id}: {str(e)}")
            
    logger.info(f"Collected metrics for {metrics_count} VPN servers")
    return metrics_count


@app.task
def cleanup_old_metrics(days=30):
    """
    Clean up old server metrics
    
    Args:
        days: Number of days to keep metrics for
    """
    from vpn.models import ServerMetrics
    
    logger.info(f"Cleaning up server metrics older than {days} days")
    
    # Calculate cutoff date
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Delete old metrics
    result = ServerMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
    
    count = result[0] if isinstance(result, tuple) and len(result) > 0 else 0
    logger.info(f"Deleted {count} old server metrics records")
    
    return count


@app.task
def add_user_to_server(user_id, server_id, **kwargs):
    """
    Add a user to a VPN server
    
    Args:
        user_id: ID of the user
        server_id: ID of the server
        **kwargs: Additional parameters for add_user_to_server
    """
    from vpn.manager import VPNManager
    
    logger.info(f"Adding user {user_id} to VPN server {server_id}")
    
    manager = VPNManager()
    success = manager.add_user_to_server(user_id, server_id, **kwargs)
    
    if success:
        logger.info(f"Successfully added user {user_id} to VPN server {server_id}")
    else:
        logger.error(f"Failed to add user {user_id} to VPN server {server_id}")
        
    return success


@app.task
def remove_user_from_server(user_id, server_id):
    """
    Remove a user from a VPN server
    
    Args:
        user_id: ID of the user
        server_id: ID of the server
    """
    from vpn.manager import VPNManager
    
    logger.info(f"Removing user {user_id} from VPN server {server_id}")
    
    manager = VPNManager()
    success = manager.remove_user_from_server(user_id, server_id)
    
    if success:
        logger.info(f"Successfully removed user {user_id} from VPN server {server_id}")
    else:
        logger.error(f"Failed to remove user {user_id} from VPN server {server_id}")
        
    return success


@app.task
def move_user(user_id, from_server_id, to_server_id):
    """
    Move a user from one VPN server to another
    
    Args:
        user_id: ID of the user
        from_server_id: ID of the source server
        to_server_id: ID of the destination server
    """
    from vpn.manager import VPNManager
    
    logger.info(f"Moving user {user_id} from VPN server {from_server_id} to {to_server_id}")
    
    manager = VPNManager()
    success = manager.move_user(user_id, from_server_id, to_server_id)
    
    if success:
        logger.info(f"Successfully moved user {user_id} from VPN server {from_server_id} to {to_server_id}")
    else:
        logger.error(f"Failed to move user {user_id} from VPN server {from_server_id} to {to_server_id}")
        
    return success 