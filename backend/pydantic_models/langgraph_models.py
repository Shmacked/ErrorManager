from typing import Any, TypedDict
from pydantic import Field
from typing import Annotated, List
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage

# This is the state model for the Langgraph graph
class ErrorLogEvaluationLanggraphState(TypedDict, total=False):
    state: str
    input: str
    output: Any
    feedback: str
    success: bool = Field(default=False)
    count: int = Field(default=0)


# Define your schema
class EvaluationSchema(BaseModel):
    # might could do an exit: bool for exiting
    success: bool = Field(description="Whether the tool answered the user")
    response: str = Field(description="The actual content of the response")


class SummaryLanggraphState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str
    user_input: Field(default="")
    tool_response: ToolMessage = Field(default={})
    tool_evaluation: EvaluationSchema = Field(default={})
    route: str | None = Field(default=None)


class ToolLanggraphState(TypedDict):
    user_input: Field(default="")
    messages: Annotated[list, add_messages]
    retry_counter: int = Field(default=0)
    route: str | None = Field(default=None)
    plan: str = Field(default="")
    tool_response: ToolMessage = Field(default={})
    tool_evaluation: EvaluationSchema = Field(default={})
    tool_calls: List[ToolMessage] = Field(default=[])
