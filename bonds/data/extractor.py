import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import bonds_collection
import pandas as pd
from dateutil.parser import parse
import pandas as pd
import re
from datetime import datetime


# Define month codes used in short bond names
month_map = {
    "JA": "01", "FE": "02", "MR": "03", "AP": "04", "MY": "05", "JN": "06",
    "JL": "07", "AU": "08", "SE": "09", "OC": "10", "NO": "11", "DE": "12"
}

# Format date from DDMMYY to readable format
def format_date(dd, mm, yy):
    try:
        return datetime.strptime(f"{dd}{mm}{yy}", "%d%m%y").date()
    except ValueError:
        return pd.NaT

def parse_gsec_symbol(symbol: str):
    symbol = symbol.strip().upper()
    symbol = symbol.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")  # Remove A/B/C suffixes

    # Pattern 1: 7.26GS2033 or 10.18GS2026
    m = re.match(r"^(\d{2,4}\.\d{1,2})GS(\d{4})$", symbol)
    if m:
        return float(m.group(1)), datetime(int(m.group(2)), 12, 31)

    # Pattern 2: 726GS2033 or 1018GS2026 or 68GS2060
    m = re.match(r"^(\d{2,4})GS(\d{2,4})$", symbol)
    if m:
        coupon_digits = m.group(1)
        if len(coupon_digits) == 2:
            rate = float(coupon_digits) / 10
        else:
            rate = float(coupon_digits) / 100
        year = int(m.group(2)) if len(m.group(2)) == 4 else int("20" + m.group(2))
        return rate, datetime(year, 12, 31)


    # Pattern 3: 75AP28 or 773AP32
    month_map = {
        "JA": "01", "FE": "02", "MR": "03", "MA": "03", "CG": "03",
        "AP": "04", "MY": "05", "JN": "06", "JL": "07",
        "AU": "08", "SE": "09", "OC": "10", "NO": "11", "DE": "12"
    }
    m = re.match(r"^(\d{2,4})([A-Z]{2})(\d{2})$", symbol)
    if m and m.group(2) in month_map:
        rate = float(m.group(1)) / 100
        mm = int(month_map[m.group(2)])
        year = int("20" + m.group(3))
        return rate, datetime(year, mm, 1)

    # Pattern 4: 74GJ26, 743CG29 — state bonds
    m = re.match(r"^(\d{2,3})([A-Z]{2})(\d{2})$", symbol)
    if m:
        rate = float(m.group(1)) / 100
        year = int("20" + m.group(3))
        return rate, datetime(year, 12, 31)

    # Pattern 5: 91D210825, 364D120226 — T-Bills
    m = re.match(r"^(\d{2,3})D(\d{2})(\d{2})(\d{2})$", symbol)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(2)}{m.group(3)}{m.group(4)}", "%d%m%y")
            return 0.0, dt
        except:
            return 0.0, pd.NaT

    # Pattern 6: GS101025C — long-form GS with date in symbol
    m = re.match(r"^GS(\d{2})(\d{2})(\d{2})[A-Z]?$", symbol)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)}{m.group(2)}{m.group(3)}", "%d%m%y")
            return None, dt
        except:
            return None, pd.NaT

    # ✅ Pattern 7: 698GR2054 — Government of India bonds
    m = re.match(r"^(\d{3})GR(\d{4})$", symbol)
    if m:
        rate = float(m.group(1)) / 100
        year = int(m.group(2))
        return rate, datetime(year, 12, 31)

    return None, pd.NaT

def load_csv_gsec(filepath: str) -> pd.DataFrame:
    """Load the CSV and coerce types for filtering."""
    df = pd.read_csv(filepath)
    df.columns = ["SYMBOL", "SERIES", "ISIN", "FACE_VALUE", "OPEN", "HIGH", "LOW", "LTP", "PREV_CLOSE", "%CHANGE", "VOLUME", "VALUE"]
    df["FACE_VALUE"] = (
        df["FACE_VALUE"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["FACE_VALUE"] = pd.to_numeric(df["FACE_VALUE"], errors='coerce')
    df["FACE_VALUE"] = df["FACE_VALUE"].fillna('')
    df["LTP"] = (
        df["LTP"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["LTP"] = pd.to_numeric(df["LTP"], errors="coerce")
    df["LTP"] = df["LTP"].fillna('')
    df["VOLUME"] = (
        df["VOLUME"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["VOLUME"]  = pd.to_numeric(df["VOLUME"], errors="coerce")
    df["VOLUME"] = df["VOLUME"].fillna(0)
    df[["COUPON_RATE", "MATURITY_DATE"]] = df["SYMBOL"].apply(lambda x: pd.Series(parse_gsec_symbol(x)))
    df["MATURITY_DATE"] = pd.to_datetime(df["MATURITY_DATE"], errors='coerce')
    nat_rows = df[pd.isna(df["MATURITY_DATE"])]
    print(nat_rows[["MATURITY_DATE", "SYMBOL"]].values.tolist())
    return df

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
    # for corporate bonds
    filepath = "MW-Bonds-on-CM-21-Jul-2025.csv"
    df = load_csv(filepath)
    filters = {
        "CREDIT_RATING": ("ne", "NA"),
        "VOLUME": ("gt", 900),
    }
    df_filtered = apply_filters(df, filters)
    inserted_ids = push_to_mongo(df_filtered)
    print(f"Inserted {len(inserted_ids)} corporate bonds into MongoDB.")


    # for government bonds
    filepath_gsec = "MW-G-Sec-on-CM-21-Jul-2025.csv"
    df_gsec = load_csv_gsec(filepath_gsec)
    filters_gsec = {
        "VOLUME": ("gt", 1000),
    }
    df_gsec_filtered = apply_filters(df_gsec, filters_gsec)
    inserted_ids_gsec = push_to_mongo(df_gsec_filtered)
    print(f"Inserted {len(inserted_ids_gsec)} government bonds into MongoDB.")


if __name__ == "__main__":
    main()
