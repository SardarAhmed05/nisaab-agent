from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    confirmed: bool
    user_id: int
    platform: str
    platform_id: str