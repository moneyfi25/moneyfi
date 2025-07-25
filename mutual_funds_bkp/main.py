from .agent import agent
from langchain.tools import tool

query = """Screen 3 best Mutual Funds based on user criteria:
  - I need to save ₹1,00,000 in 1 year.
  - I want to invest in moderate-risk funds.
  - I want to maximize returns.
  - I want to invest ₹5,000 per month.
  and give me output in list format.
"""
response = agent.invoke({
    "input": query
})
print(response.get("output", "No response from Mutual Funds agent."))


# @tool
# def mutual_funds_tool(query: str) -> str:
#     """
#     Uses the Mutual Funds agent to fetch mutual fund suggestions based on user criteria like risk, returns, etc.
#     """
#     response = agent.invoke({"input": query})
#     return response.get("output", "No response from Mutual Funds agent.")