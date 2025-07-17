import yfinance as yf
from langchain.tools import tool

@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Fetches basic stock fundamentals for a given ticker symbol (e.g., AAPL)."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return str({
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "price": info.get("currentPrice"),
        "pe_ratio": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "beta": info.get("beta"),
        "roe": info.get("returnOnEquity"),
        "recommendation": info.get("recommendationKey")
    })

@tool
def compare_stocks(ticker_csv: str) -> str:
    """
    Compares multiple stocks using a comprehensive scoring model based on:
    - Valuation (PE)
    - Profitability (ROE)
    - Dividend Yield
    - Volatility (Beta)
    - EPS Growth
    - Momentum (52w)
    - Analyst Recommendation
    - Sector PE Comparison

    Input: comma-separated ticker string, e.g. "AAPL,MSFT,GOOGL"
    Output: ranked comparison with scores and breakdown.
    """
    tickers = [t.strip() for t in ticker_csv.split(",")]
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

    results = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            pe = info.get("trailingPE")
            roe = info.get("returnOnEquity")
            dy = info.get("dividendYield")
            beta = info.get("beta")
            eps_growth = info.get("earningsGrowth")
            price = info.get("currentPrice")
            high = info.get("fiftyTwoWeekHigh")
            rec = (info.get("recommendationKey") or "").lower()
            sector = info.get("sector")
            sector_pe = SECTOR_PE.get(sector)

            score = 0
            detail = {}

            # Valuation (PE)
            if pe and 0 < pe < 40:
                val_score = 20 * (40 - pe) / 40
                score += val_score
                detail["PE Score"] = round(val_score, 2)

            # ROE
            if roe:
                roe_score = 20 * roe
                score += roe_score
                detail["ROE Score"] = round(roe_score, 2)

            # Dividend
            if dy:
                div_score = 10 * dy * 100
                score += div_score
                detail["Dividend Score"] = round(div_score, 2)

            # Beta (stability)
            if beta is not None and beta < 1:
                beta_score = 10 * (1 - beta)
                score += beta_score
                detail["Beta Score"] = round(beta_score, 2)

            # EPS Growth
            if eps_growth:
                eps_score = 15 * eps_growth
                score += eps_score
                detail["EPS Growth Score"] = round(eps_score, 2)

            # Momentum
            if price and high:
                momentum_score = 10 * (price / high)
                score += momentum_score
                detail["Momentum Score"] = round(momentum_score, 2)

            # Recommendation
            rec_score = {
                "strong buy": 10,
                "buy": 7,
                "hold": 3,
                "underperform": -5,
                "sell": -10
            }.get(rec, 0)
            score += rec_score
            detail["Sentiment Score"] = rec_score

            # Sector PE comparison
            if pe and sector_pe:
                rel_pe_score = 5 if pe < sector_pe else -2
                score += rel_pe_score
                detail["Sector PE Adj"] = rel_pe_score
            # 1-Year Return
            try:
                hist = stock.history(period="1y")
                if len(hist) >= 2:
                    start_price = hist["Close"].iloc[0]
                    end_price = hist["Close"].iloc[-1]
                    one_year_return = ((end_price - start_price) / start_price) * 100           

                    if one_year_return > 30:
                        return_score = 10
                    elif one_year_return > 15:
                        return_score = 7
                    elif one_year_return > 5:
                        return_score = 4
                    elif one_year_return > 0:
                        return_score = 1
                    else:
                        return_score = 0            

                    score += return_score
                    detail["1Y Return Score"] = return_score
                    detail["1Y Return %"] = round(one_year_return, 2)
            except:
               detail["1Y Return Score"] = "NA"

            results.append({
                "ticker": ticker,
                "name": info.get("longName"),
                "score": round(score, 2),
                "breakdown": detail
            })

        except Exception as e:
            results.append({
                "ticker": ticker,
                "error": str(e)
            })

    # Sort and format output
    ranked = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    lines = []

    for r in ranked:
        if "error" in r:
            lines.append(f"{r['ticker']}: ❌ Error - {r['error']}")
        else:
            lines.append(
                f"{r['ticker']} ({r['name']}): Score {r['score']} ➤ {r['breakdown']}"
            )

    return "\n".join(lines)
