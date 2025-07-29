from typing import Dict
from pydantic import BaseModel, Field

class PDF(BaseModel):
    folder_path: str


class Chat(BaseModel):
    user_id: str = Field(default="1", description="Unique user ID for the chat")
    input_query: str
    config: Dict
    session_id: str = Field(default="1", description="Unique session ID for the chat")