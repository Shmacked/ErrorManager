from typing import Any, TypedDict
from pydantic import Field
from typing import Annotated
from langgraph.graph.message import add_messages

# This is the state model for the Langgraph graph
class ErrorLogEvaluationLanggraphState(TypedDict, total=False):
    state: str
    input: str
    output: Any
    feedback: str
    success: bool = Field(default=False)
    count: int = Field(default=0)


class SummaryLanggraphState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str
    tool_response: dict = Field(default={})
    route: str | None = Field(default=None)

class ToolLanggraphState(TypedDict):
    messages: Annotated[list, add_messages]
    retry_counter: int = Field(default=0)
    tool_response: dict = Field(default={})