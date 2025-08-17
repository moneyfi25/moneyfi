import requests
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
import sys
import os
from dateutil.relativedelta import relativedelta
import pandas as pd

# adjust import path as needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mf_bkp_collection

def compute_annualised_returns(daily_returns_map):
    """
    Given daily_returns: { "YYYY-MM-DD": { "close": float, ... }, ... }
    Returns a dict:
      {
        "3Y_Annualised": float|None,   # in %
        "5Y_Annualised": float|None    # in %
      }
    """
    # 1) build (date,nav) list
    records = []
    for date_str, info in daily_returns_map.items():
        raw = info.get("nav", info.get("close"))
        if raw is None:
            continue
        try:
            nav = float(raw)
            dt  = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        records.append((dt, nav))

    if not records:
        return {"3Y_Annualised": None, "5Y_Annualised": None}

    # 2) series of NAVs, sorted
    nav_s = (
        pd.Series(
            [nav for _, nav in records],
            index=pd.to_datetime([dt for dt, _ in records])
        )
        .sort_index()
    )

    latest_date = nav_s.index.max()
    latest_nav  = nav_s.loc[latest_date]

    # 3) compute annualised for 3Y and 5Y
    out = {}
    for years in (3, 5):
        label = f"{years}Y_Annualised"
        target = latest_date - relativedelta(years=years)
        past = nav_s[nav_s.index <= target]
        if past.empty:
            out[label] = None
        else:
            past_nav = past.iloc[-1]
            ann = (latest_nav / past_nav)**(1/years) - 1
            out[label] = ann * 100

    return out

def compute_trailing_returns(daily_returns_map):
    """
    Given daily_returns: { "YYYY-MM-DD": { "close": float, ... }, ... }
    Compute trailing returns for 6M and 1Y as percentages.
    """
    # 1) build list of (date, nav)
    records = []
    for date_str, info in daily_returns_map.items():
        raw = info.get("nav", info.get("close"))
        if raw is None:
            continue
        try:
            nav = float(raw)
            dt  = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        records.append((dt, nav))

    if not records:
        return {"6M": None, "1Y": None}

    # 2) series of NAVs
    nav_s = (
        pd.Series(
            [nav for _, nav in records],
            index=pd.to_datetime([dt for dt, _ in records])
        )
        .sort_index()
    )

    latest_date = nav_s.index.max()
    latest_nav  = nav_s.loc[latest_date]

    # 3) define deltas
    periods = {
        "6M": relativedelta(months=6),
        "1Y": relativedelta(years=1)
    }

    trailing = {}
    for label, delta in periods.items():
        target = latest_date - delta
        past = nav_s[nav_s.index <= target]
        if past.empty:
            trailing[label] = None
        else:
            past_nav = past.iloc[-1]
            # absolute return * 100 → percentage
            trailing[label] = (latest_nav / past_nav - 1) * 100

    return trailing

def main():
    # Fetch only the fields we need, limit to first 10 docs
    cursor = mf_bkp_collection.find(
        {},
        {"schemeCode": 1, "schemeName": 1, "daily_returns": 1}
    ).limit(10)

    for fund in cursor:
        _id   = fund["_id"]
        code  = fund.get("schemeCode")
        name  = fund.get("schemeName", "<no name>")
        dr_map = fund.get("daily_returns", {})

        print(f"\n🔍 Computing trailing returns for {code} – {name}")
        trailing = compute_trailing_returns(dr_map)
        ann = compute_annualised_returns(dr_map)

        # Update back into MongoDB
        mf_bkp_collection.update_one(
            {"_id": _id},
            {
                "$set": {
                    "trailing_returns": trailing,
                    "trailing_updated": datetime.utcnow(),
                    "3Y_return": ann["3Y_Annualised"],
                    "5Y_return": ann["5Y_Annualised"],
                }
            }
        )
        print(f"✅ Updated document {_id} with trailing_returns.\n")

if __name__ == "__main__":
    main()
