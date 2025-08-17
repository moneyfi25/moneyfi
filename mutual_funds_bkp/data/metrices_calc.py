import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import sys
import os

# --- Adjust import path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mf_bkp_collection, index_collection


def get_filtered_returns_series(collection, key_field, key_value, return_field, date_limit):
    doc = collection.find_one({ key_field: key_value }, {"daily_returns": 1 })
    if not doc or "daily_returns" not in doc:
        raise ValueError(f"No daily_returns found for {key_field}={key_value}")

    returns_map = {}
    for date_str, data in doc["daily_returns"].items():
        if return_field not in data or data[return_field] is None:
            continue
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt >= date_limit:
                returns_map[dt] = float(data[return_field])
        except Exception as e:
            continue  # skip malformed dates

    return pd.Series(returns_map).sort_index()


def calculate_beta(fund_series: pd.Series, index_series: pd.Series) -> float:
    df = pd.DataFrame({
        "fund":  fund_series,
        "index": index_series
    }).dropna()
    if len(df) < 2:
        raise ValueError("Insufficient data to calculate beta")

    cov = df["fund"].cov(df["index"])
    var = df["index"].var()
    return cov / var


if __name__ == "__main__":
    try:
        # --- 3 years ago ---
        three_years_ago = datetime.today() - timedelta(days=3*365)

        # --- Get fund and index series ---
        fund_series = get_filtered_returns_series(
            mf_bkp_collection, key_field="schemeCode", key_value=100033,
            return_field="diff_%", date_limit=three_years_ago
        )

        index_series = get_filtered_returns_series(
            index_collection, key_field="symbol", key_value="^NSEI",
            return_field="percent_return", date_limit=three_years_ago
        )

        # --- Calculate beta ---
        beta_value = calculate_beta(fund_series, index_series)
        print(f"✅ 3-Year Beta: {beta_value:.4f}")

    except Exception as e:
        print(f"❌ Error: {e}")
