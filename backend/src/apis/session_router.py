from fastapi import APIRouter

from backend.src.entities.db_model import ConversationHistory

router = APIRouter(tags=["Session"])


@router.get("/sessions/{user_id}/{session_id}")
async def get_session(user_id: str, session_id: str):
    history = list(ConversationHistory.select().where(
        (ConversationHistory.conversation_id == session_id) & (ConversationHistory.user_id == user_id)).dicts())
    return {"session_id": session_id, "chat_history": history}


@router.get("/sessions/{user_id}")
async def get_all_sessions(user_id: str):
    sessions = list(ConversationHistory.select().where(ConversationHistory.user_id == user_id).distinct(
        ConversationHistory.conversation_id).dicts())
    return {"sessions": sessions}
