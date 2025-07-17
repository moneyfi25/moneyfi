from agent import agent
from toolkit import screen_post_office_schemes

query = """Screen Post Office investment schemes based on:
  - time_horizon_years: 10
  - user_age: 25
"""
response = agent.invoke({
    "input": query
})
print(response)