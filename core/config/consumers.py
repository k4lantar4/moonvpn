import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import LiveChatSession, LiveChatMessage, LiveChatOperator
from .serializers import LiveChatMessageSerializer
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        self.user = self.scope['user']

        # Check if user has access to this chat session
        if not await self.can_access_chat():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send system message about user joining
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'type': 'system',
                    'content': f'{self.user.username} joined the chat',
                    'timestamp': timezone.now().isoformat()
                }
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'room_group_name'):
            # Send system message about user leaving
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'type': 'system',
                        'content': f'{self.user.username} left the chat',
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle receiving messages from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'text')
            content = text_data_json.get('content')
            
            if not content:
                return
            
            # Save message to database
            message = await self.save_message(message_type, content)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'type': message.type,
                        'content': message.content,
                        'sender': self.user.username,
                        'timestamp': message.created_at.isoformat()
                    }
                }
            )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def can_access_chat(self):
        """Check if user has access to the chat session."""
        try:
            session = LiveChatSession.objects.get(id=self.session_id)
            return (
                self.user.is_staff or
                self.user == session.user or
                self.user == session.operator
            )
        except LiveChatSession.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_type, content):
        """Save a new message to the database."""
        session = LiveChatSession.objects.get(id=self.session_id)
        return LiveChatMessage.objects.create(
            session=session,
            sender=self.user,
            type=message_type,
            content=content
        ) 