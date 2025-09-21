import os
from dotenv import load_dotenv
from typing import Annotated,Sequence, TypedDict

import json

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages # helper function to add messages to the state

from langchain_core.messages import AIMessage, ToolMessage

from langchain_core.tools import tool
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field
import requests

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, END

from IPython.display import Image, display

from langgraph.checkpoint.memory import MemorySaver

from tools import tools
from model import model

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    number_of_steps: int


# Define the conditional edge that determines whether to continue or not
def should_continue(state: AgentState):
    """Route only if the last message is an AIMessage with tool calls."""
    if not state.get("messages"):
        return "end"
    last = state["messages"][-1]
    # Only AIMessage can contain tool_calls
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "continue"
    return "end"

tools_by_name = {tool.name: tool for tool in tools}


def call_tool(state: AgentState):
    outputs = []
    last = state["messages"][-1]
    for tool_call in last.tool_calls:
        result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        # Make sure content is a string
        if not isinstance(result, str):
            result = json.dumps(result, ensure_ascii=False)
        outputs.append(
            ToolMessage(
                content=result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

def call_model(
    state: AgentState,
    config: RunnableConfig,
):
    has_user = any(m.type == "human" for m in state["messages"])
    if not has_user:
        return {"messages": []}  # nothing new to add
    
    # Invoke the model with the system prompt and the messages
    # in call_model, just before invoke:
    print("[DEBUG] sending", len(state["messages"]), "messages to LLM:")
    for i, m in enumerate(state["messages"]):
        print(f"  {i}: {m.type} :: {getattr(m, 'content', '')[:80]!r}")

    response = model.invoke(state["messages"], config)
    # We return a list, because this will get added to the existing messages state using the add_messages reducer
    return {"messages": [response]}


# Define a new graph with our state
workflow = StateGraph(AgentState)

# 1. Add our nodes 
workflow.add_node("llm", call_model)
workflow.add_node("tools",  call_tool)
# 2. Set the entrypoint as `agent`, this is the first node called
workflow.set_entry_point("llm")
# 3. Add a conditional edge after the `llm` node is called.
workflow.add_conditional_edges(
    # Edge is used after the `llm` node is called.
    "llm",
    # The function that will determine which node is called next.
    should_continue,
    # Mapping for where to go next, keys are strings from the function return, and the values are other nodes.
    # END is a special node marking that the graph is finish.
    {
        # If `tools`, then we call the tool node.
        "continue": "tools",
        # Otherwise we finish.
        "end": END,
    },
)
# 4. Add a normal edge after `tools` is called, `llm` node is called next.
workflow.add_edge("tools", "llm")

# Now we can compile and visualize our graph

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)