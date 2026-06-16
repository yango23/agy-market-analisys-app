import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as px
from plotly.subplots import make_subplots
import time
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Aetheris • Crypto Analytics Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sleek CSS for Dark Theme and Premium UI
st.markdown("""
<style>
    /* Base styles */
    .reportview-container {
        background: #060813;
    }
    
    /* Metrics panel custom styling */
    div[data-testid="stMetric"] {
        background-color: rgba(16, 20, 38, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 15px 20px;
        border-radius: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    div[data-testid="stMetric"]:hover {
        border-color: rgba(168, 85, 247, 0.4);
        background-color: rgba(22, 28, 54, 0.85);
        box-shadow: 0 8px 20px rgba(168, 85, 247, 0.1);
        transform: translateY(-2px);
    }

    /* Section Cards styling */
    .element-container div.stAlert {
        border-radius: 10px;
    }
    
    /* Toast/Alert custom colors */
    .stToast {
        background-color: #0a0d1d !important;
        border-left: 5px solid #a855f7 !important;
        color: #f4f4f5 !important;
    }
    
    /* Sentiment badges */
    .badge-bullish {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-bearish {
        background-color: rgba(244, 63, 94, 0.15);
        color: #f43f5e;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .badge-neutral {
        background-color: rgba(255, 255, 255, 0.05);
        color: #9ca3af;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000/api"

# Session State for tracking triggered toasts to prevent spam
if "shown_toasts" not in st.session_state:
    st.session_state.shown_toasts = set()

# Helper functions to communicate with API
def fetch_api_data(endpoint: str) -> dict:
    try:
        response = httpx.get(f"{API_BASE_URL}/{endpoint}", timeout=5.0)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        return {}

def send_api_post(endpoint: str, data: dict) -> bool:
    try:
        response = httpx.post(f"{API_BASE_URL}/{endpoint}", json=data, timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False

def send_api_delete(endpoint: str) -> bool:
    try:
        response = httpx.delete(f"{API_BASE_URL}/{endpoint}", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False

# --- HEADER SECTION ---
st.title("🌌 Aetheris Crypto Terminal")
st.caption("Real-Time Analytics, Mathematical Levels Support/Resistance & News Trigger Engine")

# Sidebar navigation & configuration
st.sidebar.image("https://images.unsplash.com/photo-1621761191319-c6fb62004040?auto=format&fit=crop&w=400&q=80", caption="Aetheris Analytics Terminal", use_column_width=True)

# Fetch tracked tickers from SQLite
tickers_data = fetch_api_data("tickers")
if tickers_data:
    available_tickers = [t["symbol"] for t in tickers_data]
    ticker_names = {t["symbol"]: t["name"] for t in tickers_data}
else:
    available_tickers = ["BTC", "ETH", "SOL", "MATIC", "TON"]
    ticker_names = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "MATIC": "Polygon", "TON": "The Open Network"}

# Coin Ticker Selector
selected_ticker = st.sidebar.selectbox(
    "Select Crypto Asset",
    options=available_tickers,
    index=0
)

# Refresh interval settings
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh (10s)", value=True)

# --- TICKERS DYNAMIC MANAGEMENT IN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("Manage Monitored Assets")

# Add Ticker Form
with st.sidebar.form("add_ticker_form", clear_on_submit=True):
    new_symbol = st.text_input("Token Symbol (e.g. LINK, ADA)").upper().strip()
    new_name = st.text_input("Token Name (e.g. Chainlink)")
    add_btn = st.form_submit_button("Add Asset")
    
    if add_btn:
        if new_symbol and new_name:
            success = send_api_post("tickers", {"symbol": new_symbol, "name": new_name})
            if success:
                st.sidebar.success(f"Added {new_symbol}!")
                st.rerun()
            else:
                st.sidebar.error("Already exists or failed.")
        else:
            st.sidebar.warning("Fill in all fields.")

# Delete Ticker Selector
if len(available_tickers) > 1:
    ticker_to_delete = st.sidebar.selectbox(
        "Delete Asset",
        options=[t for t in available_tickers if t != selected_ticker],
        index=0
    )
    if st.sidebar.button("Remove Selected Asset", type="primary"):
        if send_api_delete(f"tickers/{ticker_to_delete}"):
            st.sidebar.success(f"Removed {ticker_to_delete}!")
            st.rerun()
        else:
            st.sidebar.error("Failed to remove.")

# Fetch data for selected coin
market_data = fetch_api_data(f"market/{selected_ticker}")

# Toast/Alert notifications checker
logs = fetch_api_data("alerts/logs")
if logs:
    for log in logs:
        log_id = f"{log['alert_id']}_{log['timestamp']}"
        if log_id not in st.session_state.shown_toasts:
            st.toast(log["message"], icon="⚠️")
            st.session_state.shown_toasts.add(log_id)

# --- DASHBOARD METRICS ---
if market_data:
    st.subheader(f"📊 {selected_ticker} ({ticker_names.get(selected_ticker, '')}) Market Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Prices & Volume formatting
    price = market_data.get("price", 0.0)
    change = market_data.get("change_24h", 0.0)
    volume = market_data.get("volume_24h", 0.0)
    market_cap = market_data.get("market_cap", 0.0)
    
    price_str = f"${price:,.2f}" if price >= 1.0 else f"${price:,.6f}"
    change_str = f"{change:+.2f}%"
    
    col1.metric("Current Price", price_str, change_str)
    col2.metric("24h Trading Volume", f"${volume:,.0f}")
    col3.metric("Market Capitalization", f"${market_cap:,.0f}")
    col4.metric("Last Polled", datetime.fromisoformat(market_data.get("last_updated")).strftime("%H:%M:%S"))

    # Create Tabs for layout
    tab_analytics, tab_alerts, tab_news = st.tabs(["📉 Analytics & Indicators", "🚨 Custom Alerts", "📰 Currency News Feed"])

    # --- TAB 1: ANALYTICS & INDICATORS ---
    with tab_analytics:
        st.subheader("Price Chart & Mathematical Indicators")
        
        ohlc = market_data.get("ohlc", [])
        rsi = market_data.get("rsi", [])
        macd = market_data.get("macd", {})
        levels = market_data.get("support_resistance", {})
        
        if ohlc:
            # Prepare pandas Dataframe
            df = pd.DataFrame(ohlc, columns=["timestamp", "open", "high", "low", "close"])
            df["time"] = pd.to_datetime(df["timestamp"], unit="s")
            
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.08,
                row_heights=[0.7, 0.3]
            )
            
            fig.add_trace(
                go.Candlestick(
                    x=df["time"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="Candlestick",
                    increasing_line_color="#10b981",
                    decreasing_line_color="#f43f5e"
                ),
                row=1, col=1
            )
            
            # Support/Resistance zones
            supports = levels.get("supports", [])
            resistances = levels.get("resistances", [])
            pivot_points = levels.get("pivot_points", {})
            
            # Overlay Pivot Point PP as a dotted line
            if "PP" in pivot_points:
                fig.add_hline(
                    y=pivot_points["PP"], 
                    line_dash="dash", 
                    line_color="rgba(168, 85, 247, 0.4)",
                    annotation_text=f"Pivot (PP): {pivot_points['PP']}",
                    row=1, col=1
                )
                
            # Draw supports (green)
            for idx, sup in enumerate(supports):
                fig.add_hline(
                    y=sup,
                    line_color="rgba(16, 185, 129, 0.5)",
                    annotation_text=f"Support {idx+1}: {sup}",
                    row=1, col=1
                )
                
            # Draw resistances (red)
            for idx, res in enumerate(resistances):
                fig.add_hline(
                    y=res,
                    line_color="rgba(244, 63, 94, 0.5)",
                    annotation_text=f"Resistance {idx+1}: {res}",
                    row=1, col=1
                )
            
            # Indicators Overlay Toggle
            indicator_selection = st.radio("Sub-Chart Technical Indicator", ["RSI (Relative Strength Index)", "MACD (Moving Average Convergence Divergence)"], horizontal=True)
            
            if indicator_selection == "RSI (Relative Strength Index)":
                if len(rsi) == len(df):
                    df["rsi"] = rsi
                    fig.add_trace(
                        go.Scatter(x=df["time"], y=df["rsi"], name="RSI", line=dict(color="#f59e0b", width=1.5)),
                        row=2, col=1
                    )
                    # Add RSI 30/70 thresholds
                    fig.add_hline(y=70, line_dash="dot", line_color="rgba(244, 63, 94, 0.4)", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dot", line_color="rgba(16, 185, 129, 0.4)", row=2, col=1)
            else:
                if macd and len(macd.get("macd_line", [])) == len(df):
                    df["macd"] = macd["macd_line"]
                    df["signal"] = macd["signal_line"]
                    df["hist"] = macd["histogram"]
                    
                    fig.add_trace(
                        go.Scatter(x=df["time"], y=df["macd"], name="MACD", line=dict(color="#06b6d4", width=1.5)),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Scatter(x=df["time"], y=df["signal"], name="Signal", line=dict(color="#a855f7", width=1.5)),
                        row=2, col=1
                    )
                    fig.add_trace(
                        go.Bar(x=df["time"], y=df["hist"], name="Histogram", marker_color="rgba(255, 255, 255, 0.15)"),
                        row=2, col=1
                    )
            
            # Styling updates
            fig.update_layout(
                height=650,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.03)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.03)")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display current Pivot Point levels in a list
            st.markdown("### Classical Pivot Point Levels")
            pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns(5)
            pcol1.metric("Support 2 (S2)", f"${pivot_points.get('S2'):,.2f}" if pivot_points.get('S2') else "N/A")
            pcol2.metric("Support 1 (S1)", f"${pivot_points.get('S1'):,.2f}" if pivot_points.get('S1') else "N/A")
            pcol3.metric("Pivot Point (PP)", f"${pivot_points.get('PP'):,.2f}" if pivot_points.get('PP') else "N/A")
            pcol4.metric("Resistance 1 (R1)", f"${pivot_points.get('R1'):,.2f}" if pivot_points.get('R1') else "N/A")
            pcol5.metric("Resistance 2 (R2)", f"${pivot_points.get('R2'):,.2f}" if pivot_points.get('R2') else "N/A")

    # --- TAB 2: CUSTOM ALERTS ---
    with tab_alerts:
        st.subheader("Configure Trigger Rules & View Logs")
        
        acol1, acol2 = st.columns([1, 2])
        
        with acol1:
            st.markdown("### Deploy Alert")
            with st.form("create_alert_form", clear_on_submit=True):
                alert_metric = st.selectbox("Trigger Metric", ["price", "rsi"])
                alert_condition = st.selectbox("Condition", ["above", "below"])
                
                default_val = price if alert_metric == "price" else 50.0
                alert_val = st.number_input("Threshold Value", value=float(default_val), format="%.4f")
                
                submitted = st.form_submit_button("Deploy Trigger")
                if submitted:
                    success = send_api_post("alerts", {
                        "ticker": selected_ticker,
                        "metric": alert_metric,
                        "condition": alert_condition,
                        "value": alert_val
                    })
                    if success:
                        st.success("Trigger deployed successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to deploy trigger.")
                        
            if st.button("Delete All Alert Rules", type="primary"):
                if send_api_delete("alerts"):
                    st.success("All alert rules deleted.")
                    st.rerun()

        with acol2:
            st.markdown("### Active Registry")
            rules = fetch_api_data("alerts")
            if rules:
                df_rules = pd.DataFrame(rules)
                df_rules_display = df_rules[["ticker", "metric", "condition", "value", "status", "id"]]
                st.dataframe(df_rules_display, use_container_width=True)
                
                del_id = st.text_input("Enter Alert ID to delete:")
                if st.button("Delete Rule"):
                    if del_id:
                        if send_api_delete(f"alerts/{del_id}"):
                            st.success(f"Deleted rule {del_id}")
                            st.rerun()
                        else:
                            st.error("Rule ID not found.")
            else:
                st.info("No active alerts configured.")
                
            st.markdown("### Log Feed")
            triggered_logs = fetch_api_data("alerts/logs")
            if triggered_logs:
                if st.button("Clear Logs"):
                    send_api_delete("alerts/logs")
                    st.rerun()
                for log in triggered_logs[:15]:
                    st.error(f"[{datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')}] {log['message']}")
            else:
                st.success("System status check: OK. Monitoring active. No alerts triggered.")

    # --- TAB 3: CURRENCY NEWS FEED ---
    with tab_news:
        st.subheader(f"📰 {selected_ticker} News Feed")
        
        news_list = market_data.get("news", [])
        if news_list:
            for item in news_list:
                sentiment = item.get("sentiment", "neutral").lower()
                badge_html = f'<span class="badge-{sentiment}">{sentiment.upper()}</span>'
                
                pub_time = datetime.fromisoformat(item.get("published_at")).strftime("%b %d, %H:%M")
                
                st.markdown(f"""
                **[{item.get('source')}]** • *{pub_time}* • {badge_html}
                #### [{item.get('title')}]({item.get('url')})
                ---
                """, unsafe_allow_html=True)
        else:
            st.info("No news articles found for this ticker.")
else:
    st.warning("Retrieving data from Aetheris API... Please verify the backend is running at http://localhost:8000")

# Auto rerun trigger script
if auto_refresh:
    time.sleep(10)
    st.rerun()

# Import Plotly Graph Objects for charting
import plotly.graph_objects as go
