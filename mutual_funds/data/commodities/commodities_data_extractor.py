import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from db import mutual_funds_collection, etf_collection
import pandas as pd
from pymongo import UpdateOne
from pymongo.collection import Collection
from typing import List, Any

def extract_commodities_snapshot(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.drop("Rating", axis=1, inplace=True)
    df.drop("1 Yr Ret (%)", axis=1, inplace=True)
    df.drop("1 Yr Rank", axis=1, inplace=True)
    df.drop("Analysts' View", axis=1, inplace=True)
    df.columns = ["fund_name", "riskometer", "category", "expense_ratio", "launch_date", "net_assets"]
    df["expense_ratio"] = (
        df["expense_ratio"]
        .astype(str)
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce")
    df["expense_ratio"] = df["expense_ratio"].fillna('')
    df["net_assets"] = (
        df["net_assets"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["net_assets"] = pd.to_numeric(df["net_assets"], errors="coerce")
    df["net_assets"] = df["net_assets"].fillna('')
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors='coerce')
    print(df)
    return df

def extract_commodities_short_term_plans(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.drop("1 Wk Rank", axis=1, inplace=True)
    df.drop("1 Mth Rank", axis=1, inplace=True)
    df.drop("3 Mth Rank", axis=1, inplace=True)
    df.drop("6 Mth Rank", axis=1, inplace=True)
    df.drop("1 Yr Rank", axis=1, inplace=True)
    df.columns = ["fund_name", "1_week_return", "1_month_return", "3_month_return", "6_month_return", "1_year_return" ]
    df["1_week_return"] = (
        df["1_week_return"]
        .astype(str)
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)  # keeps digits, dot, and minus (for the negative return values)
    )

    df["1_week_return"] = pd.to_numeric(df["1_week_return"], errors="coerce")
    df["1_week_return"] = df["1_week_return"].fillna('')

    df["1_month_return"] = (
        df["1_month_return"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.-]', '', regex=True)  
    )
    df["1_month_return"] = pd.to_numeric(df["1_month_return"], errors="coerce")
    df["1_month_return"] = df["1_month_return"].fillna('')

    df["3_month_return"] = (
        df["3_month_return"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)  
    )
    df["3_month_return"] = pd.to_numeric(df["3_month_return"], errors="coerce")
    df["3_month_return"] = df["3_month_return"].fillna('')

    df["6_month_return"] = (
        df["6_month_return"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)  
    )
    df["6_month_return"] = pd.to_numeric(df["6_month_return"], errors="coerce")
    df["6_month_return"] = df["6_month_return"].fillna('')

    df["1_year_return"] = (
        df["1_year_return"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)  
    )
    df["1_year_return"] = pd.to_numeric(df["1_year_return"], errors="coerce")
    df["1_year_return"] = df["1_year_return"].fillna('')
    print(df)
    return df

def extract_commodities_long_term_plans(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.drop("3 Yr Rank", axis=1, inplace=True)
    df.drop("5 Yr Rank", axis=1, inplace=True)
    df.drop("10 Yr Rank", axis=1, inplace=True)
    df.drop("15 Yr Rank", axis=1, inplace=True)
    df.drop("20 Yr Rank", axis=1, inplace=True)
    df.drop("15 Yr Ret (%)", axis=1, inplace=True)
    df.drop("20 Yr Ret (%)", axis=1, inplace=True)
    df.columns = ["fund_name", "3_year_return", "5_year_return", "10_year_return"]
    df["3_year_return"] = (
        df["3_year_return"]
        .astype(str)
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)  # keeps digits, dot, and minus (for the negative return values)
    )

    df["3_year_return"] = pd.to_numeric(df["3_year_return"], errors="coerce")
    df["3_year_return"] = df["3_year_return"].fillna('')

    df["5_year_return"] = (
        df["5_year_return"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.-]', '', regex=True)  
    )
    df["5_year_return"] = pd.to_numeric(df["5_year_return"], errors="coerce")
    df["5_year_return"] = df["5_year_return"].fillna('')

    df["10_year_return"] = (
        df["10_year_return"]
        .astype(str)
        .str.replace(',', '')
        .str.replace(r'[^\d\.-]', '', regex=True)
    )
    df["10_year_return"] = pd.to_numeric(df["10_year_return"], errors="coerce")
    df["10_year_return"] = df["10_year_return"].fillna('')
    print(df)
    return df

def extract_commodities_risk_factors(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.drop("Fund Risk Grade", axis=1, inplace=True)
    df.drop("Fund Return Grade", axis=1, inplace=True)
    df.drop("Riskometer", axis=1, inplace=True)
    df.columns = ["fund_name", "standard_deviation", "sharpe_ratio", "sortino_ratio", "beta", "alpha", "information_ratio", "r_squared"]
    df["standard_deviation"] = (
        df["standard_deviation"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["standard_deviation"] = pd.to_numeric(df["standard_deviation"], errors="coerce")
    df["standard_deviation"] = df["standard_deviation"].fillna('')

    df["sharpe_ratio"] = (
        df["sharpe_ratio"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["sharpe_ratio"] = pd.to_numeric(df["sharpe_ratio"], errors="coerce")
    df["sharpe_ratio"] = df["sharpe_ratio"].fillna('')

    df["sortino_ratio"] = (
        df["sortino_ratio"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["sortino_ratio"] = pd.to_numeric(df["sortino_ratio"], errors="coerce")
    df["sortino_ratio"] = df["sortino_ratio"].fillna('')

    df["beta"] = (
        df["beta"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
    df["beta"] = df["beta"].fillna('')

    df["alpha"] = (
        df["alpha"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["alpha"] = pd.to_numeric(df["alpha"], errors="coerce")
    df["alpha"] = df["alpha"].fillna('')

    df["information_ratio"] = (
        df["information_ratio"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["information_ratio"] = pd.to_numeric(df["information_ratio"], errors="coerce")
    df["information_ratio"] = df["information_ratio"].fillna('')

    df["r_squared"] = (
        df["r_squared"]
        .astype(str)
        .str.replace(',', '')            
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["r_squared"] = pd.to_numeric(df["r_squared"], errors="coerce")
    df["r_squared"] = df["r_squared"].fillna('')
    print(df)
    return df

def extract_commodities_fees_details(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.drop("Expense Ratio (%)", axis=1, inplace=True)
    df.columns = ["fund_name", "minimum_investment", "exit_load", "fund_manager"]
    df["minimum_investment"] = (
        df["minimum_investment"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["minimum_investment"] = pd.to_numeric(df["minimum_investment"], errors="coerce")
    df["minimum_investment"] = df["minimum_investment"].fillna('')
    df["exit_load"] = (
        df["exit_load"]
        .astype(str)            
        .str.replace(',', '')
        .str.replace(r'[^\d\.]', '', regex=True)  
    )
    df["exit_load"] = pd.to_numeric(df["exit_load"], errors="coerce")
    df["exit_load"] = df["exit_load"].fillna('')
    df["fund_manager"] = df["fund_manager"].fillna('')
    print(df)
    return df


def push_to_mongo(df: pd.DataFrame, 
                  collection: Collection,
                  key_field: str = "fund_name"
                 ) -> List[Any]:
    """
    Upsert each row in df into `collection`, matching on `key_field`. 
    Returns list of newly-inserted document IDs.
    """
    records = df.to_dict(orient="records")
    if not records:
        print("No records to upsert.")
        return []

    operations = []
    for rec in records:
        if key_field not in rec:
            continue

        filter_doc = { key_field: rec[key_field] }
        update_doc = { "$set": rec }
        operations.append(
            UpdateOne(filter_doc, update_doc, upsert=True)
        )

    # execute in bulk
    result = collection.bulk_write(operations, ordered=False)

    # result.upserted_ids is a dict: {operation_index: _id}
    new_ids = list(result.upserted_ids.values())
    print(f"Matched {result.matched_count}, "
          f"Modified {result.modified_count}, "
          f"Upserted {len(new_ids)} new docs.")
    return new_ids 


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
        elif op == "does_not_contain":
            df = df[~df[col].str.contains(val, na=False)]
        elif op == "notnull":
            df = df[df[col].notna()]
        else:
            raise ValueError(f"Unsupported filter op: {op}")
    return df


def main():
    # calling extract_commodities_snapshot function here
    commodities_snapshot_filepath = "commodities_snapshot.csv"
    df = extract_commodities_snapshot(commodities_snapshot_filepath)
    mf_filters = {
        "launch_date": ("notnull", None),
        "fund_name": ("does_not_contain", "ETF")
    }
    mf_filtered = apply_filters(df, mf_filters)
    mf_ids = push_to_mongo(mf_filtered, mutual_funds_collection, key_field="fund_name")
    print("MF IDs:", mf_ids)
    etf_filters = {
        "launch_date": ("notnull", None),
        "fund_name": ("contains", "ETF"),
    }
    etf_filtered = apply_filters(df, etf_filters)
    etf_ids = push_to_mongo(etf_filtered, etf_collection, key_field="fund_name")
    print("ETF IDs:", etf_ids)
    df = extract_commodities_snapshot(commodities_snapshot_filepath)
    print("Data loaded successfully.")

    # calling extract_commodities_short_term_plans function here
    commodities_short_term_plans_filepath = "commodities_short_term.csv"
    df_short_term_plans = extract_commodities_short_term_plans(commodities_short_term_plans_filepath)
    mf_filters = {
        "fund_name": ("does_not_contain", "ETF"),
        "1_week_return": ("notnull", None),
        "1_month_return": ("notnull", None),
        "3_month_return": ("notnull", None),
        "6_month_return": ("notnull", None),
        "1_year_return": ("notnull", None)
    }
    mf_filtered = apply_filters(df_short_term_plans, mf_filters)
    mf_ids = push_to_mongo(mf_filtered, mutual_funds_collection, key_field="fund_name")
    print("MF Short Term Plan IDs:", mf_ids)
    etf_filters = {
        "fund_name": ("contains", "ETF"),
        "1_week_return": ("notnull", None),
        "1_month_return": ("notnull", None),
        "3_month_return": ("notnull", None),
        "6_month_return": ("notnull", None),
        "1_year_return": ("notnull", None)
    }
    etf_filtered = apply_filters(df_short_term_plans, etf_filters)
    etf_ids = push_to_mongo(etf_filtered, etf_collection, key_field="fund_name")
    print("ETF Short Term Plan IDs:", etf_ids)
    print("Short Term Plans data loaded successfully.")

    # calling extract_commodities_long_term_plans function here
    commodities_long_term_plans_filepath = "commodities_long_term.csv"
    df_long_term_plans = extract_commodities_long_term_plans(commodities_long_term_plans_filepath)
    mf_filters = {
        "fund_name": ("does_not_contain", "ETF"),
        "3_year_return": ("notnull", None),
        "5_year_return": ("notnull", None),
        "10_year_return": ("notnull", None),
    }
    mf_filtered = apply_filters(df_long_term_plans, mf_filters)
    mf_ids = push_to_mongo(mf_filtered, mutual_funds_collection, key_field="fund_name")
    print("MF Long Term Plan IDs:", mf_ids)
    etf_filters = {
        "fund_name": ("contains", "ETF"),
        "3_year_return": ("notnull", None),
        "5_year_return": ("notnull", None),
        "10_year_return": ("notnull", None),
    }
    etf_filtered = apply_filters(df_long_term_plans, etf_filters)
    etf_ids = push_to_mongo(etf_filtered, etf_collection, key_field="fund_name")
    print("ETF Long Term Plan IDs:", etf_ids)
    print("Long Term Plans data loaded successfully.")

    # calling extract_commodities_risk_factors function here
    commodities_risk_factors_filepath = "commodities_risk.csv"
    df_risk_factors = extract_commodities_risk_factors(commodities_risk_factors_filepath)
    mf_filters = {
        "fund_name": ("does_not_contain", "ETF"),
        "standard_deviation": ("notnull", None),
        "sharpe_ratio": ("notnull", None),
        "sortino_ratio": ("notnull", None),
        "beta": ("notnull", None),
        "alpha": ("notnull", None),
        "information_ratio": ("notnull", None),
        "r_squared": ("notnull", None)
    }
    mf_filtered = apply_filters(df_risk_factors, mf_filters)
    mf_ids = push_to_mongo(mf_filtered, mutual_funds_collection, key_field="fund_name")
    print("MF Risk IDs:", mf_ids)
    etf_filters = {
        "fund_name": ("contains", "ETF"),
        "standard_deviation": ("notnull", None),
        "sharpe_ratio": ("notnull", None),
        "sortino_ratio": ("notnull", None),
        "beta": ("notnull", None),
        "alpha": ("notnull", None),
        "information_ratio": ("notnull", None),
        "r_squared": ("notnull", None),
    }
    etf_filtered = apply_filters(df_risk_factors, etf_filters)
    etf_ids = push_to_mongo(etf_filtered, etf_collection, key_field="fund_name")
    print("ETF Risk IDs:", etf_ids)
    print("Risk Factors data loaded successfully.")

    #calling extract_commodities_fees_details function here
    commodities_fees_details_filepath = "commodities_fees_and_details.csv"
    df_fees_details = extract_commodities_fees_details(commodities_fees_details_filepath)
    mf_filters = {
        "fund_name": ("does_not_contain", "ETF"),
        "minimum_investment": ("notnull", None),
        "exit_load": ("notnull", None),
        "fund_manager": ("notnull", None),
    }
    mf_filtered = apply_filters(df_fees_details, mf_filters)
    mf_ids = push_to_mongo(mf_filtered, mutual_funds_collection, key_field="fund_name")
    print("MF Fees IDs:", mf_ids)
    etf_filters = {
        "fund_name": ("contains", "ETF"),
        "minimum_investment": ("notnull", None),
        "exit_load": ("notnull", None),
        "fund_manager": ("notnull", None),
    }
    etf_filtered = apply_filters(df_fees_details, etf_filters)
    etf_ids = push_to_mongo(etf_filtered, etf_collection, key_field="fund_name")
    print("ETF Fees IDs:", etf_ids)
    print("Fees Details data loaded successfully.")


if __name__ == "__main__":
    main()
