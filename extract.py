from main import extract_investment_data
from agent_entry import run_orc_agent

user_inputs = {
        "objective": "Emergency Fund",
        "investment_horizon": "10 years",
        "age": 22,
        "monthly_investment": 0,
        "risk": "Conservative",
        "mutual_fund": 2400,
        "etf": 1200,
        "bond": 8400
    }

json_output = run_orc_agent(user_inputs)
print(json_output)
extract_investment_data(json_output, 331)