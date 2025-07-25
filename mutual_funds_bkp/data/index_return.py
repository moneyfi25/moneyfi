import yfinance as yf
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import index_collection

def fetch_index_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Download OHLCV index data and calculate both absolute and percentage daily returns."""
    df = yf.download([symbol], start=start, end=end, group_by="ticker")

    try:
        df = df[symbol][['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    except KeyError:
        raise KeyError(f"OHLCV data not found for symbol {symbol}. Columns available: {df.columns}")

    # Calculate returns
    df['Daily Return'] = df['Close'].diff()  # absolute change
    df['% Return'] = df['Close'].pct_change() * 100  # percentage change

    # Drop first row (NaN), reset index
    df.dropna(inplace=True)
    df.reset_index(inplace=True)

    return df


def push_to_mongo(df: pd.DataFrame, index_symbol: str, collection):
    # Normalize date format
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # Build the nested daily_returns dict
    daily_returns = {
        row['Date']: {
            'close': row['Close'],
            'daily_return': row['Daily Return'],
            'percent_return': row['% Return'],
        }
        for _, row in df.iterrows()
    }

    # Upsert by symbol
    filter_doc = { "symbol": index_symbol }
    update_doc = {
        "$set": {
            "symbol":        index_symbol,
            "daily_returns": daily_returns
        }
    }

    result = collection.update_one(filter_doc, update_doc, upsert=True)
    if result.upserted_id:
        verb = "Inserted"
    else:
        verb = "Updated"

    print(f"✅ {verb} document for symbol '{index_symbol}' with {len(daily_returns)} daily records.")



# ⚙️ Configuration
INDEX_SYMBOL = "^NSEI"          # Change to ^GSPC (S&P 500), ^BSESN (Sensex), etc.
START_DATE = "2015-01-01"
END_DATE = "2025-07-21"

# Run
df = fetch_index_data(INDEX_SYMBOL, START_DATE, END_DATE)

push_to_mongo(df, INDEX_SYMBOL, index_collection)
