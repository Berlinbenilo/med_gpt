import operator
from typing import TypedDict, Annotated, List, Dict


class MedTutorGraphState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    model_config: Dict
    remaining_steps: int
    medical_type: str
