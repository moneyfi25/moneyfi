from langchain.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import bonds_collection
import json
from datetime import datetime

@tool("fetch_ytm", return_direct=True)
def fetch_ytm() -> str:
    """Fetch all bonds and their YTM values.
    Returns a JSON array of objects:
    [{
    "SYMBOL": ..., 
    "YTM": ...},
     ...
    ]."""
    cursor = bonds_collection.find(
        {"YTM": {"$exists": True}},
    )

    results = [
        {"SYMBOL": doc["SYMBOL"],
         "YTM": doc["YTM"]}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_coupon", return_direct=True)
def fetch_coupon() -> str:
    """Fetch all bonds and their coupon rates.
    Returns a JSON array of objects:
    [{
    "SYMBOL": ..., 
    "COUPON_RATE": ...},
     ...
    ]."""
    cursor = bonds_collection.find(
        {"COUPON_RATE": {"$exists": True}},
        {"SYMBOL": 1, "COUPON_RATE": 1}
    )

    results = [
        {"SYMBOL": doc["SYMBOL"],
         "COUPON_RATE": doc["COUPON_RATE"]}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_diff_ltp_face", return_direct=True)
def fetch_diff_ltp_face() -> str:
    """Fetch all bonds and their difference between last traded price and face value.
    Returns a JSON array of objects:
    [{
    "SYMBOL": ..., 
    "diff_ltp_face": ...},
     ...
    ]."""
    cursor = bonds_collection.find(
        {"LTP": {"$exists": True}}
    )

    results = [
        {"SYMBOL": doc["SYMBOL"],
         "diff_ltp_face": abs(doc["LTP"] - doc["FACE_VALUE"])}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_maturity", return_direct=True)
def fetch_maturity() -> str:
    """Fetch all bonds and their maturity dates.
    Returns a JSON array of objects:
    [{
    "SYMBOL": ..., 
    "MATURITY_DATE": ...},
     ...
    ]."""
    cursor = bonds_collection.find(
        {"MATURITY_DATE": {"$exists": True}},
        {"SYMBOL": 1, "MATURITY_DATE": 1}
    )

    results = [
        {
            "SYMBOL": doc["SYMBOL"],
            "MATURITY_DATE": doc["MATURITY_DATE"].strftime("%Y-%m-%d") 
        }
        for doc in cursor if isinstance(doc.get("MATURITY_DATE"), datetime)
    ]
    return json.dumps(results)

@tool("fetch_ltp", return_direct=True)
def fetch_ltp() -> str:
    """Fetch all bonds and their last traded prices.
    Returns a JSON array of objects:
    [{
    "SYMBOL": ..., 
    "LTP": ...},
     ...
    ]."""
    cursor = bonds_collection.find(
        {"LTP": {"$exists": True}},
        {"SYMBOL": 1, "LTP": 1}
    )

    results = [
        {"SYMBOL": doc["SYMBOL"],
         "LTP": doc["LTP"]}
        for doc in cursor
    ]
    return json.dumps(results)

