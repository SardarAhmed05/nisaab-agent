# tests/test_graph_manual.py
import asyncio
from langchain_core.messages import HumanMessage

from app.agent.graph import app


async def main():
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="How much have i spent till now?")]}
    )
    for msg in result["messages"]:
        print(msg)


asyncio.run(main())