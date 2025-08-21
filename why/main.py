from .reasoner import invoke_reasoner_agent
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import mutual_funds_collection

mf_query_template = """
Here is the details of a mutual fund that is chosen by financial advisor:
{mutual_fund}
Your job is to tell me WHY this mutual fund is chosen for the user using all the detials provided in a SIMPLE language.
Your target audience is a user who is not familiar with financial terms. So explain it in a way that is easy to understand.
Do not use any financial jargon or complex terms. Do not directly use the terms sortino ratio, Sharpe ratio, etc, rather explain what they mean in simple terms.
Give 3-4 points(->) explanantion on why this mutual fund might be chosen by the advisor.(Don't take any assumptions, just use the data provided in the mutual fund details)
You must have the first two points for returns and risk inference, they are most important things to be explained.
"""

def mutual_fund_reasoner_tool(mutual_fund_details):
    query = mf_query_template.format(**mutual_fund_details)
    response = invoke_reasoner_agent(query)
    print(f"Reasoner Response: {response}")
    return response

if __name__ == "__main__":
    fund_name = "Edelweiss Equity Savings Fund - Direct Plan"
    fund = mutual_funds_collection.find_one({"fund_name": fund_name})
    if not fund:
        print(f"Mutual fund '{fund_name}' not found.")
    else:
        fund["_id"] = str(fund["_id"])
        reason = mutual_fund_reasoner_tool({"mutual_fund": fund})
        mutual_funds_collection.update_one(
            {"fund_name": fund_name},
            {"$set": {"advisor_reason": reason}}
        )
        print("Reason saved to DB.")
