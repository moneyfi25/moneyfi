import requests
from pymongo import MongoClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mf_bkp_collection

API_URL = "https://api.mfapi.in/mf"

def fetch_mf_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def filter_valid_schemes(schemes):
    return [
        scheme for scheme in schemes
        if scheme.get("isinGrowth") or scheme.get("isinDivReinvestment")
    ]

def store_in_mongo(data):
    try:
        if data:
            mf_bkp_collection.insert_many(data)
            print(f"✅ Inserted {len(data)} valid schemes into MongoDB.")
        else:
            print("⚠️ No valid data to insert.")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

def main():
    print("📡 Fetching data from API...")
    all_schemes = fetch_mf_data()
    print(f"📊 Total schemes fetched: {len(all_schemes)}")
    
    valid_schemes = filter_valid_schemes(all_schemes)
    print(f"✅ Valid schemes with ISINs: {len(valid_schemes)}")
    
    print("💾 Storing in MongoDB...")
    store_in_mongo(valid_schemes)

if __name__ == "__main__":
    main()
