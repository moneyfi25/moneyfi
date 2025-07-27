from agent import agent

query_template = """
Objective:
Act as an expert Mutual Fund Research Analyst with access to real-time data and analytical tools. Your goal is to provide personalized, data-driven recommendations based on the user’s financial profile, ensuring alignment with their goals, risk tolerance, and constraints.

User Inputs:

- Investment Objective: {objective} (e.g., wealth creation, retirement, child education, tax saving)
- Investment Horizon: {horizon} *(short-term: <3 years, medium-term: 3–7 years, long-term: 7+ years)*
- User Age: {age} (to assess life stage and risk capacity)
- Monthly Investment Amount: ₹{monthly_investment} (to suggest SIP/lump-sum suitability)
- Risk Appetite: {risk} (low/medium/high – quantify volatility tolerance if possible)
- Preferred Fund Type (optional): {fund_type} (e.g., equity, debt, hybrid, index, thematic, sectoral, international)
- Special Preferences/Constraints: {special_prefs} (e.g., ESG focus, low expense ratio, direct plans only, no sectoral bets)

Analysis & Recommendation Guidelines:

- Goal-Based Filtering (use fetch_short_term_returns() and fetch_long_term_returns() tools):
    - Short-term goals (<3 years): Prioritize capital preservation + low volatility (e.g., liquid funds, ultra-short duration funds).
    - Long-term goals (7+ years): Focus on high-growth equity funds (e.g., flexi-cap, large & mid-cap) with strong long-term CAGR.
    - Tax efficiency: Highlight tax-saving funds (ELSS) or funds with indexation benefits (debt funds) if relevant.
- Risk Assessment (use fetch_risk_and_volatility_parameters() tool):
    - Low risk: Debt/hybrid funds with high credit quality + low standard deviation.
    - High risk: Equity funds with higher alpha generation but clarify drawdown risks (e.g., sectoral/thematic funds).
    - Use metrics like Sharpe ratio (risk-adjusted returns), Sortino ratio (downside risk), and max drawdown to justify stability.
- Cost & Efficiency (use fetch_fees_and_details() tool):
    - Compare expense ratios (direct plans preferred) and exit loads.
    - Highlight funds with consistent performance after fees.
- Qualitative Checks (use fetch_fees_and_details() tool):
    - Fund house reputation (e.g., AUM size, parent company).
    - Manager tenure & strategy consistency.
    - Portfolio concentration (avoid overexposure to single stocks/sectors).
- Peer Comparison (use category from fetch_fees_and_details() tool):
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
 - Caveat: Underperformed in 2022 due to tech overweight; rebalanced since.
"""

user_inputs = {
    "objective": "retirement",
    "horizon": "2 years",
    "age": 25,
    "monthly_investment": 15000,
    "risk": "High",
    "fund_type": "-",
    "special_prefs": "-"
}

query = query_template.format(**user_inputs)

response = agent.invoke({
    "input": query
})

print(response.get("output", "No response from Mutual Funds agent."))