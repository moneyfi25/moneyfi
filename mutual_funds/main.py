from agent import agent

query = "I want to get the get the best mutual funds to invest which can the best returns in recent times."

response = agent.invoke({
    "input": query
})
print(response.get("output", "No response from Mutual Funds agent."))