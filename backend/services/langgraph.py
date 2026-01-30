from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, SystemMessage, RemoveMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_openai import ChatOpenAI

from backend.pydantic_models.langgraph_models import *
from backend.pydantic_models.error_models import ErrorLogBase
from backend.pydantic_models.project_models import ProjectResponse
from backend.helpers.helpers import save_langgraph_graph
from backend.helpers.lang_tools import *

from pydantic import ValidationError
import json


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2, # higher temp = more creativity
)


available_models = [
    ProjectResponse,
]
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
        tool_response = state.get("tool_response", None)
        tool_evaluation = state.get("tool_evaluation", {})

        prompt = f"""
            You are a helpful assistant that can help the user with their request.
            You have proper responses to the user. You won't ever response with "__end__" or "", for instance.
        """
        print(f"{messages = }")
        print(f"{tool_response}")
        if tool_response:
            tool = next((tool for tool in tools if tool.name == tool_response.name), None)
            prompt = f"""
            {prompt}
            You have a subordinate model made a tool call on your behalf. Here is a description of what the tool does:
            {tool.description}
            In the below ToolMessage is the result of the tool call from your subordinate model:
            {tool_response}
            It may not be as helpful, but here is the evaluation of the tool call:
            {tool_evaluation}
            The ToolMessage is more important than the evaluation.
            Use the evaluation if the evaluation alludes to a problem with the tool call, or that the tool call was not successful.
            Use this information to respond to the user's input.
            DO NOT MAKE UP INFORMATION, ONLY RESPOND WITH THE INFORMATION YOU HAVE AVAILABLE TO YOU FROM ABOVE IN THE TOOLMESSAGE.
            You do not let the user know that you are using a subordinate model, or that you are using tools.
            A simple response is a perfectly valid response.
            """
        else:
            prompt = f"""
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
            {prompt}
            IF YOU THINK IT REQUIRES A TOOL CALL OR THAT IT CAN BE PERFORMED WITH A TOOL CALL, RETURN ONLY THE STRING "TOOLBOX" AS YOUR RESPONSE.
            You do not have direct access to any of the tools you see listed, but you have indirect access to them through your subordinate model.
            It can make tool calls on your behalf, you need only to respond with the string "TOOLBOX" as your response and it will do the rest.
            This can include the user asking you to make a tool call, or you deciding to make a tool call yourself.
            Just to reiterate, return ONLY THE STRING "TOOLBOX" as your response to pass it to the subordinate model.
            You don't let the user know that you are using a subordinate model, or that you are using tools.
            """
        
        prompt = f"""
        {prompt}
        Current summary: {summary}.
        Instructions: Provide direct, natural answers to the user's prompt using the information you have available to you.
        """

        prompt = [SystemMessage(content=prompt)] + messages
        response = llm.invoke(prompt)

        # print(f"{prompt = }")
        # print(f"{response}")

        if response.content == "TOOLBOX":
            return {"route": "toolbox"}
        return {"messages": [response], "route": "__end__"}

    def get_toolbox_graph():

        def plan_tool_calls(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            user_input = state.get("user_input", "")
            route = state.get("route", None)
            retry_counter = state.get("retry_counter", 0)
            plan = state.get("plan", "")
            tool_calls = state.get("tool_calls", [])

            print("START PLAN")

            prompt = f"""
            You are a helpful assistant that can help the user with their request.
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
            Your job is to think step by step through the user's input to create a plan for another LLM to achieve the user's input or provide the information they need using tool calls and stored messages.
            Create and return ONLY THE PLAN as a string that would use the tools and stored messages to achieve the user's input or provide the information they need.
            An example user input might be: "Can you delete all of the projects?"
            A plan to achieve the example user input would be:
            1. Get all of the projects using the get_projects tool
            2. Extract the project IDs from the projects you just pulled
            3. Delete the projects using the delete_projects tool and the project IDs
            You only respond with the plan, you do not perform any tool calls, or output anything else.
            If it is impossible to create a plan with the given tools to achieve the user's input, return the string "__end__" as your response.
            """
            response = llm.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=f"{user_input}")
            ])

            print(f"{response = }")

            print("END PLAN")

            if response.content == "__end__":
                return {
                    "messages": [
                        ToolMessage(name="tool_box", content="__end__"),
                        HumanMessage(content="I'm sorry, I'm unable to create a plan to achieve the user's input with the given tools.")
                    ], 
                    "route": END
                }

            return {"plan": response.content, "route": "tool_box"}


        def tool_box(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            retry_counter = state.get("retry_counter", 0)
            user_input = state.get("user_input", "")
            route = state.get("route", None)
            plan = state.get("plan", "")
            tool_calls = state.get("tool_calls", [])

            print("START TOOL BOX")

            print(f"{'\n'.join([str(tool_call) for tool_call in tool_calls])}")

            tool_response = llm_with_tools.invoke(
                [
                    SystemMessage(content=f"""
                    YOUR ONE AND ONLY JOB IS TO PERFORM THE PROPER TOOL CALLS AND RETURN THE RESULTS BASED ON THE PLAN PROVIDED TO YOU AND ANY DATA GIVEN TO YOU.
                    IMPORTANT: YOU DO NOT MAKE A PLAN, YOU EXECUTE THE PLAN PROVIDED TO YOU.
                    You have these tools available to you:
                    {tools}
                    Here are the available models you can use to parse or filter data:
                    {[model.model_fields for model in available_models]}
                    Here is the plan to be executed:
                    {plan}
                    You might see additional feedback below this message that might help you follow the plan.
                    If you are thinking about outputting "", explain why.
                    Tell me why you also might be struggling to follow the plan.
                    Here are the tool calls you have made so far:
                    {tool_calls}
                    """)
                ] + messages[-5:]
            )

            print(f"Messages: {'\n'.join([message.content if message.content != "" else "tool call" for message in messages])}")
            print(f"{tool_response = }")

            print("END TOOL BOX")

            if len(tool_response.tool_calls) > 0:
                print("TOOL BOX - TOOL CALL")
                return {"messages": [tool_response], "route": "evaluate_tool_response"}
            else:
                if tool_response.content == "":
                    print("TOOL BOX - \"\"")
                    return {"messages": [HumanMessage(content="Please phrase your request more clearly.")]}
                else:
                    print("TOOL BOX - NOT \"\"")
                    return {"messages": [HumanMessage(content=tool_response.content)], "route": "tool_box"}
        
        def evaluate_tool_response(state: ToolLanggraphState) -> ToolLanggraphState:
            messages = state.get("messages", [])
            retry_counter = state.get("retry_counter", 0)
            user_input = state.get("user_input", "")
            route = state.get("route", None)
            plan = state.get("plan", "")
            tool_calls = state.get("tool_calls", [])

            llm_with_schema = llm.with_structured_output(EvaluationSchema)

            print("START EVALUATE TOOL")
            tool_message = messages[-1]

            evaluation = llm_with_schema.invoke([
                SystemMessage(content=f"""
                    Your one and only job is to evaluate the tool response and return the results based on the User's input.
                    The main question goal is does the tool response answer the User's input or perform the task they asked for?
                    Here is the User's input: {user_input}.
                    Here is the tool response to be evaluated: {tool_message}.
                    You do not make up any information, you only answer based on the tool response and the User's input.
                    You can not make tool calls, you only answer based on the tool response and the User's input.
                    If the tool response answers the User's input or performs the task they asked for, the success should be True and the response should be the tool response. This is largely determined by if there was an error in the tool call.
                    If the tool response does not answer the User's input or perform the task they asked for, the success should be False and the response should be the tool response.
                    If the tool is successful, return the tool response as the response.
                    """
                )
            ])
            print(f"{tool_message = }")
            print(f"{evaluation = }")
            print("END EVALUATION")

            if evaluation.success:
                print("END EVALUATION: SUCCESS")
                return {"route": END, "tool_evaluation": evaluation, "tool_response": tool_message, "tool_calls": [tool_message]}
            else:
                print("END EVALUATION: FAILURE")
                return {"messages": [HumanMessage(content=evaluation.response)], "route": "tool_box", "tool_calls": [tool_message]}

        child_builder = StateGraph(ToolLanggraphState)
        child_builder.add_node("tool_box", tool_box)
        child_builder.add_node("plan_tool_calls", plan_tool_calls)
        child_builder.add_node("tools", ToolNode(tools))
        child_builder.add_node("evaluate_tool_response", evaluate_tool_response)

        child_builder.add_edge(START, "plan_tool_calls")
        child_builder.add_conditional_edges("plan_tool_calls", lambda state: state.get("route"), {
            "tool_box": "tool_box",
            "__end__": END
        })
        child_builder.add_conditional_edges("tool_box", tools_condition, {
            "tools": "tools",
            "__end__": "tool_box"
        })
        child_builder.add_conditional_edges("evaluate_tool_response", lambda state: state.get("route"), {
            "tool_box": "tool_box",
            END: END
        })
        child_builder.add_edge("tools", "evaluate_tool_response")

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