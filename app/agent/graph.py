from langchain_groq import ChatGroq
from app.agent.tools import *
from app.agent.state import AgentState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.types import interrupt, Command
from app.agent.prompts import get_system_prompt
from app.db.crud import get_or_create_user
from app.db.session import AsyncSessionLocal
load_dotenv()

llm = ChatGroq (
    model="openai/gpt-oss-120b",
    reasoning_effort="medium",
    temperature=0
)

tools = [add_transaction, search_transaction, get_balance, get_total_expenses, get_category_summary, update_transaction, delete_transaction, create_budget, get_active_budgets, get_all_active_budgets, update_budget, delete_budget, get_budget_status]

# Tools that mutate/remove existing records and therefore require user confirmation.
RISKY_TOOLS = ["delete_transaction", "update_transaction", "delete_budget", "update_budget"]

llm_with_tools = llm.bind_tools(tools)

async def resolve_user_node(state: AgentState):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, state["platform"], state["platform_id"])
    return {"user_id": user.id}

async def agent_node(state: AgentState) -> dict:
    messages_with_system = [SystemMessage(content=get_system_prompt())] + state["messages"]
    response = await llm_with_tools.ainvoke(messages_with_system)
    return {"messages": [response]}

async def confirm_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    risky = next((t for t in last_message.tool_calls if t["name"] in RISKY_TOOLS), None)
    if risky is None:
        # Nothing to confirm (shouldn't happen given routing) — let it proceed.
        return {"confirmed": True}

    if risky["name"] in ("update_transaction", "update_budget"):
        ask = interrupt(f"Do you want to confirm these updates: {risky['args']}")
    else:  # delete_transaction, delete_budget
        ask = interrupt(f"Do you want to confirm the deletion: {risky['args']}")

    messages = [
        ("system", "You are a helpful assistant who confirms decisions."),
        ("human", f"The user was asked to confirm an action and replied: '{ask}'. Did they confirm (yes) or decline (no)? Answer with only 'yes' or 'no'."),
    ]
    ai_msg = await llm.ainvoke(messages)
    confirmed = "yes" in ai_msg.content.lower()

    if not confirmed:
        # User declined. Every tool_call on the last AIMessage is about to be
        # abandoned (we route to END without running ToolNode), so answer each
        # one with a ToolMessage — otherwise the unanswered tool_calls corrupt
        # the conversation history and break the provider on the next turn.
        cancellations = [
            ToolMessage(content="Action cancelled by the user.", tool_call_id=call["id"])
            for call in last_message.tool_calls
        ]
        return {"confirmed": False, "messages": cancellations}

    return {"confirmed": True}

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
        if call["name"] in RISKY_TOOLS:
            return True
    return False

def after_confirm(state: AgentState) -> str:
    if state["confirmed"]:
        return "tools"
    return "agent"
        
# Memory
memory = MemorySaver()

# GRAPH
graph = StateGraph(AgentState)

graph.add_node("resolve_user", resolve_user_node)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))
graph.add_node("confirm", confirm_node)

graph.set_entry_point("resolve_user")
graph.add_edge("resolve_user", "agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END, "confirm": "confirm"}
)

graph.add_conditional_edges(
    "confirm",
    after_confirm,
    {"tools": "tools", "agent": "agent", "end": END}
)

graph.add_edge("tools", "agent")

app = graph.compile(checkpointer=memory)
