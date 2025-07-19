from langchain.tools import tool
import yfinance as yf
from .risk_model import get_risk_thresholds
import pandas as pd

@tool
def shortlist_stocks_by_risk(user_input: str) -> str:
    """
    Filters stocks based on user query like:
    'I want to invest for 5 years with moderate risk for retirement goal'

    Uses risk model to find suitable stocks based on:
    - 6M, 1Y, 5Y returns
    - volatility (beta)
    """
    # Parse input
    risk = "moderate"
    horizon = 5
    goal = "wealth"

    if "low" in user_input: risk = "low"
    elif "high" in user_input: risk = "high"
    if "1 year" in user_input: horizon = 1
    elif "3 years" in user_input: horizon = 3
    elif "5 years" in user_input: horizon = 5
    if "retirement" in user_input: goal = "retirement"
    elif "child" in user_input: goal = "education"
    
    thresholds = get_risk_thresholds(risk)

    # Predefined NSE tickers (in production: fetch dynamically)
    # all_nse_stocks = pd.read_csv("https://archives.nseindia.com/content/equities/EQUITY_L.csv")
    # tickers = [f"{symbol}.NS" for symbol in all_nse_stocks['SYMBOL']]
    tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS", 
    "ICICIBANK.NS", "KOTAKBANK.NS", "BHARTIARTL.NS", "LT.NS", "ITC.NS",
    "BAJFINANCE.NS", "ASIANPAINT.NS", "HCLTECH.NS", "MARUTI.NS", "TITAN.NS",
    "SUNPHARMA.NS", "ADANIPORTS.NS", "NESTLEIND.NS", "ONGC.NS",
    "NTPC.NS", "ULTRACEMCO.NS", "AXISBANK.NS", "WIPRO.NS", "SBIN.NS"]

    shortlisted = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist_6m = stock.history(period="6mo")
            hist_1y = stock.history(period="1y")
            hist_5y = stock.history(period="5y")
            beta = stock.info.get("beta")

            def calc_return(hist):
                if len(hist) < 2: return 0
                start = hist["Close"].iloc[0]
                end = hist["Close"].iloc[-1]
                return ((end - start) / start) * 100

            r6 = calc_return(hist_6m)
            r1 = calc_return(hist_1y)
            r5 = calc_return(hist_5y)

            avg_return = (r6 + r1 + r5) / 3
            if avg_return >= thresholds["min_return"]:
                if thresholds["max_volatility"] is None or (beta and beta <= thresholds["max_volatility"]):
                    shortlisted.append(f"{ticker} ➤ AvgReturn: {round(avg_return,1)}% | Beta: {beta}")
        except:
            continue

    return ",".join([s.split(" ")[0] for s in shortlisted]) if shortlisted else "None"

