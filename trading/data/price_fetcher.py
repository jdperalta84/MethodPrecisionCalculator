"""
Price data retrieval via yfinance (free, no API key required).

Two timeframes are used:
  - 1h  candles → live signal detection (Fib, ATR, current price)
  - 1d  candles → support/resistance pivot detection (cleaner pivots)
"""
import logging
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_ohlcv(
    symbol: str,
    interval: str = "1h",
    period: str = "60d",
    retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for *symbol* at *interval* going back *period*.

    Returns an empty DataFrame on failure rather than raising, so callers
    can handle missing data gracefully.
    """
    for attempt in range(1, retries + 1):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(interval=interval, period=period, auto_adjust=True)
            if df.empty:
                logger.warning("Empty data for %s (%s, %s)", symbol, interval, period)
                return pd.DataFrame()
            df.dropna(inplace=True)
            df.index = pd.to_datetime(df.index, utc=True)
            return df
        except Exception as exc:
            logger.warning(
                "Attempt %d/%d failed for %s: %s", attempt, retries, symbol, exc
            )
            if attempt < retries:
                time.sleep(2 ** attempt)  # 2s, 4s backoff
    return pd.DataFrame()


def fetch_hourly(symbol: str) -> pd.DataFrame:
    """60 days of 1h candles — used for Fib levels, ATR, current price."""
    return fetch_ohlcv(symbol, interval="1h", period="60d")


def fetch_daily(symbol: str) -> pd.DataFrame:
    """90 days of daily candles — used for support/resistance pivots."""
    return fetch_ohlcv(symbol, interval="1d", period="90d")


def current_price(df: pd.DataFrame) -> float | None:
    """Return the most recent close price from an OHLCV DataFrame."""
    if df.empty:
        return None
    return float(df["Close"].iloc[-1])
