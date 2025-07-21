import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import bonds_collection
import pandas as pd
from dateutil.parser import parse

def load_csv(filepath: str) -> pd.DataFrame:
    """Load the CSV and coerce types for filtering."""
    df = pd.read_csv(filepath)
    df.columns = ["SYMBOL", "SERIES", "BOND_TYPE", "COUPON_RATE", "FACE_VALUE", "LTP", "%CHNG", "VOLUME", "VALUE", "", "CREDIT_RATING", "MATURITY_DATE"]
    df = df[df["MATURITY_DATE"].notna() & (df["MATURITY_DATE"].astype(str).str.strip() != '')]
    def safe_parse_date(x):
        try:
            return parse(str(x), dayfirst=True)
        except (ValueError, TypeError):
            return pd.NaT
    df["MATURITY_DATE"] = df["MATURITY_DATE"].apply(safe_parse_date)
    df = df.dropna(subset=["MATURITY_DATE"])
    df["VOLUME"] = (
        df["VOLUME"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["VOLUME"]  = pd.to_numeric(df["VOLUME"], errors="coerce")
    df["VOLUME"] = df["VOLUME"].fillna(0)
    df["LTP"] = (
        df["LTP"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")
    df["LTP"] = df["LTP"].fillna('')
    df["COUPON_RATE"] = pd.to_numeric(df["COUPON_RATE"], errors='coerce')
    df["COUPON_RATE"] = df["COUPON_RATE"].fillna('')
    df["BOND_TYPE"] = df["BOND_TYPE"].fillna('')
    df["CREDIT_RATING"] = df["CREDIT_RATING"].fillna("NA")
    df["FACE_VALUE"] = (
        df["FACE_VALUE"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["FACE_VALUE"] = pd.to_numeric(df["FACE_VALUE"], errors='coerce')
    df["FACE_VALUE"] = df["FACE_VALUE"].fillna('')
    
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
    result = bonds_collection.insert_many(records)
    return result.inserted_ids

def main():
    filepath = "MW-Bonds-on-CM-21-Jul-2025.csv"
    df = load_csv(filepath)
    filters = {
        "CREDIT_RATING": ("ne", "NA"),
        "VOLUME": ("gt", 900),
    }
    df_filtered = apply_filters(df, filters)
    
    inserted_ids = push_to_mongo(df_filtered)
    print(f"Inserted {len(inserted_ids)} documents (IDs: {inserted_ids})")

if __name__ == "__main__":
    main()
