"""
Server synchronization utilities.

This module provides functions for:
- Multi-server synchronization
- Server health monitoring
- Configuration management
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.utils import timezone
from main.models import Server, User
from v2ray.models import Inbound, Client

logger = logging.getLogger(__name__)

class ServerSyncError(Exception):
    """Base exception for server synchronization errors."""
    pass

def sync_server(server: Server) -> bool:
    """
    Synchronize server configuration and status.
    
    Args:
        server: Server instance to sync
        
    Returns:
        True if sync successful, False otherwise
    """
    try:
        # Get server status
        status = get_server_status(server)
        
        # Update server status
        server.is_active = status.get('is_active', False)
        server.is_synced = True
        server.last_sync = timezone.now()
        server.save()
        
        # Sync inbounds
        sync_inbounds(server)
        
        # Sync clients
        sync_clients(server)
        
        return True
    except Exception as e:
        logger.error(f"Error syncing server {server.name}: {str(e)}")
        server.is_synced = False
        server.save()
        return False

def get_server_status(server: Server) -> Dict:
    """
    Get server status from API.
    
    Args:
        server: Server instance
        
    Returns:
        Server status data
    """
    url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/status"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def sync_inbounds(server: Server) -> None:
    """
    Synchronize server inbounds.
    
    Args:
        server: Server instance
    """
    url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/inbounds"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    inbounds_data = response.json()
    
    for inbound_data in inbounds_data:
        Inbound.objects.update_or_create(
            server=server,
            port=inbound_data['port'],
            defaults={
                'protocol': inbound_data['protocol'],
                'settings': inbound_data['settings'],
                'stream_settings': inbound_data['stream_settings'],
                'remark': inbound_data['remark']
            }
        )

def sync_clients(server: Server) -> None:
    """
    Synchronize server clients.
    
    Args:
        server: Server instance
    """
    url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/clients"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    clients_data = response.json()
    
    for client_data in clients_data:
        try:
            user = User.objects.get(id=client_data['user_id'])
            inbound = Inbound.objects.get(
                server=server,
                port=client_data['inbound_port']
            )
            
            Client.objects.update_or_create(
                user=user,
                inbound=inbound,
                defaults={
                    'email': client_data['email'],
                    'uuid': client_data['uuid'],
                    'flow': client_data.get('flow', ''),
                    'total_gb': client_data['total_gb'],
                    'expire_days': client_data['expire_days'],
                    'enable': client_data['enable']
                }
            )
        except (User.DoesNotExist, Inbound.DoesNotExist) as e:
            logger.error(f"Error syncing client: {str(e)}")

def sync_all_servers() -> Dict[str, int]:
    """
    Synchronize all active servers.
    
    Returns:
        Dict with sync results
    """
    results = {
        'total': 0,
        'success': 0,
        'failed': 0
    }
    
    servers = Server.objects.filter(is_active=True)
    results['total'] = servers.count()
    
    for server in servers:
        if sync_server(server):
            results['success'] += 1
        else:
            results['failed'] += 1
    
    return results

def check_server_health(server: Server) -> Dict:
    """
    Check server health status.
    
    Args:
        server: Server instance
        
    Returns:
        Health status data
    """
    try:
        status = get_server_status(server)
        return {
            'is_healthy': status.get('is_active', False),
            'cpu_usage': status.get('cpu_usage', 0),
            'memory_usage': status.get('memory_usage', 0),
            'disk_usage': status.get('disk_usage', 0),
            'uptime': status.get('uptime', 0),
            'last_check': timezone.now()
        }
    except Exception as e:
        logger.error(f"Error checking server health: {str(e)}")
        return {
            'is_healthy': False,
            'error': str(e),
            'last_check': timezone.now()
        }

def get_server_metrics(server: Server, hours: int = 24) -> List[Dict]:
    """
    Get server metrics history.
    
    Args:
        server: Server instance
        hours: Number of hours of history
        
    Returns:
        List of metric data points
    """
    try:
        url = f"{settings.V2RAY_API_URL}/server/{server.sync_id}/metrics"
        params = {'hours': hours}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting server metrics: {str(e)}")
        return [] 