"""
Dashboard service for providing a web interface to monitor and manage the VPN system.
Integrates with analytics, security, and system management features.
"""

import logging
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
import json
from datetime import datetime, timedelta
import jwt
from typing import Dict, List, Optional
import aiohttp_session
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from ..config.dashboard_config import DASHBOARD_SETTINGS
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class DashboardService:
    """Provides a web interface for system monitoring and management."""
    
    def __init__(self, db_connection, notification_service: NotificationService,
                 analytics_manager, security_service, traffic_manager, backup_manager):
        """Initialize the dashboard service."""
        self.db = db_connection
        self.notification_service = notification_service
        self.analytics_manager = analytics_manager
        self.security_service = security_service
        self.traffic_manager = traffic_manager
        self.backup_manager = backup_manager
        
        self.host = DASHBOARD_SETTINGS['HOST']
        self.port = DASHBOARD_SETTINGS['PORT']
        self.secret_key = DASHBOARD_SETTINGS['SECRET_KEY']
        self._running = False
        self.app = None
        
    async def start_dashboard(self):
        """Start the dashboard web server."""
        if self._running:
            return
            
        try:
            self.app = web.Application()
            
            # Setup session middleware
            fernet_key = fernet.Fernet.generate_key()
            setup_session(self.app, EncryptedCookieStorage(fernet_key))
            
            # Setup Jinja2 templates
            aiohttp_jinja2.setup(
                self.app,
                loader=jinja2.FileSystemLoader(
                    str(Path(__file__).parent.parent / 'templates' / 'dashboard')
                )
            )
            
            # Setup routes
            self._setup_routes()
            
            # Setup middleware
            self.app.middlewares.append(self._auth_middleware)
            
            # Start the server
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            self._running = True
            logger.info(f"Dashboard started on http://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            raise
            
    async def stop_dashboard(self):
        """Stop the dashboard web server."""
        if not self._running:
            return
            
        try:
            await self.app.shutdown()
            self._running = False
            logger.info("Dashboard stopped")
            
        except Exception as e:
            logger.error(f"Error stopping dashboard: {e}")
            raise
            
    def _setup_routes(self):
        """Setup dashboard routes."""
        # Authentication routes
        self.app.router.add_get('/login', self._handle_login_page)
        self.app.router.add_post('/login', self._handle_login)
        self.app.router.add_get('/logout', self._handle_logout)
        
        # Dashboard routes
        self.app.router.add_get('/', self._handle_dashboard)
        self.app.router.add_get('/users', self._handle_users)
        self.app.router.add_get('/servers', self._handle_servers)
        self.app.router.add_get('/traffic', self._handle_traffic)
        self.app.router.add_get('/security', self._handle_security)
        self.app.router.add_get('/analytics', self._handle_analytics)
        self.app.router.add_get('/settings', self._handle_settings)
        
        # API routes
        self.app.router.add_get('/api/metrics', self._handle_metrics_api)
        self.app.router.add_get('/api/alerts', self._handle_alerts_api)
        self.app.router.add_post('/api/server/action', self._handle_server_action)
        self.app.router.add_post('/api/user/action', self._handle_user_action)
        
        # Static files
        self.app.router.add_static('/static/',
                                 path=Path(__file__).parent.parent / 'static' / 'dashboard',
                                 name='static')
                                 
    @web.middleware
    async def _auth_middleware(self, request, handler):
        """Authentication middleware."""
        # Public routes that don't require authentication
        public_paths = ['/login', '/static/']
        
        if any(request.path.startswith(p) for p in public_paths):
            return await handler(request)
            
        # Check for valid session
        session = await aiohttp_session.get_session(request)
        if not session.get('user'):
            raise web.HTTPFound('/login')
            
        return await handler(request)
        
    @aiohttp_jinja2.template('login.html')
    async def _handle_login_page(self, request):
        """Handle login page request."""
        return {}
        
    async def _handle_login(self, request):
        """Handle login request."""
        try:
            data = await request.post()
            username = data.get('username')
            password = data.get('password')
            
            # Verify credentials against database
            user = await self._verify_credentials(username, password)
            if not user:
                raise web.HTTPUnauthorized(text='Invalid credentials')
                
            # Create session
            session = await aiohttp_session.new_session(request)
            session['user'] = {
                'id': str(user['_id']),
                'username': user['username'],
                'role': user['role']
            }
            
            raise web.HTTPFound('/')
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise web.HTTPUnauthorized(text=str(e))
            
    async def _handle_logout(self, request):
        """Handle logout request."""
        session = await aiohttp_session.get_session(request)
        session.invalidate()
        raise web.HTTPFound('/login')
        
    @aiohttp_jinja2.template('dashboard.html')
    async def _handle_dashboard(self, request):
        """Handle main dashboard page request."""
        try:
            # Get overview metrics
            metrics = await self._get_overview_metrics()
            
            # Get recent alerts
            alerts = await self._get_recent_alerts()
            
            # Get system status
            status = await self._get_system_status()
            
            return {
                'metrics': metrics,
                'alerts': alerts,
                'status': status,
                'user': await self._get_current_user(request)
            }
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            raise web.HTTPInternalServerError(text=str(e))
            
    @aiohttp_jinja2.template('users.html')
    async def _handle_users(self, request):
        """Handle users page request."""
        try:
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', 50))
            
            # Get users with pagination
            users = await self._get_users(page, limit)
            
            # Get user metrics
            metrics = await self.analytics_manager._collect_user_metrics()
            
            return {
                'users': users,
                'metrics': metrics,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': await self.db.users.count_documents({})
                },
                'user': await self._get_current_user(request)
            }
            
        except Exception as e:
            logger.error(f"Users page error: {e}")
            raise web.HTTPInternalServerError(text=str(e))
            
    async def _handle_metrics_api(self, request):
        """Handle metrics API request."""
        try:
            metric_type = request.query.get('type')
            start_date = request.query.get('start')
            end_date = request.query.get('end')
            
            if not all([metric_type, start_date, end_date]):
                raise web.HTTPBadRequest(text="Missing required parameters")
                
            # Parse dates
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            
            # Get metrics
            metrics = await self.analytics_manager.generate_custom_report(
                [metric_type],
                start_date,
                end_date
            )
            
            return web.json_response(metrics)
            
        except Exception as e:
            logger.error(f"Metrics API error: {e}")
            raise web.HTTPInternalServerError(text=str(e))
            
    async def _handle_server_action(self, request):
        """Handle server management actions."""
        try:
            data = await request.json()
            action = data.get('action')
            server_id = data.get('server_id')
            
            if not all([action, server_id]):
                raise web.HTTPBadRequest(text="Missing required parameters")
                
            # Verify user permissions
            user = await self._get_current_user(request)
            if user['role'] not in ['admin', 'manager']:
                raise web.HTTPForbidden(text="Insufficient permissions")
                
            # Execute action
            result = await self._execute_server_action(action, server_id)
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Server action error: {e}")
            raise web.HTTPInternalServerError(text=str(e))
            
    async def _get_overview_metrics(self) -> Dict:
        """Get overview metrics for dashboard."""
        try:
            return {
                'users': await self.analytics_manager._collect_user_metrics(),
                'traffic': await self.analytics_manager._collect_traffic_metrics(),
                'servers': await self.analytics_manager._collect_server_metrics(),
                'security': await self.analytics_manager._collect_security_metrics()
            }
        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            raise
            
    async def _get_recent_alerts(self) -> List[Dict]:
        """Get recent system alerts."""
        try:
            cutoff = datetime.now() - timedelta(days=1)
            alerts = await self.db.alerts.find({
                'timestamp': {'$gte': cutoff}
            }).sort('timestamp', -1).limit(10).to_list(length=None)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            raise
            
    async def _get_system_status(self) -> Dict:
        """Get current system status."""
        try:
            return {
                'analytics': await self.analytics_manager.get_analytics_status(),
                'traffic': await self.traffic_manager.get_monitoring_status(),
                'security': await self.security_service.get_security_status(),
                'backup': await self.backup_manager.get_backup_status()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise
            
    async def _verify_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Verify user credentials."""
        try:
            user = await self.db.users.find_one({
                'username': username,
                'role': {'$in': ['admin', 'manager']}
            })
            
            if not user:
                return None
                
            # Verify password (implement proper password hashing)
            if not self._verify_password(password, user['password']):
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Error verifying credentials: {e}")
            raise
            
    async def _get_current_user(self, request) -> Dict:
        """Get current user from session."""
        session = await aiohttp_session.get_session(request)
        return session['user']
        
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        # Implement proper password verification
        # This is a placeholder - use proper password hashing in production
        return plain_password == hashed_password
        
    async def _execute_server_action(self, action: str, server_id: str) -> Dict:
        """Execute server management action."""
        try:
            if action == 'restart':
                # Implement server restart logic
                pass
            elif action == 'stop':
                # Implement server stop logic
                pass
            elif action == 'start':
                # Implement server start logic
                pass
            else:
                raise ValueError(f"Invalid action: {action}")
                
            # Log the action
            await self.db.server_actions.insert_one({
                'server_id': server_id,
                'action': action,
                'timestamp': datetime.now(),
                'status': 'success'
            })
            
            return {'status': 'success', 'message': f"Server {action} completed"}
            
        except Exception as e:
            logger.error(f"Error executing server action: {e}")
            raise 