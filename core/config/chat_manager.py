"""
Live chat support service.

This module handles:
- Real-time chat between users and support agents
- Chat history and persistence
- Agent assignment and management
- Chat metrics and analytics
"""

import logging
import uuid
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChatStatus(Enum):
    """Chat status enumeration."""
    OPEN = "open"
    WAITING = "waiting"
    CLOSED = "closed"
    RESOLVED = "resolved"

class UserRole(Enum):
    """User role enumeration."""
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"

@dataclass
class ChatMessage:
    """Chat message data class."""
    id: str
    chat_id: str
    user_id: str
    role: UserRole
    content: str
    created_at: datetime
    is_read: bool
    attachments: List[str]
    metadata: Dict

@dataclass
class ChatSession:
    """Chat session data class."""
    id: str
    user_id: str
    agent_id: Optional[str]
    status: ChatStatus
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    messages: List[ChatMessage]
    tags: List[str]
    priority: int
    category: str
    notes: List[str]
    rating: Optional[int]
    feedback: Optional[str]
    resolution_time: Optional[float]
    transfer_count: int

@dataclass
class AgentInfo:
    """Support agent information data class."""
    user_id: str
    name: str
    role: UserRole
    is_available: bool
    active_chats: Set[str]
    total_chats: int
    avg_rating: float
    response_time: float
    resolution_rate: float
    specialties: List[str]
    working_hours: Dict[str, List[str]]
    last_active: datetime

class ChatManager:
    """Manages live chat support system."""
    
    def __init__(self):
        self.chats: Dict[str, ChatSession] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.user_chats: Dict[str, Set[str]] = {}  # user_id -> set of chat_ids
        self.agent_chats: Dict[str, Set[str]] = {}  # agent_id -> set of chat_ids
        self.categories = {
            "general": "General Support",
            "technical": "Technical Issues",
            "billing": "Billing & Payments",
            "account": "Account Issues",
            "other": "Other"
        }
    
    async def create_chat(
        self,
        user_id: str,
        category: str = "general",
        priority: int = 1
    ) -> ChatSession:
        """Create a new chat session."""
        chat_id = str(uuid.uuid4())
        
        chat = ChatSession(
            id=chat_id,
            user_id=user_id,
            agent_id=None,
            status=ChatStatus.WAITING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_message_at=datetime.now(),
            messages=[],
            tags=[],
            priority=priority,
            category=category,
            notes=[],
            rating=None,
            feedback=None,
            resolution_time=None,
            transfer_count=0
        )
        
        self.chats[chat_id] = chat
        
        # Update user's chat list
        if user_id not in self.user_chats:
            self.user_chats[user_id] = set()
        self.user_chats[user_id].add(chat_id)
        
        return chat
    
    async def get_chat(self, chat_id: str) -> Optional[ChatSession]:
        """Get chat session by ID."""
        return self.chats.get(chat_id)
    
    async def get_user_chats(self, user_id: str) -> List[ChatSession]:
        """Get all chats for a user."""
        chat_ids = self.user_chats.get(user_id, set())
        return [self.chats[cid] for cid in chat_ids if cid in self.chats]
    
    async def get_agent_chats(self, agent_id: str) -> List[ChatSession]:
        """Get all active chats for an agent."""
        chat_ids = self.agent_chats.get(agent_id, set())
        return [self.chats[cid] for cid in chat_ids if cid in self.chats]
    
    async def add_message(
        self,
        chat_id: str,
        user_id: str,
        role: UserRole,
        content: str,
        attachments: List[str] = None,
        metadata: Dict = None
    ) -> ChatMessage:
        """Add a message to a chat session."""
        chat = await self.get_chat(chat_id)
        if not chat:
            raise ValueError("Chat not found")
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            role=role,
            content=content,
            created_at=datetime.now(),
            is_read=False,
            attachments=attachments or [],
            metadata=metadata or {}
        )
        
        chat.messages.append(message)
        chat.last_message_at = message.created_at
        chat.updated_at = message.created_at
        
        return message
    
    async def assign_agent(
        self,
        chat_id: str,
        agent_id: str
    ) -> bool:
        """Assign an agent to a chat session."""
        chat = await self.get_chat(chat_id)
        agent = self.agents.get(agent_id)
        
        if not chat or not agent or not agent.is_available:
            return False
        
        # Remove from previous agent if any
        if chat.agent_id:
            if chat.agent_id in self.agent_chats:
                self.agent_chats[chat.agent_id].remove(chat_id)
        
        # Assign to new agent
        chat.agent_id = agent_id
        chat.status = ChatStatus.OPEN
        
        if agent_id not in self.agent_chats:
            self.agent_chats[agent_id] = set()
        self.agent_chats[agent_id].add(chat_id)
        
        return True
    
    async def close_chat(
        self,
        chat_id: str,
        resolved: bool = False,
        rating: Optional[int] = None,
        feedback: Optional[str] = None
    ) -> bool:
        """Close a chat session."""
        chat = await self.get_chat(chat_id)
        if not chat or chat.status == ChatStatus.CLOSED:
            return False
        
        chat.status = ChatStatus.RESOLVED if resolved else ChatStatus.CLOSED
        chat.updated_at = datetime.now()
        
        if rating is not None:
            chat.rating = rating
        if feedback is not None:
            chat.feedback = feedback
        
        # Calculate resolution time
        if resolved:
            chat.resolution_time = (
                chat.updated_at - chat.created_at
            ).total_seconds() / 60  # in minutes
        
        # Update agent stats
        if chat.agent_id:
            agent = self.agents.get(chat.agent_id)
            if agent:
                agent.total_chats += 1
                if resolved:
                    agent.resolution_rate = (
                        (agent.resolution_rate * (agent.total_chats - 1) + 1)
                        / agent.total_chats
                    )
                if rating is not None:
                    agent.avg_rating = (
                        (agent.avg_rating * (agent.total_chats - 1) + rating)
                        / agent.total_chats
                    )
        
        # Clean up
        if chat.agent_id in self.agent_chats:
            self.agent_chats[chat.agent_id].remove(chat_id)
        
        return True
    
    async def transfer_chat(
        self,
        chat_id: str,
        new_agent_id: str
    ) -> bool:
        """Transfer a chat to a different agent."""
        chat = await self.get_chat(chat_id)
        if not chat or not chat.agent_id:
            return False
        
        # Add transfer note
        chat.notes.append(
            f"Transferred from {chat.agent_id} to {new_agent_id} at {datetime.now()}"
        )
        chat.transfer_count += 1
        
        # Reassign agent
        return await self.assign_agent(chat_id, new_agent_id)
    
    async def add_agent(
        self,
        user_id: str,
        name: str,
        specialties: List[str] = None,
        working_hours: Dict[str, List[str]] = None
    ) -> AgentInfo:
        """Add a new support agent."""
        if user_id in self.agents:
            return self.agents[user_id]
        
        agent = AgentInfo(
            user_id=user_id,
            name=name,
            role=UserRole.AGENT,
            is_available=True,
            active_chats=set(),
            total_chats=0,
            avg_rating=0.0,
            response_time=0.0,
            resolution_rate=0.0,
            specialties=specialties or [],
            working_hours=working_hours or {},
            last_active=datetime.now()
        )
        
        self.agents[user_id] = agent
        return agent
    
    async def update_agent_status(
        self,
        agent_id: str,
        is_available: bool
    ) -> bool:
        """Update agent's availability status."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        agent.is_available = is_available
        agent.last_active = datetime.now()
        return True
    
    async def get_agent_stats(self, agent_id: str) -> Dict:
        """Get detailed statistics for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        active_chats = await self.get_agent_chats(agent_id)
        
        return {
            "agent": {
                "id": agent.user_id,
                "name": agent.name,
                "role": agent.role.value,
                "is_available": agent.is_available,
                "specialties": agent.specialties,
                "working_hours": agent.working_hours,
                "last_active": agent.last_active.isoformat()
            },
            "performance": {
                "total_chats": agent.total_chats,
                "active_chats": len(active_chats),
                "avg_rating": agent.avg_rating,
                "resolution_rate": agent.resolution_rate,
                "response_time": agent.response_time
            },
            "active_chats": [
                {
                    "id": chat.id,
                    "user_id": chat.user_id,
                    "category": chat.category,
                    "priority": chat.priority,
                    "created_at": chat.created_at.isoformat(),
                    "last_message": chat.last_message_at.isoformat()
                }
                for chat in active_chats
            ]
        }
    
    async def get_chat_stats(self, chat_id: str) -> Dict:
        """Get detailed statistics for a chat session."""
        chat = await self.get_chat(chat_id)
        if not chat:
            return None
        
        return {
            "chat": {
                "id": chat.id,
                "user_id": chat.user_id,
                "agent_id": chat.agent_id,
                "status": chat.status.value,
                "category": chat.category,
                "priority": chat.priority,
                "created_at": chat.created_at.isoformat(),
                "updated_at": chat.updated_at.isoformat(),
                "last_message": chat.last_message_at.isoformat(),
                "transfer_count": chat.transfer_count,
                "resolution_time": chat.resolution_time,
                "rating": chat.rating,
                "feedback": chat.feedback
            },
            "messages": {
                "total": len(chat.messages),
                "unread": len([m for m in chat.messages if not m.is_read]),
                "by_role": {
                    role.value: len([m for m in chat.messages if m.role == role])
                    for role in UserRole
                }
            },
            "tags": chat.tags,
            "notes": chat.notes
        } 