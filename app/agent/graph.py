from langchain_groq import ChatGroq
from app.agent.tools import *
from app.agent.state import AgentState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt, Command
from app.agent.prompts import get_system_prompt
load_dotenv()

llm = ChatGroq (
    model="openai/gpt-oss-120b",
    reasoning_effort="medium",
    temperature=0
)

tools = [add_transaction, search_transaction, get_balance, get_total_expenses, get_category_summary, update_transaction, delete_transaction, create_budget, get_active_budgets, get_all_active_budgets, update_budget, delete_budget, get_budget_status]

llm_with_tools = llm.bind_tools(tools)

async def agent_node(state: AgentState) -> dict:
    messages_with_system = [SystemMessage(content=get_system_prompt())] + state["messages"]
    response = await llm_with_tools.ainvoke(messages_with_system)
    return {"messages": [response]}

async def confirm_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    for tool in last_message.tool_calls:
        if tool["name"] in ["delete_transaction", "update_transaction", "delete_budget", "update_budget"]:
            risky = tool
        
    if risky["name"] == "update_transaction":
        ask = interrupt(f"Do you want to confirm these updates: {risky['args']}")

    if risky["name"] == "delete_transaction":
        ask = interrupt(f"Do you want to confirm the deletion: {risky['args']}")

    if risky["name"] == "update_budget":
        ask = interrupt(f"Do you want to confirm the updates: {risky['args']}")

    if risky["name"] == "delete_budget":
        ask = interrupt(f"Do you want to confirm the deletion: {risky['args']}")

    messages = [
        ("system", "You are a helpful assistant who confirms decisions."),
        ("human", f"The user was asked to confirm an action and replied: '{ask}'. Did they confirm (yes) or decline (no)? Answer with only 'yes' or 'no'."),
    ]
    ai_msg = await llm.ainvoke(messages)
    confirmed = "yes" in ai_msg.content.lower()

    return {"confirmed": confirmed}

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return "end"
    
    if needs_confirmation(state):
        return "confirm"
    
    return "tools"

def needs_confirmation(state: AgentState) -> bool:
    last_message = state["messages"][-1]
    for call in last_message.tool_calls:
        if call["name"] in ["delete_transaction", "update_transaction", "delete_budget", "update_budget"]:
            return True
    return False

def after_confirm(state: AgentState) -> str:
    if state["confirmed"]:
        return "tools"
    return "end"
        
# Memory
memory = MemorySaver()

# GRAPH
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.add_node("confirm", confirm_node)

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END, "confirm": "confirm"}
)

graph.add_conditional_edges(
    "confirm",
    after_confirm,
    {"tools": "tools", "end": END}
)

graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=memory)
