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
    "lumpsum_investment": {mutual_fund_lumpsum},
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
    "lumpsum_investment": {etf_lumpsum},
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
    "lumpsum_investment": {bond_lumpsum},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

For sgb_tool(user_inputs):
user_inputs = {{
    "objective": "{objective}",
    "horizon": "{investment_horizon} years",
    "age": {age},
    "monthly_investment": {sgb},
    "lumpsum_investment": {sgb_lumpsum},
    "risk": "{risk}",
    "fund_type": "-",
    "special_prefs": "-"
}}

Instructions:
1. Pass the user_inputs object as argument to the tools correctly without any error in values
2. Use the tools to get the best mutual funds, ETFs, and bonds based on the user's inputs
3. If both {mutual_fund} and {mutual_fund_lumpsum} are 0, skip mutual funds tool
4. If both {etf} and {etf_lumpsum} are 0, skip ETFs tool
5. If both {bond} and {bond_lumpsum} are 0, skip bonds tool
6. If both {sgb} and {sgb_lumpsum} are 0, skip SGBs tool
7. Do not summarize or filter any information from the tools output - include EACH and EVERY detailed information provided by the tools

IMPORTANT: 
- Do NOT skip any details provided by the tools
- Include every single fund, ETF, and bond suggested
- Preserve all metrics, ratios, and performance data
- Maintain the exact formatting structure shown below

Produce your recommendation strictly as valid JSON, matching this schema exactly:
{{
  "Investment Portfolio Recommendation": {{
    "Monthly Investment":{{
      Allocation": {{
      "Mutual Funds": <number>,
      "ETFs": <number>,
      "Bonds": <number>,
      "SGBs": <number>
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
          "Category": "<string>",
          "5-Year Return": <number>,
          "Expense Ratio": <number>,
          "Key Metrics": {{ /* all metrics returned by etfs_tool */ }}
        }}
      /* repeat for each ETF */
      ],
      "Bonds Details": [
        {{
          "Bond Name": "<string>",
          "YTM": <number>,
          "Coupon Rate": <number>,
          "Maturity Date": "<date>",
          "Last Traded Price": <number>,
          "Key Metrics": {{ /* all metrics returned by bonds_tool */ }}
        }}
      /* repeat for each bond */
      ],
      "SGBs Details": [
        {{
          "Bond Name": "<string>",
          "Last Traded Price (LTP)": <number>,
          "Interest Rate": <number>,
          "Maturity Date": "<date>",
          "Expected Returns": <number>,
        }}
      /* repeat for each SGB */
    }},
    Lumpsum Investment": {{
      "Allocation": {{
      "Mutual Funds": <number>,
      "ETFs": <number>,
      "Bonds": <number>,
      "SGBs": <number>
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
      /* repat for ETFs, Bonds, and SGBs as above */
  }}
}}
"""

def run_orc_agent(user_inputs):
    agent = get_agent()
    query = query_template.format(**user_inputs)
    response = agent.invoke({"input": query})
    return response.get("output", "No response from ORC agent.")

if __name__ == "__main__":
    user_inputs = {
        "objective": "Emergency Fund",
        "investment_horizon": "5 years",
        "age": 22,
        "mutual_fund": 2000,
        "mutual_fund_lumpsum": 0,
        "etf": 0,
        "etf_lumpsum": 0,
        "bond": 8000,
        "bond_lumpsum": 0,
        "sgb": 0,
        "sgb_lumpsum": 12000,
        "risk": "Aggressive"
    }
    print(run_orc_agent(user_inputs))

