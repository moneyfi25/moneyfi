from pymongo import ASCENDING, DESCENDING
import json
from langchain_core.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import mutual_funds_collection

@tool("fetch_risk_scores", return_direct=True)
def fetch_risk_scores(top_n: int = 5) -> str:
    """
    Fetch the top_n mutual funds sorted by ascending risk_score (lowest risk first).
    Returns a JSON array of objects: [{"name":..., "risk_score":...}, ...].
    """
    cursor = mutual_funds_collection.find(
        {"risk_score": {"$exists": True}}
    ).sort("risk_score", ASCENDING).limit(int(top_n))

    results = [
        {"name": doc["name"], "risk_score": doc["risk_score"]}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_return_scores", return_direct=True)
def fetch_return_scores(top_n: int = 5) -> str:
    """
    Fetch the top_n mutual funds sorted by descending return_score (highest returns first).
    Returns a JSON array of objects: [{"name": ..., "return_score": ...}, ...].
    """
    cursor = mutual_funds_collection.find(
        {"return_score": {"$exists": True}}
    ).sort("return_score", DESCENDING).limit(int(top_n))

    results = [
        {"name": doc["name"], "return_score": doc["return_score"]}
        for doc in cursor
    ]
    return json.dumps(results)