from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import operator
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Define the State (Ensure the name matches throughout the code)
class SupportState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    should_escalate: bool
    issue_type: str
    user_tier: str  # "vip" or "standard"

# --- Nodes (The Steps) ---

def check_tier(state: SupportState):
    print(f"--- Checking Tier: {state.get('user_tier')} ---")
    return state

def vip_path(state: SupportState):
    # Wrapped string in AIMessage to match BaseMessage type
    return {
        "messages": [AIMessage(content="System: VIP status detected. Auto-resolving issue.")],
        "should_escalate": False
    }

def standard_path(state: SupportState):
    # Logic to decide if it's complex
    is_complex = len(state['messages']) > 1 
    if is_complex:
        return {
            "messages": [AIMessage(content="System: Standard issue is complex. Escalating to human.")],
            "should_escalate": True
        }
    return {
        "messages": [AIMessage(content="System: Standard issue resolved via FAQ.")],
        "should_escalate": False
    }

# --- Routing Logic ---

def route_by_tier(state: SupportState):
    if state["user_tier"].upper() == "VIP":
        return "vip"
    return "standard"

# --- Building the Graph ---

workflow = StateGraph(SupportState)

# 1. Add Nodes
workflow.add_node("check_tier", check_tier)
workflow.add_node("vip_path", vip_path)
workflow.add_node("standard_path", standard_path)

# 2. Set Entry Point
workflow.set_entry_point("check_tier")

# 3. Add Conditional Edges
workflow.add_conditional_edges(
    "check_tier",
    route_by_tier,
    {
        "vip": "vip_path",
        "standard": "standard_path"
    }
)

# 4. Connect to End
workflow.add_edge("vip_path", END)
workflow.add_edge("standard_path", END)

app = workflow.compile()

if __name__ == "__main__":
    # Test 1: VIP
    print("--- Testing VIP Path ---")
    input_vip = {"messages": [HumanMessage(content="Help!")], "user_tier": "VIP"}
    output_vip = app.invoke(input_vip)
    print(f"Result: {output_vip['messages'][-1].content}\n")

    # Test 2: Standard Complex
    print("--- Testing Standard Path (Complex) ---")
    input_std = {
        "messages": [HumanMessage(content="Hi"), HumanMessage(content="My PC won't turn on")], 
        "user_tier": "Standard"
    }
    output_std = app.invoke(input_std)
    print(f"Result: {output_std['messages'][-1].content}")