"""
News retrieval from free RSS feeds — no API key required.

Uses feedparser for RSS parsing and vaderSentiment for scoring.
Each feed is fetched independently; failures are logged and skipped
so a single broken feed never kills the whole scan.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

_analyzer = SentimentIntensityAnalyzer()


def _parse_published(entry) -> Optional[datetime]:
    """Convert feedparser's published_parsed tuple to a tz-aware datetime."""
    raw = entry.get("published_parsed") or entry.get("updated_parsed")
    if raw is None:
        return None
    try:
        return datetime(*raw[:6], tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_articles(feeds: list[str], max_age_hours: int = 6) -> list[dict]:
    """
    Fetch articles from all *feeds* published within *max_age_hours*.

    Returns a list of dicts with keys: title, summary, published, url.
    Silently skips feeds that time-out or return errors.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    articles: list[dict] = []

    for url in feeds:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "TradingBot/1.0"})
            for entry in feed.entries:
                pub = _parse_published(entry)
                if pub is None or pub < cutoff:
                    continue
                articles.append(
                    {
                        "title":     entry.get("title", ""),
                        "summary":   entry.get("summary", ""),
                        "published": pub,
                        "url":       entry.get("link", ""),
                        "source":    feed.feed.get("title", url),
                    }
                )
        except Exception as exc:
            logger.warning("Feed fetch failed for %s: %s", url, exc)

    # Deduplicate by title
    seen: set[str] = set()
    unique: list[dict] = []
    for a in articles:
        key = a["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(a)

    logger.debug("Fetched %d unique articles from %d feeds", len(unique), len(feeds))
    return unique


def filter_articles(
    articles: list[dict], symbol: str, aliases: list[str]
) -> list[dict]:
    """Return articles that mention *symbol* or any of its *aliases*."""
    terms = {t.upper() for t in ([symbol] + aliases)}
    matched = []
    for a in articles:
        text = (a["title"] + " " + a["summary"]).upper()
        if any(t in text for t in terms):
            matched.append(a)
    return matched


def score_sentiment(
    articles: list[dict], symbol: str, aliases: list[str]
) -> tuple[float, int, list[dict]]:
    """
    Score sentiment for articles matching *symbol* / *aliases*.

    Returns:
        mean_compound   - float in [-1, 1]; positive = bullish
        article_count   - number of matching articles scored
        scored_articles - list of dicts with added 'compound' key
    """
    matched = filter_articles(articles, symbol, aliases)
    scored = []
    for a in matched:
        text = a["title"] + ". " + a["summary"]
        vs = _analyzer.polarity_scores(text)
        scored.append({**a, "compound": vs["compound"]})

    if not scored:
        return 0.0, 0, []

    mean_score = sum(s["compound"] for s in scored) / len(scored)
    return mean_score, len(scored), scored
