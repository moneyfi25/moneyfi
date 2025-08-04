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
    Coin out 3 stratergies to imporve investment of customer by balancing risk and returns.
    Available instruemnts are:
    - Growth
      - Mutual Funds
      - ETFs
    - Fixed Income
      - Bonds

    user_inputs = 
    {{
        "objective": "{objective}",
        "horizon": "{investment_horizon} years",
        "age": {age},
        "monthly_investment": Rs. {monthly_investment},
        "risk": "{risk}",
        "fund_type": "-",
        "special_prefs": "-"
    }}

    What should be the stratergy to divide the money between these instruments?
    """

user_inputs = {
    "objective": "Emergency Fund",
    "investment_horizon": "5 years",
    "age": 22,
    "monthly_investment": 100000,
    "risk": "Moderate",
    "fund_type": "-",
    "special_prefs": "-"
}

res = graph.invoke(query_template.format(**user_inputs))
print(res[-1].tool_calls[0]["args"]["answer"])
# print(res)
