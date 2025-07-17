from agent import agent

query = """Screen Mutual Funds based on:
  - 1-year return greater than 3%
  and give me output in list format.
"""
response = agent.invoke({
    "input": query
})
print(response)