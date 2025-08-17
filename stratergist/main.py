from typing import List
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, MessageGraph
from .chains import revisor, first_responder
from .tool_executor import execute_tools
import json
import ast

MAX_ITERATIONS = 1
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
Coin out 3-4 diverse strategies to improve investment of customer by balancing risk and returns.
Your task is to divide funds between different instruments based on the user's investment interests.
Available instruments are:
- Growth
  - Mutual Funds 
  - ETFs
- Fixed Income
  - Bonds (Government Securities, Corporate Bonds, etc.)
  - Sovereign Gold Bonds (SGBs)

user_inputs = 
{{
    "lumpsum": Rs. {lumpsum},
    "horizon": "{investment_horizon} years",
    "monthly_investment": Rs. {monthly_investment}
}}

What should be the strategy to divide the money between these instruments?
Give output in the following JSON format:
{{
  "answer": {{
    "strategies": [
      {{
        "name": "...",
        "description": "...",
        "allocation": [
          "monthly": 
          {{
            "MutualFunds%": 50,
            "ETFs%": 0,
            "Bonds%": 0,
            "SGBs%": 50,
          }},
          "lumpsum":
          {{
            "MutualFunds%": 100,
            "ETFs%": 0,
            "Bonds%": 0,
            "SGBs%": 0,
          }},
        ],
        "expectedReturn": "~10%",
        "mautityAmount": [calculate the maturity amount based on expected return, investment horizon, lumpsum investment and monthly investment],
        "riskLevel": "Moderate",
      }},
      {{
        "name": "...",
        "description": "...",
        "allocation": [
          "monthly": 
          {{
            "MutualFunds%": 50,
            "ETFs%": 30,
            "Bonds%": 20,
            "SGBs%": 0,
          }},
          "lumpsum":
          {{
            "MutualFunds%": 0,
            "ETFs%": 0,
            "Bonds%": 100,
            "SGBs%": 0,
          }},
        ],
        "expectedReturn": "~8%",
        "mautityAmount": [calculate the maturity amount based on expected return, investment horizon, lumpsum investment and monthly investment],
        "riskLevel": "Low",
      }},
      ...
    ]
  }}
}}
"""

user_inputs = {
    "investment_horizon": "5 years",
    "monthly_investment": 1000,
    "lumpsum": 10000
}

def run_strategist_agent(user_inputs):
    """
    Runs the strategist agent with the provided user inputs.
    """
    if isinstance(user_inputs, str):
        try:
            user_inputs = json.loads(user_inputs)
        except json.JSONDecodeError:
            try:
                user_inputs = ast.literal_eval(user_inputs)
            except (ValueError, SyntaxError):
                print("❌ Failed to parse user_inputs string")
                return "Error: Could not parse user inputs"
    
    query = query_template.format(**user_inputs)
    response = graph.invoke(query)
    return response[-1].tool_calls[0]["args"]["answer"]