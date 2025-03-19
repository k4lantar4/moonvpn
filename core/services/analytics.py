"""
Analytics manager service for collecting and analyzing system metrics.
Handles user behavior tracking, performance monitoring, and data analysis.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import aiofiles
from collections import defaultdict
import pandas as pd
import numpy as np
from prometheus_client import start_http_server, Counter, Gauge, Histogram

from .notification_service import NotificationService
from ..config.security_config import ANALYTICS_SETTINGS

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Manages analytics collection and analysis for the VPN service."""
    
    def __init__(self, db_connection, notification_service: NotificationService):
        """Initialize the analytics manager."""
        self.db = db_connection
        self.notification_service = notification_service
        self.metrics_cache = {}
        self.update_interval = ANALYTICS_SETTINGS.get('UPDATE_INTERVAL', 3600)  # 1 hour
        self.retention_days = ANALYTICS_SETTINGS.get('RETENTION_DAYS', 90)
        self._running = False
        
        # Prometheus metrics
        self.active_users = Gauge('vpn_active_users', 'Number of active VPN users')
        self.traffic_total = Counter('vpn_traffic_total', 'Total VPN traffic in bytes')
        self.server_load = Gauge('vpn_server_load', 'Server load percentage')
        self.request_latency = Histogram('vpn_request_latency', 'Request latency in seconds')

    async def start_analytics_service(self):
        """Start the analytics service."""
        if self._running:
            return

        self._running = True
        # Start Prometheus metrics server
        start_http_server(ANALYTICS_SETTINGS.get('PROMETHEUS_PORT', 9090))
        asyncio.create_task(self._analytics_loop())
        logger.info("Analytics service started")

    async def stop_analytics_service(self):
        """Stop the analytics service."""
        self._running = False
        logger.info("Analytics service stopped")

    async def _analytics_loop(self):
        """Main analytics loop that collects and processes metrics."""
        while self._running:
            try:
                metrics = await self.collect_metrics()
                await self._store_metrics(metrics)
                await self._analyze_trends(metrics)
                await self._generate_reports(metrics)
                await self._cleanup_old_data()
                
                # Update Prometheus metrics
                await self._update_prometheus_metrics(metrics)
                
            except Exception as e:
                logger.error(f"Analytics loop error: {e}")
                await self.notification_service.notify_admin(
                    f"Analytics Error: {str(e)}"
                )
            
            await asyncio.sleep(self.update_interval)

    async def collect_metrics(self) -> Dict:
        """Collect all system metrics."""
        try:
            metrics = {
                'user_metrics': await self._collect_user_metrics(),
                'server_metrics': await self._collect_server_metrics(),
                'traffic_metrics': await self._collect_traffic_metrics(),
                'security_metrics': await self._collect_security_metrics(),
                'financial_metrics': await self._collect_financial_metrics(),
                'performance_metrics': await self._collect_performance_metrics()
            }
            
            self.metrics_cache = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            raise

    async def _collect_user_metrics(self) -> Dict:
        """Collect user-related metrics."""
        try:
            active_users = await self.db.users.count_documents({'status': 'active'})
            self.active_users.set(active_users)
            
            return {
                'total_users': await self.db.users.count_documents({}),
                'active_users': active_users,
                'new_users_24h': await self._count_new_users(hours=24),
                'subscription_distribution': await self._get_subscription_distribution(),
                'user_retention': await self._calculate_user_retention(),
                'geographic_distribution': await self._get_user_locations(),
                'device_distribution': await self._get_device_distribution(),
                'peak_usage_times': await self._analyze_usage_patterns()
            }
        except Exception as e:
            logger.error(f"Error collecting user metrics: {e}")
            raise

    async def _collect_server_metrics(self) -> Dict:
        """Collect server performance metrics."""
        try:
            servers = await self.db.servers.find({}).to_list(length=None)
            metrics = {
                'total_servers': len(servers),
                'active_servers': sum(1 for s in servers if s['status'] == 'active'),
                'server_load': {},
                'bandwidth_usage': {},
                'connection_count': {},
                'error_rates': {},
                'latency': {}
            }
            
            for server in servers:
                server_id = str(server['_id'])
                load = await self._get_server_load(server_id)
                self.server_load.labels(server_id=server_id).set(load)
                
                metrics['server_load'][server_id] = load
                metrics['bandwidth_usage'][server_id] = await self._get_bandwidth_usage(server_id)
                metrics['connection_count'][server_id] = await self._get_connection_count(server_id)
                metrics['error_rates'][server_id] = await self._get_error_rate(server_id)
                metrics['latency'][server_id] = await self._get_server_latency(server_id)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting server metrics: {e}")
            raise

    async def _collect_traffic_metrics(self) -> Dict:
        """Collect traffic-related metrics."""
        try:
            current_traffic = await self._get_current_traffic()
            self.traffic_total.inc(current_traffic['total_bytes'])
            
            return {
                'total_traffic': current_traffic,
                'traffic_by_protocol': await self._get_traffic_by_protocol(),
                'peak_traffic_times': await self._analyze_traffic_patterns(),
                'bandwidth_utilization': await self._get_bandwidth_utilization(),
                'traffic_anomalies': await self._detect_traffic_anomalies()
            }
        except Exception as e:
            logger.error(f"Error collecting traffic metrics: {e}")
            raise

    async def _collect_security_metrics(self) -> Dict:
        """Collect security-related metrics."""
        try:
            return {
                'blocked_ips': await self._get_blocked_ips_count(),
                'suspicious_activities': await self._get_suspicious_activities(),
                'failed_logins': await self._get_failed_login_attempts(),
                'security_incidents': await self._get_security_incidents(),
                'vulnerability_scan': await self._perform_vulnerability_scan()
            }
        except Exception as e:
            logger.error(f"Error collecting security metrics: {e}")
            raise

    async def _analyze_trends(self, metrics: Dict):
        """Analyze metric trends and patterns."""
        try:
            trends = {
                'user_growth': await self._calculate_growth_rate(metrics['user_metrics']),
                'server_health': await self._analyze_server_health(metrics['server_metrics']),
                'traffic_patterns': await self._analyze_traffic_trends(metrics['traffic_metrics']),
                'security_trends': await self._analyze_security_trends(metrics['security_metrics']),
                'performance_trends': await self._analyze_performance_trends(metrics['performance_metrics'])
            }
            
            # Store trends for reporting
            await self._store_trends(trends)
            
            # Check for anomalies and send alerts
            await self._check_anomalies(trends)
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            raise

    async def _generate_reports(self, metrics: Dict):
        """Generate analytics reports."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            reports = {
                'daily_summary': await self._generate_daily_summary(metrics),
                'weekly_analysis': await self._generate_weekly_analysis(metrics),
                'monthly_report': await self._generate_monthly_report(metrics)
            }
            
            # Save reports
            report_path = f"{ANALYTICS_SETTINGS['REPORTS_PATH']}/report_{timestamp}.json"
            async with aiofiles.open(report_path, 'w') as f:
                await f.write(json.dumps(reports, indent=2))
            
            # Send notification for important findings
            await self._notify_important_findings(reports)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            raise

    async def _cleanup_old_data(self):
        """Clean up old analytics data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Clean up old metrics
            await self.db.metrics.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            # Clean up old reports
            await self._cleanup_old_reports(cutoff_date)
            
            logger.info(f"Cleaned up analytics data older than {cutoff_date}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise

    async def get_analytics_status(self) -> Dict:
        """Get current analytics service status."""
        try:
            return {
                'running': self._running,
                'last_update': self.metrics_cache.get('timestamp'),
                'metrics_count': len(self.metrics_cache),
                'update_interval': self.update_interval,
                'retention_days': self.retention_days,
                'storage_usage': await self._get_storage_usage(),
                'enabled_metrics': list(self.metrics_cache.keys())
            }
        except Exception as e:
            logger.error(f"Error getting analytics status: {e}")
            return {
                'error': str(e),
                'running': self._running
            }

    async def _update_prometheus_metrics(self, metrics: Dict):
        """Update Prometheus metrics."""
        try:
            # Update user metrics
            self.active_users.set(metrics['user_metrics']['active_users'])
            
            # Update traffic metrics
            self.traffic_total.inc(metrics['traffic_metrics']['total_traffic']['total_bytes'])
            
            # Update server metrics
            for server_id, load in metrics['server_metrics']['server_load'].items():
                self.server_load.labels(server_id=server_id).set(load)
            
            # Update latency metrics
            for server_id, latency in metrics['server_metrics']['latency'].items():
                self.request_latency.observe(latency)
                
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
            raise

    async def _notify_important_findings(self, reports: Dict):
        """Notify administrators of important findings."""
        try:
            findings = []
            
            # Check for significant changes
            if reports['daily_summary']['user_growth_rate'] > 10:
                findings.append(f"High user growth rate: {reports['daily_summary']['user_growth_rate']}%")
            
            if reports['daily_summary']['error_rate'] > 5:
                findings.append(f"High error rate: {reports['daily_summary']['error_rate']}%")
            
            if reports['daily_summary']['server_load'] > 80:
                findings.append(f"High server load: {reports['daily_summary']['server_load']}%")
            
            if findings:
                await self.notification_service.notify_admin(
                    "Important Analytics Findings",
                    "\n".join(findings)
                )
                
        except Exception as e:
            logger.error(f"Error notifying important findings: {e}")
            raise

    async def export_analytics_data(self, start_date: datetime, end_date: datetime,
                                  format: str = 'json') -> str:
        """Export analytics data for a specific time range."""
        try:
            data = await self.db.metrics.find({
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }).to_list(length=None)
            
            if format == 'csv':
                df = pd.DataFrame(data)
                return df.to_csv(index=False)
            else:
                return json.dumps(data, default=str, indent=2)
                
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            raise

    async def generate_custom_report(self, metrics: List[str],
                                   start_date: datetime,
                                   end_date: datetime) -> Dict:
        """Generate a custom analytics report."""
        try:
            report_data = {}
            
            for metric in metrics:
                data = await self.db.metrics.find({
                    'metric_type': metric,
                    'timestamp': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }).to_list(length=None)
                
                report_data[metric] = {
                    'data': data,
                    'summary': await self._generate_metric_summary(data)
                }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            raise

    async def _generate_metric_summary(self, data: List[Dict]) -> Dict:
        """Generate summary statistics for a metric."""
        try:
            values = [d['value'] for d in data if 'value' in d]
            
            if not values:
                return {}
                
            return {
                'count': len(values),
                'mean': np.mean(values),
                'median': np.median(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'percentiles': {
                    '25': np.percentile(values, 25),
                    '75': np.percentile(values, 75),
                    '90': np.percentile(values, 90),
                    '95': np.percentile(values, 95),
                    '99': np.percentile(values, 99)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating metric summary: {e}")
            raise 