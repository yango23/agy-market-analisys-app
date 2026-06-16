# -*- coding: utf-8 -*-
# Aetheris Crypto Analytics Terminal - Frontend
# Imports MUST all be at the top to avoid NameError in Streamlit exec context
import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
from typing import Optional

# ==============================================================================
# PAGE CONFIG (must be first Streamlit call)
# ==============================================================================
st.set_page_config(
    page_title="Aetheris Crypto Terminal",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# GLOBAL CSS
# ==============================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: linear-gradient(135deg, #060813 0%, #0a0d1a 60%, #060813 100%);
}

section[data-testid="stSidebar"] {
    background: rgba(8, 10, 24, 0.98);
    border-right: 1px solid rgba(168, 85, 247, 0.15);
}

div[data-testid="stMetric"] {
    background: rgba(14, 18, 38, 0.75);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px 20px;
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(168, 85, 247, 0.4);
    box-shadow: 0 6px 24px rgba(168, 85, 247, 0.1);
    transform: translateY(-2px);
}
div[data-testid="stMetricLabel"] p {
    color: #6b7280 !important;
    font-size: 0.73rem !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
div[data-testid="stMetricValue"] {
    color: #f4f4f5 !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(10, 13, 28, 0.7);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #6b7280 !important;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 8px 18px;
}
.stTabs [aria-selected="true"] {
    background: rgba(168, 85, 247, 0.18) !important;
    color: #a855f7 !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important;
}

.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    border: none;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(168, 85, 247, 0.45);
    transform: translateY(-1px);
}

.news-card {
    background: rgba(14, 18, 38, 0.6);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.badge-bullish {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 0.72rem;
    font-weight: 700;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.badge-bearish {
    background: rgba(244, 63, 94, 0.15);
    color: #f43f5e;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 0.72rem;
    font-weight: 700;
    border: 1px solid rgba(244, 63, 94, 0.3);
}
.badge-neutral {
    background: rgba(255,255,255,0.05);
    color: #9ca3af;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 0.72rem;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.12);
}
.alert-row {
    background: rgba(244, 63, 94, 0.07);
    border-left: 3px solid #f43f5e;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 8px;
    color: #f4f4f5;
    font-size: 0.85rem;
}
.online-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    padding: 4px 11px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# CONSTANTS
# ==============================================================================
API_BASE = "http://localhost:8000/api"

DEFAULT_COINS = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "MATIC": "Polygon",
    "TON": "The Open Network",
}

# ==============================================================================
# SESSION STATE
# ==============================================================================
if "seen_alerts" not in st.session_state:
    st.session_state.seen_alerts = set()

# ==============================================================================
# API HELPERS
# ==============================================================================
def api_get(path: str):
    """GET from the backend API. Returns parsed JSON or None on error."""
    try:
        resp = httpx.get(f"{API_BASE}/{path}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def api_post(path: str, payload: dict) -> bool:
    """POST to the backend API. Returns True on success."""
    try:
        resp = httpx.post(f"{API_BASE}/{path}", json=payload, timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


def api_delete(path: str) -> bool:
    """DELETE at the backend API. Returns True on success."""
    try:
        resp = httpx.delete(f"{API_BASE}/{path}", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


def to_datetime(raw_ts) -> Optional[datetime]:
    """
    Convert a raw timestamp (seconds or milliseconds) to a datetime object.
    Returns None if the value is out of a valid range (2000-2100).
    """
    try:
        ts = float(raw_ts)
        if ts > 1e10:          # milliseconds -> seconds
            ts /= 1000.0
        # Reject obviously bad values (before year 2000 or after 2100)
        if not (946_684_800 <= ts <= 4_102_444_800):
            return None
        return datetime.utcfromtimestamp(ts)
    except Exception:
        return None


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("## 🌌 Aetheris")
    st.caption("Crypto Analytics Terminal")
    st.divider()

    # Backend health
    root_resp = api_get("../")   # calls http://localhost:8000/
    if root_resp:
        st.markdown(
            '<span class="online-badge">&#9679; API Online</span>',
            unsafe_allow_html=True,
        )
    else:
        st.error("Backend offline — start FastAPI first")
    st.markdown("")

    # Load ticker list
    raw_tickers = api_get("tickers")
    if raw_tickers and isinstance(raw_tickers, list) and len(raw_tickers) > 0:
        ticker_list = [t["symbol"] for t in raw_tickers]
        ticker_names = {t["symbol"]: t["name"] for t in raw_tickers}
    else:
        ticker_list = list(DEFAULT_COINS.keys())
        ticker_names = dict(DEFAULT_COINS)

    # Asset selector
    st.markdown("**Select Asset**")
    selected_coin = st.selectbox(
        "Asset",
        options=ticker_list,
        format_func=lambda s: f"{s}  —  {ticker_names.get(s, s)}",
        label_visibility="collapsed",
    )

    st.divider()

    # Auto refresh
    auto_refresh = st.checkbox("Auto-refresh (30 s)", value=False)

    st.divider()

    # Add new asset
    st.markdown("**Track New Asset**")
    with st.form("form_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_sym = st.text_input("Symbol", placeholder="LINK")
        with c2:
            new_name = st.text_input("Name", placeholder="Chainlink")
        if st.form_submit_button("Add", use_container_width=True):
            sym = new_sym.upper().strip()
            nam = new_name.strip()
            if sym and nam:
                if api_post("tickers", {"symbol": sym, "name": nam}):
                    st.success(f"{sym} added!")
                    st.rerun()
                else:
                    st.error("Already tracked or API error.")
            else:
                st.warning("Fill in both fields.")

    # Remove asset
    removable = [t for t in ticker_list if t != selected_coin]
    if removable:
        st.markdown("**Remove Asset**")
        to_remove = st.selectbox("Asset", removable, label_visibility="collapsed")
        if st.button(f"Remove {to_remove}", use_container_width=True):
            if api_delete(f"tickers/{to_remove}"):
                st.success(f"Removed {to_remove}")
                st.rerun()
            else:
                st.error("Failed to remove.")

# ==============================================================================
# FETCH MARKET DATA & TOAST ALERTS
# ==============================================================================
market = api_get(f"market/{selected_coin}")

alert_logs = api_get("alerts/logs") or []
for log in alert_logs[:5]:
    log_key = f"{log.get('alert_id')}_{log.get('timestamp')}"
    if log_key not in st.session_state.seen_alerts:
        st.toast(log.get("message", "Alert fired"), icon="🚨")
        st.session_state.seen_alerts.add(log_key)

# ==============================================================================
# MAIN HEADER + METRICS
# ==============================================================================
coin_label = ticker_names.get(selected_coin, selected_coin)
st.markdown(f"## {selected_coin} &nbsp;·&nbsp; {coin_label}", unsafe_allow_html=True)

if market:
    price   = float(market.get("price", 0))
    change  = float(market.get("change_24h", 0))
    volume  = float(market.get("volume_24h", 0))
    mktcap  = float(market.get("market_cap", 0))

    price_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
    chg_str   = f"{change:+.2f}%"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Price (USD)", price_str, chg_str)
    col2.metric("24 h Change", chg_str)
    col3.metric("24 h Volume", f"${volume:,.0f}")
    col4.metric("Market Cap", f"${mktcap:,.0f}")

    st.markdown("")

    # ========================================================================
    # TABS
    # ========================================================================
    tab_chart, tab_alerts, tab_news = st.tabs(
        ["📉  Chart & Indicators", "🚨  Alert Engine", "📰  News Feed"]
    )

    # ------------------------------------------------------------------------
    # TAB 1 — CHART & INDICATORS
    # ------------------------------------------------------------------------
    with tab_chart:
        ohlc_raw  = market.get("ohlc", [])
        rsi_vals  = market.get("rsi", [])
        macd_data = market.get("macd", {})
        levels    = market.get("support_resistance", {})

        if not ohlc_raw:
            st.info("Waiting for OHLC data from the backend — backend may still be doing its first tick.")
        else:
            # Build a clean DataFrame, skipping any bad timestamps
            rows = []
            for candle in ohlc_raw:
                dt = to_datetime(candle[0])
                if dt is not None:
                    rows.append({
                        "time":  dt,
                        "open":  float(candle[1]),
                        "high":  float(candle[2]),
                        "low":   float(candle[3]),
                        "close": float(candle[4]),
                    })

            if not rows:
                st.warning("All candle timestamps were invalid. Backend may be sending bad data.")
            else:
                df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)

                indicator = st.radio(
                    "Sub-chart indicator",
                    ["RSI", "MACD"],
                    horizontal=True,
                )

                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.06,
                    row_heights=[0.72, 0.28],
                )

                # Candlestick chart
                fig.add_trace(
                    go.Candlestick(
                        x=df["time"],
                        open=df["open"],
                        high=df["high"],
                        low=df["low"],
                        close=df["close"],
                        name="Price",
                        increasing_line_color="#10b981",
                        decreasing_line_color="#f43f5e",
                        increasing_fillcolor="#10b981",
                        decreasing_fillcolor="#f43f5e",
                    ),
                    row=1, col=1,
                )

                # Support / Resistance levels
                pivots      = levels.get("pivot_points", {})
                supports    = levels.get("supports", [])
                resistances = levels.get("resistances", [])

                pp = pivots.get("PP")
                if pp:
                    fig.add_hline(
                        y=pp,
                        line_dash="dash",
                        line_color="rgba(168,85,247,0.55)",
                        annotation_text=f"PP {pp:,.2f}",
                        annotation_font_color="#a855f7",
                        row=1, col=1,
                    )

                for idx, s in enumerate(supports[:3]):
                    fig.add_hline(
                        y=s,
                        line_dash="dot",
                        line_color="rgba(16,185,129,0.45)",
                        annotation_text=f"S{idx+1} {s:,.2f}",
                        annotation_font_color="#10b981",
                        row=1, col=1,
                    )

                for idx, r in enumerate(resistances[:3]):
                    fig.add_hline(
                        y=r,
                        line_dash="dot",
                        line_color="rgba(244,63,94,0.45)",
                        annotation_text=f"R{idx+1} {r:,.2f}",
                        annotation_font_color="#f43f5e",
                        row=1, col=1,
                    )

                # Sub-chart: RSI or MACD
                if indicator == "RSI" and rsi_vals:
                    rsi_trimmed = rsi_vals[-len(df):]
                    if len(rsi_trimmed) == len(df):
                        fig.add_trace(
                            go.Scatter(
                                x=df["time"],
                                y=rsi_trimmed,
                                name="RSI",
                                line=dict(color="#f59e0b", width=1.8),
                            ),
                            row=2, col=1,
                        )
                        fig.add_hline(y=70, line_dash="dot", line_color="rgba(244,63,94,0.4)", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dot", line_color="rgba(16,185,129,0.4)", row=2, col=1)
                        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(244,63,94,0.04)", line_width=0, row=2, col=1)
                        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(16,185,129,0.04)", line_width=0, row=2, col=1)

                elif indicator == "MACD" and macd_data:
                    ml = macd_data.get("macd_line", [])[-len(df):]
                    sl = macd_data.get("signal_line", [])[-len(df):]
                    hi = macd_data.get("histogram", [])[-len(df):]

                    if len(ml) == len(df):
                        bar_colors = ["#10b981" if v >= 0 else "#f43f5e" for v in hi]
                        fig.add_trace(
                            go.Bar(x=df["time"], y=hi, name="Histogram",
                                   marker_color=bar_colors, opacity=0.55),
                            row=2, col=1,
                        )
                        fig.add_trace(
                            go.Scatter(x=df["time"], y=ml, name="MACD",
                                       line=dict(color="#06b6d4", width=1.8)),
                            row=2, col=1,
                        )
                        fig.add_trace(
                            go.Scatter(x=df["time"], y=sl, name="Signal",
                                       line=dict(color="#a855f7", width=1.8)),
                            row=2, col=1,
                        )

                fig.update_layout(
                    height=640,
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=8, r=8, t=28, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(6,8,20,0.65)",
                    font=dict(color="#9ca3af", size=11),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom", y=1.01,
                        xanchor="right", x=1,
                    ),
                    hovermode="x unified",
                )
                fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", showline=False)
                fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", showline=False)

                st.plotly_chart(fig, use_container_width=True)

                # Pivot point level cards
                st.markdown("**Classical Pivot Point Levels**")
                p1, p2, p3, p4, p5 = st.columns(5)
                for col, key, label in [
                    (p1, "S2", "S2 — Support 2"),
                    (p2, "S1", "S1 — Support 1"),
                    (p3, "PP", "PP — Pivot"),
                    (p4, "R1", "R1 — Resistance 1"),
                    (p5, "R2", "R2 — Resistance 2"),
                ]:
                    val = pivots.get(key)
                    col.metric(label, f"${val:,.2f}" if val else "—")

    # ------------------------------------------------------------------------
    # TAB 2 — ALERT ENGINE
    # ------------------------------------------------------------------------
    with tab_alerts:
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            st.markdown("#### Create Alert Rule")
            st.caption(f"Monitoring **{selected_coin}** · Price: **{price_str}**")

            with st.form("form_alert", clear_on_submit=True):
                metric_choice = st.selectbox(
                    "Metric",
                    ["price", "rsi"],
                    format_func=lambda x: "Price (USD)" if x == "price" else "RSI (0-100)",
                )
                cond_choice = st.selectbox(
                    "Condition",
                    ["above", "below"],
                    format_func=lambda x: "Rises Above ↑" if x == "above" else "Falls Below ↓",
                )
                default_thresh = price if metric_choice == "price" else 70.0
                threshold = st.number_input("Threshold", value=float(default_thresh), format="%.4f")

                if st.form_submit_button("Deploy Alert", use_container_width=True, type="primary"):
                    ok = api_post("alerts", {
                        "ticker":    selected_coin,
                        "metric":    metric_choice,
                        "condition": cond_choice,
                        "value":     threshold,
                    })
                    if ok:
                        st.success("Alert rule deployed!")
                        st.rerun()
                    else:
                        st.error("Failed — check the backend.")

            st.divider()
            st.markdown("#### Delete Rules")

            del_id = st.text_input("Alert ID to delete", placeholder="Copy ID from table →")
            d1, d2 = st.columns(2)
            with d1:
                if st.button("Delete by ID", use_container_width=True):
                    if del_id:
                        if api_delete(f"alerts/{del_id}"):
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error("ID not found.")
                    else:
                        st.warning("Paste an ID above.")
            with d2:
                if st.button("Clear All Rules", use_container_width=True):
                    api_delete("alerts")
                    st.success("All cleared.")
                    st.rerun()

        with right_col:
            st.markdown("#### Active Rules")
            rules = api_get("alerts") or []
            if rules:
                display_cols = [c for c in ["id", "ticker", "metric", "condition", "value", "status"]
                                if c in pd.DataFrame(rules).columns]
                st.dataframe(pd.DataFrame(rules)[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No active rules. Create one on the left.")

            st.markdown("#### Triggered Logs")
            logs = api_get("alerts/logs") or []
            if logs:
                r1, r2 = st.columns([3, 1])
                with r2:
                    if st.button("Clear Logs", use_container_width=True):
                        api_delete("alerts/logs")
                        st.rerun()
                for log in logs[:20]:
                    try:
                        ts = datetime.fromisoformat(log.get("timestamp", "")).strftime("%H:%M:%S")
                    except Exception:
                        ts = log.get("timestamp", "?")
                    st.markdown(
                        f'<div class="alert-row">🚨 <strong>{ts}</strong> — {log.get("message", "Alert fired")}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No alerts triggered — system nominal.")

    # ------------------------------------------------------------------------
    # TAB 3 — NEWS FEED
    # ------------------------------------------------------------------------
    with tab_news:
        st.markdown(f"#### {selected_coin} News")
        news_items = market.get("news", [])

        if not news_items:
            st.info("No news available. Set CRYPTOPANIC_API_TOKEN env variable to enable news.")
        else:
            for item in news_items:
                sentiment = item.get("sentiment", "neutral").lower()
                badge = f'<span class="badge-{sentiment}">{sentiment.upper()}</span>'

                try:
                    pub = datetime.fromisoformat(item.get("published_at", "")).strftime("%b %d · %H:%M")
                except Exception:
                    pub = item.get("published_at", "")

                source = item.get("source", "Unknown")
                title  = item.get("title", "No title")
                url    = item.get("url", "#")

                st.markdown(
                    f"""
<div class="news-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="color:#6b7280;font-size:0.78rem;">{source} &nbsp;·&nbsp; {pub}</span>
    {badge}
  </div>
  <a href="{url}" target="_blank"
     style="color:#e2e8f0;font-weight:600;font-size:0.95rem;text-decoration:none;line-height:1.45;">
    {title}
  </a>
</div>
""",
                    unsafe_allow_html=True,
                )

else:
    # Backend not reachable or data not loaded yet
    st.markdown("")
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.error(
            f"""
### Backend Not Reachable

Could not load data for **{selected_coin}**.

**Start the backend in a terminal:**
```
cd F:\\AGACP\\agy-cryptomarket-app
.venv\\Scripts\\activate
uvicorn backend.app.main:app --reload
```
Then refresh this page.
"""
        )

# ==============================================================================
# AUTO REFRESH
# ==============================================================================
if auto_refresh:
    time.sleep(30)
    st.rerun()
