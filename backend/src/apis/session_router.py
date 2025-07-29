from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel

from backend.src.services.chat_service import ChatService

# Request/Response models for better API documentation
class SessionCreateRequest(BaseModel):
    user_id: str
    title: str = "New Chat"
    model_config: Optional[Dict] = None

class SessionUpdateTitleRequest(BaseModel):
    title: str

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

class SessionWithMessagesResponse(BaseModel):
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    model_config: Optional[Dict]
    messages: List[Dict]

router = APIRouter(tags=["Session"])


@router.get("/sessions/{user_id}/{session_id}")
async def get_session(user_id: str, session_id: str):
    """Get a specific session with all its messages"""
    session_data = ChatService.get_session_with_messages(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify the session belongs to the user
    if session_data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session_data


@router.get("/sessions/{user_id}")
async def get_all_sessions(user_id: str):
    """Get all sessions for a user"""
    sessions = ChatService.get_user_sessions(user_id)
    
    session_list = [
        {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": session.message_count,
        }
        for session in sessions
    ]
    
    return {"sessions": session_list}


@router.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """Delete a session and all its messages"""
    # Verify session exists and belongs to user
    session = ChatService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = ChatService.delete_session(session_id)
    if success:
        return {"message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.put("/sessions/{user_id}/{session_id}/title")
async def update_session_title(user_id: str, session_id: str, request: SessionUpdateTitleRequest):
    """Update session title"""
    # Verify session exists and belongs to user
    session = ChatService.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = ChatService.update_session_title(session_id, request.title)
    if success:
        return {"message": "Title updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update title")
