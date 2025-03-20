from datetime import datetime, timedelta
from bson import ObjectId
from aiohttp import web
import aiohttp_jinja2
from typing import Dict, List, Optional
import csv
import io
import json
import logging

from ..services.notification_service import NotificationService
from ..services.analytics_manager import AnalyticsManager
from ..services.traffic_manager import TrafficManager
from ..config.dashboard_config import DASHBOARD_SETTINGS, ROLE_PERMISSIONS
from ..utils.security import hash_password, verify_password, check_password_strength

logger = logging.getLogger(__name__)

class UserRoutes:
    """Handles all user management related routes."""
    
    def __init__(self, db_connection, notification_service: NotificationService,
                 analytics_manager: AnalyticsManager, traffic_manager: TrafficManager):
        """Initialize user routes with required services."""
        self.db = db_connection
        self.notification_service = notification_service
        self.analytics_manager = analytics_manager
        self.traffic_manager = traffic_manager
        
    async def setup_routes(self, app: web.Application):
        """Setup all user management routes."""
        app.router.add_get('/users', self.handle_users_page)
        app.router.add_get('/api/users', self.handle_users_list)
        app.router.add_post('/api/users', self.handle_create_user)
        app.router.add_get('/api/users/{user_id}', self.handle_get_user)
        app.router.add_put('/api/users/{user_id}', self.handle_update_user)
        app.router.add_delete('/api/users/{user_id}', self.handle_delete_user)
        app.router.add_get('/api/users/{user_id}/details', self.handle_user_details)
        app.router.add_get('/api/users/export', self.handle_export_users)
        
    @aiohttp_jinja2.template('users.html')
    async def handle_users_page(self, request: web.Request) -> Dict:
        """Handle the users page request."""
        try:
            # Get current user from session
            session = await self._get_session(request)
            if not session.get('user'):
                raise web.HTTPFound('/login')
                
            current_user = session['user']
            
            # Check permissions
            if not self._has_permission(current_user['role'], 'users', 'view'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get query parameters
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', DASHBOARD_SETTINGS['UI']['items_per_page']))
            search = request.query.get('search', '')
            
            # Build query
            query = {}
            if search:
                query['$or'] = [
                    {'username': {'$regex': search, '$options': 'i'}},
                    {'email': {'$regex': search, '$options': 'i'}}
                ]
                
            # Get users with pagination
            skip = (page - 1) * limit
            total = await self.db.users.count_documents(query)
            users = await self.db.users.find(query).skip(skip).limit(limit).to_list(length=None)
            
            # Process user data
            users = await self._process_users_data(users)
            
            # Calculate pagination
            total_pages = (total + limit - 1) // limit
            pages = range(max(1, page - 2), min(total_pages + 1, page + 3))
            
            return {
                'users': users,
                'pagination': {
                    'current': page,
                    'total': total,
                    'pages': list(pages),
                    'has_previous': page > 1,
                    'has_next': page < total_pages,
                    'start': skip + 1,
                    'end': min(skip + limit, total)
                },
                'user': current_user
            }
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling users page: {e}")
            raise web.HTTPInternalServerError(text=str(e))
            
    async def handle_users_list(self, request: web.Request) -> web.Response:
        """Handle API request for users list."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'view'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get query parameters
            page = int(request.query.get('page', 1))
            limit = int(request.query.get('limit', DASHBOARD_SETTINGS['UI']['items_per_page']))
            search = request.query.get('search', '')
            
            # Build query
            query = {}
            if search:
                query['$or'] = [
                    {'username': {'$regex': search, '$options': 'i'}},
                    {'email': {'$regex': search, '$options': 'i'}}
                ]
                
            # Get users
            users = await self.db.users.find(query).skip((page - 1) * limit).limit(limit).to_list(length=None)
            users = await self._process_users_data(users)
            
            return web.json_response({'users': users})
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling users list: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_create_user(self, request: web.Request) -> web.Response:
        """Handle user creation request."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'create'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get form data
            data = await request.post()
            
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'role', 'plan', 'expires_at', 'traffic_limit']
            if not all(field in data for field in required_fields):
                return web.json_response({'error': 'Missing required fields'}, status=400)
                
            # Check password strength
            is_valid, error_msg = await check_password_strength(data['password'])
            if not is_valid:
                return web.json_response({'error': error_msg}, status=400)
                
            # Check if username or email already exists
            if await self.db.users.find_one({'$or': [
                {'username': data['username']},
                {'email': data['email']}
            ]}):
                return web.json_response({'error': 'Username or email already exists'}, status=400)
                
            # Hash password
            hashed_password = await hash_password(data['password'])
            
            # Create user document
            user = {
                'username': data['username'],
                'email': data['email'],
                'password': hashed_password,
                'role': data['role'],
                'subscription': {
                    'plan': data['plan'],
                    'expires_at': datetime.fromisoformat(data['expires_at']),
                    'status': 'active'
                },
                'traffic': {
                    'limit': int(data['traffic_limit']) * 1024 * 1024 * 1024,  # Convert GB to bytes
                    'used': 0
                },
                'status': data['status'],
                'created_at': datetime.now(),
                'last_active': None
            }
            
            # Insert user
            result = await self.db.users.insert_one(user)
            
            # Log action
            await self._log_action(
                current_user['id'],
                'user_create',
                f"Created user {data['username']}"
            )
            
            # Send notification
            await self.notification_service.send_notification(
                'user',
                f"New user {data['username']} created",
                'success'
            )
            
            return web.json_response({
                'success': True,
                'user_id': str(result.inserted_id)
            })
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_get_user(self, request: web.Request) -> web.Response:
        """Handle request for user details."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'view'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get user
            user_id = request.match_info['user_id']
            user = await self.db.users.find_one({'_id': ObjectId(user_id)})
            
            if not user:
                raise web.HTTPNotFound(text='User not found')
                
            # Process user data
            user = await self._process_user_data(user)
            
            return web.json_response(user)
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_update_user(self, request: web.Request) -> web.Response:
        """Handle user update request."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'edit'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get user ID and form data
            user_id = request.match_info['user_id']
            data = await request.post()
            
            # Get existing user
            user = await self.db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                raise web.HTTPNotFound(text='User not found')
                
            # Build update document
            update = {
                '$set': {
                    'email': data['email'],
                    'role': data['role'],
                    'subscription.plan': data['plan'],
                    'subscription.expires_at': datetime.fromisoformat(data['expires_at']),
                    'traffic.limit': int(data['traffic_limit']) * 1024 * 1024 * 1024,
                    'status': data['status']
                }
            }
            
            # Update password if provided
            if data.get('password'):
                # Check password strength
                is_valid, error_msg = await check_password_strength(data['password'])
                if not is_valid:
                    return web.json_response({'error': error_msg}, status=400)
                
                # Hash new password
                update['$set']['password'] = await hash_password(data['password'])
            
            # Update user
            await self.db.users.update_one({'_id': ObjectId(user_id)}, update)
            
            # Log action
            await self._log_action(
                current_user['id'],
                'user_update',
                f"Updated user {user['username']}"
            )
            
            # Send notification
            await self.notification_service.send_notification(
                'user',
                f"User {user['username']} updated",
                'success'
            )
            
            return web.json_response({'success': True})
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_delete_user(self, request: web.Request) -> web.Response:
        """Handle user deletion request."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'delete'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get user
            user_id = request.match_info['user_id']
            user = await self.db.users.find_one({'_id': ObjectId(user_id)})
            
            if not user:
                raise web.HTTPNotFound(text='User not found')
                
            # Delete user
            await self.db.users.delete_one({'_id': ObjectId(user_id)})
            
            # Log action
            await self._log_action(
                current_user['id'],
                'user_delete',
                f"Deleted user {user['username']}"
            )
            
            # Send notification
            await self.notification_service.send_notification(
                'user',
                f"User {user['username']} deleted",
                'warning'
            )
            
            return web.json_response({'success': True})
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_user_details(self, request: web.Request) -> web.Response:
        """Handle request for detailed user information."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'view'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get user
            user_id = request.match_info['user_id']
            user = await self.db.users.find_one({'_id': ObjectId(user_id)})
            
            if not user:
                raise web.HTTPNotFound(text='User not found')
                
            # Get traffic history
            traffic_history = await self.traffic_manager.get_user_traffic_history(user_id)
            
            # Get recent activity
            recent_activity = await self._get_user_activity(user_id)
            
            # Get active sessions
            active_sessions = await self.db.sessions.count_documents({
                'user_id': ObjectId(user_id),
                'active': True
            })
            
            return web.json_response({
                'username': user['username'],
                'email': user['email'],
                'total_traffic': user['traffic']['used'],
                'active_sessions': active_sessions,
                'created_at': user['created_at'].isoformat(),
                'traffic_history': traffic_history,
                'recent_activity': recent_activity
            })
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user details: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def handle_export_users(self, request: web.Request) -> web.Response:
        """Handle user data export request."""
        try:
            # Verify permissions
            current_user = await self._get_current_user(request)
            if not self._has_permission(current_user['role'], 'users', 'export'):
                raise web.HTTPForbidden(text='Insufficient permissions')
                
            # Get all users
            users = await self.db.users.find().to_list(length=None)
            users = await self._process_users_data(users)
            
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'username', 'email', 'role', 'plan', 'expires_at', 'traffic_used',
                'traffic_limit', 'status', 'created_at', 'last_active'
            ])
            
            writer.writeheader()
            for user in users:
                writer.writerow({
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'plan': user['subscription']['plan'],
                    'expires_at': user['subscription']['expires_at'],
                    'traffic_used': user['traffic']['used'],
                    'traffic_limit': user['traffic']['limit'],
                    'status': user['status'],
                    'created_at': user['created_at'],
                    'last_active': user['last_active'] or ''
                })
                
            # Log action
            await self._log_action(
                current_user['id'],
                'user_export',
                'Exported user data'
            )
            
            # Prepare response
            response = web.Response(
                body=output.getvalue().encode(),
                content_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d")}.csv'
                }
            )
            
            return response
            
        except web.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            return web.json_response({'error': str(e)}, status=500)
            
    async def _process_users_data(self, users: List[Dict]) -> List[Dict]:
        """Process user data for display."""
        processed_users = []
        for user in users:
            processed_user = await self._process_user_data(user)
            processed_users.append(processed_user)
        return processed_users
        
    async def _process_user_data(self, user: Dict) -> Dict:
        """Process individual user data."""
        return {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'subscription': {
                'plan': user['subscription']['plan'],
                'expires_at': user['subscription']['expires_at'].isoformat(),
                'status': user['subscription']['status']
            },
            'traffic': {
                'used': user['traffic']['used'],
                'limit': user['traffic']['limit'],
                'percentage': round(user['traffic']['used'] / user['traffic']['limit'] * 100, 1)
            },
            'status': user['status'],
            'created_at': user['created_at'].isoformat(),
            'last_active': user['last_active'].isoformat() if user['last_active'] else None
        }
        
    async def _get_user_activity(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent user activity."""
        activities = await self.db.user_activity.find({
            'user_id': ObjectId(user_id)
        }).sort('timestamp', -1).limit(limit).to_list(length=None)
        
        return [{
            'type': activity['type'],
            'message': activity['message'],
            'timestamp': activity['timestamp'].isoformat(),
            'icon': self._get_activity_icon(activity['type'])
        } for activity in activities]
        
    def _get_activity_icon(self, activity_type: str) -> str:
        """Get icon for activity type."""
        icons = {
            'login': 'sign-in-alt',
            'logout': 'sign-out-alt',
            'traffic': 'network-wired',
            'subscription': 'credit-card',
            'settings': 'cog',
            'security': 'shield-alt'
        }
        return icons.get(activity_type, 'circle')
        
    async def _log_action(self, user_id: str, action_type: str, message: str):
        """Log user action."""
        await self.db.user_activity.insert_one({
            'user_id': ObjectId(user_id),
            'type': action_type,
            'message': message,
            'timestamp': datetime.now()
        })
        
    async def _get_current_user(self, request: web.Request) -> Dict:
        """Get current user from session."""
        session = await self._get_session(request)
        if not session.get('user'):
            raise web.HTTPUnauthorized(text='Not authenticated')
        return session['user']
        
    def _has_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if role has permission for action on resource."""
        return action in ROLE_PERMISSIONS.get(role, {}).get(resource, [])
        
    async def _get_session(self, request: web.Request):
        """Get session from request."""
        return await aiohttp_session.get_session(request)
        
    async def verify_user_password(self, user_id: str, password: str) -> bool:
        """
        Verify user's password.
        
        Args:
            user_id: User ID
            password: Password to verify
            
        Returns:
            bool: True if password matches
        """
        try:
            user = await self.db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False
            
            return await verify_password(user['password'], password)
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False 