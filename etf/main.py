from .agent import get_etfs_agent
from .pre_agent import invoke_pre_agent
from .toolkit import fetch_long_term_returns
import re
import json
import ast
from langchain.tools import tool

pre_query_template = """
You are an expert ETF Research Analyst. Your task is to define the filter parameters for selecting ETFs from the MongoDB database based on the user's financial profile.

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

query_template = """
Objective:
Act as an expert ETF Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized,
data-driven recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} 
- User Age: {age} 
- Monthly Investment Amount: {monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Analysis & Recommendation Guidelines:

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

query_template_test = """
Objective:
Act as an expert ETF Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized, data-driven ETF recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

User Inputs:

- Investment Objective: {objective} 
- Investment Horizon: {horizon} years
- User Age: {age} 
- Monthly Investment Amount: ₹{monthly_investment} 
- Risk Appetite: {risk} 
- Preferred Fund Type (optional): {fund_type} 
- Special Preferences/Constraints: {special_prefs} 

Analysis & Recommendation Guidelines:

1. **Goal-Based Filtering**:
   - Short-term goals (<3 years): Focus on capital preservation and low volatility ETFs such as liquid ETFs, ultra-short duration ETFs, and money market ETFs.
   - Medium-term goals (3-7 years): Include hybrid ETFs and large-cap equity ETFs for balanced growth.
   - Long-term goals (7+ years): Prioritize high-growth equity ETFs such as flexi-cap, mid-cap, and small-cap ETFs with strong long-term CAGR.
   - Tax efficiency: Highlight tax-saving ETFs (e.g., ELSS) or ETFs with indexation benefits (e.g., debt ETFs) if relevant.

2. **Risk Assessment**:
   - Low risk: Recommend debt ETFs, hybrid ETFs, or gold ETFs with high credit quality and low standard deviation.
   - Moderate risk: Include large-cap and multi-cap ETFs with balanced risk-return profiles.
   - High risk: Suggest thematic, sectoral, or small-cap ETFs with higher alpha generation but clarify drawdown risks.
   - Use metrics like Sharpe ratio (risk-adjusted returns), Sortino ratio (downside risk), and max drawdown to justify stability.

3. **Performance Metrics**:
   - Conservative:
     - Expense Ratio: ≤ 1.0%
     - Standard Deviation: ≤ 15
     - Sharpe Ratio: ≥ 0.8
     - 1-Year Return: ≥ 6%
   - Moderate:
     - Expense Ratio: ≤ 1.5%
     - Standard Deviation: ≤ 20
     - Sharpe Ratio: ≥ 1.0
     - 1-Year Return: ≥ 8%
   - Aggressive:
     - Expense Ratio: ≤ 2.0%
     - Standard Deviation: ≤ 25
     - Sharpe Ratio: ≥ 1.2
     - 1-Year Return: ≥ 10%

4. **Liquidity and AUM**:
   - Ensure ETFs have sufficient liquidity (e.g., daily trading volume ≥ ₹1 crore).
   - Net Assets (AUM): ≥ ₹100 crores for stability and reliability.

5. **Cost & Efficiency**:
   - Compare expense ratios (direct plans preferred) and exit loads.
   - Highlight ETFs with consistent performance after fees.

6. **Peer Comparison**:
   - Benchmark ETFs against category averages (e.g., "This ETF outperformed 90% of peers over 5 years").
   - Explain outliers (e.g., "ETF X has higher risk but topped returns in bull markets").

7. **Qualitative Checks**:
   - Fund house reputation (e.g., AUM size, parent company).
   - Manager tenure and strategy consistency.
   - Portfolio concentration (avoid overexposure to single stocks/sectors).

Output Format:

Top 3–5 Recommended ETFs (ranked by suitability)

For each ETF, provide:

- **ETF Name & Category** (e.g., "ABC Flexi-Cap ETF – Equity")
- **Why It Fits**:
    - Match to goal/horizon/risk.
    - Key metrics (e.g., "5Y CAGR: 12% | Sharpe: 1.2 | Expense: 0.5%").
- **Peer Comparison**:
    - How it ranks vs. category (top 10%/median/bottom).
    - Consistency across market cycles.
- **Caveats**:
    - Recent underperformance, sector bets, liquidity risks, etc.

Example:

1. XYZ Bluechip ETF (Large-Cap Equity)

 - **Why It Fits**: Ideal for long-term growth (7Y CAGR: 14% vs. category 12%) with lower volatility (Sharpe 1.3).
 - **Peer Rank**: Top 15% over 3/5/10Y periods.
 - **Key Metrics**: Expense Ratio: 0.5%, Standard Deviation: 12, Sharpe Ratio: 1.3.
 - **Caveat**: Underperformed in 2022 due to tech overweight; rebalanced since.
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

    pre_agent_response = invoke_pre_agent(pre_query)

    query_match = re.search(r"query = (\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", pre_agent_response, re.DOTALL)
    if query_match:
        mongo_query = query_match.group(1)  
        print("✅ Extracted Query:", mongo_query)
    else:
        print("❌ Query block not found in the response.")
        mongo_query = "{}"  

    user_inputs["mongo_query"] = mongo_query

    query = query_template.format(**user_inputs)
    agent = get_etfs_agent()
    response = agent.invoke({"input": query})
    return response.get("output", "No response from ETFs agent.")

if __name__ == "__main__":
    user_inputs = {
        "objective": "Wealth Creation",
        "horizon": "2 years",
        "age": 30,
        "monthly_investment": 10000,
        "risk": "Moderate",
        "fund_type": "-",
        "special_prefs": "-"
    }
    print(etfs_tool(user_inputs))