from .stock_agent import agent
from langchain.tools import tool

# query = """
# Evaluate stocks RELIANCE.NS, ONGC.NS, HDFCBANK.NS for investment.
# Tell me which one is better based on fundamentals.
# """
@tool
def stock_tool(query: str) -> str:  
    """
    Uses the Stock agent to fetch stock evaluation based on user criteria like fundamentals, growth, etc.
    """
    response = agent.invoke({"input": query})
    return response.get("output", "No response from Stock agent.")


