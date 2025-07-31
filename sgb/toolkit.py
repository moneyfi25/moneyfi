from pymongo import ASCENDING, DESCENDING
from langchain_core.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import sgb_collection

@tool
def fetch_top_sgbs(num: int = 5) -> list[dict]:
    """
    Fetch the top `num` Sovereign Gold Bonds from MongoDB,
    sorted by `return_score` descending.

    Args:
        num: how many top‐scoring SGBs to return.

    Returns:
        A list of dicts, each containing:
          - symbol
          - return_score
          - last_traded_price (if available)
          - premium_percent (if available)
    """
    cursor = (
        sgb_collection.find(
            {
                "return_score": {"$exists": True},
                "safe_premium": True
            },
            {
                "SYMBOL \n": 1,
                "return_score": 1,
                "LTP \n": 1,
                "premium_percent": 1,
                "safe_premium": 1,
                "365 D % CHNG \n": 1
            }
        )
        .sort("return_score", -1)
        .limit(int(num))
    )

    results = []
    for doc in cursor:
        results.append({
            "symbol":             doc.get("SYMBOL \n"),
            "return_score":       doc.get("return_score"),
            "last_traded_price":  doc.get("LTP \n"),
            "premium_percent":    doc.get("premium_percent"),
            "Last 1 year Returns": doc.get("365 D % CHNG \n")
        })

    return results