# -*- coding: utf-8 -*-
"""
Aetheris — Криптовалютный Аналитический Терминал
Frontend на Streamlit
"""
import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ СТРАНИЦЫ
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Aetheris • Крипто Терминал",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: linear-gradient(135deg,#060813 0%,#0a0d1a 60%,#060813 100%);
}
section[data-testid="stSidebar"] {
    background: rgba(8,10,24,0.98);
    border-right: 1px solid rgba(168,85,247,0.15);
}

/* Метрики */
div[data-testid="stMetric"] {
    background: rgba(14,18,38,0.75);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px 20px;
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(168,85,247,0.4);
    box-shadow: 0 6px 24px rgba(168,85,247,0.1);
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

/* Табы */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(10,13,28,0.7);
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
    background: rgba(168,85,247,0.18) !important;
    color: #a855f7 !important;
    border: 1px solid rgba(168,85,247,0.3) !important;
}

/* Кнопки */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#7c3aed,#a855f7);
    border: none;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(168,85,247,0.45);
    transform: translateY(-1px);
}

/* Карточка ИИ-аналитики */
.ai-card {
    background: rgba(10,13,30,0.85);
    border: 1px solid rgba(168,85,247,0.25);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 32px rgba(168,85,247,0.08);
}
.ai-card-title {
    font-size: 0.72rem;
    color: #a855f7;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
    font-weight: 600;
}
.ai-summary {
    font-size: 0.95rem;
    color: #e2e8f0;
    line-height: 1.65;
}
.signal-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-right: 8px;
    margin-bottom: 4px;
}
.signal-buy {
    background: rgba(16,185,129,0.15);
    color: #10b981;
    border: 1px solid rgba(16,185,129,0.35);
}
.signal-sell {
    background: rgba(244,63,94,0.15);
    color: #f43f5e;
    border: 1px solid rgba(244,63,94,0.35);
}
.signal-neutral {
    background: rgba(245,158,11,0.15);
    color: #f59e0b;
    border: 1px solid rgba(245,158,11,0.35);
}
.signal-watch {
    background: rgba(6,182,212,0.12);
    color: #06b6d4;
    border: 1px solid rgba(6,182,212,0.3);
}

/* Блок индикатора в аналитике */
.ind-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.ind-label { color: #9ca3af; font-size: 0.83rem; }
.ind-val   { font-size: 0.83rem; font-weight: 600; }
.val-green { color: #10b981; }
.val-red   { color: #f43f5e; }
.val-yellow{ color: #f59e0b; }
.val-white { color: #e2e8f0; }

/* Новости */
.news-card {
    background: rgba(14,18,38,0.6);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.badge-bullish {
    background: rgba(16,185,129,0.15); color: #10b981;
    padding: 2px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
    border: 1px solid rgba(16,185,129,0.3);
}
.badge-bearish {
    background: rgba(244,63,94,0.15); color: #f43f5e;
    padding: 2px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
    border: 1px solid rgba(244,63,94,0.3);
}
.badge-neutral {
    background: rgba(255,255,255,0.05); color: #9ca3af;
    padding: 2px 9px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
    border: 1px solid rgba(255,255,255,0.12);
}
.alert-row {
    background: rgba(244,63,94,0.07);
    border-left: 3px solid #f43f5e;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px; margin-bottom: 8px;
    color: #f4f4f5; font-size: 0.85rem;
}
.online-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3);
    color: #10b981; padding: 4px 11px; border-radius: 20px;
    font-size: 0.74rem; font-weight: 600;
}
.hint-box {
    background: rgba(6,182,212,0.06);
    border: 1px solid rgba(6,182,212,0.2);
    border-radius: 10px;
    padding: 10px 14px;
    color: #9ca3af;
    font-size: 0.78rem;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# КОНСТАНТЫ
# ══════════════════════════════════════════════════════════════════════════════
API_BASE = "http://localhost:8000/api"

DEFAULT_COINS = {
    "BTC":   "Bitcoin",
    "ETH":   "Ethereum",
    "SOL":   "Solana",
    "MATIC": "Polygon",
    "TON":   "The Open Network",
}

SENTIMENT_RU = {
    "bullish": "БЫЧИЙ",
    "bearish": "МЕДВЕЖИЙ",
    "neutral": "НЕЙТРАЛЬНЫЙ",
}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "seen_alerts" not in st.session_state:
    st.session_state.seen_alerts = set()

# ══════════════════════════════════════════════════════════════════════════════
# API ХЕЛПЕРЫ
# ══════════════════════════════════════════════════════════════════════════════
def api_get(path: str):
    try:
        r = httpx.get(f"{API_BASE}/{path}", timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def api_post(path: str, payload: dict) -> bool:
    try:
        r = httpx.post(f"{API_BASE}/{path}", json=payload, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

def api_delete(path: str) -> bool:
    try:
        r = httpx.delete(f"{API_BASE}/{path}", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

def to_dt(raw) -> Optional[datetime]:
    try:
        ts = float(raw)
        if ts > 1e10:
            ts /= 1000.0
        if not (946_684_800 <= ts <= 4_102_444_800):
            return None
        return datetime.utcfromtimestamp(ts)
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════════════
# ИИ-АНАЛИТИКА (на основе индикаторов)
# ══════════════════════════════════════════════════════════════════════════════
def build_ai_analysis(ticker: str, market: dict) -> dict:
    """
    Генерирует структурированный аналитический отчёт на русском языке
    на основе RSI, MACD, уровней поддержки/сопротивления и изменения цены.
    """
    price      = float(market.get("price", 0))
    change_24h = float(market.get("change_24h", 0))
    rsi_list   = market.get("rsi", [])
    macd_data  = market.get("macd", {})
    levels     = market.get("support_resistance", {})

    rsi = rsi_list[-1] if rsi_list else 50.0
    pivots      = levels.get("pivot_points", {})
    supports    = levels.get("supports", [])
    resistances = levels.get("resistances", [])

    # ── RSI сигнал ──────────────────────────────────────────────────────────
    if rsi >= 70:
        rsi_signal = "sell"
        rsi_text   = f"RSI = {rsi:.1f} — зона перекупленности. Вероятна коррекция вниз."
    elif rsi <= 30:
        rsi_signal = "buy"
        rsi_text   = f"RSI = {rsi:.1f} — зона перепроданности. Возможен отскок вверх."
    elif rsi >= 55:
        rsi_signal = "watch"
        rsi_text   = f"RSI = {rsi:.1f} — умеренно бычий импульс."
    elif rsi <= 45:
        rsi_signal = "watch"
        rsi_text   = f"RSI = {rsi:.1f} — умеренно медвежий импульс."
    else:
        rsi_signal = "neutral"
        rsi_text   = f"RSI = {rsi:.1f} — нейтральная зона, направление не определено."

    # ── MACD сигнал ─────────────────────────────────────────────────────────
    macd_line   = macd_data.get("macd_line", [])
    signal_line = macd_data.get("signal_line", [])
    hist        = macd_data.get("histogram", [])

    if macd_line and signal_line and len(hist) >= 2:
        last_macd   = macd_line[-1]
        last_signal = signal_line[-1]
        last_hist   = hist[-1]
        prev_hist   = hist[-2]

        if last_macd > last_signal and prev_hist < 0 <= last_hist:
            macd_signal = "buy"
            macd_text   = "MACD: бычье пересечение — линия MACD пробила сигнальную снизу вверх."
        elif last_macd < last_signal and prev_hist > 0 >= last_hist:
            macd_signal = "sell"
            macd_text   = "MACD: медвежье пересечение — линия MACD пробила сигнальную сверху вниз."
        elif last_macd > last_signal:
            macd_signal = "watch"
            macd_text   = f"MACD выше сигнальной ({last_macd:.2f} > {last_signal:.2f}) — бычий тренд сохраняется."
        elif last_macd < last_signal:
            macd_signal = "watch"
            macd_text   = f"MACD ниже сигнальной ({last_macd:.2f} < {last_signal:.2f}) — медвежий тренд доминирует."
        else:
            macd_signal = "neutral"
            macd_text   = "MACD: нейтральное положение, без чёткого сигнала."
    else:
        macd_signal = "neutral"
        macd_text   = "MACD: недостаточно данных для анализа."

    # ── Уровни S/R ──────────────────────────────────────────────────────────
    pp = pivots.get("PP")
    r1 = pivots.get("R1")
    s1 = pivots.get("S1")

    level_lines = []
    if pp:
        rel = ((price - pp) / pp) * 100
        if price > pp:
            level_lines.append(f"Цена выше пивот-уровня (PP={pp:,.2f}), что указывает на бычье настроение рынка.")
        else:
            level_lines.append(f"Цена ниже пивот-уровня (PP={pp:,.2f}), что указывает на медвежье давление.")
    if r1 and price:
        pct_to_r1 = ((r1 - price) / price) * 100
        level_lines.append(f"Ближайшее сопротивление R1 = {r1:,.2f} (+{pct_to_r1:.1f}% от текущей цены).")
    if s1 and price:
        pct_to_s1 = ((price - s1) / price) * 100
        level_lines.append(f"Ближайшая поддержка S1 = {s1:,.2f} (-{pct_to_s1:.1f}% от текущей цены).")

    level_text = " ".join(level_lines) if level_lines else "Пивот-уровни рассчитываются..."

    # ── Динамика за 24 ч ────────────────────────────────────────────────────
    if change_24h >= 5:
        trend_text  = f"Сильный рост за 24 ч: +{change_24h:.2f}%. Высокий бычий импульс."
        trend_signal = "buy"
    elif change_24h >= 1:
        trend_text  = f"Умеренный рост за 24 ч: +{change_24h:.2f}%."
        trend_signal = "watch"
    elif change_24h <= -5:
        trend_text  = f"Сильное падение за 24 ч: {change_24h:.2f}%. Высокое медвежье давление."
        trend_signal = "sell"
    elif change_24h <= -1:
        trend_text  = f"Умеренное снижение за 24 ч: {change_24h:.2f}%."
        trend_signal = "watch"
    else:
        trend_text  = f"Незначительное изменение за 24 ч: {change_24h:+.2f}%. Боковик."
        trend_signal = "neutral"

    # ── Итоговый сигнал ─────────────────────────────────────────────────────
    signals = [rsi_signal, macd_signal, trend_signal]
    buy_count  = signals.count("buy")  + signals.count("watch") * 0.4
    sell_count = signals.count("sell") + signals.count("watch") * 0.4

    if buy_count > sell_count and buy_count >= 1.5:
        overall_signal = "buy"
        overall_label  = "БЫЧИЙ"
        overall_text   = (
            f"Совокупность индикаторов указывает на бычий перевес. "
            f"Зона интереса для покупок — в районе S1 ({s1:,.2f}) " if s1 else
            "Совокупность индикаторов указывает на бычий перевес. "
        )
        conclusion = (
            f"Рекомендуемая зона для рассмотрения лонгов: вблизи {(s1 or price*0.98):,.2f}. "
            f"Целевой уровень: {(r1 or price*1.03):,.2f}."
        )
    elif sell_count > buy_count and sell_count >= 1.5:
        overall_signal = "sell"
        overall_label  = "МЕДВЕЖИЙ"
        overall_text   = "Совокупность индикаторов указывает на медвежий перевес. Шорт-давление доминирует."
        conclusion = (
            f"Рекомендуемая зона для рассмотрения шортов: вблизи {(r1 or price*1.02):,.2f}. "
            f"Целевой уровень: {(s1 or price*0.97):,.2f}."
        )
    else:
        overall_signal = "neutral"
        overall_label  = "НЕЙТРАЛЬНЫЙ"
        overall_text   = "Сигналы противоречивы или нейтральны. Рынок не даёт чёткого направления."
        conclusion     = "Рекомендуется ожидать подтверждения пробоя уровней перед открытием позиции."

    # Итог
    summary = (
        f"{trend_text} {rsi_text} {macd_text} {level_text} "
        f"{overall_text} {conclusion}"
    )

    return {
        "overall_signal":  overall_signal,
        "overall_label":   overall_label,
        "rsi":             rsi,
        "rsi_signal":      rsi_signal,
        "rsi_text":        rsi_text,
        "macd_signal":     macd_signal,
        "macd_text":       macd_text,
        "trend_signal":    trend_signal,
        "trend_text":      trend_text,
        "level_text":      level_text,
        "summary":         summary,
        "conclusion":      conclusion,
        "price":           price,
        "change_24h":      change_24h,
        "s1":              s1,
        "r1":              r1,
        "pp":              pp,
    }

def signal_badge_html(signal: str, text: str) -> str:
    cls = {
        "buy": "signal-buy", "sell": "signal-sell",
        "neutral": "signal-neutral", "watch": "signal-watch",
    }.get(signal, "signal-neutral")
    icon = {"buy": "▲", "sell": "▼", "neutral": "●", "watch": "◆"}.get(signal, "●")
    return f'<span class="signal-badge {cls}">{icon} {text}</span>'

def signal_color(signal: str) -> str:
    return {"buy": "val-green", "sell": "val-red", "neutral": "val-yellow", "watch": "val-yellow"}.get(signal, "val-yellow")

# ══════════════════════════════════════════════════════════════════════════════
# БОКОВАЯ ПАНЕЛЬ
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌌 Aetheris")
    st.caption("Аналитический крипто-терминал")
    st.divider()

    root_ok = api_get("../")
    if root_ok:
        st.markdown('<span class="online-badge">&#9679; API подключён</span>', unsafe_allow_html=True)
    else:
        st.error("Бэкенд не запущен!")
    st.markdown("")

    raw_tickers = api_get("tickers")
    if raw_tickers and isinstance(raw_tickers, list):
        ticker_list  = [t["symbol"] for t in raw_tickers]
        ticker_names = {t["symbol"]: t["name"] for t in raw_tickers}
    else:
        ticker_list  = list(DEFAULT_COINS.keys())
        ticker_names = dict(DEFAULT_COINS)

    st.markdown("**Выбор актива**")
    selected_coin = st.selectbox(
        "Актив",
        options=ticker_list,
        format_func=lambda s: f"{s}  —  {ticker_names.get(s, s)}",
        label_visibility="collapsed",
    )
    st.divider()

    auto_refresh = st.checkbox("Авто-обновление (30 с)", value=False)
    st.divider()

    st.markdown("**Добавить актив**")
    with st.form("form_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_sym  = st.text_input("Тикер", placeholder="LINK")
        with c2:
            new_name = st.text_input("Название", placeholder="Chainlink")
        if st.form_submit_button("Добавить", use_container_width=True):
            sym = new_sym.upper().strip()
            nam = new_name.strip()
            if sym and nam:
                if api_post("tickers", {"symbol": sym, "name": nam}):
                    st.success(f"{sym} добавлен!")
                    st.rerun()
                else:
                    st.error("Уже отслеживается или ошибка.")
            else:
                st.warning("Заполните оба поля.")

    removable = [t for t in ticker_list if t != selected_coin]
    if removable:
        st.markdown("**Удалить актив**")
        to_remove = st.selectbox("Актив", removable, label_visibility="collapsed")
        if st.button(f"Удалить {to_remove}", use_container_width=True):
            if api_delete(f"tickers/{to_remove}"):
                st.success(f"{to_remove} удалён")
                st.rerun()
            else:
                st.error("Не удалось удалить.")

# ══════════════════════════════════════════════════════════════════════════════
# ПОЛУЧЕНИЕ ДАННЫХ + УВЕДОМЛЕНИЯ
# ══════════════════════════════════════════════════════════════════════════════
market = api_get(f"market/{selected_coin}")

for log in (api_get("alerts/logs") or [])[:5]:
    key = f"{log.get('alert_id')}_{log.get('timestamp')}"
    if key not in st.session_state.seen_alerts:
        st.toast(log.get("message", "Алерт сработал"), icon="🚨")
        st.session_state.seen_alerts.add(key)

# ══════════════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ КОНТЕНТ
# ══════════════════════════════════════════════════════════════════════════════
coin_label = ticker_names.get(selected_coin, selected_coin)
st.markdown(f"## {selected_coin} &nbsp;·&nbsp; {coin_label}", unsafe_allow_html=True)

if not market:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.error("""
### Бэкенд недоступен
Запустите сервер:
```
cd F:\\AGACP\\agy-cryptomarket-app
.venv\\Scripts\\activate
uvicorn backend.app.main:app --reload
```
        """)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    st.stop()

# ── Верхние метрики ──────────────────────────────────────────────────────────
price   = float(market.get("price", 0))
change  = float(market.get("change_24h", 0))
volume  = float(market.get("volume_24h", 0))
mktcap  = float(market.get("market_cap", 0))

price_str = f"${price:,.2f}" if price >= 1 else f"${price:,.6f}"
chg_str   = f"{change:+.2f}%"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Цена (USD)", price_str, chg_str)
m2.metric("Изменение за 24 ч", chg_str)
m3.metric("Объём за 24 ч", f"${volume:,.0f}")
m4.metric("Рыночная капитализация", f"${mktcap:,.0f}")

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
# ИИ-АНАЛИТИКА — главный блок
# ══════════════════════════════════════════════════════════════════════════════
analysis = build_ai_analysis(selected_coin, market)

overall_badge = signal_badge_html(analysis["overall_signal"], f"СИГНАЛ: {analysis['overall_label']}")
rsi_badge     = signal_badge_html(analysis["rsi_signal"], f"RSI: {analysis['rsi']:.1f}")
macd_badge    = signal_badge_html(analysis["macd_signal"], "MACD")
trend_badge   = signal_badge_html(analysis["trend_signal"], f"24Ч: {analysis['change_24h']:+.2f}%")

st.markdown(f"""
<div class="ai-card">
  <div class="ai-card-title">🤖 ИИ-Аналитика · {selected_coin} · {datetime.utcnow().strftime("%d.%m.%Y %H:%M")} UTC</div>
  <div style="margin-bottom:14px;">
    {overall_badge}{rsi_badge}{macd_badge}{trend_badge}
  </div>
  <div class="ai-summary">{analysis["summary"]}</div>
  <hr style="border-color:rgba(255,255,255,0.06);margin:14px 0;">
  <div style="display:flex;gap:40px;flex-wrap:wrap;">
    <div>
      <div class="ind-row">
        <span class="ind-label">RSI (14)</span>
        <span class="ind-val {signal_color(analysis['rsi_signal'])}">{analysis['rsi']:.2f}</span>
      </div>
      <div class="ind-row">
        <span class="ind-label">Изменение 24 ч</span>
        <span class="ind-val {'val-green' if change>=0 else 'val-red'}">{change:+.2f}%</span>
      </div>
    </div>
    <div>
      <div class="ind-row">
        <span class="ind-label">Пивот (PP)</span>
        <span class="ind-val val-white">{f"${analysis['pp']:,.2f}" if analysis['pp'] else "—"}</span>
      </div>
      <div class="ind-row">
        <span class="ind-label">Поддержка S1</span>
        <span class="ind-val val-green">{f"${analysis['s1']:,.2f}" if analysis['s1'] else "—"}</span>
      </div>
      <div class="ind-row">
        <span class="ind-label">Сопротивление R1</span>
        <span class="ind-val val-red">{f"${analysis['r1']:,.2f}" if analysis['r1'] else "—"}</span>
      </div>
    </div>
  </div>
  <div style="margin-top:12px;padding:10px 14px;background:rgba(168,85,247,0.07);border-radius:8px;font-size:0.82rem;color:#c4b5fd;">
    ⚠️ Данная аналитика носит информационный характер и не является финансовым советом. Всегда проверяйте сигналы и управляйте рисками.
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ТАБЫ
# ══════════════════════════════════════════════════════════════════════════════
tab_chart, tab_alerts, tab_news = st.tabs([
    "📉  График и Индикаторы",
    "🚨  Алерты",
    "📰  Новости",
])

# ────────────────────────────────────────────────────────────────────────────
# ТАБ 1: ГРАФИК
# ────────────────────────────────────────────────────────────────────────────
with tab_chart:
    ohlc_raw  = market.get("ohlc", [])
    rsi_vals  = market.get("rsi", [])
    macd_data = market.get("macd", {})
    levels    = market.get("support_resistance", {})

    if not ohlc_raw:
        st.info("Ожидание OHLC данных от бэкенда...")
    else:
        rows = []
        for candle in ohlc_raw:
            dt = to_dt(candle[0])
            if dt is not None:
                rows.append({
                    "time":  dt,
                    "open":  float(candle[1]),
                    "high":  float(candle[2]),
                    "low":   float(candle[3]),
                    "close": float(candle[4]),
                })

        if not rows:
            st.warning("Некорректные временные метки в свечах.")
        else:
            df = pd.DataFrame(rows).sort_values("time").reset_index(drop=True)

            ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])
            with ctrl1:
                indicator = st.radio(
                    "Индикатор под графиком",
                    ["RSI", "MACD"],
                    horizontal=True,
                )
            with ctrl2:
                show_levels = st.checkbox("Показать уровни S/R", value=True)
            with ctrl3:
                st.markdown(
                    '<div class="hint-box">🖱️ <b>Масштаб:</b> колёсико мыши · '
                    'перетащи для зума · двойной клик — сброс · '
                    'кнопки периода ниже графика</div>',
                    unsafe_allow_html=True,
                )

            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.70, 0.30],
            )

            # Свечной график
            fig.add_trace(
                go.Candlestick(
                    x=df["time"],
                    open=df["open"], high=df["high"],
                    low=df["low"],   close=df["close"],
                    name="Цена",
                    increasing_line_color="#10b981",
                    decreasing_line_color="#f43f5e",
                    increasing_fillcolor="#10b981",
                    decreasing_fillcolor="#f43f5e",
                ),
                row=1, col=1,
            )

            # Уровни S/R
            if show_levels:
                pivots      = levels.get("pivot_points", {})
                supports    = levels.get("supports", [])
                resistances = levels.get("resistances", [])

                pp_val = pivots.get("PP")
                if pp_val:
                    fig.add_hline(
                        y=pp_val, line_dash="dash",
                        line_color="rgba(168,85,247,0.6)",
                        annotation_text=f"PP {pp_val:,.2f}",
                        annotation_font_color="#a855f7",
                        row=1, col=1,
                    )
                for idx, s in enumerate(supports[:3]):
                    fig.add_hline(
                        y=s, line_dash="dot",
                        line_color="rgba(16,185,129,0.5)",
                        annotation_text=f"S{idx+1} {s:,.2f}",
                        annotation_font_color="#10b981",
                        row=1, col=1,
                    )
                for idx, r in enumerate(resistances[:3]):
                    fig.add_hline(
                        y=r, line_dash="dot",
                        line_color="rgba(244,63,94,0.5)",
                        annotation_text=f"R{idx+1} {r:,.2f}",
                        annotation_font_color="#f43f5e",
                        row=1, col=1,
                    )

            # Под-график: RSI
            if indicator == "RSI" and rsi_vals:
                rsi_trimmed = rsi_vals[-len(df):]
                if len(rsi_trimmed) == len(df):
                    fig.add_trace(
                        go.Scatter(x=df["time"], y=rsi_trimmed, name="RSI",
                                   line=dict(color="#f59e0b", width=1.8)),
                        row=2, col=1,
                    )
                    fig.add_hline(y=70, line_dash="dot", line_color="rgba(244,63,94,0.4)", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dot", line_color="rgba(16,185,129,0.4)", row=2, col=1)
                    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(244,63,94,0.04)", line_width=0, row=2, col=1)
                    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(16,185,129,0.04)", line_width=0, row=2, col=1)
                    fig.update_yaxes(range=[0, 100], row=2, col=1)

            # Под-график: MACD
            elif indicator == "MACD" and macd_data:
                ml = macd_data.get("macd_line", [])[-len(df):]
                sl = macd_data.get("signal_line", [])[-len(df):]
                hi = macd_data.get("histogram", [])[-len(df):]
                if len(ml) == len(df):
                    bar_colors = ["#10b981" if v >= 0 else "#f43f5e" for v in hi]
                    fig.add_trace(go.Bar(x=df["time"], y=hi, name="Гистограмма",
                                         marker_color=bar_colors, opacity=0.55), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df["time"], y=ml, name="MACD",
                                             line=dict(color="#06b6d4", width=1.8)), row=2, col=1)
                    fig.add_trace(go.Scatter(x=df["time"], y=sl, name="Сигнал",
                                             line=dict(color="#a855f7", width=1.8)), row=2, col=1)

            # Кнопки диапазона + rangeslider
            fig.update_layout(
                height=640,
                margin=dict(l=8, r=8, t=28, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(6,8,20,0.65)",
                font=dict(color="#9ca3af", size=11),
                legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
                hovermode="x unified",
                xaxis=dict(
                    rangeslider=dict(visible=True, thickness=0.04, bgcolor="rgba(14,18,38,0.8)"),
                    rangeselector=dict(
                        bgcolor="rgba(14,18,38,0.9)",
                        activecolor="rgba(168,85,247,0.4)",
                        bordercolor="rgba(255,255,255,0.1)",
                        font=dict(color="#9ca3af"),
                        buttons=[
                            dict(count=7,  label="7Д",  step="day",   stepmode="backward"),
                            dict(count=14, label="14Д", step="day",   stepmode="backward"),
                            dict(count=1,  label="1М",  step="month", stepmode="backward"),
                            dict(step="all", label="Всё"),
                        ],
                    ),
                    type="date",
                ),
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", showline=False)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", showline=False)

            st.plotly_chart(fig, use_container_width=True)

            # Пивот-уровни под графиком
            st.markdown("**Классические пивот-уровни**")
            pivots_full = levels.get("pivot_points", {})
            pc1, pc2, pc3, pc4, pc5 = st.columns(5)
            for col, key, lbl in [
                (pc1, "S2", "S2 Поддержка 2"),
                (pc2, "S1", "S1 Поддержка 1"),
                (pc3, "PP", "PP Пивот"),
                (pc4, "R1", "R1 Сопротивление 1"),
                (pc5, "R2", "R2 Сопротивление 2"),
            ]:
                val = pivots_full.get(key)
                col.metric(lbl, f"${val:,.2f}" if val else "—")

# ────────────────────────────────────────────────────────────────────────────
# ТАБ 2: АЛЕРТЫ
# ────────────────────────────────────────────────────────────────────────────
with tab_alerts:
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("#### Создать правило алерта")
        st.caption(f"Актив: **{selected_coin}** · Цена: **{price_str}**")

        with st.form("form_alert", clear_on_submit=True):
            metric_choice = st.selectbox(
                "Метрика",
                ["price", "rsi"],
                format_func=lambda x: "Цена (USD)" if x == "price" else "RSI (0-100)",
            )
            cond_choice = st.selectbox(
                "Условие",
                ["above", "below"],
                format_func=lambda x: "Поднимется выше ↑" if x == "above" else "Упадёт ниже ↓",
            )
            default_thresh = price if metric_choice == "price" else 70.0
            threshold = st.number_input("Порог", value=float(default_thresh), format="%.4f")

            if st.form_submit_button("Активировать алерт", use_container_width=True, type="primary"):
                ok = api_post("alerts", {
                    "ticker": selected_coin, "metric": metric_choice,
                    "condition": cond_choice, "value": threshold,
                })
                if ok:
                    st.success("Алерт создан!")
                    st.rerun()
                else:
                    st.error("Ошибка создания.")

        st.divider()
        st.markdown("#### Удалить правила")
        del_id = st.text_input("ID алерта для удаления", placeholder="Скопируйте ID из таблицы →")
        d1, d2 = st.columns(2)
        with d1:
            if st.button("Удалить по ID", use_container_width=True):
                if del_id:
                    if api_delete(f"alerts/{del_id}"):
                        st.success("Удалён.")
                        st.rerun()
                    else:
                        st.error("ID не найден.")
                else:
                    st.warning("Вставьте ID.")
        with d2:
            if st.button("Очистить всё", use_container_width=True):
                api_delete("alerts")
                st.success("Все удалены.")
                st.rerun()

    with right_col:
        st.markdown("#### Активные правила")
        rules = api_get("alerts") or []
        if rules:
            df_r = pd.DataFrame(rules)
            cols = [c for c in ["id", "ticker", "metric", "condition", "value", "status"] if c in df_r.columns]
            st.dataframe(df_r[cols], use_container_width=True, hide_index=True)
        else:
            st.info("Нет активных правил. Создайте слева.")

        st.markdown("#### Журнал срабатываний")
        logs = api_get("alerts/logs") or []
        if logs:
            r1c, r2c = st.columns([3, 1])
            with r2c:
                if st.button("Очистить лог", use_container_width=True):
                    api_delete("alerts/logs")
                    st.rerun()
            for log in logs[:20]:
                try:
                    ts = datetime.fromisoformat(log.get("timestamp", "")).strftime("%H:%M:%S")
                except Exception:
                    ts = log.get("timestamp", "?")
                st.markdown(
                    f'<div class="alert-row">🚨 <strong>{ts}</strong> — {log.get("message", "")}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Срабатываний нет — система работает штатно.")

# ────────────────────────────────────────────────────────────────────────────
# ТАБ 3: НОВОСТИ
# ────────────────────────────────────────────────────────────────────────────
with tab_news:
    st.markdown(f"#### Новости: {selected_coin} / {coin_label}")
    st.caption("Источник: CryptoPanic · Перевод заголовков — через ссылку Google Translate")

    news_items = market.get("news", [])
    if not news_items:
        st.info("Новости не найдены. Установите переменную окружения CRYPTOPANIC_API_TOKEN.")
    else:
        for item in news_items:
            sentiment = item.get("sentiment", "neutral").lower()
            sent_ru   = SENTIMENT_RU.get(sentiment, "НЕЙТРАЛЬНЫЙ")
            badge     = f'<span class="badge-{sentiment}">{sent_ru}</span>'

            try:
                pub = datetime.fromisoformat(item.get("published_at", "")).strftime("%d.%m %H:%M")
            except Exception:
                pub = item.get("published_at", "")

            source = item.get("source", "")
            title  = item.get("title", "Без заголовка")
            url    = item.get("url", "#")
            # Google Translate ссылка для перевода статьи
            translate_url = f"https://translate.google.com/translate?sl=en&tl=ru&u={url}"

            st.markdown(f"""
<div class="news-card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="color:#6b7280;font-size:0.78rem;">{source} &nbsp;·&nbsp; {pub}</span>
    {badge}
  </div>
  <a href="{url}" target="_blank"
     style="color:#e2e8f0;font-weight:600;font-size:0.95rem;text-decoration:none;line-height:1.45;display:block;margin-bottom:8px;">
    {title}
  </a>
  <a href="{translate_url}" target="_blank"
     style="color:#6b7280;font-size:0.75rem;text-decoration:none;">
    🌐 Читать на русском (Google Translate)
  </a>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# АВТО-ОБНОВЛЕНИЕ
# ══════════════════════════════════════════════════════════════════════════════
if auto_refresh:
    time.sleep(30)
    st.rerun()
