import requests
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
import sys
import os
from dateutil.relativedelta import relativedelta

# adjust import path as needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mf_bkp_collection

API_URL_TEMPLATE = "https://api.mfapi.in/mf/{}"

def fetch_nav_data(scheme_code):
    try:
        url = API_URL_TEMPLATE.format(scheme_code)
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ Error fetching NAV for {scheme_code}: {e}")
        return None

def calculate_daily_returns(nav_list):
    """
    nav_list: list of dicts with keys 'date' (dd-mm-yyyy) and 'nav' (string)
    Returns a dict:
      {
        '2025-01-02': { 'nav': 1234.56, 'diff_in_nav': None,    'diff_%': None    },
        '2025-01-03': { 'nav': 1240.00, 'diff_in_nav': 5.44,    'diff_%': 0.4403 },
        ...
      }
    """
    # 1. Parse and sort
    parsed = []
    for item in nav_list:
        # convert "dd-mm-yyyy" → datetime, nav → float
        dt = datetime.strptime(item['date'], '%d-%m-%Y')
        nav = float(item['nav'].replace(',', ''))
        parsed.append((dt, nav))
    parsed.sort(key=lambda x: x[0])

    # 2. Build the daily-returns dict
    daily_returns = {}
    prev_nav = None
    for dt, nav in parsed:
        date_str = dt.strftime('%Y-%m-%d')
        if prev_nav is None:
            diff = None
            pct  = None
        else:
            diff = nav - prev_nav
            pct  = (diff / prev_nav) * 100 if prev_nav != 0 else None

        daily_returns[date_str] = {
            'nav': nav,
            'diff_in_nav': diff,
            'diff_%': pct
        }
        prev_nav = nav

    return daily_returns
import pandas as pd


def main():
    all_schemes = list(mf_bkp_collection.find().limit(10))

    for fund in all_schemes:
        scheme_code = fund.get("schemeCode")
        if not scheme_code:
            continue

        print(f"📊 Processing schemeCode: {scheme_code} - {fund.get('schemeName')}")

        api_data = fetch_nav_data(scheme_code)
        if not api_data or "data" not in api_data:
            continue

        daily_returns = calculate_daily_returns(api_data["data"])

        # update the document with the nested daily_returns map
        mf_bkp_collection.update_one(
            {"schemeCode": scheme_code},
            {"$set": {
                "fund_house":      api_data.get("meta", {}).get("fund_house"),
                "scheme_type":     api_data.get("meta", {}).get("scheme_type"),
                "scheme_category": api_data.get("meta", {}).get("scheme_category"),
                "daily_returns":   daily_returns,
                "last_updated":    datetime.now()
            }},
            upsert=True
        )
        print(f"✅ Stored {len(daily_returns)} daily returns for {scheme_code}.\n")

if __name__ == "__main__":
    main()
