"""
Entry, stop-loss, and take-profit calculation.

Uses ATR (Average True Range) on the hourly timeframe to set stop distance,
adapting to current volatility instead of a fixed pip value.

Long trade:
    entry      = current price
    stop_loss  = entry - (ATR * ATR_MULTIPLIER)
    take_profit= entry + (risk * RR_RATIO)

Short trade:
    entry      = current price
    stop_loss  = entry + (ATR * ATR_MULTIPLIER)
    take_profit= entry - (risk * RR_RATIO)
"""
from dataclasses import dataclass

import pandas as pd

from trading import config


@dataclass
class TradeLevels:
    direction: str       # "long" | "short"
    entry: float
    stop_loss: float
    take_profit: float
    risk_pct: float      # risk as % of entry
    reward_pct: float    # reward as % of entry
    atr: float
    rr_ratio: float


def calculate_atr(df: pd.DataFrame, period: int = None) -> float:
    """
    Compute ATR over *period* candles without TA-Lib.
    Returns 0.0 if data is insufficient.
    """
    period = period or config.ATR_PERIOD
    if len(df) < period + 1:
        return 0.0

    high  = df["High"]
    low   = df["Low"]
    close = df["Close"]

    tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low  - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return float(tr.rolling(period).mean().iloc[-1])


def compute_trade_levels(
    df: pd.DataFrame,
    direction: str,
    atr_multiplier: float = None,
    rr_ratio: float = None,
) -> TradeLevels:
    """
    Compute entry, stop-loss, and take-profit for *direction*.

    Args:
        df            : hourly OHLCV DataFrame
        direction     : "long" or "short"
        atr_multiplier: override config.ATR_MULTIPLIER
        rr_ratio      : override config.RR_RATIO

    Returns a TradeLevels dataclass.
    """
    atr_multiplier = atr_multiplier or config.ATR_MULTIPLIER
    rr_ratio       = rr_ratio       or config.RR_RATIO

    entry = float(df["Close"].iloc[-1])
    atr   = calculate_atr(df, config.ATR_PERIOD)

    # Fallback: use 1% of price when ATR cannot be calculated
    if atr == 0.0:
        atr = entry * 0.01

    risk = atr * atr_multiplier

    if direction == "long":
        stop_loss   = entry - risk
        take_profit = entry + risk * rr_ratio
    else:
        stop_loss   = entry + risk
        take_profit = entry - risk * rr_ratio

    risk_pct   = abs(entry - stop_loss)   / entry * 100
    reward_pct = abs(take_profit - entry) / entry * 100

    return TradeLevels(
        direction=direction,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_pct=risk_pct,
        reward_pct=reward_pct,
        atr=atr,
        rr_ratio=rr_ratio,
    )
