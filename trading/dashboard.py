"""
Streamlit dashboard for the trading notification app.

Run alongside the scheduler (separate terminal):
    streamlit run trading/dashboard.py

Shows:
  - Live signal status for each watchlist symbol (refreshes every 60s)
  - Alert history table with entry/exit levels
  - Fibonacci levels chart on a price chart
  - Config overview

Matches the existing dark GitHub-inspired theme used in tolerance_calculator_web.py.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Trading Signal Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme — matches existing tolerance_calculator_web.py dark theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
    }
    code, pre, .stCode { font-family: 'DM Mono', monospace; }

    .stApp { background-color: #0d1117; }

    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }
    .signal-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: 'DM Mono', monospace;
    }
    .badge-long    { background: #1a4731; color: #3fb950; border: 1px solid #238636; }
    .badge-short   { background: #4d0f13; color: #f85149; border: 1px solid #da3633; }
    .badge-neutral { background: #1c2128; color: #8b949e; border: 1px solid #30363d; }

    .stDataFrame { background: #161b22; }
    div[data-testid="stMetricValue"] { color: #58a6ff; font-family: 'DM Mono', monospace; }
    div[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace; }

    h1, h2, h3 { color: #e6edf3; font-family: 'Sora', sans-serif; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
    .stButton button {
        background: #238636; color: #fff; border: none; border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).parent.parent
LOG_FILE   = BASE_DIR / "trading_alerts.json"
STATE_FILE = BASE_DIR / "trading_state.json"

WATCHLIST_DEFAULT = ["AAPL", "TSLA", "SPY", "NVDA", "BTC-USD", "ETH-USD"]


@st.cache_data(ttl=60)
def load_alert_log() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    try:
        return json.loads(LOG_FILE.read_text())
    except Exception:
        return []


@st.cache_data(ttl=60)
def load_price_data(symbol: str) -> pd.DataFrame:
    """Load 1h OHLCV for the mini chart — cached for 60s."""
    try:
        import yfinance as yf
        df = yf.Ticker(symbol).history(interval="1h", period="5d", auto_adjust=True)
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def direction_badge(direction: str) -> str:
    if direction == "long":
        return '<span class="signal-badge badge-long">LONG</span>'
    if direction == "short":
        return '<span class="signal-badge badge-short">SHORT</span>'
    return '<span class="signal-badge badge-neutral">—</span>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Trading Monitor")
    st.caption("Real-time signal tracker")

    st.markdown("---")
    st.subheader("Settings")

    signal_threshold = st.slider(
        "Alert threshold (signals required)",
        min_value=1, max_value=3, value=2,
        help="Number of signals that must align to trigger an alert.",
    )
    cooldown_hours = st.number_input(
        "Alert cooldown (hours)", min_value=0.5, max_value=24.0, value=1.0, step=0.5
    )
    auto_refresh = st.checkbox("Auto-refresh every 60s", value=True)

    st.markdown("---")
    st.subheader("Watchlist")
    watchlist_input = st.text_area(
        "Symbols (one per line)",
        value="\n".join(WATCHLIST_DEFAULT),
        height=150,
    )
    watchlist = [s.strip().upper() for s in watchlist_input.splitlines() if s.strip()]

    st.markdown("---")
    st.caption(f"Last page load: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_live, tab_history, tab_chart, tab_about = st.tabs(
    ["Live Signals", "Alert History", "Price Chart", "About"]
)

# ---- TAB 1: Live Signals ---------------------------------------------------
with tab_live:
    st.header("Live Signal Status")
    st.caption("Signals are evaluated by the running scheduler. This view reflects the last scan.")

    alerts = load_alert_log()
    state  = load_state()

    # Build a per-symbol summary from the latest alert log entry
    latest_per_symbol: dict[str, dict] = {}
    for a in alerts:
        sym = a.get("symbol", "")
        if sym not in latest_per_symbol:
            latest_per_symbol[sym] = a

    cols = st.columns(3)
    for idx, symbol in enumerate(watchlist):
        col = cols[idx % 3]
        with col:
            rec = latest_per_symbol.get(symbol)
            last_alert_str = state.get(symbol, "Never")

            with st.container():
                st.markdown(f"### {symbol}")
                if rec:
                    price      = rec.get("price", 0)
                    direction  = rec.get("direction", "none")
                    sig_count  = rec.get("signal_count", 0)
                    timestamp  = rec.get("timestamp", "—")

                    st.markdown(direction_badge(direction), unsafe_allow_html=True)
                    st.metric("Price",        f"${price:,.4f}")
                    st.metric("Signals",      f"{sig_count}/3")

                    if rec.get("should_alert"):
                        st.metric("Entry",       f"${rec.get('entry', 0):,.4f}")
                        st.metric("Stop Loss",   f"${rec.get('stop_loss', 0):,.4f}")
                        st.metric("Take Profit", f"${rec.get('take_profit', 0):,.4f}")

                    st.caption(f"Last scan: {timestamp}")
                else:
                    st.markdown(
                        '<span class="signal-badge badge-neutral">No data yet</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption("Waiting for first scan cycle…")

    if auto_refresh:
        time.sleep(0)  # just trigger re-run below
        st.caption("Auto-refresh active. Page will reload every 60 seconds.")
        st.markdown(
            '<meta http-equiv="refresh" content="60">',
            unsafe_allow_html=True,
        )

# ---- TAB 2: Alert History --------------------------------------------------
with tab_history:
    st.header("Alert History")

    alerts = load_alert_log()
    if not alerts:
        st.info("No alerts have been fired yet. Start the scheduler to begin scanning.")
    else:
        df = pd.DataFrame(alerts)
        display_cols = [
            "timestamp", "symbol", "direction", "signal_count",
            "price", "entry", "stop_loss", "take_profit",
            "risk_pct", "reward_pct", "rr_ratio", "signal_summary",
        ]
        existing_cols = [c for c in display_cols if c in df.columns]
        df_display = df[existing_cols].copy()

        # Format numeric columns
        for col in ["price", "entry", "stop_loss", "take_profit"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].map(lambda x: f"${x:,.4f}" if pd.notna(x) else "—")
        for col in ["risk_pct", "reward_pct"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "—")

        df_display = df_display.sort_values("timestamp", ascending=False)
        st.dataframe(df_display, use_container_width=True, height=500)

        st.metric("Total alerts fired", len(alerts))

        # Download button
        csv = df_display.to_csv(index=False)
        st.download_button(
            "Download CSV", csv, "trading_alerts.csv", "text/csv"
        )

# ---- TAB 3: Price Chart ----------------------------------------------------
with tab_chart:
    st.header("Price Chart with Levels")

    selected = st.selectbox("Symbol", watchlist, index=0)

    with st.spinner(f"Loading {selected} price data…"):
        price_df = load_price_data(selected)

    if price_df.empty:
        st.warning("Could not load price data for this symbol.")
    else:
        # Compute Fibonacci and S/R levels to overlay
        try:
            from trading.signals.fibonacci import check_fibonacci, compute_fib_levels, _trend_direction, _swing_high_low
            from trading.signals.support_resistance import compute_sr_zones
            from trading.data.price_fetcher import fetch_daily

            fib_res     = check_fibonacci(price_df)
            daily_df    = fetch_daily(selected)
            sr_zones    = compute_sr_zones(daily_df) if not daily_df.empty else []

            # Build chart data
            chart_df = price_df[["Close"]].copy()
            chart_df.index = pd.to_datetime(chart_df.index)

            st.subheader(f"{selected} — 1h Close Price (last 5 days)")
            st.line_chart(chart_df["Close"])

            # Show Fibonacci levels
            if fib_res.all_levels:
                st.subheader("Fibonacci Levels")
                fib_data = {
                    f"Fib {r*100:.1f}%": [f"${p:.4f}"]
                    for r, p in sorted(fib_res.all_levels.items())
                }
                fib_table = pd.DataFrame(fib_data, index=["Price"])
                st.dataframe(fib_table, use_container_width=True)

                st.caption(
                    f"Swing High: ${fib_res.swing_high:.4f}  |  "
                    f"Swing Low: ${fib_res.swing_low:.4f}  |  "
                    f"{fib_res.note}"
                )

            # Show S/R zones
            if sr_zones:
                st.subheader("Support / Resistance Zones")
                current_p = float(price_df["Close"].iloc[-1])
                zones_df = pd.DataFrame(
                    [
                        {
                            "Zone Price": f"${z:.4f}",
                            "Type": "Support" if z < current_p else "Resistance",
                            "Distance": f"{abs(z - current_p) / current_p * 100:.2f}%",
                        }
                        for z in sr_zones
                    ]
                ).sort_values("Zone Price")
                st.dataframe(zones_df, use_container_width=True)

        except Exception as exc:
            st.warning(f"Could not compute levels: {exc}")
            st.line_chart(price_df["Close"])

# ---- TAB 4: About ----------------------------------------------------------
with tab_about:
    st.header("About This App")
    st.markdown(
        """
### Trading Notification Bot

Scans a configurable watchlist every 10 minutes and fires alerts when **2 of 3 signals** align:

| Signal | Method | Data Source |
|--------|--------|-------------|
| **Fibonacci** | Price within ±0.5% of a key retracement level (23.6%, 38.2%, 50%, 61.8%, 78.6%) | Yahoo Finance via `yfinance` |
| **Support / Resistance** | Price within ±0.5% of a clustered pivot zone (daily candles) | Yahoo Finance via `yfinance` |
| **News Sentiment** | Mean VADER compound score of recent headlines ≥ ±0.08 | Free RSS feeds (Reuters, Yahoo Finance, CNBC, MarketWatch) |

### Trade Levels

- **Entry** — current price at signal time
- **Stop Loss** — entry ± (ATR × 1.5)
- **Take Profit** — entry ± (risk × 2.0)  *(2:1 R:R)*

### Notifications

- **Discord** — set `DISCORD_WEBHOOK_URL` in your `.env` file
- **WhatsApp** — set Twilio env vars in `.env` (optional)

### Running the Bot

```bash
# Terminal 1 — scanner
python -m trading.scheduler

# Terminal 2 — this dashboard
streamlit run trading/dashboard.py
```

### Free Data Sources Only

No paid API keys are required. All data comes from:
- **yfinance** (Yahoo Finance scraper)
- **RSS feeds** from Reuters, Yahoo Finance, CNBC, MarketWatch, Investing.com, WSJ
        """
    )
