"""
Support / Resistance signal via pivot point detection.

Algorithm:
  1. Find pivot highs and lows on daily OHLCV data (5-bar rule).
  2. Cluster nearby pivots (within SR_CLUSTER_PCT of each other).
  3. Check whether the current price is within SR_PROXIMITY_PCT of any cluster.
  4. Classify the zone as support (below price) or resistance (above price).
"""
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from trading import config


@dataclass
class SRResult:
    hit: bool
    direction: str             # "long" (support) | "short" (resistance) | "none"
    zone_price: Optional[float]
    zone_type: str             # "support" | "resistance" | "none"
    all_zones: list[float] = field(default_factory=list)
    note: str = ""


def _find_pivot_highs(df: pd.DataFrame, left: int, right: int) -> list[float]:
    highs = []
    for i in range(left, len(df) - right):
        window = df["High"].iloc[i - left: i + right + 1]
        if df["High"].iloc[i] == window.max():
            highs.append(float(df["High"].iloc[i]))
    return highs


def _find_pivot_lows(df: pd.DataFrame, left: int, right: int) -> list[float]:
    lows = []
    for i in range(left, len(df) - right):
        window = df["Low"].iloc[i - left: i + right + 1]
        if df["Low"].iloc[i] == window.min():
            lows.append(float(df["Low"].iloc[i]))
    return lows


def _cluster_levels(levels: list[float], tolerance_pct: float) -> list[float]:
    """Merge price levels within *tolerance_pct* of each other into clusters."""
    if not levels:
        return []
    sorted_levels = sorted(levels)
    clusters: list[float] = [sorted_levels[0]]
    for price in sorted_levels[1:]:
        if abs(price - clusters[-1]) / clusters[-1] <= tolerance_pct:
            clusters[-1] = (clusters[-1] + price) / 2  # running average
        else:
            clusters.append(price)
    return clusters


def compute_sr_zones(daily_df: pd.DataFrame) -> list[float]:
    """Return a sorted list of clustered S/R price levels."""
    if daily_df.empty:
        return []

    pivot_highs = _find_pivot_highs(daily_df, config.SR_PIVOT_LEFT, config.SR_PIVOT_RIGHT)
    pivot_lows  = _find_pivot_lows(daily_df,  config.SR_PIVOT_LEFT, config.SR_PIVOT_RIGHT)
    all_pivots  = pivot_highs + pivot_lows
    return _cluster_levels(all_pivots, config.SR_CLUSTER_PCT)


def check_support_resistance(
    hourly_df: pd.DataFrame, daily_df: pd.DataFrame
) -> SRResult:
    """
    Main entry point. Returns a SRResult for the latest price.
    """
    if hourly_df.empty or daily_df.empty:
        return SRResult(hit=False, direction="none", zone_price=None,
                        zone_type="none", note="insufficient data")

    price = float(hourly_df["Close"].iloc[-1])
    zones = compute_sr_zones(daily_df)

    if not zones:
        return SRResult(hit=False, direction="none", zone_price=None,
                        zone_type="none", all_zones=[], note="no pivots found")

    # Find the closest zone
    closest: Optional[float] = min(zones, key=lambda z: abs(z - price))
    distance_pct = abs(price - closest) / price

    if distance_pct > config.SR_PROXIMITY_PCT:
        return SRResult(
            hit=False, direction="none", zone_price=closest,
            zone_type="none", all_zones=zones,
            note=f"Nearest zone {closest:.4f} is {distance_pct*100:.2f}% away",
        )

    zone_type = "support" if closest <= price else "resistance"
    direction  = "long" if zone_type == "support" else "short"

    return SRResult(
        hit=True,
        direction=direction,
        zone_price=closest,
        zone_type=zone_type,
        all_zones=zones,
        note=f"Price {price:.4f} near {zone_type} at {closest:.4f}",
    )
