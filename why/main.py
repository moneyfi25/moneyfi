from .reasoner import invoke_reasoner_agent
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import mutual_funds_collection

mf_query_template = """
Here is the details of a mutual fund that is chosen by financial advisor:
{mutual_fund}
Your job is to tell me WHY this mutual fund is chosen for the user using all the detials provided.
Give 3-4 points explanantion on why this mutual fund might be chosen by the advisor.(Don't make it too long, just 3-4 points)
"""

def mutual_fund_reasoner_tool(mutual_fund_details):
    query = mf_query_template.format(**mutual_fund_details)
    response = invoke_reasoner_agent(query)
    print(f"Reasoner Response: {response}")
    return response

if __name__ == "__main__":
    fund_name = "HDFC Large Cap Fund - Direct Plan"
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
