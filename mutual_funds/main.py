from agent import agent

query = """Screen 3 best Mutual Funds based on user criteria:
  - I need to save ₹1,000,000 in 10 years.
  - I want to invest in low-risk funds.
  - I want to maximize returns.
  - I want to invest ₹5,000 per month.
  and give me output in list format.
"""
response = agent.invoke({
    "input": query
})
print(response)