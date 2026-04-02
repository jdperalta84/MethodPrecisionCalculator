"""
News sentiment signal.

Wraps the raw news_fetcher score into a structured result and applies
the bullish/bearish thresholds from config.
"""
from dataclasses import dataclass, field

from trading import config
from trading.data.news_fetcher import score_sentiment


@dataclass
class SentimentResult:
    hit: bool
    direction: str       # "long" (bullish) | "short" (bearish) | "none"
    label: str           # "bullish" | "bearish" | "neutral"
    score: float         # mean VADER compound score in [-1, 1]
    article_count: int
    articles: list[dict] = field(default_factory=list)
    note: str = ""


def check_sentiment(
    articles: list[dict],
    symbol: str,
    aliases: list[str],
) -> SentimentResult:
    """
    Evaluate news sentiment for *symbol* using pre-fetched *articles*.
    Requires at least SENTIMENT_MIN_ARTICLES matching articles to fire.
    """
    mean_score, count, scored = score_sentiment(articles, symbol, aliases)

    if count < config.SENTIMENT_MIN_ARTICLES:
        return SentimentResult(
            hit=False,
            direction="none",
            label="neutral",
            score=mean_score,
            article_count=count,
            articles=scored,
            note=f"Only {count} matching articles (need {config.SENTIMENT_MIN_ARTICLES})",
        )

    if mean_score >= config.SENTIMENT_BULL_THRESH:
        label, direction = "bullish", "long"
        hit = True
    elif mean_score <= config.SENTIMENT_BEAR_THRESH:
        label, direction = "bearish", "short"
        hit = True
    else:
        label, direction = "neutral", "none"
        hit = False

    return SentimentResult(
        hit=hit,
        direction=direction,
        label=label,
        score=mean_score,
        article_count=count,
        articles=scored,
        note=f"{count} articles, mean score {mean_score:.3f}",
    )
