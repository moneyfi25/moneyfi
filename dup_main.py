from Stock_Screener.screener_agent import agent
from Stocks.stock_agent import agent as stock_agent

query = """
I'm planning for retirement in 15 years. I want to invest in Indian stocks with moderate risk appetite.
Which stocks should I shortlist? Shortlist 5 stocks by rank and give me output in comma separated list format.
"""

tickers = agent.invoke(query)

print("\n🎯 Shortlisted Stocks:", tickers)


print("\n📊 Running Stock Agent on filtered tickers...\n")
response = stock_agent.invoke(f"Analyze these Indian stocks: {tickers}. Tell me which are strongest fundamentally.")
print(response)