import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from backend.src.entities.db_model import ChatSession, ChatMessage


class ChatService:
    """Service class for managing chat sessions and messages"""
    
    @staticmethod
    def create_session(user_id: str, session_id: str = None, model_config: Dict = None) -> ChatSession:
        """Create a new chat session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = ChatSession.create(
            session_id=session_id,
            user_id=user_id,
            title="New Chat",
            model_config=json.dumps(model_config) if model_config else None
        )
        return session
    
    @staticmethod
    def get_session(session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        try:
            return ChatSession.get(ChatSession.session_id == session_id)
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_sessions(user_id: str) -> List[ChatSession]:
        """Get all sessions for a user"""
        return list(ChatSession.select().where(ChatSession.user_id == user_id)
                   .order_by(ChatSession.updated_at.desc()))
    
    @staticmethod
    def update_session_title(session_id: str, title: str) -> bool:
        """Update session title"""
        try:
            query = ChatSession.update(title=title, updated_at=datetime.now()).where(
                ChatSession.session_id == session_id
            )
            return query.execute() > 0
        except:
            return False
    
    @staticmethod
    def add_message(session_id: str, role: str, content: str, node_type: str = None, 
                   metadata: Dict = None) -> ChatMessage:
        """Add a message to a chat session"""
        # Get the next message order
        last_message = (ChatMessage.select()
                       .where(ChatMessage.session_id == session_id)
                       .order_by(ChatMessage.message_order.desc())
                       .first())
        
        message_order = (last_message.message_order + 1) if last_message else 1
        
        message = ChatMessage.create(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            message_order=message_order,
            node_type=node_type,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        # Update session message count and timestamp
        ChatSession.update(
            message_count=ChatSession.message_count + 1,
            updated_at=datetime.now()
        ).where(ChatSession.session_id == session_id).execute()
        
        return message
    
    @staticmethod
    def get_session_messages(session_id: str, limit: int = None) -> List[ChatMessage]:
        """Get messages for a session"""
        query = (ChatMessage.select()
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.message_order))
        
        if limit:
            query = query.limit(limit)
            
        return list(query)
    
    @staticmethod
    def get_recent_user_messages(session_id: str, limit: int = 7) -> List[str]:
        """Get recent user messages for context (used in query preprocessing)"""
        messages = (ChatMessage.select()
                   .where((ChatMessage.session_id == session_id) & 
                         (ChatMessage.role == 'user'))
                   .order_by(ChatMessage.message_order.desc())
                   .limit(limit))
        
        return [msg.content for msg in reversed(list(messages))]
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            # Delete messages first (foreign key constraint)
            ChatMessage.delete().where(ChatMessage.session_id == session_id).execute()
            # Delete session
            ChatSession.delete().where(ChatSession.session_id == session_id).execute()
            return True
        except:
            return False
    
    @staticmethod
    def get_session_with_messages(session_id: str) -> Optional[Dict]:
        """Get session with all its messages"""
        session = ChatService.get_session(session_id)
        if not session:
            return None
        
        messages = ChatService.get_session_messages(session_id)
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": session.message_count,
            "model_config": json.loads(session.model_config) if session.model_config else None,
            "messages": [
                {
                    "message_id": msg.message_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "node_type": msg.node_type,
                    "metadata": json.loads(msg.metadata) if msg.metadata else None
                }
                for msg in messages
            ]
        }

    @staticmethod
    def generate_session_title(first_user_message: str, max_length: int = 50) -> str:
        """Generate a session title from the first user message"""
        if len(first_user_message) <= max_length:
            return first_user_message
        
        # Truncate and add ellipsis
        return first_user_message[:max_length-3] + "..."
