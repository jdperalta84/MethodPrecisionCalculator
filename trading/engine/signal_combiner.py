"""
Signal combiner — the core decision engine.

Receives results from the three signal modules and decides:
  1. How many signals fired.
  2. Whether directions are consistent (long / short / conflicted).
  3. Whether to fire an alert.

Direction resolution rules:
  - Fib and S/R signals both have directional opinions; they must agree.
  - Sentiment can be "none" (neutral) and still allow the alert.
  - If Fib and S/R disagree → suppress alert (conflicted).
  - If only one of Fib/S/R hit, use that as the primary direction.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from trading import config
from trading.signals.fibonacci import FibResult
from trading.signals.support_resistance import SRResult
from trading.signals.sentiment import SentimentResult
from trading.engine.trade_levels import TradeLevels


@dataclass
class AlertPayload:
    symbol: str
    timestamp: str
    direction: str              # "long" | "short"
    signal_count: int
    should_alert: bool

    # Price levels
    price: float
    entry: float
    stop_loss: float
    take_profit: float
    risk_pct: float
    reward_pct: float
    rr_ratio: float
    atr: float

    # Signal details
    fib_hit: bool
    fib_ratio: Optional[float]
    fib_level: Optional[float]

    sr_hit: bool
    sr_zone: Optional[float]
    sr_zone_type: str

    sentiment_hit: bool
    sentiment_label: str
    sentiment_score: float
    sentiment_articles: int

    # Human-readable summary
    signal_summary: str
    top_headlines: list[str] = field(default_factory=list)

    conflict: bool = False
    conflict_reason: str = ""


def _resolve_direction(
    fib: FibResult, sr: SRResult, sentiment: SentimentResult
) -> tuple[str, bool, str]:
    """
    Determine consensus trade direction from the three signals.

    Returns: (direction, is_conflict, reason)
    """
    directions = []
    if fib.hit and fib.direction != "none":
        directions.append(("fib", fib.direction))
    if sr.hit and sr.direction != "none":
        directions.append(("sr", sr.direction))
    if sentiment.hit and sentiment.direction != "none":
        directions.append(("sentiment", sentiment.direction))

    if not directions:
        return "none", False, "no directional signals"

    # Check for conflicts between Fib and S/R (the two price-based signals)
    price_dirs = {src: d for src, d in directions if src in ("fib", "sr")}
    if len(price_dirs) == 2:
        vals = list(price_dirs.values())
        if vals[0] != vals[1]:
            return "none", True, "Fib and S/R point in opposite directions"

    # Majority vote
    long_count  = sum(1 for _, d in directions if d == "long")
    short_count = sum(1 for _, d in directions if d == "short")

    if long_count > short_count:
        return "long", False, ""
    if short_count > long_count:
        return "short", False, ""

    # Tie → defer to Fib direction if available
    if fib.hit and fib.direction != "none":
        return fib.direction, False, "tie broken by Fib"

    return "none", False, "directional tie"


def _build_signal_summary(
    fib: FibResult, sr: SRResult, sentiment: SentimentResult
) -> str:
    parts = []
    if fib.hit:
        pct = f"{fib.ratio*100:.1f}%" if fib.ratio else "unknown"
        parts.append(f"Fib {pct}")
    if sr.hit:
        parts.append(f"{sr.zone_type.title()} zone @ {sr.zone_price:.2f}")
    if sentiment.hit:
        parts.append(f"Sentiment: {sentiment.label} ({sentiment.score:+.2f})")
    return " | ".join(parts) if parts else "No signals"


def combine_signals(
    symbol: str,
    fib: FibResult,
    sr: SRResult,
    sentiment: SentimentResult,
    trade: TradeLevels,
    threshold: int = None,
) -> AlertPayload:
    """
    Combine all three signal results into an AlertPayload.

    *threshold* defaults to config.SIGNAL_THRESHOLD (2 of 3).
    """
    threshold = threshold or config.SIGNAL_THRESHOLD
    signal_count = int(fib.hit) + int(sr.hit) + int(sentiment.hit)
    direction, conflict, conflict_reason = _resolve_direction(fib, sr, sentiment)

    should_alert = (signal_count >= threshold) and (not conflict) and (direction != "none")

    top_headlines = [
        a["title"] for a in sentiment.articles[:3]
    ] if sentiment.articles else []

    return AlertPayload(
        symbol=symbol,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        direction=direction,
        signal_count=signal_count,
        should_alert=should_alert,

        price=trade.entry,
        entry=trade.entry,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        risk_pct=trade.risk_pct,
        reward_pct=trade.reward_pct,
        rr_ratio=trade.rr_ratio,
        atr=trade.atr,

        fib_hit=fib.hit,
        fib_ratio=fib.ratio,
        fib_level=fib.level_price,

        sr_hit=sr.hit,
        sr_zone=sr.zone_price,
        sr_zone_type=sr.zone_type,

        sentiment_hit=sentiment.hit,
        sentiment_label=sentiment.label,
        sentiment_score=sentiment.score,
        sentiment_articles=sentiment.article_count,

        signal_summary=_build_signal_summary(fib, sr, sentiment),
        top_headlines=top_headlines,
        conflict=conflict,
        conflict_reason=conflict_reason,
    )
