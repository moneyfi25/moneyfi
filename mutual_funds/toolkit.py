from pymongo import ASCENDING, DESCENDING
import json
from langchain_core.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import mutual_funds_collection

@tool("fetch_return_parameters", return_direct=True)
def fetch_returns() -> str:
    """
    Fetch the mutual funds and their returns
    Returns a JSON array of objects: [{"name":..., "1_month_return":...}, ...].
    """
    cursor = mutual_funds_collection.find(
        {"1_week_return": {"$exists": True}}
    )

    results = [
        {"fund_name": doc["fund_name"],
         "1_week_return": doc["1_week_return"],
         "1_month_return": doc["1_month_return"],
         "3_month_return": doc["3_month_return"],
         "6_month_return": doc["6_month_return"],
         "1_year_return": doc["1_year_return"],}
        for doc in cursor
    ]
    return json.dumps(results)