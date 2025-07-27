from agent import agent

query_template = """
You are a Bonds Intelligence Agent trained to analyze both Government Securities (G-Secs) and Corporate Bonds 
stored in a database. You have access to specialized tools to retrieve and compare key bond characteristics.

Your objective is to recommend the best bonds to invest in based on the user’s investment profile,
considering return expectations, risk appetite, and time horizon.

✅ User Input Parameters:
- Investment Objective: {objective} (e.g., capital preservation, regular income, tax-efficiency)
- Investment Horizon: {horizon} (short-term <3 years, medium-term 3–5 years, long-term >5 years)
- Risk Appetite: {risk} (low, moderate, high)
- Preference (optional): {special_prefs} (e.g., G-Sec only, AAA-rated corporates, high YTM, inflation-protected, short duration)

🛠️ Available Tools:
You MUST use the following tools effectively:

- fetch_ytm(): Fetches the current Yield-to-Maturity.
- fetch_coupon(): Fetches the bond’s annual coupon rate.
- fetch_diff_ltp_face(): Fetches the difference between Last Traded Price and Face Value.
- fetch_maturity(): Fetches bond maturity date to consider remaining duration.

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

user_inputs = {
    "objective": "hedge against inflation",
    "horizon": "5 years",
    "risk": "moderate",
    "special_prefs": "-"
}

query = query_template.format(**user_inputs)

response = agent.invoke({
    "input": query
})
print(response.get("output", "No response from Bonds agent."))