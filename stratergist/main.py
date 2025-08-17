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
Coin out 3-4 diverse investment strategies to improve the customer's portfolio by balancing risk and returns.
Divide funds between different instruments based on the user's investment interests and risk appetite.
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

Guidelines:
- Provide at least one strategy for each risk level: "High", "Moderate", "Moderate-Low", "Low".
- For each strategy, allocations for "monthly" and "lumpsum" must each sum to 100%.
- All allocation percentages must be integers.
- All currency values must be in the format "Rs. 123456" (no formulas).
- Each strategy should have a clear, concise description explaining the rationale and risk/return tradeoff.
- Use realistic, diverse allocations for each risk level.

Give output in the following JSON format:
{{
  "answer": {{
    "strategies": [
      {{
        "name": "...",
        "description": "...",
        "allocation": {{
          "monthly": {{
            "MutualFunds%": ...,
            "ETFs%": ...,
            "Bonds%": ...,
            "SGBs%": ...,
          }},
          "lumpsum": {{
            "MutualFunds%": ...,
            "ETFs%": ...,
            "Bonds%": ...,
            "SGBs%": ...,
          }},
        }},
        "expectedReturn": "~12% annualised",
        "riskLevel": "High"
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