from typing import TypedDict, Annotated, Dict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class MedTutorGraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    model_config: Dict
    remaining_steps: int
    medical_type: str
    question_type: str
