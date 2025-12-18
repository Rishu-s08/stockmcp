import asyncio
import os
from typing import TypedDict

import requests
from dotenv import load_dotenv

from mcp_define import mcp


class StockPrice(TypedDict):
    symbol: str
    week_prices: list[float]


load_dotenv()
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")


# @mcp.tool()
async def fetch_price(symbol: str) -> StockPrice:
    """Fetch recent close prices for a ticker from Alpha Vantage (TIME_SERIES_DAILY).
    Returns the seven most recent daily closes (newest first) as week_prices.
    """
    if not ALPHAVANTAGE_API_KEY:
        raise ValueError("ALPHAVANTAGE_API_KEY is not set in the environment.")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": ALPHAVANTAGE_API_KEY,
    }


    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    time_series = data.get("Time Series (Daily)")
    if not time_series:
        raise ValueError(f"No time series data returned for {symbol}: {data}")

    # dates come sorted descending when we sort keys reverse=True
    sorted_dates = sorted(time_series.keys(), reverse=True)
    closes = []
    for dt in sorted_dates[:7]:
        close_str = time_series[dt].get("4. close")
        if close_str is None:
            continue
        closes.append(float(close_str))
    if not closes:
        raise ValueError(f"No closes parsed for {symbol}: {data}")
    return StockPrice(symbol=symbol.upper(), week_prices=closes)

