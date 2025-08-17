from .agent import get_etfs_agent
from .pre_agent import invoke_pre_agent
from .toolkit import fetch_long_term_returns
from .mixer_agent import invoke_mixer_agent
import re
import json
import ast
from langchain.tools import tool

pre_query_template = """
You are an expert ETF Research Analyst. Your task is to define the filter parameters for selecting ETFs from the MongoDB database based on the user's financial profile.

[NOTE: This query is specifically for monthly SIP investments. Ignore lumpsum investment {lumpsum_investment}.]
User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} years
- User Age: {age} 
- Monthly Investment Amount: ₹{monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Filtering Guidelines:

1. **Return-Based Filtering**:
   - Short-term (<3 years): Focus on ETFs with stable short-term returns.
     - 6-Month Return: ≥ 3%
     - 1-Year Return: ≥ 5%
   - Medium-term (3-7 years): Focus on ETFs with consistent medium-term returns.
     - 1-Year Return: ≥ 7%
     - 3-Year Return: ≥ 8%
   - Long-term (7+ years): Focus on ETFs with strong long-term growth potential.
     - 1-Year Return: ≥ 8%
     - 3-Year Return: ≥ 10%
     - 5-Year Return: ≥ 12%

Instructions:

- Use the above guidelines to construct a MongoDB query object for filtering ETFs.
- Include only relevant filters based on the user's profile.
- Ensure the query is clean and concise, like this sample (Nothing extra like risk, liquidity, etc.):

query = {{
    "6_month_return": {{"$gte": ...}},
    "1_year_return": {{"$gte": ...}},
    "3_year_return": {{"$gte": ...}},
    "5_year_return": {{"$gte": ...}},
    "minimum_investment": {{"$lte": {monthly_investment}}}
}}
"""

pre_query_lumpsum_template = """
You are an expert ETF Research Analyst. Your task is to define the filter parameters for selecting ETFs from the MongoDB database based on the user's financial profile.

[NOTE: This query is specifically for lump sum investments. Ignore monthly investment {monthly_investment}.]
User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} years
- User Age: {age} 
- Lumpsum Investment Amount: ₹{lumpsum_investment}
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Filtering Guidelines:

1. **Return-Based Filtering**:
   - Short-term (<3 years): Focus on ETFs with stable short-term returns.
     - 6-Month Return: ≥ 3%
     - 1-Year Return: ≥ 5%
   - Medium-term (3-7 years): Focus on ETFs with consistent medium-term returns.
     - 1-Year Return: ≥ 7%
     - 3-Year Return: ≥ 8%
   - Long-term (7+ years): Focus on ETFs with strong long-term growth potential.
     - 1-Year Return: ≥ 8%
     - 3-Year Return: ≥ 10%
     - 5-Year Return: ≥ 12%

Instructions:

- Use the above guidelines to construct a MongoDB query object for filtering ETFs.
- Include only relevant filters based on the user's profile.
- Ensure the query is clean and concise, like this sample (Nothing extra like risk, liquidity, etc.):

query = {{
    "6_month_return": {{"$gte": ...}},
    "1_year_return": {{"$gte": ...}},
    "3_year_return": {{"$gte": ...}},
    "5_year_return": {{"$gte": ...}},
    "minimum_investment": {{"$lte": {lumpsum_investment}}}
}}
"""

query_monthly_template = """
Objective:
Act as an expert ETF Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized,
data-driven recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

NOTE: This query is specifically for monthly SIP investments. Ignore lumpsum investment {lumpsum_investment}.
User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} 
- User Age: {age} 
- Monthly Investment Amount: {monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Analysis & Recommendation Guidelines:

- Ignore {mongo_query_lumpsum}
- Pass {mongo_query} to all the tools to fetch the data.

1. **Goal-Based Filtering** (use `fetch_short_term_returns("{mongo_query}")` and `fetch_long_term_returns("{mongo_query}")` tools):
   - **Short-term goals (<3 years)**:
     - Focus on capital preservation and low volatility ETFs such as liquid ETFs, ultra-short duration ETFs, and money market ETFs.
     - Prioritize ETFs with stable returns and low drawdowns.
   - **Medium-term goals (3-7 years)**:
     - Include hybrid ETFs and large-cap equity ETFs for balanced growth.
     - Ensure a mix of equity and debt exposure to reduce risk.
   - **Long-term goals (7+ years)**:
     - Prioritize high-growth equity ETFs such as flexi-cap, mid-cap, and small-cap ETFs with strong long-term CAGR.
     - Highlight ETFs with consistent performance across market cycles.
   - **Tax efficiency**:
     - Highlight tax-saving ETFs (e.g., ELSS) or ETFs with indexation benefits (e.g., debt ETFs) if relevant.

2. **Risk Assessment** (use `fetch_risk_and_volatility_parameters("{mongo_query}")` tool):
   - **Low risk**:
     - Recommend debt ETFs, hybrid ETFs, or gold ETFs with high credit quality and low standard deviation.
     - Focus on ETFs with low beta and high Sharpe ratios.
   - **Moderate risk**:
     - Include large-cap and multi-cap ETFs with balanced risk-return profiles.
     - Ensure ETFs have moderate volatility and consistent returns.
   - **High risk**:
     - Suggest thematic, sectoral, or small-cap ETFs with higher alpha generation but clarify drawdown risks.
     - Use metrics like Sharpe ratio (risk-adjusted returns), Sortino ratio (downside risk), and max drawdown to justify stability.

3. **Performance Metrics** (use `fetch_risk_and_volatility_parameters("{mongo_query}")` tool):
   - **Conservative**:
     - Expense Ratio: ≤ 1.0%
     - Standard Deviation: ≤ 15
     - Sharpe Ratio: ≥ 0.8
     - 1-Year Return: ≥ 6%
   - **Moderate**:
     - Expense Ratio: ≤ 1.5%
     - Standard Deviation: ≤ 20
     - Sharpe Ratio: ≥ 1.0
     - 1-Year Return: ≥ 8%
   - **Aggressive**:
     - Expense Ratio: ≤ 2.0%
     - Standard Deviation: ≤ 25
     - Sharpe Ratio: ≥ 1.2
     - 1-Year Return: ≥ 10%

4. **Cost & Efficiency** (use `fetch_fees_and_details("{mongo_query}")` tool):
   - Compare expense ratios (direct plans preferred) and exit loads.
   - Highlight ETFs with consistent performance after fees.
   - Ensure the ETF aligns with the user's budget and SIP amount.

7. **Qualitative Checks** (use `fetch_fund_details("{mongo_query}")` tool):
   - Fund house reputation (e.g., AUM size, parent company).
   - Manager tenure and strategy consistency.
   - Portfolio concentration (avoid overexposure to single stocks/sectors).

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

query_lumpsum_template = """
Objective:
Act as an expert ETF Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized,
data-driven recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

NOTE: This query is specifically for lump sum investments. Ignore monthly investment {monthly_investment}.
User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} 
- User Age: {age} 
- Lumpsum Investment Amount: ₹{lumpsum_investment}
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Analysis & Recommendation Guidelines:

- Ignore {mongo_query}
- Pass {mongo_query_lumpsum} to all the tools to fetch the data.

1. **Goal-Based Filtering** (use `fetch_short_term_returns("{mongo_query_lumpsum}")` and `fetch_long_term_returns("{mongo_query_lumpsum}")` tools):
   - **Short-term goals (<3 years)**:
     - Focus on capital preservation and low volatility ETFs such as liquid ETFs, ultra-short duration ETFs, and money market ETFs.
     - Prioritize ETFs with stable returns and low drawdowns.
   - **Medium-term goals (3-7 years)**:
     - Include hybrid ETFs and large-cap equity ETFs for balanced growth.
     - Ensure a mix of equity and debt exposure to reduce risk.
   - **Long-term goals (7+ years)**:
     - Prioritize high-growth equity ETFs such as flexi-cap, mid-cap, and small-cap ETFs with strong long-term CAGR.
     - Highlight ETFs with consistent performance across market cycles.
   - **Tax efficiency**:
     - Highlight tax-saving ETFs (e.g., ELSS) or ETFs with indexation benefits (e.g., debt ETFs) if relevant.

2. **Risk Assessment** (use `fetch_risk_and_volatility_parameters("{mongo_query_lumpsum}")` tool):
   - **Low risk**:
     - Recommend debt ETFs, hybrid ETFs, or gold ETFs with high credit quality and low standard deviation.
     - Focus on ETFs with low beta and high Sharpe ratios.
   - **Moderate risk**:
     - Include large-cap and multi-cap ETFs with balanced risk-return profiles.
     - Ensure ETFs have moderate volatility and consistent returns.
   - **High risk**:
     - Suggest thematic, sectoral, or small-cap ETFs with higher alpha generation but clarify drawdown risks.
     - Use metrics like Sharpe ratio (risk-adjusted returns), Sortino ratio (downside risk), and max drawdown to justify stability.

3. **Performance Metrics** (use `fetch_risk_and_volatility_parameters("{mongo_query_lumpsum}")` tool):
   - **Conservative**:
     - Expense Ratio: ≤ 1.0%
     - Standard Deviation: ≤ 15
     - Sharpe Ratio: ≥ 0.8
     - 1-Year Return: ≥ 6%
   - **Moderate**:
     - Expense Ratio: ≤ 1.5%
     - Standard Deviation: ≤ 20
     - Sharpe Ratio: ≥ 1.0
     - 1-Year Return: ≥ 8%
   - **Aggressive**:
     - Expense Ratio: ≤ 2.0%
     - Standard Deviation: ≤ 25
     - Sharpe Ratio: ≥ 1.2
     - 1-Year Return: ≥ 10%

4. **Cost & Efficiency** (use `fetch_fees_and_details("{mongo_query_lumpsum}")` tool):
   - Compare expense ratios (direct plans preferred) and exit loads.
   - Highlight ETFs with consistent performance after fees.
   - Ensure the ETF aligns with the user's budget and SIP amount.

7. **Qualitative Checks** (use `fetch_fund_details("{mongo_query_lumpsum}")` tool):
   - Fund house reputation (e.g., AUM size, parent company).
   - Manager tenure and strategy consistency.
   - Portfolio concentration (avoid overexposure to single stocks/sectors).

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

mixer_query_template = """
Your job is to combine the results from lumpsum and monthly SIP agent responses into a single response.
Lumpsum response is:
{lumpsum_response}
Monthly SIP response is:
{monthly_response}

Return the combined response in the following format:
For Lumpsum Investment:
1. XYZ Bluechip Fund
 - Why? Ideal for long-term growth (7Y CAGR: 14% vs. category 12%) with lower volatility (Sharpe 1.3).
 - Peer Rank: Top '15%' over 3/5/10Y periods.
 - Key Metrices: (performance, risk, fees) 
 - Caveat: Underperformed in 2022 due to tech overweight; rebalanced since.

For Monthly SIP Investment:
1. ABC Flexi-Cap Fund
 - Why? Best for medium-term growth (3Y CAGR: 12% vs. category 10%) with moderate risk (Sharpe 1.1).
 - Peer Rank: Top '20%' over 1/3/5Y periods.
 - Key Metrices: (performance, risk, fees) 
 - Caveat: Recent sector rotation; monitor closely.
"""

def etfs_tool(user_inputs) -> str:
    """
    Uses the ETFs agent to fetch personalized ETF recommendations
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
    pre_query_lumpsum = pre_query_lumpsum_template.format(**user_inputs)
    pre_agent_response = invoke_pre_agent(pre_query)
    pre_lumpsum_agent_response = invoke_pre_agent(pre_query_lumpsum)

    query_match = re.search(r"query = (\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", pre_agent_response, re.DOTALL)
    query_lumpsum_match = re.search(r"query = (\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", pre_lumpsum_agent_response, re.DOTALL)
    if query_match:
        mongo_query = query_match.group(1)  # Extract the matched query block
        print("✅ Extracted Query:", mongo_query)
    else:
        print("❌ Query block not found in the response.")
        mongo_query = "{}"  # Default to an empty query if not found
    if query_lumpsum_match:
        mongo_query_lumpsum = query_lumpsum_match.group(1)
        print("✅ Extracted Lumpsum Query:", mongo_query_lumpsum)
    else:
        print("❌ Lumpsum Query block not found in the response.")
        mongo_query_lumpsum = "{}"

    user_inputs["mongo_query"] = mongo_query
    user_inputs["mongo_query_lumpsum"] = mongo_query_lumpsum

    agent = get_etfs_agent()
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
        "objective": "Wealth Creation",
        "horizon": "7 years",
        "age": 30,
        "monthly_investment": 1000,
        "lumpsum_investment": 5000,
        "risk": "Moderate",
        "fund_type": "-",
        "special_prefs": "-"
    }
    print(etfs_tool(user_inputs))