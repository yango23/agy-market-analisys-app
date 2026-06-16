# AI Agents Developer Guide: Aetheris Crypto Terminal

This document provides system design documentation, architectural guidelines, and codebase conventions for other AI developer agents (such as Gemini, Claude, or Aider) working on this project.

---

## 1. High-Level Architecture

The project consists of an asynchronous **FastAPI backend** and an interactive **Streamlit frontend**. 

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Background Task Engine                         │
│                                                                        │
│  ┌──────────────────┐      Polls (30s)      ┌───────────────────────┐  │
│  │ CoinGeckoClient  ├──────────────────────►│   BackgroundWorker    │  │
│  └──────────────────┘                       │                       │  │
│  ┌──────────────────┐      Polls (30s)      │  - Runs Calculations  │  │
│  │CryptoPanicClient ├──────────────────────►│  - Evaluates Rules    │  │
│  └──────────────────┘                       │  - Writes to Cache    │  │
│                                             └──────────┬────────────┘  │
└────────────────────────────────────────────────────────┼───────────────┘
                                                         │ Updates
                                                         ▼
                                              ┌───────────────────────┐
                                              │ GLOBAL_MARKET_CACHE   │
                                              └──────────▲────────────┘
                                                         │ Reads
                                                         │
┌────────────────────────┐                    ┌──────────┴────────────┐
│   Streamlit Frontend   │     HTTP requests  │      FastAPI App      │
│                        ├───────────────────►│                       │
│  - Renders Charts      │                    │  - REST Routes        │
│  - Polls for Toasts    │                    │  - Alert Registration │
└────────────────────────┘                    └───────────────────────┘
```

### Core Design Principle: Decoupling of Updates from Web Requests
**CRITICAL**: Do NOT invoke external APIs (CoinGecko, CryptoPanic) directly inside the FastAPI route handlers. CoinGecko public API has strict rate limits (429 errors). Instead:
- All external API polling, data manipulation, indicator calculations, and alert triggers are handled by the async `BackgroundWorker` loop.
- Calculated results are saved to a global memory-cache structure (`GLOBAL_MARKET_CACHE`).
- Route handlers simply read from `GLOBAL_MARKET_CACHE` and return cached results instantly.

---

## 2. Codebase Components & Symbols Reference

When modifying or expanding the codebase, map your edits to these files:

### Clients
- [coingecko.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/clients/coingecko.py): Interfaces with CoinGecko API for spot price and historical OHLC. Includes fallback local memory caching for error conditions.
- [cryptopanic.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/clients/cryptopanic.py): Interfaces with CryptoPanic API for currency news. Generates mock articles for supported currencies (BTC, ETH, SOL, MATIC, TON) if no token is available.

### Services (Pure Business Logic)
- [market.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/services/market.py): Contains mathematics and statistical calculations:
  - `calculate_rsi`: Wilder's RSI.
  - `calculate_macd`: Fast/Slow EMA crossover logic.
  - `calculate_support_resistance`: Classical pivot points + fractal-clustering zones.
- [alerts.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/services/alerts.py): Memory-based alert registry. Evaluates active trigger conditions against prices and indicators, logs triggers, and outputs notices to the console.

### Workers & Routes
- [updates.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/workers/updates.py): Declares `BackgroundWorker` loop and shares `GLOBAL_MARKET_CACHE` states.
- [routes.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/api/routes.py): FastAPI REST routes. Handles endpoint requests for alerts registry, metrics, and news.

### Frontend
- [app.py](file:///F:/AGACP/agy-cryptomarket-app/frontend/app.py): Streamlit dashboard app layout, Plotly subplots, alert creation Forms, and trigger notification toasts.

---

## 3. Extending the Codebase: Guidelines

### Adding New Cryptocurrency Assets
To track a new token:
1. Map the symbol token to the CoinGecko coin ID in `TICKER_MAP` inside [coingecko.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/clients/coingecko.py).
2. Append the new asset to the `tickers` list in `BackgroundWorker.__init__` inside [updates.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/workers/updates.py).
3. Add the token symbol to `available_tickers` inside [app.py](file:///F:/AGACP/agy-cryptomarket-app/frontend/app.py).

### Introducing a New Technical Indicator
To add a new indicator (e.g. SMA, ATR, Bollinger Bands):
1. Implement the calculation logic as a method in `MarketService` inside [market.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/services/market.py) using Pandas or NumPy.
2. Update the background worker in [updates.py](file:///F:/AGACP/agy-cryptomarket-app/backend/app/workers/updates.py) to run the calculation and save it to the cache dict.
3. Update [app.py](file:///F:/AGACP/agy-cryptomarket-app/frontend/app.py) to plot the indicator on the Plotly charts.

### Session State Maintenance in Streamlit
Since Streamlit re-runs the script from top-to-bottom on every action:
- To prevent displaying the same notification toast multiple times, use the `shown_toasts` set in `st.session_state` to track shown alert timestamps.
