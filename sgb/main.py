from langchain.tools import tool
from .agent import get_sgb_agent
from .mixer_agent import invoke_mixer_agent
import json
import ast

query_monthly_template = """
You are a Sovereign Gold Bond (SGB) expert with deep knowledge of inflation protection, returns, and portfolio diversification.

✅ User Input Parameters:
- Investment Objective: hedge against inflation
- Investment Horizon: {horizon} years
- Monthly Investment Amount: ₹{monthly_investment}

Instructions:
1. Recommend the best Sovereign Gold Bond (SGB) for the user based on their profile.
2. Ensure the Last Traded Price (LTP) of the recommended SGB is less than or equal to ₹{monthly_investment}.
3. Provide the following details for the recommended SGB:
   - **Bond Name**: [Name of the SGB]
   - **Last Traded Price (LTP)**: ₹[LTP]
   - **Maturity Date**: [Date of maturity]
   - **Expected Returns**: Get from [Last 1 year Returns]
4. Explain why this SGB is suitable for the user's profile.
5. If no SGB meets the criteria, suggest alternative options like gold ETFs or gold mutual funds.

Output Format:
**Recommended SGB: [Bond Name]**
- **Last Traded Price (LTP)**: ₹[LTP]
- **Interest Rate**: 2.5 % (bi-annually)
- **Maturity Date**: [Date]
- **Expected Returns**: [Last 1 year Returns] % per annum

If no SGB is available within the user's budget, provide this output:
**No Suitable SGB Found**
- Suggest alternatives like gold ETFs or gold mutual funds with a brief explanation.

Make sure your response is concise and actionable.
"""

query_lumpsum_template = """
You are a Sovereign Gold Bond (SGB) expert with deep knowledge of inflation protection, returns, and portfolio diversification.

✅ User Input Parameters:
- Investment Objective: hedge against inflation
- Investment Horizon: {horizon} years
- Lumpsum Investment Amount: ₹{lumpsum_investment}

Instructions:
1. Recommend the best Sovereign Gold Bond (SGB) for the user based on their profile.
2. Ensure the Last Traded Price (LTP) of the recommended SGB is less than or equal to ₹{lumpsum_investment}.
3. Provide the following details for the recommended SGB:
   - **Bond Name**: [Name of the SGB]
   - **Last Traded Price (LTP)**: ₹[LTP]
   - **Maturity Date**: [Date of maturity]
   - **Expected Returns**: Get from [Last 1 year Returns]
4. Explain why this SGB is suitable for the user's profile.
5. If no SGB meets the criteria, suggest alternative options like gold ETFs or gold mutual funds.

Output Format:
**Recommended SGB: [Bond Name]**
- **Last Traded Price (LTP)**: ₹[LTP]
- **Interest Rate**: 2.5 % (bi-annually)
- **Maturity Date**: [Date]
- **Expected Returns**: [Last 1 year Returns] % per annum

If no SGB is available within the user's budget, provide this output:
**No Suitable SGB Found**
- Suggest alternatives like gold ETFs or gold mutual funds with a brief explanation.

Make sure your response is concise and actionable.
"""

mixer_query_template = """
Your job is to combine the results from lumpsum and monthly SIP agent responses into a single response.
Lumpsum response is:
{lumpsum_response}
Monthly SIP response is:
{monthly_response}

Return the combined response in the following format:
For Lumpsum Investment:
**Recommended SGB: [Bond Name]**
- **Last Traded Price (LTP)**: ₹[LTP]
- **Interest Rate**: 2.5 % (bi-annually)
- **Maturity Date**: [Date]
- **Expected Returns**: [Last 1 year Returns] % per annum

For Monthly SIP Investment:
**Recommended SGB: [Bond Name]**
- **Last Traded Price (LTP)**: ₹[LTP]
- **Interest Rate**: 2.5 % (bi-annually)
- **Maturity Date**: [Date]
- **Expected Returns**: [Last 1 year Returns] % per annum
"""

def sgb_tool(user_inputs) -> str:
    """
    Uses the SGB agent to fetch the best Sovereign Gold Bond suggestion 
    based on user goals like inflation protection, returns, etc.
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
    agent = get_sgb_agent()
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
        "objective": "Hedge against inflation",
        "horizon": "5 years",
        "age": 22,
        "monthly_investment": 0,
        "lumpsum_investment": 11000,
        "risk": "Moderate",
        "fund_type": "-",
        "special_prefs": "-"
    }
    print(sgb_tool(user_inputs))