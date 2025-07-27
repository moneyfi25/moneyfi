from pymongo import ASCENDING, DESCENDING
import json
from langchain_core.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import mutual_funds_collection

@tool("fetch_short_term_returns", return_direct=True)
def fetch_short_term_returns() -> str:
    """Fetch all the mutual funds and their short term returns -
    which includes returns for 1 week, 1 month, 3 months, 6 months, and 1 year.
    Returns a JSON array of objects: 
    [{"fund_name":...,
      "1_week_return": ...,
      "1_month_return": ...,
      "3_month_return": ...,
      "6_month_return": ...,
      "1_year_return": ...},
      ...
    ]."""
    cursor = mutual_funds_collection.find(
        {"1_week_return": {"$exists": True}}
    )

    results = [
        {"fund_name": doc["fund_name"],
         "1_week_return": doc["1_week_return"],
         "1_month_return": doc.get("1_month_return", None),
         "3_month_return": doc.get("3_month_return", None),
         "6_month_return": doc.get("6_month_return", None),
         "1_year_return": doc.get("1_year_return", None)}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_long_term_returns", return_direct=True)
def fetch_long_term_returns() -> str:
    """Fetch all the mutual funds and their long term returns -
    which includes returns for 3 years, 5 years, and 10 years.
    Returns a JSON array of objects: 
    [{"fund_name":...,
      "3_year_return": ...
      "5_year_return": ...,
      "10_year_return": ...]},
      ...
    ]."""
    cursor = mutual_funds_collection.find(
        {"3_year_return": {"$exists": True}}
    )

    results = [
        {"fund_name": doc["fund_name"],
         "3_year_return": doc["3_year_return"],
         "5_year_return": doc.get("5_year_return", None),
         "10_year_return": doc.get("10_year_return", None)}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_risk_and_volatility_parameters", return_direct=True)
def fetch_risk_and_volatility_parameters() -> str:
    """Fetch all the mutual funds and their risk parameters -
    which includes Sharpe ratio, Sortino ratio, Beta, Alpha, Standard Deviation, Information ratio and r-squared.
    Returns a JSON array of objects: 
    [{"fund_name":...,
      "sharpe_ratio": ...,
      "sortino_ratio": ...,
      "beta": ...,
      "alpha": ...,
      "standard_deviation": ...,
      "information_ratio": ...,
      "r_squared": ...},
      ...
    ]."""
    cursor = mutual_funds_collection.find(
        {"shrape_ratio": {"$exists": True}}
    )

    results = [
        {"fund_name": doc["fund_name"],
         "sharpe_ratio": doc["shrape_ratio"],
         "sortino_ratio": doc.get("sortino_ratio", None),
         "beta": doc.get("beta", None),
         "alpha": doc.get("alpha", None),
         "standard_deviation": doc.get("standard_deviation", None),
         "information_ratio": doc.get("information_ratio", None),
         "r_squared": doc.get("r_squared", None)}
        for doc in cursor
    ]
    return json.dumps(results)

@tool("fetch_fees_and_details", return_direct=True)
def fetch_fees_and_details() -> str:
    """Fetch all the mutual funds and their fees and details -
    which includes expense ratio, minimum investment, fund manager and exit load.
    Returns a JSON array of objects: 
    [{"fund_name": ...,
      "category": ...,
      "expense_ratio": ...,
      "minimum_investment": ...,
      "exit_load": ...,
      "fund_manager": ...},
      ...
    ]."""
    cursor = mutual_funds_collection.find(
        {"minimum_investment": {"$exists": True}}
    )

    results = [
        {"fund_name": doc["fund_name"],
         "category": doc.get("category", None),
         "expense_ratio": doc.get("expense_ratio", None),
         "minimum_investment": doc.get("minimum_investment"),
         "exit_load": doc.get("exit_load", None),
         "fund_manager": doc.get("fund_manager", None)}
        for doc in cursor
    ]
    return json.dumps(results)