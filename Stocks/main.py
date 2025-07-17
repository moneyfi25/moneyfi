from stock_agent import agent

query = """
Evaluate stocks RELIANCE.NS, ONGC.NS, HDFCBANK.NS for investment.
Tell me which one is better based on fundamentals.
"""

response = agent.invoke({"input": query})
print(response)


