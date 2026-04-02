"""
Discord notification via webhook.

Sends a rich embed with color-coded direction, price levels, and signal details.
No Discord bot token required — just a webhook URL set in DISCORD_WEBHOOK_URL.

Webhook setup:
  1. Open Discord channel → Edit channel → Integrations → Webhooks → New Webhook
  2. Copy the webhook URL
  3. Set DISCORD_WEBHOOK_URL=<url> in your .env file
"""
import logging
from typing import Optional

import requests

from trading.engine.signal_combiner import AlertPayload

logger = logging.getLogger(__name__)

# Embed colors
COLOR_LONG    = 0x3FB950  # green
COLOR_SHORT   = 0xF85149  # red
COLOR_NEUTRAL = 0x8B949E  # grey


def _build_embed(payload: AlertPayload) -> dict:
    color = COLOR_LONG if payload.direction == "long" else COLOR_SHORT

    direction_label = payload.direction.upper()
    title = f"{'🟢' if payload.direction == 'long' else '🔴'} {direction_label} Signal — {payload.symbol}  ({payload.signal_count}/3 signals)"

    fields = [
        {"name": "Price",       "value": f"`${payload.price:.4f}`",        "inline": True},
        {"name": "Entry",       "value": f"`${payload.entry:.4f}`",        "inline": True},
        {"name": "\u200b",      "value": "\u200b",                         "inline": True},  # spacer
        {
            "name": "Stop Loss",
            "value": f"`${payload.stop_loss:.4f}`  (-{payload.risk_pct:.2f}%)",
            "inline": True,
        },
        {
            "name": "Take Profit",
            "value": f"`${payload.take_profit:.4f}`  (+{payload.reward_pct:.2f}%)",
            "inline": True,
        },
        {
            "name": "R:R",
            "value": f"`{payload.rr_ratio:.1f}:1`",
            "inline": True,
        },
        {
            "name": "Signals Fired",
            "value": payload.signal_summary or "—",
            "inline": False,
        },
        {
            "name": "ATR (14h)",
            "value": f"`{payload.atr:.4f}`",
            "inline": True,
        },
    ]

    if payload.top_headlines:
        headlines_text = "\n".join(f"• {h[:120]}" for h in payload.top_headlines)
        fields.append({
            "name": "Recent Headlines",
            "value": headlines_text,
            "inline": False,
        })

    embed = {
        "title": title,
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"Trading Bot  •  {payload.timestamp} UTC  •  Data: Yahoo Finance / RSS"
        },
    }
    return embed


def send_discord_alert(webhook_url: str, payload: AlertPayload) -> bool:
    """
    POST a rich embed to a Discord webhook.

    Returns True on success (HTTP 204), False otherwise.
    Logs warnings on failure but never raises.
    """
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set — skipping Discord notification")
        return False

    embed = _build_embed(payload)
    try:
        resp = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10,
        )
        if resp.status_code == 204:
            logger.info("Discord alert sent for %s (%s)", payload.symbol, payload.direction)
            return True
        logger.warning(
            "Discord webhook returned %d: %s", resp.status_code, resp.text[:200]
        )
        return False
    except requests.RequestException as exc:
        logger.error("Discord webhook request failed: %s", exc)
        return False
