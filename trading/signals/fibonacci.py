"""
Fibonacci retracement signal.

Detects whether the current price is within a tolerance band of a key
Fibonacci level derived from the recent swing high and swing low.

Also determines trend direction (up vs down) from a 50-period SMA slope
so we know which retracement set is "active":
  - Uptrend  → price retracing down toward a Fib support
  - Downtrend → price bouncing up toward a Fib resistance
"""
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from trading import config


@dataclass
class FibResult:
    hit: bool
    direction: str          # "long" | "short" | "none"
    ratio: Optional[float]
    level_price: Optional[float]
    swing_high: float
    swing_low: float
    all_levels: dict[float, float] = field(default_factory=dict)
    note: str = ""


def _swing_high_low(df: pd.DataFrame, lookback: int) -> tuple[float, float]:
    """Return (swing_high, swing_low) from the last *lookback* candles."""
    window = df.tail(lookback)
    return float(window["High"].max()), float(window["Low"].min())


def _trend_direction(df: pd.DataFrame, sma_period: int = 50) -> str:
    """
    Return 'up' or 'down' based on the slope of the SMA over the last
    *sma_period* candles.
    """
    if len(df) < sma_period + 1:
        return "up"  # default to uptrend on insufficient data
    sma = df["Close"].rolling(sma_period).mean()
    recent = sma.dropna()
    if len(recent) < 2:
        return "up"
    return "up" if float(recent.iloc[-1]) >= float(recent.iloc[-sma_period // 2]) else "down"


def compute_fib_levels(
    swing_high: float,
    swing_low: float,
    trend: str,
) -> dict[float, float]:
    """
    Calculate Fibonacci retracement levels.

    In an uptrend the levels act as support (price retracing from high).
    In a downtrend the levels act as resistance (price bouncing from low).
    """
    diff = swing_high - swing_low
    if trend == "up":
        return {r: swing_high - diff * r for r in config.FIB_RATIOS}
    else:
        return {r: swing_low + diff * r for r in config.FIB_RATIOS}


def check_fibonacci(df: pd.DataFrame) -> FibResult:
    """
    Main entry point. Returns a FibResult for the latest price.
    """
    if df.empty or len(df) < config.FIB_LOOKBACK_CANDLES:
        return FibResult(
            hit=False, direction="none", ratio=None,
            level_price=None, swing_high=0.0, swing_low=0.0,
            note="insufficient data",
        )

    price = float(df["Close"].iloc[-1])
    swing_high, swing_low = _swing_high_low(df, config.FIB_LOOKBACK_CANDLES)
    trend = _trend_direction(df)
    levels = compute_fib_levels(swing_high, swing_low, trend)

    # Check proximity
    hit_ratio: Optional[float] = None
    hit_price: Optional[float] = None
    for ratio, level in sorted(levels.items()):
        if abs(price - level) / price <= config.FIB_PROXIMITY_PCT:
            hit_ratio = ratio
            hit_price = level
            break  # take the closest hit

    hit = hit_ratio is not None
    direction = ("long" if trend == "up" else "short") if hit else "none"

    return FibResult(
        hit=hit,
        direction=direction,
        ratio=hit_ratio,
        level_price=hit_price,
        swing_high=swing_high,
        swing_low=swing_low,
        all_levels=levels,
        note=f"Trend: {trend}, Price: {price:.4f}",
    )
