from agent import agent

query = """I want to get the top 5 bonds to invest in : """

response = agent.invoke({
    "input": query
})
print(response.get("output", "No response from Bonds agent."))