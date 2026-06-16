import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aetheris • Crypto Terminal",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Premium Dark Theme CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Dark background */
    .stApp {
        background: linear-gradient(135deg, #060813 0%, #0a0d1a 50%, #060813 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(10, 13, 29, 0.98);
        border-right: 1px solid rgba(168, 85, 247, 0.15);
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stTextInput label {
        color: #9ca3af !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(16, 20, 40, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 18px 20px;
        transition: all 0.25s ease;
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(168, 85, 247, 0.35);
        background: rgba(22, 28, 54, 0.85);
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.1);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetricValue"] {
        color: #f4f4f5 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
    }
    div[data-testid="stMetricDelta"] svg { display: none; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(10, 13, 29, 0.6);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(255,255,255,0.06);
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #6b7280 !important;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(168, 85, 247, 0.2) !important;
        color: #a855f7 !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        border: none;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 14px rgba(168, 85, 247, 0.4);
        transform: translateY(-1px);
    }

    /* Form inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: rgba(16, 20, 40, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: #f4f4f5 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: rgba(168, 85, 247, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.1) !important;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Alert/info boxes */
    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    /* Status dot badge */
    .status-online {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #10b981;
        padding: 4px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #10b981;
        animation: pulse-green 2s infinite; display: inline-block; }
    @keyframes pulse-green {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    /* News badges */
    .badge-bullish {
        background: rgba(16, 185, 129, 0.15); color: #10b981;
        padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-bearish {
        background: rgba(244, 63, 94, 0.15); color: #f43f5e;
        padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .badge-neutral {
        background: rgba(255,255,255,0.05); color: #9ca3af;
        padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
        border: 1px solid rgba(255,255,255,0.12);
    }

    /* Alert log row */
    .alert-row {
        background: rgba(244, 63, 94, 0.08);
        border-left: 3px solid #f43f5e;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin-bottom: 8px;
        color: #f4f4f5;
        font-size: 0.85rem;
    }

    /* Section title */
    .section-title {
        font-size: 0.72rem; color: #6b7280;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin-bottom: 10px; margin-top: 4px;
    }

    /* Sidebar brand */
    .brand-title {
        font-size: 1.2rem; font-weight: 700;
        background: linear-gradient(135deg, #a855f7, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .brand-sub {
        font-size: 0.72rem; color: #4b5563; margin-top: 2px;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ────────────────────────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000/api"

KNOWN_COINS = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana",
    "MATIC": "Polygon", "TON": "The Open Network", "BNB": "BNB",
    "XRP": "Ripple", "AVAX": "Avalanche", "DOGE": "Dogecoin", "ADA": "Cardano"
}

# ─── Session State ────────────────────────────────────────────────────────────
if "shown_toasts" not in st.session_state:
    st.session_state.shown_toasts = set()

# ─── API Helpers ──────────────────────────────────────────────────────────────
def api_get(endpoint: str) -> dict | list | None:
    try:
        r = httpx.get(f"{API_BASE_URL}/{endpoint}", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def api_post(endpoint: str, data: dict) -> bool:
    try:
        r = httpx.post(f"{API_BASE_URL}/{endpoint}", json=data, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

def api_delete(endpoint: str) -> bool:
    try:
        r = httpx.delete(f"{API_BASE_URL}/{endpoint}", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

def safe_timestamp(ts_val):
    """Convert a numeric timestamp to datetime safely, handling ms or seconds."""
    try:
        ts = float(ts_val)
        # If timestamp is in ms (>1e10), convert to seconds
        if ts > 1e10:
            ts = ts / 1000.0
        # Clamp to a sane range: 2000-01-01 to 2100-01-01
        if ts < 946684800 or ts > 4102444800:
            return None
        return datetime.utcfromtimestamp(ts)
    except Exception:
        return None

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-title">🌌 Aetheris</div>
    <div class="brand-sub">Crypto Analytics Terminal</div>
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Check backend health
    health = api_get("../")  # hits root "/"
    if health:
        st.markdown('<span class="status-online"><span class="status-dot"></span>API Connected</span>', unsafe_allow_html=True)
    else:
        st.error("⚠️ Backend offline — start FastAPI first")

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch available tickers
    tickers_raw = api_get("tickers")
    if tickers_raw and isinstance(tickers_raw, list):
        available = [t["symbol"] for t in tickers_raw]
        names_map = {t["symbol"]: t["name"] for t in tickers_raw}
    else:
        available = list(KNOWN_COINS.keys())
        names_map = KNOWN_COINS

    # Coin selector
    st.markdown('<div class="section-title">📈 Asset Selection</div>', unsafe_allow_html=True)
    selected = st.selectbox(
        "Cryptocurrency",
        options=available,
        format_func=lambda s: f"{s} — {names_map.get(s, s)}",
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Auto-refresh
    st.markdown('<div class="section-title">⚙️ Settings</div>', unsafe_allow_html=True)
    auto_refresh = st.checkbox("Auto-refresh every 30 s", value=False)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Add new asset
    st.markdown('<div class="section-title">➕ Track New Asset</div>', unsafe_allow_html=True)
    with st.form("add_ticker_form", clear_on_submit=True):
        col_sym, col_name = st.columns(2)
        with col_sym:
            new_sym = st.text_input("Symbol", placeholder="LINK").upper().strip()
        with col_name:
            new_name = st.text_input("Name", placeholder="Chainlink")
        if st.form_submit_button("Add Asset", use_container_width=True):
            if new_sym and new_name:
                if api_post("tickers", {"symbol": new_sym, "name": new_name}):
                    st.success(f"✅ {new_sym} added!")
                    st.rerun()
                else:
                    st.error("Already tracked or failed.")
            else:
                st.warning("Fill both fields.")

    # Remove asset
    if len(available) > 1:
        st.markdown('<div class="section-title">🗑️ Remove Asset</div>', unsafe_allow_html=True)
        removable = [t for t in available if t != selected]
        to_remove = st.selectbox("Asset to remove", removable, label_visibility="collapsed")
        if st.button(f"Remove {to_remove}", use_container_width=True):
            if api_delete(f"tickers/{to_remove}"):
                st.success(f"Removed {to_remove}")
                st.rerun()
            else:
                st.error("Failed to remove.")

# ─── Fetch market data for selected coin ─────────────────────────────────────
market = api_get(f"market/{selected}")

# Push toast notifications for new triggered alerts
logs_raw = api_get("alerts/logs")
if logs_raw:
    for log in logs_raw[:5]:
        log_id = f"{log.get('alert_id')}_{log.get('timestamp')}"
        if log_id not in st.session_state.shown_toasts:
            st.toast(log.get("message", "Alert triggered"), icon="🚨")
            st.session_state.shown_toasts.add(log_id)

# ─── Main Header ─────────────────────────────────────────────────────────────
coin_name = names_map.get(selected, selected)
st.markdown(f"## {selected} &nbsp;·&nbsp; {coin_name}", unsafe_allow_html=True)

# ─── Top Metrics Row ─────────────────────────────────────────────────────────
if market:
    price   = market.get("price", 0.0)
    change  = market.get("change_24h", 0.0)
    volume  = market.get("volume_24h", 0.0)
    mktcap  = market.get("market_cap", 0.0)
    updated = market.get("last_updated", "")

    price_fmt = f"${price:,.2f}" if price >= 1.0 else f"${price:,.6f}"
    chg_fmt   = f"{change:+.2f}%"
    chg_delta = "↑" if change >= 0 else "↓"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Price", price_fmt, chg_fmt)
    m2.metric("24 h Change", chg_fmt)
    m3.metric("24 h Volume", f"${volume:,.0f}")
    m4.metric("Market Cap", f"${mktcap:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Tabs ────────────────────────────────────────────────────────────────
    tab_chart, tab_alerts, tab_news = st.tabs([
        "📉  Price & Indicators",
        "🚨  Alert Engine",
        "📰  News Feed",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: PRICE CHART & INDICATORS
    # ════════════════════════════════════════════════════════════════════════
    with tab_chart:
        ohlc_raw = market.get("ohlc", [])
        rsi_vals = market.get("rsi", [])
        macd_data = market.get("macd", {})
        levels   = market.get("support_resistance", {})

        if ohlc_raw:
            # Build DataFrame with safe timestamp handling
            rows = []
            for candle in ohlc_raw:
                ts_dt = safe_timestamp(candle[0])
                if ts_dt is not None:
                    rows.append({
                        "time": ts_dt,
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low":  float(candle[3]),
                        "close": float(candle[4]),
                    })

            if not rows:
                st.warning("No valid candle data to display.")
            else:
                df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)

                # Indicator selector
                indicator = st.radio(
                    "Sub-chart indicator",
                    ["RSI", "MACD"],
                    horizontal=True,
                    label_visibility="visible"
                )

                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.06,
                    row_heights=[0.72, 0.28],
                    subplot_titles=("", indicator)
                )

                # ── Candlesticks ──
                fig.add_trace(go.Candlestick(
                    x=df["time"],
                    open=df["open"], high=df["high"],
                    low=df["low"],   close=df["close"],
                    name="Price",
                    increasing_line_color="#10b981",
                    decreasing_line_color="#f43f5e",
                    increasing_fillcolor="#10b981",
                    decreasing_fillcolor="#f43f5e",
                ), row=1, col=1)

                # ── Support / Resistance ──
                pivot_pts = levels.get("pivot_points", {})
                supports  = levels.get("supports", [])
                resistances = levels.get("resistances", [])

                if pivot_pts.get("PP"):
                    fig.add_hline(y=pivot_pts["PP"], line_dash="dash",
                                  line_color="rgba(168,85,247,0.5)",
                                  annotation_text=f"Pivot {pivot_pts['PP']:,.2f}",
                                  annotation_font_color="#a855f7", row=1, col=1)

                for i, sup in enumerate(supports[:3]):
                    fig.add_hline(y=sup, line_color="rgba(16,185,129,0.4)",
                                  line_dash="dot",
                                  annotation_text=f"S{i+1}: {sup:,.2f}",
                                  annotation_font_color="#10b981", row=1, col=1)

                for i, res in enumerate(resistances[:3]):
                    fig.add_hline(y=res, line_color="rgba(244,63,94,0.4)",
                                  line_dash="dot",
                                  annotation_text=f"R{i+1}: {res:,.2f}",
                                  annotation_font_color="#f43f5e", row=1, col=1)

                # ── Sub-chart: RSI or MACD ──
                if indicator == "RSI" and rsi_vals:
                    # Align RSI to df length
                    rsi_aligned = rsi_vals[-len(df):]
                    if len(rsi_aligned) == len(df):
                        fig.add_trace(go.Scatter(
                            x=df["time"], y=rsi_aligned,
                            name="RSI", line=dict(color="#f59e0b", width=1.8)
                        ), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dot", line_color="rgba(244,63,94,0.4)", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dot", line_color="rgba(16,185,129,0.4)", row=2, col=1)
                        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(244,63,94,0.04)", line_width=0, row=2, col=1)
                        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(16,185,129,0.04)", line_width=0, row=2, col=1)

                elif indicator == "MACD" and macd_data:
                    ml = macd_data.get("macd_line", [])
                    sl = macd_data.get("signal_line", [])
                    hi = macd_data.get("histogram", [])

                    ml = ml[-len(df):]
                    sl = sl[-len(df):]
                    hi = hi[-len(df):]

                    if len(ml) == len(df):
                        bar_colors = ["#10b981" if v >= 0 else "#f43f5e" for v in hi]
                        fig.add_trace(go.Bar(
                            x=df["time"], y=hi, name="Histogram",
                            marker_color=bar_colors, opacity=0.6
                        ), row=2, col=1)
                        fig.add_trace(go.Scatter(
                            x=df["time"], y=ml, name="MACD",
                            line=dict(color="#06b6d4", width=1.8)
                        ), row=2, col=1)
                        fig.add_trace(go.Scatter(
                            x=df["time"], y=sl, name="Signal",
                            line=dict(color="#a855f7", width=1.8)
                        ), row=2, col=1)

                fig.update_layout(
                    height=640,
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=8, r=8, t=30, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(6,8,19,0.6)",
                    font=dict(color="#9ca3af", size=11),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.01,
                        xanchor="right", x=1, font=dict(size=11)
                    ),
                    hovermode="x unified",
                )
                fig.update_xaxes(
                    gridcolor="rgba(255,255,255,0.04)",
                    showline=False,
                )
                fig.update_yaxes(
                    gridcolor="rgba(255,255,255,0.04)",
                    showline=False,
                )

                st.plotly_chart(fig, use_container_width=True)

                # ── Pivot Point Level Cards ──
                st.markdown('<div class="section-title">Classical Pivot Point Levels</div>', unsafe_allow_html=True)
                pp_cols = st.columns(5)
                for col, (key, label) in zip(pp_cols, [("S2","S2"),("S1","S1"),("PP","PP"),("R1","R1"),("R2","R2")]):
                    val = pivot_pts.get(key)
                    col.metric(label, f"${val:,.2f}" if val else "—")

        else:
            st.info("⏳ Waiting for OHLC data from the backend. Make sure the backend is running and has completed its first tick.")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: ALERT ENGINE
    # ════════════════════════════════════════════════════════════════════════
    with tab_alerts:
        left, right = st.columns([1, 1], gap="large")

        # ── Left: Create alert ──
        with left:
            st.markdown("#### Create Alert Rule")
            st.caption(f"Watching: **{selected}** · Current price: **{price_fmt}**")

            with st.form("create_alert_form", clear_on_submit=True):
                a_metric = st.selectbox("Metric to Watch", ["price", "rsi"],
                                        format_func=lambda x: "Price (USD)" if x == "price" else "RSI (0–100)")
                a_cond   = st.selectbox("Condition", ["above", "below"],
                                        format_func=lambda x: "↑ Rises Above" if x == "above" else "↓ Falls Below")
                default_val = float(price) if a_metric == "price" else 70.0
                a_val = st.number_input("Threshold Value", value=default_val, format="%.4f")

                if st.form_submit_button("🚀 Deploy Alert", use_container_width=True, type="primary"):
                    ok = api_post("alerts", {
                        "ticker": selected,
                        "metric": a_metric,
                        "condition": a_cond,
                        "value": a_val
                    })
                    if ok:
                        st.success("✅ Alert rule deployed!")
                        st.rerun()
                    else:
                        st.error("Failed to deploy alert.")

            # Quick alert delete
            st.markdown("---")
            st.markdown("#### Delete a Specific Rule")
            del_id = st.text_input("Alert ID to delete", placeholder="paste the ID from the table →")
            del_col1, del_col2 = st.columns(2)
            with del_col1:
                if st.button("Delete Rule", use_container_width=True):
                    if del_id:
                        if api_delete(f"alerts/{del_id}"):
                            st.success(f"Deleted {del_id}")
                            st.rerun()
                        else:
                            st.error("ID not found.")
                    else:
                        st.warning("Enter an ID.")
            with del_col2:
                if st.button("Clear All Rules", use_container_width=True):
                    if api_delete("alerts"):
                        st.success("All rules cleared.")
                        st.rerun()

        # ── Right: Active rules + logs ──
        with right:
            st.markdown("#### Active Alert Rules")
            rules = api_get("alerts")
            if rules:
                df_rules = pd.DataFrame(rules)
                show_cols = [c for c in ["id", "ticker", "metric", "condition", "value", "status"] if c in df_rules.columns]
                st.dataframe(
                    df_rules[show_cols],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No active alert rules. Create one on the left.")

            st.markdown("#### Triggered Log Feed")
            logs = api_get("alerts/logs")
            if logs:
                log_hdr_col1, log_hdr_col2 = st.columns([3, 1])
                with log_hdr_col2:
                    if st.button("🗑️ Clear Logs", use_container_width=True):
                        api_delete("alerts/logs")
                        st.rerun()
                for log in logs[:20]:
                    ts_str = ""
                    try:
                        ts_str = datetime.fromisoformat(log.get("timestamp", "")).strftime("%H:%M:%S")
                    except Exception:
                        ts_str = log.get("timestamp", "")
                    st.markdown(
                        f'<div class="alert-row">🚨 <strong>{ts_str}</strong> — {log.get("message", "Alert fired")}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.success("✅ No alerts triggered — all conditions nominal.")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: NEWS FEED
    # ════════════════════════════════════════════════════════════════════════
    with tab_news:
        st.markdown(f"#### Latest {selected} News")

        news = market.get("news", [])
        if news:
            for item in news:
                sentiment = item.get("sentiment", "neutral").lower()
                badge = f'<span class="badge-{sentiment}">{sentiment.upper()}</span>'

                pub_raw = item.get("published_at", "")
                try:
                    pub_str = datetime.fromisoformat(pub_raw).strftime("%b %d · %H:%M")
                except Exception:
                    pub_str = pub_raw

                source = item.get("source", "Unknown")
                title  = item.get("title", "No title")
                url    = item.get("url", "#")

                st.markdown(f"""
<div style="background:rgba(16,20,40,0.55);border:1px solid rgba(255,255,255,0.07);
border-radius:12px;padding:16px 20px;margin-bottom:12px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
<span style="color:#6b7280;font-size:0.78rem;">{source} &nbsp;·&nbsp; {pub_str}</span>
{badge}
</div>
<a href="{url}" target="_blank" style="color:#f4f4f5;font-weight:600;font-size:0.95rem;
text-decoration:none;line-height:1.4;">{title}</a>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No news found. The CryptoPanic token may not be set, or no news is available for this asset.")

else:
    # ── Backend not ready ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.error("""
### ⚠️ Backend not reachable

Data for **{selected}** could not be loaded.

**Start the backend first:**
```bash
cd F:\\AGACP\\agy-cryptomarket-app
.venv\\Scripts\\activate
uvicorn backend.app.main:app --reload
```

Then refresh this page.
""".format(selected=selected))

# ─── Auto refresh ─────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(30)
    st.rerun()
