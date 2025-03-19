"""
API utility functions for interacting with the backend.

This module provides utility functions for:
- Server monitoring and health checks
- Traffic usage tracking
- System metrics collection
- Data formatting and caching
"""

import logging
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import time
from functools import lru_cache
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    pass

class APIRequestError(APIError):
    """Exception for API request errors."""
    pass

class APITimeoutError(APIError):
    """Exception for API timeout errors."""
    pass

def format_number(number: Union[int, float], decimal_places: int = 2) -> str:
    """
    Format a number with commas as thousands separators and fixed decimal places.
    
    Args:
        number: The number to format
        decimal_places: Number of decimal places to show
        
    Returns:
        Formatted number string
    """
    if isinstance(number, int):
        return f"{number:,}"
    return f"{number:,.{decimal_places}f}"

def format_date(date_obj: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format a date object or string as a readable date string.
    
    Args:
        date_obj: The date to format (datetime object or ISO format string)
        format_str: The format string to use
        
    Returns:
        Formatted date string
    """
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except ValueError:
            return date_obj
    
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_str)
    
    return str(date_obj)

def _create_session() -> requests.Session:
    """
    Create a requests session with retry strategy.
    
    Returns:
        Configured requests session
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def _make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: int = 30
) -> Dict:
    """
    Make an API request to the backend with retry logic.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        data: Request body data
        params: Query parameters
        headers: Additional headers
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dict
        
    Raises:
        APIRequestError: If request fails
        APITimeoutError: If request times out
    """
    url = f"{settings.API_BASE_URL}{endpoint}"
    
    try:
        session = _create_session()
        response = session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"API request timed out: {endpoint}")
        raise APITimeoutError(f"Request to {endpoint} timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise APIRequestError(f"Request to {endpoint} failed: {str(e)}")
    finally:
        session.close()

@lru_cache(maxsize=100)
def get_server_status(server_id: int) -> Dict:
    """
    Get server status and monitoring data with caching.
    
    Args:
        server_id: Server ID
        
    Returns:
        Server status data
    """
    return _make_request('GET', f'/v2ray/monitoring/{server_id}/')

@lru_cache(maxsize=100)
def get_server_stats(server_id: int) -> Dict:
    """
    Get server statistics with caching.
    
    Args:
        server_id: Server ID
        
    Returns:
        Server statistics data
    """
    return _make_request('GET', f'/v2ray/monitoring/{server_id}/stats/')

def get_server_history(
    server_id: int,
    hours: int = 24
) -> List[Dict]:
    """
    Get server monitoring history.
    
    Args:
        server_id: Server ID
        hours: Number of hours of history to retrieve
        
    Returns:
        List of monitoring data points
    """
    return _make_request(
        'GET',
        f'/v2ray/monitoring/{server_id}/history/',
        params={'hours': hours}
    )

@lru_cache(maxsize=1)
def get_all_servers_health() -> List[Dict]:
    """
    Get health status for all servers with caching.
    
    Returns:
        List of server health data
    """
    return _make_request('GET', '/v2ray/monitoring/all_health/')

def get_server_traffic(server_id: int) -> Dict:
    """
    Get server traffic statistics.
    
    Args:
        server_id: Server ID
        
    Returns:
        Traffic statistics data
    """
    return _make_request('GET', f'/v2ray/monitoring/{server_id}/traffic/')

def get_server_system(server_id: int) -> Dict:
    """
    Get server system statistics.
    
    Args:
        server_id: Server ID
        
    Returns:
        System statistics data
    """
    return _make_request('GET', f'/v2ray/monitoring/{server_id}/system/')

def get_server_network(server_id: int) -> Dict:
    """
    Get server network statistics.
    
    Args:
        server_id: Server ID
        
    Returns:
        Network statistics data
    """
    return _make_request('GET', f'/v2ray/monitoring/{server_id}/network/')

def format_bytes(bytes_value: Union[int, float]) -> str:
    """
    Format bytes to human readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g. "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"

def format_speed(bytes_per_sec: float) -> str:
    """
    Format bytes per second to Mbps.
    
    Args:
        bytes_per_sec: Bytes per second
        
    Returns:
        Formatted string (e.g. "10.5 Mbps")
    """
    return f"{bytes_per_sec * 8 / 1_000_000:.2f} Mbps"

def format_percentage(value: float) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value
        
    Returns:
        Formatted string (e.g. "45.2%")
    """
    return f"{value:.1f}%"

def format_uptime(seconds: int) -> str:
    """
    Format uptime in seconds to human readable string.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Formatted string (e.g. "5 days 2 hours")
    """
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} days")
    if hours > 0:
        parts.append(f"{hours} hours")
    if minutes > 0:
        parts.append(f"{minutes} minutes")
        
    return " ".join(parts) if parts else "Less than a minute"

def get_server_health_status(server_id: int) -> Tuple[str, str]:
    """
    Get server health status and emoji.
    
    Args:
        server_id: Server ID
        
    Returns:
        Tuple of (status, emoji)
    """
    try:
        status = get_server_status(server_id)
        health = status.get('health_status', 'unknown')
        
        emojis = {
            'healthy': '🟢',
            'warning': '🟡',
            'critical': '🔴',
            'offline': '⚫',
            'unknown': '⚪'
        }
        
        return health, emojis.get(health, '⚪')
    except APIError:
        return 'unknown', '⚪'

def get_server_performance_summary(server_id: int) -> Dict:
    """
    Get server performance summary.
    
    Args:
        server_id: Server ID
        
    Returns:
        Performance summary data
    """
    try:
        stats = get_server_stats(server_id)
        return {
            'cpu': {
                'current': stats['cpu']['avg'],
                'max': stats['cpu']['max'],
                'trend': 'increasing' if stats['cpu']['max'] > 80 else 'stable'
            },
            'memory': {
                'current': stats['memory']['avg'],
                'max': stats['memory']['max'],
                'trend': 'increasing' if stats['memory']['max'] > 80 else 'stable'
            },
            'disk': {
                'current': stats['disk']['avg'],
                'max': stats['disk']['max'],
                'trend': 'increasing' if stats['disk']['max'] > 80 else 'stable'
            },
            'network': {
                'current': stats['network']['current_speed_mbps'][1],
                'max': stats['network']['total_usage_gb'],
                'trend': 'increasing' if stats['network']['total_usage_gb'] > 100 else 'stable'
            }
        }
    except APIError:
        return {} 