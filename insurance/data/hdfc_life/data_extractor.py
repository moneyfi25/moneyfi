import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from db import insurance_collection
import pandas as pd
from pymongo import UpdateOne
from pymongo.collection import Collection
from typing import List, Any

def load_csv(filepath: str) -> pd.DataFrame:
    """Load CSV file into a DataFrame."""
    df = pd.read_csv(filepath)
    print(df)
    return df

def main():
    insurance_collection.delete_many({})  # Clear existing data
    plan_filepath = "hdfc_click2invest_extracted.csv"
    plans_df = load_csv(plan_filepath)

if __name__ == "__main__":
    main()