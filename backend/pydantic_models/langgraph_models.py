from typing import Any, TypedDict


# This is the state model for the Langgraph graph
class ErrorLogEvaluationLanggraphState(TypedDict, total=False):
    state: str
    input: str
    output: Any
    feedback: str
