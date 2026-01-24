from langgraph.graph import StateGraph, START, END
from backend.pydantic_models.langgraph_models import ErrorLogEvaluationLanggraphState
from backend.pydantic_models.error_models import ErrorLogBase
from langchain_ollama import ChatOllama
from pydantic import ValidationError
from backend.helpers.helpers import save_langgraph_graph


llm = ChatOllama(
    model="llama3.2:latest", # the model we are using (llama3.2:3b)
    temperature=0.2, # higher temp = more creativity
)


def get_evaulation_error_log_graph():
    def control_node(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.input
        output = state.output
        _state = state.state
        feedback = state.feedback

        if output is None:
            return {"state": "parse_error_log"}
        elif output is not None and _state == "parse_error_log":
            return {"state": "evaluate_error_log"}
        elif output is not None and _state == "evaluate_error_log":
            return {"state": "END"}
        else:
            return {"state": "END"}
    
    def evaluate_error_log(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.input
        output = state.output
        _state = state.state
        feedback = state.feedback

        try:
            ErrorLogBase.model_validate_json(output)
            return {"output": output, "state": "END"}
        except ValidationError as e:
            return {"output": output, "state": "parse_error_log", "feedback": e.errors()}

    def parse_error_log(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.input
        output = state.output
        _state = state.state
        feedback = state.feedback

        prompt = (
            "You are a helpful assistant that can help record error logs in a structured format."
            "The error log should be structured based on the following fields:"
            f"{ErrorLogBase.model_json_schema()}"
            "If the traceback is long and contains multiple errors, parse for the error that most likely caused the main exception to be raised."
            "Here is the error log to be evaluated, which may or may not have user input, and may or may not have the full traceback:"
            "{_input}"
            "Here is the feedback from the previous step, which may simply be another error log or nothing at all:"
            "{feedback}"
        )

        response = llm.invoke(prompt)
        return {"output": response, "state": "evaluate_error_log"}
    
    builder = StateGraph(ErrorLogEvaluationLanggraphState)

    builder.add_node("control_node", control_node)
    builder.add_node("parse_error_log", parse_error_log)
    builder.add_node("evaluate_error_log", evaluate_error_log)

    builder.add_edge(START, "control_node")
    builder.add_conditional_edges(
        "control_node",
        lambda state: state.state,
        {
            "parse_error_log": "parse_error_log",
            "evaluate_error_log": "evaluate_error_log",
            "END": END
        }
    )
    builder.add_edge("parse_error_log", "control_node")
    builder.add_edge("evaluate_error_log", "control_node")

    graph = builder.compile()

    save_langgraph_graph("backend/images/error_log_evaluation_graph.png", graph)
    return graph
