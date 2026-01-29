from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, SystemMessage, RemoveMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.pydantic_models.langgraph_models import *
from backend.pydantic_models.error_models import ErrorLogBase
from langchain_ollama import ChatOllama
from pydantic import ValidationError
from backend.helpers.helpers import save_langgraph_graph
from backend.helpers.lang_tools import *
import json



llm = ChatOllama(
    model="llama3.2:latest", # the model we are using (llama3.2:3b)
    temperature=0.2, # higher temp = more creativity
)


tools = [
    get_current_date_time,
    get_projects,
    get_project,
    create_project,
    update_project,
    delete_projects
]
llm_with_tools = llm.bind_tools(tools)


def get_evaulation_error_log_graph():
    def control_node(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.get("input")
        output = state.get("output")
        _state = state.get("state")
        feedback = state.get("feedback")
        success = state.get("success")
        count = state.get("count", 0)

        print(f"{count = }")

        # state in the control node is the state of the next step
        if count == 5:
            return {"state": "END"}
        elif _state == "parse_error_log":
            return {"state": "evaluate_error_log"}
        elif _state == "evaluate_error_log" and success:
            return {"state": "END"}
        elif _state == "evaluate_error_log" and not success:
            return {"state": "parse_error_log"}
        else:
            return {"state": "parse_error_log"}
    
    def evaluate_error_log(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.get("input")
        output = state.get("output")
        _state = state.get("state")
        feedback = state.get("feedback")
        success = state.get("success")
        count = state.get("count", 0)

        try:
            _output = json.dumps(json.loads(output))
            _output = ErrorLogBase.model_validate_json(_output)
            return {"output": _output, "state": "evaluate_error_log", "success": True}
        except json.JSONDecodeError as e:
            return {"output": output, "state": "evaluate_error_log", "feedback": str(e), "success": False}
        except ValidationError as e:
            return {"output": output, "state": "evaluate_error_log", "feedback": e.errors(), "success": False}

    def parse_error_log(state: ErrorLogEvaluationLanggraphState) -> ErrorLogEvaluationLanggraphState:
        _input = state.get("input")
        output = state.get("output")
        _state = state.get("state")
        feedback = state.get("feedback")
        success = state.get("success")
        count = state.get("count", 0)

        prompt = (
            "You are a helpful assistant that can help record error logs in a structured format.\n"
            "Here is the error log schema:\n"
            f"{ErrorLogBase.model_fields}\n"
            "ONLY RESPOND BY FORMATTING THE ERROR ACCORDING TO THE SCHEMA ABOVE. IT MUST BE IN JSON FORMAT. DO NOT INCLUDE NEW LINE CHARACTERS.\n"
            "If the traceback is long and contains multiple errors, parse for the error that most likely caused the main exception to be raised.\n"
            "The main exception is the exception that is most likely to be raised by the programmer, and not from a library or framework.\n"
            "Do not let any paths contain excess '\\' characters, only what is necessary to make the path valid.\n"
            "Here is the error log to be evaluated, which may or may not have user input, and may or may not have the full traceback:\n"
            f"{_input}\n"
            "Here is the feedback from your previous attempt at parsing the error log, which may simply be another error log or nothing at all:\n"
            f"{feedback}\n"
        )

        print(f"{feedback = }")
        print(f"{prompt = }")
        response = llm.invoke(prompt)
        print(f"{response.content = }")
        return {"output": response.content, "state": "parse_error_log", "count": count + 1}
    
    builder = StateGraph(ErrorLogEvaluationLanggraphState)

    builder.add_node("control_node", control_node)
    builder.add_node("parse_error_log", parse_error_log)
    builder.add_node("evaluate_error_log", evaluate_error_log)

    builder.add_edge(START, "control_node")
    builder.add_conditional_edges(
        "control_node",
        lambda state: state.get("state"),
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


def get_summary_graph():
    def summarize_content(state: SummaryLanggraphState) -> SummaryLanggraphState:
        messages = state.get("messages", [])
        summary = state.get("summary", "")
        route = state.get("route")
        user_input = state.get("user_input", "")

        if len(messages) > 10:
            to_summarize = messages[:-10]

            prompt = (
                "You are a helpful assistant that can help summarize content."
                "Here is the content to be summarized:\n"
                f"{to_summarize}\n"
                "Here is the summary from your previous attempt at summarizing the content, which may simply be another summary or nothing at all:\n"
                f"{summary}\n"
                "Summarize the content, including the old summary, in a concise and informative manner, focusing on the main points and key insights. DO NOT REPEAT THE OLD SUMMARY.\n"
            )
            response = llm.invoke(prompt)

            delete_messages = [RemoveMessage(id=m.id) for m in to_summarize if getattr(m, "id", None)]

            return {"summary": response.content, "messages": delete_messages}
        
        return {}
    
    def call_model(state: SummaryLanggraphState) -> SummaryLanggraphState:
        messages = state.get("messages", [])
        summary = state.get("summary", "")
        route = state.get("route")
        user_input = state.get("user_input", "")
        
        if route == "toolbox":
            print("EXITING")
            return {"route": "__end__"}
        prompt = [
            SystemMessage(
                content=f"""
                            You are a helpful assistant that can help the user with their request.
                            You have proper responses to the user. You won't ever response with "__end__", for instance.
                            You have a subordinate model that can access the tools you see listed:
                            {
                                [
                                    {
                                        "name": tool.name,
                                        "description": tool.description,
                                        "arguments": tool.args
                                    }
                                    for tool in tools
                                ]
                            }
                            IF YOU THINK IT REQUIRES A TOOL CALL, RETURN THE STRING "TOOLBOX" AS YOUR RESPONSE.
                            You do not have direct access to any of the tools you see listed, but you have indirect access to them through your subordinate model.
                            It can make tool calls on your behalf, you need only to respond with the string "TOOLBOX" as your response and it will do the rest.
                            This can include the user asking you to make a tool call, or you deciding to make a tool call yourself.
                            Just to reiterate, return "TOOLBOX" as your response to pass it to the subordinate model.
                            You don't let the user know that you are using a subordinate model, or that you are using tools.
                            Current summary: {summary}.
                            Instructions: Provide direct, natural answers to the user from the information you have available to you.
                            If you do not think it requires a tool call, return the string "__end__" as your response.
                        """
            )] + messages
        response = llm.invoke(prompt)
        if response.content == "TOOLBOX":
            return {"route": "toolbox"}
        return {"messages": [response], "route": "__end__"}

    def get_toolbox_graph():
        def tool_box(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            retry_counter = state.get("retry_counter", 0)
            user_input = state.get("user_input", "")
            route = state.get("route", None)
            
            print("START TOOLBOX")

            response = llm_with_tools.invoke(
                [
                    SystemMessage(
                        content=f"""
                        Your only job is to use the tools you see listed to accomplish the user's request or provide a response to the user's input.
                        IMPORTANT: When calling tools, you must provide raw values (strings, numbers, lists). 
                        NEVER use Python code, variable names, or function calls as arguments.
                        NEVER guess at the arguments for the tools. For instance:
                        If you need information to perform a task, you should call the appropriate tool to get the information to use in your response or make subsequent tool calls.
                        If the user asks to delete all of the projects, you should not guess the project IDs and pass them in as an argument.
                        You should call the 'get_projects' tool to get the IDs of all the projects, then call the 'delete_projects' tool and pass in the IDs of the projects to delete.
                        You think critically about how to call the tools to get the best result.
                        You think critically about how to obtain information from the tools to use in your response or make subsequent tool calls.
                        For example, if the user asks to delete all of the projects, you should call the "get_projects" tool to get the IDs of all the projects, then call the "delete_projects" tool and pass in the IDs of the projects to delete.
                        If you do not succeed, you try again, up to 5 times, which I will track for you.
                        You must return a truthful and accurate response to the user's input.
                        """
                    ),
                    (
                        HumanMessage(
                            content=user_input
                        )
                    )
                ] + messages[-2:])

            print(f"{response = }")
            
            print("END TOOLBOX")

            return {
                "messages": [response]
            }
        
        def call_tools(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            retry_counter = state.get("retry_counter", 0)
            user_input = state.get("user_input", "")
            route = state.get("route", None)

            responses = []

            print("START TOOLS")

            if len(messages[-1].tool_calls) == 0:
                print("NO TOOL CALLS")
                print("END TOOLS")
                return {
                    "messages": messages,
                    "route": "tool_box"
                }
            
            for tool_call in messages[-1].tool_calls:
                selected_tool = next(t for t in tools if t.name == tool_call.get("name"))
                try:
                    tool_output = selected_tool.invoke(tool_call.get("args"))
                except Exception as e:
                    tool_output = f"Error calling tool: {str(e)}"
                responses.append(ToolMessage(
                    content=tool_output,
                    tool_call_id=tool_call.get("id")
                ))

            print("END TOOLS")
            
            return {
                "messages": responses
            }
        
        def evaluate_tool_response(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            retry_counter = state.get("retry_counter", 0)
            retry_counter += 1
            user_input = state.get("user_input", "")
            route = state.get("route", None)

            print("START EVALUATE")

            if retry_counter > 4:
                error_msg = AIMessage(content="I'm sorry, I'm unable to process your request.")
                print(f"{state = }")
                return {
                    "messages": [error_msg],
                    "route": "__end__"
                }
            
            response = llm.invoke(
                [
                    SystemMessage(
                        content=f"""
                        You are a helpful assistant that can help evaluate tool responses to a user's input.
                        You do not make the tool call. You only evaluate the tool response.
                        Evaluating the response is your one and only job.
                        Here is the User's input. User's input: {user_input}.
                        You look at the whole tool response and determine if it is successful or not.
                        Success is defined as the tool response being able to accomplish the user's request or provide a response to the user's input.
                        If you think the tool response is successful, return the JSON object {{"status": "SUCCESS", "critique": ""}} as your response.
                        If you think the tool response is not successful, return the JSON object {{"status": "FAILURE", "critique": *Your critique of the tool response*}} as your response.
                        You will find the other messages attached to potentially assist you.
                        You only respond with the JSON object, no other text or commentary.
                        An empty JSON response is not a valid response.
                        The next message is the tool response to be evaluated.
                        """
                    )
                ] + [messages[-1]]
            )

            print(f"{'\n'.join([e.content for e in messages[-3:]]) = }")

            print(f"{response.content = }")

            try:
                _output = json.loads(response.content)
                status = _output.get("status", "")
                critique = _output.get("critique", "")
            except json.JSONDecodeError as e:
                return {"route": "tool_box",}

            if critique == "":
                return {"route": "tool_box",}
            messages.append(AIMessage(content=critique))

            print("END EVALUATE")

            if status == "SUCCESS":
                return {"route": "__end__", "messages": messages, "retry_counter": retry_counter}
            elif status == "FAILURE":
                return {"route": "tool_box", "messages": messages, "retry_counter": retry_counter}
            else:
                return {"route": "evaluate_tool_response", "messages": messages, "retry_counter": retry_counter}


        child_builder = StateGraph(ToolLanggraphState)
        child_builder.add_node("tool_box", tool_box)
        child_builder.add_node("call_tools", call_tools)
        child_builder.add_node("evaluate_tool_response", evaluate_tool_response)

        child_builder.add_edge(START, "tool_box")
        child_builder.add_edge("tool_box", "call_tools")
        child_builder.add_edge("call_tools", "evaluate_tool_response")
        child_builder.add_conditional_edges(
            "evaluate_tool_response",
            lambda state: state.get("route"),
            {
                "tool_box": "tool_box",
                "evaluate_tool_response": "evaluate_tool_response",
                END: END
            }
        )

        child_graph = child_builder.compile()
        save_langgraph_graph("backend/images/tool_box_graph.png", child_graph)
        return child_graph

    toolbox_graph = get_toolbox_graph()

    def call_toolbox(state: SummaryLanggraphState) -> SummaryLanggraphState:
        messages = state.get("messages", [])
        tool_response = state.get("tool_response", {})
        route = state.get("route", None)
        user_input = state.get("user_input", "")
        summary = state.get("summary", "")

        # 1. Pass ONLY what the child needs (e.g., the last few messages)
        child_input = {"user_input": user_input}
        
        # 2. Invoke the child graph
        result = toolbox_graph.invoke(child_input)
        
        # 3. Return only the final message to the parent state
        # This prevents the parent's 'messages' list from seeing all the 
        # messy intermediate ToolMessages from the child.
        final_msg = result["messages"][-1]
        return {"messages": [final_msg], "route": None}

    # Build the Graph
    builder = StateGraph(SummaryLanggraphState)
    builder.add_node("assistant", call_model)
    builder.add_node("summarize", summarize_content)
    builder.add_node("toolbox", call_toolbox)

    builder.set_entry_point("assistant")
    
    builder.add_conditional_edges(
        "assistant",
        lambda state: state.get("route", "__end__"),
        {
            "toolbox": "toolbox",
            "__end__": "summarize" # This will route to summarize if no tools are called
        }
    )

    # After tools run, they must always go back to the assistant to interpret results
    builder.add_edge("toolbox", "assistant")
    
    # Finally, link summarize to the end
    builder.add_edge("summarize", END)

    graph = builder.compile(checkpointer=MemorySaver())

    save_langgraph_graph("backend/images/summary_graph.png", graph)
    return graph