from langchain.tools import tool
from .agent import agent

# query = """Find only one and the best Sovereign Gold Bond (SGB) using the tools provided.
# I want to use it to hedge my growth portfolio.
# I want to fight iflation and get a good return.
# """
@tool
def sgb_tool(query: str) -> str:
    """
    Uses the SGB agent to fetch the best Sovereign Gold Bond suggestion 
    based on user goals like inflation protection, returns, etc.
    """
    response = agent.invoke({"input": query})
    return response.get("output", "No response from SGB agent.")