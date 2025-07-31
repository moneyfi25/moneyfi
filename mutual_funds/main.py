from .agent import get_mutual_funds_agent
from .pre_agent import invoke_pre_agent
from .toolkit import fetch_long_term_returns
import re
import json
import ast
from langchain.tools import tool

# user_inputs = {
#     "objective": "Marriage",
#    
#     "risk": "Conservative",
#     "fund_type": "-",
#     "special_prefs": "-"
# }

pre_query_template = """
You are an expert Mutual Fund Research Analyst. You know the parameters to filter mutual funds based on the user portfolio.
You have to define the filter parameters for filtering mutual funds from my mongo db based on the user portfolio:

User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} 
- User Age: {age} 
- Monthly Investment Amount: ₹{monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Mapping Guidelines:
1. **Risk-Category Mapping:(Find from category list in instruction)**
   - Conservative/Low: DT-* (debt), HY-* (hybrid), Gold/Silver funds
   - Moderate: EQ-LC, EQ-L&MC, EQ-MLC and hybrid funds (HY-)
   - Aggressive/High: EQ-FLX, EQ-MC, EQ-SC, EQ-THEMATIC, sector-specific EQ funds

2. **Horizon-Based Filters:**
   - Short-term (<3 years): Focus on DT-LIQ, DT-SD, DT-MM
   - Medium-term (3-7 years): HY-* funds, EQ-LC
   - Long-term (7+ years): EQ-* funds with higher growth potential

3. **Performance Criteria (use only relevant fields):**
   - Conservative: expense_ratio ≤ 1.0, standard_deviation ≤ 15, sharpe_ratio ≥ 0.8
   - Moderate: expense_ratio ≤ 1.5, standard_deviation ≤ 20, sharpe_ratio ≥ 1.0
   - Aggressive: expense_ratio ≤ 2.0, standard_deviation ≤ 25, sharpe_ratio ≥ 1.2

4. **Risk Criteria:**
   - Conservative: beta ≤ 0.5, alpha ≥ 0.5
   - Moderate: beta ≤ 1.0, alpha ≥ 1.0
   - Aggressive: beta ≤ 1.5, alpha ≥ 1.5

Instructions:

- All the "category" in the mutual fund list are - ['DT-BK & PSU', 'DT-CB', 'DT-CR', 'DT-DB', 'DT-Floater', 'DT-GL',
'DT-Gilt 10Y CD', 'DT-LD', 'DT-LIQ', 'DT-LONG D', 'DT-M to LD', 'DT-MD', 'DT-MM', 'DT-OTH', 'DT-OVERNHT',
'DT-SD', 'DT-TM', 'DT-USD', 'EQ-BANK', 'EQ-Consumption', 'EQ-DIV Y', 'EQ-ELSS', 'EQ-Energy', 'EQ-FLX', 'EQ-INFRA',
'EQ-INTL', 'EQ-IT', 'EQ-L&MC', 'EQ-LC', 'EQ-MC', 'EQ-MLC', 'EQ-MNC', 'EQ-PSU', 'EQ-Pharma', 'EQ-SC', 'EQ-T-ESG',
'EQ-THEMATIC', 'EQ-VAL', 'Gold-Funds', 'HY-AH', 'HY-AR', 'HY-BH', 'HY-CH', 'HY-DAA', 'HY-EQ S', 'HY-MAA', 'Silver-Funds']
- All returns are in percentage.
- "net_assets" is in crores
- Only include relevant filters based on user profile
- Use appropriate value ranges for risk appetite
- Ensure minimum_investment is reasonable for monthly SIP
- Return only the MongoDB query object (no comments)

Keep it clean like this sample query:
query = {{
    "category": {{"$in": [...]}},
    "net_assets": {{"$gte": ...}},
    "1_year_return": {{"$gte": ...}},
    "6_month_return": {{"$gte": ...}},
    "5_year_return": {{"$gte": ...}},
    "expense_ratio": {{"$lte": ...}},
    "sharpe_ratio": {{"$gte": ...}},
    "sortino_ratio": {{"$gte": ...}},
    "standard_deviation": {{"$lte": ...}},
    "beta": {{"$lte": ...}},
    "alpha": {{"$gte": ...}},
    "minimum_investment": {{"$lte": {{monthly_investment}}}},
    "r_squared": {{"$gte": ...}},
    "information_ratio": {{"$gte": ...}},
}}
"""


query_template = """
Objective:
Act as an expert Mutual Fund Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized, data-driven recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} 
- User Age: {age} 
- Monthly Investment Amount: ₹{monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Analysis & Recommendation Guidelines:

- Pass {mongo_query} to all the tools to fetch the data.
- Goal-Based Filtering (use fetch_short_term_returns("{mongo_query}") and fetch_long_term_returns("{mongo_query}") tools):
    - Short-term goals (<3 years): Prioritize capital preservation + low volatility (e.g., liquid funds, ultra-short duration funds).
    - Long-term goals (7+ years): Focus on high-growth equity funds (e.g., flexi-cap, large & mid-cap) with strong long-term CAGR.
    - Tax efficiency: Highlight tax-saving funds (ELSS) or funds with indexation benefits (debt funds) if relevant.
- Risk Assessment (use fetch_risk_and_volatility_parameters("{mongo_query}") tool):
    - Low risk: Debt/hybrid funds with high credit quality + low standard deviation.
    - High risk: Equity funds with higher alpha generation but clarify drawdown risks (e.g., sectoral/thematic funds).
    - Use metrics like Sharpe ratio (risk-adjusted returns), Sortino ratio (downside risk), and max drawdown to justify stability.
- Cost & Efficiency (use fetch_fees_and_details("{mongo_query}") tool):
    - Compare expense ratios (direct plans preferred) and exit loads.
    - Highlight funds with consistent performance after fees.
- Qualitative Checks (use fetch_fees_and_details("{mongo_query}") tool):
    - Fund house reputation (e.g., AUM size, parent company).
    - Manager tenure & strategy consistency.
    - Portfolio concentration (avoid overexposure to single stocks/sectors).
- Peer Comparison (use category from fetch_fees_and_details("{mongo_query}") tool):
    - Benchmark against category averages (e.g., "This fund outperformed '90%' of peers over 5Y").
    - Explain outliers (e.g., "Fund X has higher risk but topped returns in bull markets").

Output Format:

Top 3–5 Recommended Funds (ranked by suitability)

For each fund, provide:

- Fund Name & Category (e.g., "ABC Flexi-Cap Fund – Equity")
- Why It Fits?
    - Match to goal/horizon/risk.
    - Key metrics (e.g., "5Y CAGR: 12% | Sharpe: 1.2 | Expense: 0.5%").
- Peer Comparison:
    - How it ranks vs. category (top 10%/median/bottom).
    - Consistency across market cycles.
- Caveats:
    - Recent underperformance, sector bets, liquidity risks, etc.

Example:

1. XYZ Bluechip Fund (Large-Cap Equity)

 - Why? Ideal for long-term growth (7Y CAGR: 14% vs. category 12%) with lower volatility (Sharpe 1.3).
 - Peer Rank: Top '15%' over 3/5/10Y periods.
 - Key Metrices: (performance, risk, fees) 
 - Caveat: Underperformed in 2022 due to tech overweight; rebalanced since.
"""

# query = query_template.format(**user_inputs)

# response = agent.invoke({
#     "input": query
# })

# print(response.get("output", "No response from Mutual Funds agent."))

# result = fetch_long_term_returns(user_inputs["mongo_query"])
# print(result)


@tool
def mutual_funds_tool(user_inputs) -> str:
    """
    Uses the Mutual Funds agent to fetch personalized mutual fund recommendations
    based on user goals, risk tolerance, and investment horizon.
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
    
    print("🔍 User Inputs:", user_inputs)
    pre_query = pre_query_template.format(**user_inputs)

    pre_agent_response = invoke_pre_agent(pre_query)

    query_match = re.search(r"query = (\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", pre_agent_response, re.DOTALL)
    if query_match:
        mongo_query = query_match.group(1)  # Extract the matched query block
        print("✅ Extracted Query:", mongo_query)
    else:
        print("❌ Query block not found in the response.")
        mongo_query = "{}"  # Default to an empty query if not found

    user_inputs["mongo_query"] = mongo_query

    query = query_template.format(**user_inputs)
    agent = get_mutual_funds_agent()
    response = agent.invoke({"input": query})
    return response.get("output", "No response from Mutual Funds agent.")

# if __name__ == "__main__":
#     user_inputs = {"objective": "Emergency Fund", "horizon": "5 years", "age": 22, "monthly_investment": 10000, "risk": "Conservative", "fund_type": "-", "special_prefs": "-"}
#     print(mutual_funds_tool(user_inputs))