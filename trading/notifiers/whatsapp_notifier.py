"""
WhatsApp notification via Twilio (optional).

Only activates when ALL four Twilio env vars are set:
  TWILIO_ACCOUNT_SID
  TWILIO_AUTH_TOKEN
  TWILIO_WHATSAPP_FROM   (e.g. whatsapp:+14155238886)
  TWILIO_WHATSAPP_TO     (e.g. whatsapp:+1XXXXXXXXXX)

If any are missing, send_whatsapp_alert() is a no-op that returns False.

Twilio free trial notes:
  - Free sandbox requires the recipient to first send "join <sandbox-word>"
    to the Twilio sandbox number before receiving messages.
  - Paid plans use a dedicated number or WhatsApp Business API.

Setup:
  1. Create a Twilio account at https://www.twilio.com
  2. Enable the WhatsApp Sandbox in the Twilio Console
  3. Follow sandbox join instructions with your phone
  4. Copy credentials into your .env file
"""
import logging
import os

from trading.engine.signal_combiner import AlertPayload

logger = logging.getLogger(__name__)


def _twilio_available() -> bool:
    return all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_WHATSAPP_FROM"),
        os.getenv("TWILIO_WHATSAPP_TO"),
    ])


def _format_message(payload: AlertPayload) -> str:
    direction_emoji = "🟢" if payload.direction == "long" else "🔴"
    lines = [
        f"{direction_emoji} *{payload.direction.upper()} Signal — {payload.symbol}*",
        f"Signals: {payload.signal_count}/3  |  {payload.timestamp} UTC",
        "",
        f"💰 Entry:       ${payload.entry:.4f}",
        f"🛑 Stop Loss:   ${payload.stop_loss:.4f}  (-{payload.risk_pct:.2f}%)",
        f"🎯 Take Profit: ${payload.take_profit:.4f}  (+{payload.reward_pct:.2f}%)",
        f"📊 R:R Ratio:   {payload.rr_ratio:.1f}:1",
        "",
        f"Signals: {payload.signal_summary}",
    ]
    if payload.top_headlines:
        lines.append("")
        lines.append("📰 Headlines:")
        for h in payload.top_headlines[:2]:
            lines.append(f"• {h[:100]}")
    return "\n".join(lines)


def send_whatsapp_alert(payload: AlertPayload) -> bool:
    """
    Send a WhatsApp message via Twilio.

    Returns True on success, False if Twilio is not configured or on error.
    """
    if not _twilio_available():
        logger.debug("Twilio env vars not set — WhatsApp notification skipped")
        return False

    try:
        from twilio.rest import Client  # noqa: import-outside-toplevel

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_FROM")
        to_number   = os.getenv("TWILIO_WHATSAPP_TO")

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=_format_message(payload),
            from_=from_number,
            to=to_number,
        )
        logger.info(
            "WhatsApp alert sent for %s, SID=%s", payload.symbol, message.sid
        )
        return True
    except ImportError:
        logger.warning("twilio package not installed — WhatsApp notification skipped")
        return False
    except Exception as exc:
        logger.error("WhatsApp notification failed: %s", exc)
        return False
