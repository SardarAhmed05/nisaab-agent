from langchain_groq import ChatGroq
from app.agent.tools import add_transaction, search_transaction, get_balance, get_total_expenses, update_transaction, delete_transaction
from app.agent.state import AgentState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.prompts import get_system_prompt
load_dotenv()

llm = ChatGroq (
    model="qwen/qwen3-32b",
    reasoning_effort="none",
)

tools = [add_transaction, search_transaction, get_balance, get_total_expenses, update_transaction, delete_transaction]

llm_with_tools = llm.bind_tools(tools)

async def agent_node(state: AgentState) -> dict:
    messages_with_system = [SystemMessage(content=get_system_prompt())] + state["messages"]
    response = await llm_with_tools.ainvoke(messages_with_system)
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "end"

# GRAPH
graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", "end": END}
)

graph.add_edge("tools", "agent")

app = graph.compile()
