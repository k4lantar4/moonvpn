"""
MoonVPN Telegram Bot - System Stats Model

This module provides the SystemStats model for tracking and analyzing system metrics.
"""

import logging
import json
import psutil
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from core.database import execute_query, execute_insert, execute_update, execute_delete

logger = logging.getLogger(__name__)

class SystemStats:
    """System Stats model for tracking system metrics and performance."""
    
    @staticmethod
    def collect_system_stats() -> Dict[str, Any]:
        """
        Collect current system statistics.
        
        Returns:
            Dict[str, Any]: Dictionary with system statistics
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(logical=True),
                'physical_count': psutil.cpu_count(logical=False)
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            },
            'system': {
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'hostname': platform.node()
            }
        }
        
        # Get Docker container stats if applicable
        try:
            docker_stats = subprocess.check_output(
                "docker stats --no-stream --format '{{.Name}}: {{.CPUPerc}} CPU, {{.MemUsage}}' 2>/dev/null",
                shell=True, text=True
            )
            if docker_stats:
                stats['docker'] = docker_stats.strip().split('\n')
        except:
            stats['docker'] = []
            
        return stats
        
    @staticmethod
    def save_system_stats() -> int:
        """
        Collect and save current system statistics to database.
        
        Returns:
            int: ID of the saved stats record
        """
        stats = SystemStats.collect_system_stats()
        
        query = """
            INSERT INTO system_stats (
                stats_data, created_at
            ) VALUES (
                %s, CURRENT_TIMESTAMP
            )
        """
        
        return execute_insert(query, (json.dumps(stats),))
        
    @staticmethod
    def get_latest_stats() -> Dict[str, Any]:
        """
        Get the latest system statistics.
        
        Returns:
            Dict[str, Any]: Latest system statistics
        """
        query = """
            SELECT stats_data
            FROM system_stats
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = execute_query(query, fetch="one")
        
        if result and 'stats_data' in result:
            try:
                return json.loads(result['stats_data'])
            except:
                pass
                
        # If no stats in database or error, collect new stats
        return SystemStats.collect_system_stats()
        
    @staticmethod
    def get_app_stats() -> Dict[str, Any]:
        """
        Get application statistics (users, accounts, etc.).
        
        Returns:
            Dict[str, Any]: Application statistics
        """
        # Get user counts
        query1 = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 HOURS' THEN 1 END) as new_users_24h,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 DAYS' THEN 1 END) as new_users_7d,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 DAYS' THEN 1 END) as new_users_30d
            FROM users
        """
        result1 = execute_query(query1, fetch="one")
        
        # Get account counts
        query2 = """
            SELECT 
                COUNT(*) as total_accounts,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_accounts,
                COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_accounts,
                COUNT(CASE WHEN status = 'suspended' THEN 1 END) as suspended_accounts,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 HOURS' THEN 1 END) as new_accounts_24h,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 DAYS' THEN 1 END) as new_accounts_7d
            FROM vpn_accounts
        """
        result2 = execute_query(query2, fetch="one")
        
        # Get payment stats
        query3 = """
            SELECT 
                COUNT(*) as total_payments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_payments,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_payments,
                SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as total_revenue,
                SUM(CASE WHEN status = 'completed' AND created_at >= NOW() - INTERVAL '24 HOURS' THEN amount ELSE 0 END) as revenue_24h,
                SUM(CASE WHEN status = 'completed' AND created_at >= NOW() - INTERVAL '7 DAYS' THEN amount ELSE 0 END) as revenue_7d,
                SUM(CASE WHEN status = 'completed' AND created_at >= NOW() - INTERVAL '30 DAYS' THEN amount ELSE 0 END) as revenue_30d
            FROM payments
        """
        result3 = execute_query(query3, fetch="one")
        
        # Get ticket stats
        query4 = """
            SELECT 
                COUNT(*) as total_tickets,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_tickets,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_tickets,
                COUNT(CASE WHEN assigned_to IS NULL AND status = 'open' THEN 1 END) as unassigned_tickets,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 HOURS' THEN 1 END) as new_tickets_24h
            FROM tickets
        """
        result4 = execute_query(query4, fetch="one")
        
        # Get server stats
        query5 = """
            SELECT 
                COUNT(*) as total_servers,
                COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_servers,
                COUNT(CASE WHEN is_active = FALSE THEN 1 END) as inactive_servers
            FROM servers
        """
        result5 = execute_query(query5, fetch="one")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'users': result1 or {},
            'accounts': result2 or {},
            'payments': result3 or {},
            'tickets': result4 or {},
            'servers': result5 or {}
        }
        
    @staticmethod
    def get_daily_stats(days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the past N days.
        
        Args:
            days (int, optional): Number of days to retrieve. Defaults to 30.
            
        Returns:
            List[Dict[str, Any]]: List of daily statistics
        """
        query = """
            WITH dates AS (
                SELECT generate_series(
                    NOW() - INTERVAL '%s DAYS',
                    NOW(),
                    INTERVAL '1 DAY'
                )::DATE as date
            ),
            new_users AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM users
                WHERE created_at >= NOW() - INTERVAL '%s DAYS'
                GROUP BY DATE(created_at)
            ),
            new_accounts AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM vpn_accounts
                WHERE created_at >= NOW() - INTERVAL '%s DAYS'
                GROUP BY DATE(created_at)
            ),
            payments AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as revenue
                FROM payments
                WHERE created_at >= NOW() - INTERVAL '%s DAYS'
                GROUP BY DATE(created_at)
            ),
            tickets AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM tickets
                WHERE created_at >= NOW() - INTERVAL '%s DAYS'
                GROUP BY DATE(created_at)
            )
            SELECT 
                d.date,
                COALESCE(u.count, 0) as new_users,
                COALESCE(a.count, 0) as new_accounts,
                COALESCE(p.count, 0) as payments,
                COALESCE(p.revenue, 0) as revenue,
                COALESCE(t.count, 0) as tickets
            FROM dates d
            LEFT JOIN new_users u ON d.date = u.date
            LEFT JOIN new_accounts a ON d.date = a.date
            LEFT JOIN payments p ON d.date = p.date
            LEFT JOIN tickets t ON d.date = t.date
            ORDER BY d.date
        """
        
        results = execute_query(query, (days, days, days, days, days))
        
        return [dict(result) for result in results]
        
    @staticmethod
    def clean_old_stats(days: int = 90) -> int:
        """
        Delete old system statistics.
        
        Args:
            days (int, optional): Days to keep. Defaults to 90.
            
        Returns:
            int: Number of records deleted
        """
        query = """
            DELETE FROM system_stats
            WHERE created_at < NOW() - INTERVAL %s DAY
        """
        
        return execute_delete(query, (days,))
        
    @staticmethod
    def get_database_size() -> Dict[str, Any]:
        """
        Get database size statistics.
        
        Returns:
            Dict[str, Any]: Database size statistics
        """
        # Get database size
        query1 = """
            SELECT pg_database_size(current_database()) as size
        """
        result1 = execute_query(query1, fetch="one")
        
        # Get table sizes
        query2 = """
            SELECT 
                table_name,
                pg_relation_size('public.' || quote_ident(table_name)) as size,
                pg_total_relation_size('public.' || quote_ident(table_name)) as total_size
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY total_size DESC
        """
        result2 = execute_query(query2)
        
        return {
            'database_size': result1.get('size', 0) if result1 else 0,
            'tables': result2
        }
        
    @staticmethod
    def get_system_uptime() -> Dict[str, Any]:
        """
        Get system uptime statistics.
        
        Returns:
            Dict[str, Any]: System uptime statistics
        """
        # System uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        # Try to get service uptime (bot, api, etc.)
        service_uptimes = {}
        try:
            # Bot service
            bot_output = subprocess.check_output(
                "systemctl show moonvpn-bot -p ActiveState,SubState,ActiveEnterTimestamp 2>/dev/null",
                shell=True, text=True
            )
            if bot_output:
                lines = bot_output.strip().split('\n')
                state = next((line.split('=')[1] for line in lines if line.startswith('ActiveState=')), None)
                timestamp_line = next((line for line in lines if line.startswith('ActiveEnterTimestamp=')), None)
                if timestamp_line and state == 'active':
                    timestamp_str = timestamp_line.split('=')[1].strip()
                    timestamp = datetime.strptime(timestamp_str, '%a %Y-%m-%d %H:%M:%S %Z')
                    service_uptimes['bot'] = (datetime.now() - timestamp).total_seconds()
                    
            # API service
            api_output = subprocess.check_output(
                "systemctl show moonvpn-api -p ActiveState,SubState,ActiveEnterTimestamp 2>/dev/null",
                shell=True, text=True
            )
            if api_output:
                lines = api_output.strip().split('\n')
                state = next((line.split('=')[1] for line in lines if line.startswith('ActiveState=')), None)
                timestamp_line = next((line for line in lines if line.startswith('ActiveEnterTimestamp=')), None)
                if timestamp_line and state == 'active':
                    timestamp_str = timestamp_line.split('=')[1].strip()
                    timestamp = datetime.strptime(timestamp_str, '%a %Y-%m-%d %H:%M:%S %Z')
                    service_uptimes['api'] = (datetime.now() - timestamp).total_seconds()
        except:
            logger.exception("Error getting service uptime")
            
        return {
            'system_boot_time': boot_time.isoformat(),
            'system_uptime_seconds': uptime.total_seconds(),
            'system_uptime_days': uptime.days,
            'service_uptimes': service_uptimes
        }
        
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format bytes to human-readable size.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Human-readable size
        """
        if size_bytes == 0:
            return "0B"
            
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
            
        return f"{size_bytes:.2f}{size_names[i]}"
        
    @staticmethod
    def format_uptime(seconds: int) -> str:
        """
        Format seconds to human-readable uptime.
        
        Args:
            seconds (int): Uptime in seconds
            
        Returns:
            str: Human-readable uptime
        """
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s" 