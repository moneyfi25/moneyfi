from orc_agent import get_agent
# from stratergist.agent import get_stratergy_agent


query_template = """
You are an expert Financial Investment Advisor.

For mutual_funds_tool(user_inputs):
user_inputs = {{
    "objective": "{objective}",
    "horizon": "{investment_horizon} years",
    "age": {age},
    "monthly_investment": {mutual_fund},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

For etfs_tool(user_inputs):
user_inputs = {{
    "objective": "{objective}",
    "horizon": "{investment_horizon} years",
    "age": {age},
    "monthly_investment": {etf},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

For bonds_tool(user_inputs):
user_inputs = {{  
    "objective": "{objective}",
    "horizon": "{investment_horizon} years",
    "age": {age},
    "monthly_investment": {bond},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

Instructions:
1. Pass the user_inputs object as argument to the tools correctly without any error in values
2. Use the tools to get the best mutual funds, ETFs, and bonds based on the user's inputs
5. If any of {mutual_fund}, {etf}, {bond} is 0, then do not call the respective tool
6. Do not summarize or filter any information from the tools output - include EACH and EVERy detailed information provided by the tools

Produce your recommendation strictly as valid JSON, matching this schema exactly:
{{
  "Investment Portfolio Recommendation": {{
    "Monthly Investment Allocation": {{
      "Mutual Funds": <number>,
      "ETFs": <number>,
      "Bonds": <number>
    }},
    "Mutual Funds Details": [
      {{
        "Fund Name": "<string>",
        "Category": "<string>",
        "5-Year Return": <number>,
        "Expense Ratio": <number>,
        "Key Metrics": {{ /* all metrics returned by mutual_funds_tool */ }}
      }}
      /* repeat for each mutual fund */
    ],
    "ETFs Details": [
      {{
        "ETF Name": "<string>",
        "3-Year Return": <number>,
        "Expense Ratio": <number>,
        "Standard Deviation": <number>,
        "Key Metrics": {{ /* all metrics returned by etfs_tool */ }}
      }}
      /* repeat for each ETF */
    ],
    "Bonds Details": [
      {{
        "Bond Name": "<string>",
        "YTM": <number>,
        "Coupon Rate": <number>,
        "Maturity Date": "<YYYY-MM-DD>",
        "Additional Details": {{ /* all details returned by bonds_tool */ }}
      }}
      /* repeat for each bond */
    ]
  }}
}}

### Portfolio Summary
- **Total Monthly Investment:** ₹{monthly_investment}
- **Expected Portfolio Return:** [X-Y]% per annum
- **Risk Level:** [Based on user's risk appetite]
- **Investment Horizon:** {investment_horizon} years

IMPORTANT: 
- Do NOT skip any details provided by the tools
- Include every single fund, ETF, and bond suggested
- Preserve all metrics, ratios, and performance data
- Maintain the exact formatting structure shown above
"""

stratergy_query_template = """
You are an expert Financial Investment Strategist. You know how to create diversified investment strategies based on user inputs.

user_inputs = {{
    "objective": "{objective}",
    "horizon": "{investment_horizon} years",
    "age": {age},
    "monthly_investment": {monthly_investment},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

Instructions:
1. Create 4-5 different investment strategies for the user based on their profile
2. Each strategy should have a clear name and allocation breakdown
3. Allocate the monthly investment amount of ₹{monthly_investment} across different asset classes
4. Consider the user's risk appetite, age, objective, and time horizon
5. Include expected returns and risk level for each strategy

Asset Classes to Consider:
- Equity Mutual Funds (Large Cap, Mid Cap, Small Cap, Flexi Cap)
- Debt Mutual Funds (Liquid, Short Duration, Corporate Bond)
- Sovereign Gold Bonds (SGBs)
- Bonds (G-Secs, Corporate Bonds)

Output Format:
For each strategy, provide:

**Strategy [Number]: [Strategy Name]**
- **Risk Level**: [Low/Moderate/High]
- **Expected Return**: [X]% per annum
- **Asset Allocation**:
  - Equity Mutual Funds: ₹[amount] ([percentage]%)
  - Debt Instruments: ₹[amount] ([percentage]%)
  - Sovereign Gold Bonds: ₹[amount] ([percentage]%)
  - [Other assets if applicable]: ₹[amount] ([percentage]%)
- **Why This Strategy**: [Brief explanation of suitability]
- **Best For**: [Target investor profile]

**Example:**
Strategy 1: Balanced Growth Portfolio
- Risk Level: Moderate
- Expected Return: 12-14% per annum
- Asset Allocation:
  - Equity Mutual Funds: ₹6,000 (60%)
  - Debt Mutual Funds: ₹3,000 (30%)
  - Sovereign Gold Bonds: ₹1,000 (10%)
- Why This Strategy: Provides balanced growth with moderate risk, suitable for medium-term goals
- Best For: Investors seeking steady growth with manageable risk

Ensure each strategy is distinct and caters to different risk-return preferences within the user's profile.
"""

def run_orc_agent(user_inputs):
    agent = get_agent()
    query = query_template.format(**user_inputs)
    response = agent.invoke({"input": query})
    return response.get("output", "No response from ORC agent.")

# def run_stratergist_agent(user_inputs):
#     agent = get_stratergy_agent()
#     stratergy_query = stratergy_query_template.format(**user_inputs)
#     response = agent.invoke(stratergy_query)
#     return response.content

if __name__ == "__main__":
    user_inputs = {
        "objective": "Emergency Fund",
        "investment_horizon": "5 years",
        "age": 22,
        "monthly_investment": 0,
        "risk": "Aggresive",
        "mutual_fund": 8400,
        "etf": 3000,
        "bond": 600
    }
    print(run_orc_agent(user_inputs))

