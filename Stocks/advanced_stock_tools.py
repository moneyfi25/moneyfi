from langchain.tools import tool
import yfinance as yf

# EPS Growth Tool
@tool
def get_eps_growth(ticker: str) -> str:
    """Returns EPS growth for a stock (if available)."""
    stock = yf.Ticker(ticker)
    eg = stock.info.get("earningsGrowth")
    return f"{ticker} EPS growth (YoY): {eg}" if eg else f"No EPS growth data for {ticker}"

# 52-Week Momentum Tool
@tool
def get_52w_momentum(ticker: str) -> str:
    """Returns how close a stock is to its 52-week high or low."""
    stock = yf.Ticker(ticker)
    price = stock.info.get("currentPrice")
    high = stock.info.get("fiftyTwoWeekHigh")
    low = stock.info.get("fiftyTwoWeekLow")
    if not (price and high and low):
        return f"{ticker} missing 52w data"
    near_high = (price / high) * 100
    near_low = (price / low) * 100
    return f"{ticker}: Price is {near_high:.1f}% of 52w high and {near_low:.1f}% of 52w low"

# Volatility Tool
@tool
def get_volatility_label(ticker: str) -> str:
    """Classifies a stock as low/medium/high volatility based on beta."""
    beta = yf.Ticker(ticker).info.get("beta")
    if beta is None:
        return f"{ticker} beta not found"
    if beta < 0.8:
        return f"{ticker} is LOW volatility (beta {beta})"
    elif beta < 1.2:
        return f"{ticker} is MODERATE volatility (beta {beta})"
    else:
        return f"{ticker} is HIGH volatility (beta {beta})"

# Dividend Stability Tool
@tool
def get_dividend_consistency(ticker: str) -> str:
    """Checks if dividends have been paid consistently over 3+ years."""
    stock = yf.Ticker(ticker)
    div = stock.dividends
    if div.empty:
        return f"{ticker} has not paid any dividends"
    years = div.index.year.unique()
    if len(years) >= 3:
        return f"{ticker} has paid dividends for {len(years)} years consistently"
    return f"{ticker} has sporadic or recent dividend history"

# Insider Summary (placeholder)
@tool
def get_insider_summary(ticker: str) -> str:
    """(Placeholder) Returns insider activity summary — ideally from Finviz or OpenInsider."""
    return f"{ticker}: Insider activity data requires external integration (e.g., Finviz)"

# Sector P/E Benchmark Tool
SECTOR_PE = {
    "Technology": 28,
    "Financial Services": 14,
    "Consumer Defensive": 18,
    "Healthcare": 22,
    "Industrials": 17,
    "Energy": 12,
    "Consumer Cyclical": 20,
    "Utilities": 15,
}

@tool
def compare_to_sector_pe(ticker: str) -> str:
    """Checks if a stock's PE is above or below its sector average."""
    stock = yf.Ticker(ticker)
    pe = stock.info.get("trailingPE")
    sector = stock.info.get("sector")
    sector_pe = SECTOR_PE.get(sector)
    if not pe or not sector_pe:
        return f"{ticker}: Missing PE or sector data"
    status = "undervalued" if pe < sector_pe else "overvalued"
    return f"{ticker}: PE {pe} vs {sector} sector avg PE {sector_pe} → {status}"

# Analyst Sentiment Tool
@tool
def get_analyst_sentiment(ticker: str) -> str:
    """Returns OpenAI-style explanation of recommendationKey."""
    rec = yf.Ticker(ticker).info.get("recommendationKey")
    if not rec:
        return f"No recommendation data for {ticker}"
    rec = rec.lower()
    map = {
        "strong buy": "Analysts are very bullish.",
        "buy": "Analysts are optimistic.",
        "hold": "Analysts are neutral.",
        "underperform": "Analysts are cautious.",
        "sell": "Analysts expect poor performance."
    }
    return f"{ticker} sentiment: {map.get(rec, 'Unknown')}"
