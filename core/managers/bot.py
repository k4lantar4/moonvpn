"""
Bot service manager implementation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from app.core.managers.base import ResourceManager
from app.core.exceptions import BotError, ResourceError
from app.core.models.bot import BotUser, BotCommand, BotMessage
from app.core.schemas.bot import BotUserCreate, BotUserUpdate, BotCommandCreate, BotCommandUpdate

class BotManager(ResourceManager):
    """Manager for Telegram bot operations."""
    
    def __init__(self):
        super().__init__()
        self.resource_type = "bot"
        
    async def _create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create bot user or command."""
        try:
            if "type" not in data:
                raise ValidationError("Resource type not specified")
                
            if data["type"] == "user":
                user = BotUserCreate(**data)
                bot_user = await BotUser.create(user)
                await self.metrics.record_resource_operation(
                    resource_type="bot_user",
                    operation="create",
                    success=True
                )
                return bot_user.dict()
                
            elif data["type"] == "command":
                command = BotCommandCreate(**data)
                bot_command = await BotCommand.create(command)
                await self.metrics.record_resource_operation(
                    resource_type="bot_command",
                    operation="create",
                    success=True
                )
                return bot_command.dict()
                
            else:
                raise ValidationError(f"Invalid resource type: {data['type']}")
                
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="create",
                success=False
            )
            raise ResourceError(f"Failed to create {self.resource_type}: {str(e)}")
            
    async def _get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get bot user or command by ID."""
        try:
            # Try to get from cache first
            cache_key = f"bot:{resource_id}"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            resource = await BotUser.get_by_id(resource_id) or await BotCommand.get_by_id(resource_id)
            if not resource:
                return None
                
            # Cache the result
            await self.cache.set(cache_key, resource.dict(), ttl=300)
            return resource.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="get",
                success=False
            )
            raise ResourceError(f"Failed to get {self.resource_type}: {str(e)}")
            
    async def _update_resource(
        self,
        resource_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update bot user or command."""
        try:
            # Get existing resource
            resource = await BotUser.get_by_id(resource_id) or await BotCommand.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Update based on type
            if isinstance(resource, BotUser):
                update_data = BotUserUpdate(**data)
                updated = await BotUser.update(resource_id, update_data)
            else:
                update_data = BotCommandUpdate(**data)
                updated = await BotCommand.update(resource_id, update_data)
                
            # Invalidate cache
            await self.cache.delete(f"bot:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=True
            )
            return updated.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=False
            )
            raise ResourceError(f"Failed to update {self.resource_type}: {str(e)}")
            
    async def _delete_resource(self, resource_id: str) -> None:
        """Delete bot user or command."""
        try:
            # Get resource type
            resource = await BotUser.get_by_id(resource_id) or await BotCommand.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Delete based on type
            if isinstance(resource, BotUser):
                await BotUser.delete(resource_id)
            else:
                await BotCommand.delete(resource_id)
                
            # Invalidate cache
            await self.cache.delete(f"bot:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=True
            )
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=False
            )
            raise ResourceError(f"Failed to delete {self.resource_type}: {str(e)}")
            
    async def send_message(
        self,
        user_id: int,
        message: str,
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """Send message to Telegram user."""
        try:
            # Get user
            user = await BotUser.get_by_telegram_id(user_id)
            if not user:
                raise ResourceError(f"Bot user not found: {user_id}")
                
            # Send message
            result = await self.execute_with_retry(
                operation="send_message",
                func=self._send_telegram_message,
                user_id=user_id,
                message=message,
                parse_mode=parse_mode
            )
            
            # Record message
            await BotMessage.create({
                "user_id": user.id,
                "message": message,
                "direction": "outgoing",
                "status": "sent"
            })
            
            await self.metrics.record_bot_metrics(
                active_users=await BotUser.count_active(),
                command="send_message"
            )
            
            return result
            
        except Exception as e:
            await self.metrics.record_error("send_message", str(e))
            raise BotError(f"Failed to send message: {str(e)}")
            
    async def _send_telegram_message(
        self,
        user_id: int,
        message: str,
        parse_mode: str
    ) -> Dict[str, Any]:
        """Send message using Telegram API."""
        # Implementation depends on specific Telegram bot API
        pass
        
    async def handle_command(
        self,
        user_id: int,
        command: str,
        args: List[str] = None
    ) -> Dict[str, Any]:
        """Handle Telegram bot command."""
        try:
            # Get user
            user = await BotUser.get_by_telegram_id(user_id)
            if not user:
                raise ResourceError(f"Bot user not found: {user_id}")
                
            # Get command
            bot_command = await BotCommand.get_by_name(command)
            if not bot_command:
                raise ResourceError(f"Command not found: {command}")
                
            # Execute command
            result = await self.execute_with_retry(
                operation="handle_command",
                func=self._execute_bot_command,
                user_id=user_id,
                command=command,
                args=args
            )
            
            # Record command
            await BotMessage.create({
                "user_id": user.id,
                "message": f"/{command} {' '.join(args) if args else ''}",
                "direction": "incoming",
                "status": "processed"
            })
            
            await self.metrics.record_bot_metrics(
                active_users=await BotUser.count_active(),
                command=command
            )
            
            return result
            
        except Exception as e:
            await self.metrics.record_error("handle_command", str(e))
            raise BotError(f"Failed to handle command: {str(e)}")
            
    async def _execute_bot_command(
        self,
        user_id: int,
        command: str,
        args: List[str]
    ) -> Dict[str, Any]:
        """Execute bot command."""
        # Implementation depends on specific command handlers
        pass
        
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get bot user statistics."""
        try:
            user = await BotUser.get_by_telegram_id(user_id)
            if not user:
                raise ResourceError(f"Bot user not found: {user_id}")
                
            # Get user messages
            messages = await BotMessage.get_by_user_id(user.id)
            
            # Calculate stats
            stats = {
                "total_messages": len(messages),
                "incoming_messages": len([m for m in messages if m.direction == "incoming"]),
                "outgoing_messages": len([m for m in messages if m.direction == "outgoing"]),
                "last_active": user.last_active,
                "created_at": user.created_at
            }
            
            return stats
            
        except Exception as e:
            await self.metrics.record_error("get_user_stats", str(e))
            raise BotError(f"Failed to get user stats: {str(e)}")
            
    async def get_active_users(self) -> List[Dict[str, Any]]:
        """Get active bot users."""
        try:
            # Try to get from cache first
            cache_key = "bot:active_users"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            users = await BotUser.get_all_active()
            
            # Cache the result
            await self.cache.set(cache_key, [user.dict() for user in users], ttl=300)
            return [user.dict() for user in users]
            
        except Exception as e:
            await self.metrics.record_error("get_active_users", str(e))
            raise BotError(f"Failed to get active users: {str(e)}")
            
    async def update_user_status(
        self,
        user_id: int,
        status: str,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update bot user status."""
        try:
            user = await BotUser.get_by_telegram_id(user_id)
            if not user:
                raise ResourceError(f"Bot user not found: {user_id}")
                
            # Update status
            updated = await BotUser.update_status(user.id, status, details)
            
            # Invalidate cache
            await self.cache.delete(f"bot:user:{user_id}")
            
            return updated.dict()
            
        except Exception as e:
            await self.metrics.record_error("update_user_status", str(e))
            raise BotError(f"Failed to update user status: {str(e)}") 