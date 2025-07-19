from orc_agent import agent

query = """
I want to get investment suggestions for my portfolio. My profile is:
- I am 30 years old.
- I want to invest ₹10,000 per month.
- I want to save for retirement in 30 years.
- I want to maximize returns.
- I am okay with moderate risk.

Give me a diversified portfolio.
"""
response = agent.invoke({
    "input": query
})
print(response.get("output", "No response from ORC agent."))