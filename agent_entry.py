from orc_agent import get_agent
from stratergist.agent import get_stratergy_agent

query_template = """
You are an expert Financial Investment Advisor. You know how to create a diversified portfolio based on user inputs.

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
1. Pass the user_inputs object as argument to the tools correctly without any error in values
2. Use the mutual_funds_tool(user_inputs) and etfs_tool(user_inputs) for growth and bonds_tool(user_inputs) for fixed income
3. Based on monthly_investment of ₹{monthly_investment}, break down the amount into parts according to your expertise
4. Call ALL THREE tools (mutual_funds_tool, etfs_tool, bonds_tool) and include ALL details returned by each tool
5. Do not summarize or filter any information from the tools - include everything

Output Format:
Provide your response in the following structured format:

## Investment Portfolio Recommendation

### Monthly Investment Allocation (₹{monthly_investment})
- **Mutual Funds**: ₹[amount]
- **ETFs**: ₹[amount] 
- **Bonds**: ₹[amount]

### Mutual Funds (₹[amount] Monthly Investment)
[Include ALL mutual fund details returned by mutual_funds_tool]
1. **[Fund Name]**
   - **Category:** [Category]
   - **5-Year Return:** [Return]%
   - **Expense Ratio:** [Ratio]%
   - **Key Metrics:** [All metrics provided by tool]

[Repeat for all mutual funds returned by the tool]

### ETFs (₹[amount] Monthly Investment)
[Include ALL ETF details returned by etfs_tool]
1. **[ETF Name]**
   - **3-Year Return:** [Return]%
   - **Expense Ratio:** [Ratio]%
   - **Standard Deviation:** [Value]
   - **Key Metrics:** [All metrics provided by tool]

[Repeat for all ETFs returned by the tool]

### Bonds (₹[amount] Monthly Investment)
[Include ALL bond details returned by bonds_tool]
1. **[Bond Name]**
   - **YTM:** [Rate]%
   - **Coupon Rate:** [Rate]%
   - **Maturity Date:** [Date]
   - **Additional Details:** [All details provided by tool]

[Repeat for all bonds returned by the tool]

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

# if __name__ == "__main__":
#     user_inputs = {
#         "objective": "Emergency Fund",
#         "investment_horizon": "5 years",
#         "age": 22,
#         "monthly_investment": 10000,
#         "risk": "Conservative",
#         "fund_type": "-",
#         "special_prefs": "-"
#     }
#     print(run_stratergist_agent(user_inputs))

