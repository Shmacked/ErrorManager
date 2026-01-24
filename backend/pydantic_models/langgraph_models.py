from pydantic import BaseModel
from typing import Any


# This is the state model for the Langgraph graph
class ErrorLogEvaluationLanggraphState(BaseModel):
    state: str
    input: str
    output: Any
    feedback: str
