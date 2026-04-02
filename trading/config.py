"""
Central configuration for the trading notification app.
All tunables live here — no magic numbers scattered in modules.
Copy .env.example to .env and fill in your webhook URLs before running.
"""
import os

# ---------------------------------------------------------------------------
# Watchlist — symbols to scan each cycle
# ---------------------------------------------------------------------------
WATCHLIST = [
    "AAPL",    # Apple
    "TSLA",    # Tesla
    "SPY",     # S&P 500 ETF
    "NVDA",    # NVIDIA
    "BTC-USD", # Bitcoin
    "ETH-USD", # Ethereum
]

# Human-readable aliases used for news matching (keyed by symbol)
SYMBOL_ALIASES: dict[str, list[str]] = {
    "AAPL":    ["Apple", "Apple Inc"],
    "TSLA":    ["Tesla", "Tesla Inc", "Elon Musk"],
    "SPY":     ["S&P 500", "SPY", "S&P500", "stock market", "equity market"],
    "NVDA":    ["NVIDIA", "Nvidia", "Jensen Huang"],
    "BTC-USD": ["Bitcoin", "BTC", "crypto", "cryptocurrency"],
    "ETH-USD": ["Ethereum", "ETH", "crypto", "cryptocurrency"],
}

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
SCAN_INTERVAL_MINUTES = 10   # how often to run a full scan

# ---------------------------------------------------------------------------
# Fibonacci settings
# ---------------------------------------------------------------------------
FIB_LOOKBACK_CANDLES = 50    # candles (1h) to detect swing high/low
FIB_PROXIMITY_PCT    = 0.005 # ±0.5% band around each level counts as a hit
FIB_RATIOS           = [0.236, 0.382, 0.5, 0.618, 0.786]

# ---------------------------------------------------------------------------
# Support / Resistance settings
# ---------------------------------------------------------------------------
SR_LOOKBACK_DAYS  = 60       # daily candles for pivot detection
SR_PIVOT_LEFT     = 3        # candles to the left of a pivot
SR_PIVOT_RIGHT    = 3        # candles to the right of a pivot
SR_CLUSTER_PCT    = 0.003    # cluster pivots within 0.3% of each other
SR_PROXIMITY_PCT  = 0.005    # ±0.5% around an S/R zone counts as a hit

# ---------------------------------------------------------------------------
# News / Sentiment settings
# ---------------------------------------------------------------------------
SENTIMENT_HOURS        = 6   # only consider articles from the last N hours
SENTIMENT_MIN_ARTICLES = 2   # need at least this many matching articles
SENTIMENT_BULL_THRESH  =  0.08  # compound score above this = bullish
SENTIMENT_BEAR_THRESH  = -0.08  # compound score below this = bearish

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://finance.yahoo.com/rss/topstories",
    "https://feeds.marketwatch.com/marketwatch/topstories",
    "https://search.cnbc.com/rs/search/combinedcombined/rss/?partnerId=wrss01&id=100003114",
    "https://www.investing.com/rss/news.rss",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets
]

# ---------------------------------------------------------------------------
# Trade levels
# ---------------------------------------------------------------------------
ATR_PERIOD      = 14   # periods for ATR calculation
ATR_MULTIPLIER  = 1.5  # stop distance = ATR * multiplier
RR_RATIO        = 2.0  # take-profit = risk * RR_RATIO

# ---------------------------------------------------------------------------
# Signal combination
# ---------------------------------------------------------------------------
SIGNAL_THRESHOLD     = 2    # require at least N of 3 signals to fire an alert
ALERT_COOLDOWN_HOURS = 1    # suppress duplicate alerts for the same symbol

# ---------------------------------------------------------------------------
# Notification — loaded from environment variables
# ---------------------------------------------------------------------------
DISCORD_WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK_URL", "")

# WhatsApp via Twilio (optional — leave blank to disable)
TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER   = os.getenv("TWILIO_WHATSAPP_FROM", "")  # e.g. whatsapp:+14155238886
TWILIO_TO_NUMBER     = os.getenv("TWILIO_WHATSAPP_TO", "")    # e.g. whatsapp:+1XXXXXXXXXX

# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------
STATE_FILE = "trading_state.json"   # tracks last alert times per symbol
LOG_FILE   = "trading_alerts.json"  # persistent alert history for dashboard
