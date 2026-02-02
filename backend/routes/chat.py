from fastapi import APIRouter, Depends
from backend.services.langgraph import get_summary_graph, get_date_parser_graph
from backend.pydantic_models.langgraph_models import SummaryLanggraphState
from backend.helpers.dependencies import get_session_id
from backend.pydantic_models.chat_models import ChatMessage


summary_graph = get_summary_graph()
date_parser_graph = get_date_parser_graph()

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/summary")
def get_summary(chat_input: ChatMessage, session_id: str = Depends(get_session_id)):
    config = {"configurable": {"thread_id": session_id}}
    result = summary_graph.invoke(
        {
            "messages": [
                ("user", chat_input.message)
            ],
            "user_input": chat_input.message
        },
        config=config
    )
    return result["messages"][-1].content

@router.post("/date_parser")
def get_date_parser(chat_input: ChatMessage, session_id: str = Depends(get_session_id)):
    config = {"configurable": {"thread_id": session_id}}
    result = date_parser_graph.invoke(
        {
            "messages": [
                ("user", chat_input.message)
            ],
            "string_to_parse": chat_input.message
        },
        config=config
    )
    return result