import pandas as pd
from pymongo import MongoClient
import sys
import os

# adjust import path as needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mutual_funds_collection, index_collection

import pandas as pd

def get_returns_series(collection, key_field, key_value, field="percent_return"):
    doc = collection.find_one({ key_field: key_value }, {"daily_returns": 1})
    if not doc or "daily_returns" not in doc:
        raise ValueError(f"No daily_returns found for {key_field}={key_value}")

    # Build a date->value mapping
    data: dict = doc["daily_returns"]
    returns_map = {}
    for date_str, info in data.items():
        # skip days where the field isn't present or is null
        if field not in info or info[field] is None:
            continue
        returns_map[date_str] = float(info[field])

    # Turn into a time-indexed Series
    series = pd.Series(
        returns_map,
        index=pd.to_datetime(list(returns_map.keys())),
        name=key_value,
        dtype=float
    )
    return series.sort_index()


def calculate_beta(fund_series: pd.Series, index_series: pd.Series) -> float:
    """
    Given two pd.Series of daily % returns (indexed by datetime),
    return the beta of the fund vs. the index.
    """
    df = pd.DataFrame({
        "fund":  fund_series,
        "index": index_series
    }).dropna()
    cov = df["fund"].cov(df["index"])
    print(cov)
    var = df["index"].var()
    return cov / var

if __name__ == "__main__":

    # 2. Load the returns
    fund_returns  = get_returns_series(mutual_funds_collection,   "schemeCode", 100033)
    index_returns = get_returns_series(index_collection,  "symbol",     "^NSEI")
    print(f"Fund Returns:\n{fund_returns}")

    # 3. Compute beta
    beta_value = calculate_beta(fund_returns, index_returns)
    print(f"Calculated Beta: {beta_value:.4f}")
