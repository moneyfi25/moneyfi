import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import sgb_collection
import pandas as pd
from pymongo import MongoClient

def load_csv(filepath: str) -> pd.DataFrame:
    """Load the CSV and coerce types for filtering."""
    df = pd.read_csv(filepath)
    
    df["VOLUME \n"]  = pd.to_numeric(df["VOLUME \n"], errors="coerce")
    df["30D   %CHNG \n"] = pd.to_numeric(df["30D   %CHNG \n"], errors="coerce")
    df["365 D % CHNG \n"] = pd.to_numeric(df["365 D % CHNG \n"], errors="coerce")
    df['LTP \n'] = (
        df['LTP \n']
        .astype(str)
        .str.replace(',', '')            # remove thousands‐separator
        .str.replace(r'[^\d\.]', '', regex=True)  # drop anything but digits or dot
        .astype(float)                   # or pd.to_numeric(..., errors='coerce')
    )
    
    return df

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Filter the DataFrame according to a dict of conditions.
    filters example:
      {
        "tenure_years": ("eq", 5),
        "coupon_rate": ("gt", 6.5),
        "issue_date": ("ge", "2023-01-01")
      }
    Supported ops: eq, ne, gt, ge, lt, le, contains
    """
    for col, (op, val) in filters.items():
        if op == "eq":
            df = df[df[col] == val]
        elif op == "ne":
            df = df[df[col] != val]
        elif op == "gt":
            df = df[df[col] > val]
        elif op == "ge":
            df = df[df[col] >= val]
        elif op == "lt":
            df = df[df[col] < val]
        elif op == "le":
            df = df[df[col] <= val]
        elif op == "contains":
            df = df[df[col].str.contains(val, na=False)]
        else:
            raise ValueError(f"Unsupported filter op: {op}")
    return df

def push_to_mongo(df: pd.DataFrame) -> list:
    """Insert DataFrame rows into MongoDB and return the list of inserted IDs."""
    records = df.to_dict(orient="records")
    if not records:
        print("No records to insert.")
        return []
    sgb_collection.delete_many({})  # Clear existing records
    result = sgb_collection.insert_many(records)
    return result.inserted_ids

def main():
    filepath = "MW-SGB-10-Aug-2025.csv"
    df = load_csv(filepath)
    print("Columns:", df.columns.tolist())
    filters = {
        "VOLUME \n": ("gt", 200),
    }
    df_filtered = apply_filters(df, filters)
    
    # 3) Push to MongoDB
    inserted_ids = push_to_mongo(df_filtered)
    print(f"Inserted {len(inserted_ids)} documents (IDs: {inserted_ids})")

if __name__ == "__main__":
    main()
