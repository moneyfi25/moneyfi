from .agent import initialize_bonds_agent
from .mixer_agent import invoke_mixer_agent
from langchain.tools import tool
import json 
import ast

query_monthly_template = """
You are a Bonds Intelligence Agent trained to analyze both Government Securities (G-Secs) and Corporate Bonds 
stored in a database. You have access to specialized tools to retrieve and compare key bond characteristics.

Your objective is to recommend the best bonds to invest in based on the user’s investment profile,
considering return expectations, risk appetite, and time horizon.

✅ User Input Parameters: (ignore lumpsum investment {lumpsum_investment})
- Investment Objective: hedge against inflation
- Investment Horizon: {horizon} 
- Monthly Investment Amount: ₹{monthly_investment}
- Risk Appetite: {risk} 
- Preference (optional): {special_prefs} 

🛠️ Available Tools:
You MUST use the following tools effectively:

- fetch_ytm(): Fetches the current Yield-to-Maturity.
- fetch_coupon(): Fetches the bond’s annual coupon rate.
- fetch_diff_ltp_face(): Fetches the difference between Last Traded Price and Face Value.
- fetch_maturity(): Fetches bond maturity date to consider remaining duration.
- fetch_ltp(): Fetches the Last Traded Price to ensure it fits within the {monthly_investment} budget.

🧠 Decision Strategy:
- Filter bonds based on user’s horizon and risk appetite.
- Compare return potential using fetch_ytm and fetch_coupon.
- Evaluate risk using:
    - G-Sec vs Corporate (prefer G-Secs for low-risk profiles).
    - Price deviation (fetch_diff_ltp_face) – avoid deep premiums for short-term.
    - Maturity match with user horizon.
- Prioritize bonds that offer the best YTM for given risk and term alignment.

🎯 Your Output Must Include:
- Top 3–5 bond recommendations.
- Bond type (G-Sec or Corporate), Name/Symbol.
- Key metrics: YTM, Coupon, Time to Maturity, Price vs Face Value.
- Clear reasoning for recommendation and risk-return tradeoff.
- Any warnings or limitations (e.g., low liquidity, callable bond, reinvestment risk).
"""

query_lumpsum_template = """
You are a Bonds Intelligence Agent trained to analyze both Government Securities (G-Secs) and Corporate Bonds 
stored in a database. You have access to specialized tools to retrieve and compare key bond characteristics.

Your objective is to recommend the best bonds to invest in based on the user’s investment profile,
considering return expectations, risk appetite, and time horizon.

✅ User Input Parameters: (ignoore monthly investment {monthly_investment})
- Investment Objective: hedge against inflation
- Investment Horizon: {horizon} 
- Lumpsum Investment Amount: ₹{lumpsum_investment}
- Risk Appetite: {risk} 
- Preference (optional): {special_prefs} 

🛠️ Available Tools:
You MUST use the following tools effectively:

- fetch_ytm(): Fetches the current Yield-to-Maturity.
- fetch_coupon(): Fetches the bond’s annual coupon rate.
- fetch_diff_ltp_face(): Fetches the difference between Last Traded Price and Face Value.
- fetch_maturity(): Fetches bond maturity date to consider remaining duration.
- fetch_ltp(): Fetches the Last Traded Price of the bond. Make sure the LTP is less than or equal to ₹{lumpsum_investment}.

🧠 Decision Strategy:
- Filter bonds based on user’s horizon and risk appetite.
- Compare return potential using fetch_ytm and fetch_coupon.
- Evaluate risk using:
    - G-Sec vs Corporate (prefer G-Secs for low-risk profiles).
    - Price deviation (fetch_diff_ltp_face) – avoid deep premiums for short-term.
    - Maturity match with user horizon.
- Prioritize bonds that offer the best YTM for given risk and term alignment.

🎯 Your Output Must Include:
- Top 3–5 bond recommendations.
- Bond type (G-Sec or Corporate), Name/Symbol.
- Key metrics: YTM, Coupon, Time to Maturity, Price vs Face Value.
- Clear reasoning for recommendation and risk-return tradeoff.
- Any warnings or limitations (e.g., low liquidity, callable bond, reinvestment risk).
"""

mixer_query_template = """
Your job is to combine the results from lumpsum and monthly SIP agent responses into a single response.
Lumpsum response is:
{lumpsum_response}
Monthly SIP response is:
{monthly_response}

Return the combined response in the following format:
For Lumpsum Investment:
1. ABC Bond
   - YTM: 7.5%
   - Coupon Rate: 6.5%
   - Maturity Date: 2025-12-31
   - Last Traded Price: ₹1000
...

For Monthly SIP Investment:
1. XYZ Bond
   - YTM: 7.0%
   - Coupon Rate: 6.0%
   - Maturity Date: 2026-06-30
   - Last Traded Price: ₹980
...
"""

def bonds_tool(user_inputs):
    """
    This tool is used to interact with the Bonds Intelligence Agent.
    It takes user inputs and returns bond recommendations based on the query template.
    """
    if isinstance(user_inputs, str):
        try:
            user_inputs = json.loads(user_inputs)
        except json.JSONDecodeError:
            try:
                user_inputs = ast.literal_eval(user_inputs)
            except (ValueError, SyntaxError):
                print("❌ Failed to parse user_inputs string")
                return "Error: Could not parse user inputs"
    agent = initialize_bonds_agent()
    query_monthly = query_monthly_template.format(**user_inputs)
    response_monthly = agent.invoke({"input": query_monthly})
    if(user_inputs["lumpsum_investment"] == 0):
        query_lumpsum = "No Lumpsum Investment Found"
        response_lumpsum = {"output": "No Lumpsum Investment Found"}
    else:
        query_lumpsum = query_lumpsum_template.format(**user_inputs)
        response_lumpsum = agent.invoke({"input": query_lumpsum})
    
    mixer_query = mixer_query_template.format(
        lumpsum_response=response_lumpsum.get("output", "No response from Lumpsum agent."),
        monthly_response=response_monthly.get("output", "No response from Monthly SIP agent.")
    )
    response = invoke_mixer_agent(mixer_query)
    return response

if __name__ == "__main__":
    user_inputs = {
        "objective": "Emergency Fund",
        "horizon": "5 years",
        "age": 22,
        "monthly_investment": 200,
        "lumpsum_investment": 2000,
        "risk": "Moderate",
        "special_prefs": "-"
    } 
    print(bonds_tool(user_inputs))