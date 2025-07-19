from .screener_agent import agent
from langchain.tools import tool

@tool
def stock_screen_tool(query: str) -> str:
    """
    Uses the Stock Scrneer agent to fetch stocks based on user criteria like fundamentals, growth, etc.
    """
    response = agent.invoke({"input": query})
    return response.get("output", "No response from Stock agent.")