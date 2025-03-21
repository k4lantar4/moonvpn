"""
Monitoring service for MoonVPN Telegram Bot.

This module provides services for monitoring system status and sending updates.
"""

import asyncio
import psutil
import platform
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database.models.admin import AdminGroupType
from app.bot.services.notification_service import NotificationService

class MonitoringService:
    """Service for monitoring system status and sending updates."""
    
    def __init__(self, db: Session, notification_service: NotificationService):
        """Initialize the monitoring service.
        
        Args:
            db: Database session
            notification_service: Notification service instance
        """
        self.db = db
        self.notification_service = notification_service
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_monitoring(self, interval: int = 300) -> None:
        """Start the monitoring service.
        
        Args:
            interval: Monitoring interval in seconds (default: 5 minutes)
        """
        if self._is_running:
            return
        
        self._is_running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring service."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self, interval: int) -> None:
        """Run the monitoring loop.
        
        Args:
            interval: Monitoring interval in seconds
        """
        while self._is_running:
            try:
                # Get system status
                status = self._get_system_status()
                
                # Send status update
                await self.notification_service.send_system_status(
                    status=status,
                    target_groups=[AdminGroupType.MANAGE, AdminGroupType.REPORTS]
                )
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                # Log error and continue monitoring
                print(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status.
        
        Returns:
            Dictionary containing system status information
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network status
            net_io = psutil.net_io_counters()
            network_status = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
            # System uptime
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            # System information
            system_info = {
                'os': platform.system(),
                'os_release': platform.release(),
                'os_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor()
            }
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory_percent,
                'disk_usage': disk_percent,
                'network_status': network_status,
                'uptime': uptime_str,
                'system_info': system_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting system status: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Check the health of various services.
        
        Returns:
            Dictionary containing service health information
        """
        try:
            # Check database connection
            db_status = self._check_database_connection()
            
            # Check network connectivity
            network_status = self._check_network_connectivity()
            
            # Check disk space
            disk_status = self._check_disk_space()
            
            # Check memory usage
            memory_status = self._check_memory_usage()
            
            # Check CPU usage
            cpu_status = self._check_cpu_usage()
            
            return {
                'database': db_status,
                'network': network_status,
                'disk': disk_status,
                'memory': memory_status,
                'cpu': cpu_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error checking service health: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connection status.
        
        Returns:
            Dictionary containing database status
        """
        try:
            # Try to execute a simple query
            self.db.execute("SELECT 1")
            return {
                'status': 'healthy',
                'message': 'Database connection is working'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database connection error: {str(e)}'
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity status.
        
        Returns:
            Dictionary containing network status
        """
        try:
            # Get network interface statistics
            net_if_stats = psutil.net_if_stats()
            net_if_addrs = psutil.net_if_addrs()
            
            # Check if any interface is up
            active_interfaces = [
                iface for iface, stats in net_if_stats.items()
                if stats.isup
            ]
            
            if active_interfaces:
                return {
                    'status': 'healthy',
                    'message': f'Network is up with {len(active_interfaces)} active interfaces',
                    'active_interfaces': active_interfaces
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'No active network interfaces found'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Network check error: {str(e)}'
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space status.
        
        Returns:
            Dictionary containing disk status
        """
        try:
            disk = psutil.disk_usage('/')
            
            # Define thresholds
            warning_threshold = 80  # 80%
            critical_threshold = 90  # 90%
            
            if disk.percent >= critical_threshold:
                status = 'critical'
                message = f'Disk space critically low: {disk.percent}% used'
            elif disk.percent >= warning_threshold:
                status = 'warning'
                message = f'Disk space running low: {disk.percent}% used'
            else:
                status = 'healthy'
                message = f'Disk space is good: {disk.percent}% used'
            
            return {
                'status': status,
                'message': message,
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Disk check error: {str(e)}'
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage status.
        
        Returns:
            Dictionary containing memory status
        """
        try:
            memory = psutil.virtual_memory()
            
            # Define thresholds
            warning_threshold = 80  # 80%
            critical_threshold = 90  # 90%
            
            if memory.percent >= critical_threshold:
                status = 'critical'
                message = f'Memory usage critically high: {memory.percent}%'
            elif memory.percent >= warning_threshold:
                status = 'warning'
                message = f'Memory usage high: {memory.percent}%'
            else:
                status = 'healthy'
                message = f'Memory usage is good: {memory.percent}%'
            
            return {
                'status': status,
                'message': message,
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Memory check error: {str(e)}'
            }
    
    def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage status.
        
        Returns:
            Dictionary containing CPU status
        """
        try:
            # Get CPU usage for the last 1 second
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Define thresholds
            warning_threshold = 80  # 80%
            critical_threshold = 90  # 90%
            
            if cpu_percent >= critical_threshold:
                status = 'critical'
                message = f'CPU usage critically high: {cpu_percent}%'
            elif cpu_percent >= warning_threshold:
                status = 'warning'
                message = f'CPU usage high: {cpu_percent}%'
            else:
                status = 'healthy'
                message = f'CPU usage is good: {cpu_percent}%'
            
            return {
                'status': status,
                'message': message,
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'CPU check error: {str(e)}'
            } 