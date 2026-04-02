"""
Main scheduler — ties all modules together and runs on a recurring interval.

Usage:
    python -m trading.scheduler

The scanner fetches data, evaluates signals, and fires notifications.
A local state file prevents duplicate alerts within ALERT_COOLDOWN_HOURS.
All alerts are appended to trading_alerts.json for the dashboard to read.

Logs go to stdout and trading_bot.log.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from trading import config
from trading.data.price_fetcher import fetch_hourly, fetch_daily, current_price
from trading.data.news_fetcher import fetch_articles
from trading.signals.fibonacci import check_fibonacci
from trading.signals.support_resistance import check_support_resistance
from trading.signals.sentiment import check_sentiment
from trading.engine.trade_levels import compute_trade_levels
from trading.engine.signal_combiner import combine_signals
from trading.notifiers.discord_notifier import send_discord_alert
from trading.notifiers.whatsapp_notifier import send_whatsapp_alert

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("trading_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).parent.parent
STATE_FILE = BASE_DIR / config.STATE_FILE
LOG_FILE   = BASE_DIR / config.LOG_FILE


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _load_alert_log() -> list:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return []


def _append_alert_log(payload_dict: dict) -> None:
    log = _load_alert_log()
    log.append(payload_dict)
    # Keep last 500 alerts
    LOG_FILE.write_text(json.dumps(log[-500:], indent=2))


def _is_on_cooldown(symbol: str, state: dict) -> bool:
    last_str = state.get(symbol)
    if not last_str:
        return False
    last_dt = datetime.fromisoformat(last_str)
    return datetime.now(timezone.utc) - last_dt < timedelta(hours=config.ALERT_COOLDOWN_HOURS)


def _set_cooldown(symbol: str, state: dict) -> None:
    state[symbol] = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Core scan logic
# ---------------------------------------------------------------------------

def scan_symbol(symbol: str, articles: list[dict]) -> dict | None:
    """
    Run all signal checks for *symbol* and return an alert dict if triggered,
    or None if no alert should be fired.
    """
    logger.info("Scanning %s …", symbol)

    hourly_df = fetch_hourly(symbol)
    if hourly_df.empty:
        logger.warning("No hourly data for %s — skipping", symbol)
        return None

    daily_df = fetch_daily(symbol)

    price = current_price(hourly_df)
    logger.info("%s  current price = %s", symbol, price)

    # --- Run signals ---
    fib_result = check_fibonacci(hourly_df)
    sr_result  = check_support_resistance(hourly_df, daily_df)
    sent_result = check_sentiment(
        articles,
        symbol,
        config.SYMBOL_ALIASES.get(symbol, []),
    )

    logger.info(
        "%s signals: fib=%s sr=%s sentiment=%s",
        symbol,
        fib_result.hit,
        sr_result.hit,
        sent_result.hit,
    )

    # --- Determine direction for trade levels ---
    # Use any directional signal to set up the trade math
    direction = "long"  # default
    if fib_result.hit and fib_result.direction != "none":
        direction = fib_result.direction
    elif sr_result.hit and sr_result.direction != "none":
        direction = sr_result.direction
    elif sent_result.hit and sent_result.direction != "none":
        direction = sent_result.direction

    trade = compute_trade_levels(hourly_df, direction)

    # --- Combine & decide ---
    payload = combine_signals(symbol, fib_result, sr_result, sent_result, trade)

    # Always log the scan result (even if no alert)
    scan_dict = {
        "symbol":       symbol,
        "timestamp":    payload.timestamp,
        "price":        payload.price,
        "signal_count": payload.signal_count,
        "direction":    payload.direction,
        "fib_hit":      payload.fib_hit,
        "sr_hit":       payload.sr_hit,
        "sentiment_hit":payload.sentiment_hit,
        "should_alert": payload.should_alert,
    }

    if not payload.should_alert:
        if payload.conflict:
            logger.info("%s — suppressed (conflict: %s)", symbol, payload.conflict_reason)
        else:
            logger.info(
                "%s — no alert (%d/%d signals)",
                symbol, payload.signal_count, config.SIGNAL_THRESHOLD,
            )
        return scan_dict

    return {**scan_dict, "payload": payload}


def run_scan() -> None:
    """Full scan of all watchlist symbols."""
    logger.info("=" * 60)
    logger.info("Starting scan cycle at %s UTC", datetime.now(timezone.utc).strftime("%H:%M:%S"))

    state = _load_state()

    # Fetch news once for all symbols (saves network calls)
    logger.info("Fetching RSS news …")
    articles = fetch_articles(config.RSS_FEEDS, max_age_hours=config.SENTIMENT_HOURS)
    logger.info("Fetched %d articles", len(articles))

    for symbol in config.WATCHLIST:
        try:
            result = scan_symbol(symbol, articles)
            if result is None:
                continue

            # Log scan result regardless of alert
            payload = result.get("payload")
            if payload is None:
                continue  # no alert condition

            # Cooldown check
            if _is_on_cooldown(symbol, state):
                logger.info("%s — alert suppressed (cooldown active)", symbol)
                continue

            # Fire notifications
            logger.info(
                "ALERT: %s %s — %d/%d signals fired",
                symbol, payload.direction.upper(),
                payload.signal_count, 3,
            )

            discord_ok  = send_discord_alert(config.DISCORD_WEBHOOK_URL, payload)
            whatsapp_ok = send_whatsapp_alert(payload)

            # Record alert
            alert_record = {
                "symbol":        payload.symbol,
                "timestamp":     payload.timestamp,
                "direction":     payload.direction,
                "signal_count":  payload.signal_count,
                "price":         payload.price,
                "entry":         payload.entry,
                "stop_loss":     payload.stop_loss,
                "take_profit":   payload.take_profit,
                "risk_pct":      payload.risk_pct,
                "reward_pct":    payload.reward_pct,
                "rr_ratio":      payload.rr_ratio,
                "signal_summary":payload.signal_summary,
                "fib_ratio":     payload.fib_ratio,
                "sr_zone":       payload.sr_zone,
                "sentiment_score":payload.sentiment_score,
                "discord_sent":  discord_ok,
                "whatsapp_sent": whatsapp_ok,
            }
            _append_alert_log(alert_record)
            _set_cooldown(symbol, state)

            time.sleep(0.5)  # gentle rate-limit between symbols

        except Exception as exc:
            logger.exception("Unexpected error scanning %s: %s", symbol, exc)

    _save_state(state)
    logger.info("Scan cycle complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Validate critical config
    if not config.DISCORD_WEBHOOK_URL:
        logger.warning(
            "DISCORD_WEBHOOK_URL is not set. Alerts will not be sent to Discord. "
            "Set it in your .env file."
        )

    logger.info(
        "Trading bot starting. Watchlist: %s. Scan interval: %d min.",
        config.WATCHLIST,
        config.SCAN_INTERVAL_MINUTES,
    )

    # Run once immediately on startup
    run_scan()

    # Then on a schedule
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_scan,
        "interval",
        minutes=config.SCAN_INTERVAL_MINUTES,
        id="trading_scan",
    )
    logger.info(
        "Scheduler started. Next scan in %d minutes.", config.SCAN_INTERVAL_MINUTES
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")


if __name__ == "__main__":
    main()
