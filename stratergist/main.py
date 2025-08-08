from typing import List
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, MessageGraph
from chains import revisor, first_responder
from tool_executor import execute_tools

MAX_ITERATIONS = 2
builder = MessageGraph()
builder.add_node("draft", first_responder)
builder.add_node("execute_tools", execute_tools)
builder.add_node("revise", revisor)
builder.add_edge("draft", "execute_tools")
builder.add_edge("execute_tools", "revise")


def event_loop(state: List[BaseMessage]) -> str:
    count_tool_visits = sum(isinstance(item, ToolMessage) for item in state)
    num_iterations = count_tool_visits
    if num_iterations > MAX_ITERATIONS:
        return END
    return "execute_tools"


builder.add_conditional_edges("revise", event_loop, {END:END, "execute_tools":"execute_tools"})
builder.set_entry_point("draft")
graph = builder.compile()

# print(graph.get_graph().draw_mermaid())

query_template = """
Coin out 3 strategies to improve investment of customer by balancing risk and returns.
Available instruments are:
- Growth
  - Mutual Funds
  - ETFs
- Fixed Income
  - Bonds

user_inputs = 
{{
    "horizon": "{investment_horizon} years",
    "monthly_investment": Rs. {monthly_investment}
}}

What should be the strategy to divide the money between these instruments?
Give output in the following JSON format:

{{
  "answer": {{
    "strategies": [
      {{
        "name": "Balanced Growth",
        "description": "A balanced approach for moderate risk and steady growth.",
        "allocation": {{
          "Mutual Funds": 5000,
          "Mutual Funds%": 50,
          "ETFs": 3000,
          "ETFs%": 30,
          "Bonds": 2000,
          "Bonds%": 20
        }},
        "expectedReturn": "10-12%",
        "mautityAmount": [calculate the maturity amount based on expected return, investment horizon and monthly investment],
        "riskLevel": "Moderate",
      }},
      {{
        "name": "Aggressive Equity",
        "description": "Higher equity allocation for aggressive growth seekers.",
        "allocation": {{
          "Mutual Funds": 7000,
          "Mutual Funds%": 70,
          "ETFs": 2500,
          "ETFs%": 25,
          "Bonds": 500,
          "Bonds%": 5
        }},
        "expectedReturn": "13-16%",
        "mautityAmount": [calculate the maturity amount based on expected return, investment horizon and monthly investment],
        "riskLevel": "High",
      }},
      {{
        "name": "Conservative Income",
        "description": "Focuses on capital preservation and steady income with minimal risk.",
        "allocation": {{
          "Mutual Funds": 2000,
          "Mutual Funds%": 20,
          "ETFs": 1000,
          "ETFs%": 10,
          "Bonds": 7000,
          "Bonds%": 70
        }},
        "expectedReturn": "6-8%",
        "mautityAmount": [calculate the maturity amount based on expected return, investment horizon and monthly investment],
        "riskLevel": "Low",
      }}
    ]
  }}
}}
"""

user_inputs = {
    "investment_horizon": "10 years",
    "monthly_investment": 12000
}

res = graph.invoke(query_template.format(**user_inputs))
print(res[-1].tool_calls[0]["args"]["answer"])
