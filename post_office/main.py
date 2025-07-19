from .agent import agent
from langchain.tools import tool

# query = """Screen Post Office investment schemes based on:
#   - time_horizon_years: 10
#   - user_age: 25
# """
@tool
def post_office_tool(query: str) -> str:
    """
    Uses the Post Office agent to fetch investment schemes based on user criteria like time horizon, age, etc.
    """
    response = agent.invoke({"input": query})
    return response.get("output", "No response from Post Office agent.")