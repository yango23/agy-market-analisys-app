# Aetheris: Custom Crypto Analytics Terminal

A modular, real-time cryptocurrency analytical dashboard built with a **FastAPI** backend and a **Streamlit** frontend. The terminal aggregates price tickers, volume, and market capitalization, calculates support/resistance levels and technical indicators (RSI, MACD), displays live news feeds, and checks trigger alert conditions in a non-blocking background loop.

---

## Project Structure

```
agy-cryptomarket-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py      # FastAPI REST routes (market data, alerts, logs)
│   │   ├── clients/
│   │   │   ├── coingecko.py   # CoinGecko client (market/historical candles caching)
│   │   │   └── cryptopanic.py # CryptoPanic News client (sentiment parsing & mock generator)
│   │   ├── services/
│   │   │   ├── alerts.py      # Memory-based rules & alert evaluation service
│   │   │   └── market.py      # Indicators & Support/Resistance levels calculations
│   │   ├── workers/
│   │   │   └── updates.py     # Background worker loop polling CoinGecko/CryptoPanic
│   │   └── main.py            # FastAPI main entrypoint
├── frontend/
│   └── app.py                 # Streamlit dashboard layout & Plotly charts UI
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Setup Virtual Environment
Create and activate a virtual environment, then install dependencies:

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Terminal

The terminal requires both the Backend API and Frontend Streamlit dashboard to be running simultaneously.

### 1. Run the FastAPI Backend
Start the backend using Uvicorn:
```bash
# From the project root directory
.venv\Scripts\uvicorn backend.app.main:app --reload
```
*(On macOS/Linux, replace `.venv\Scripts\` with `.venv/bin/`)*

The backend will start on **`http://localhost:8000`**. You will see the background task worker warm up and fetch initial market data in the console.

### 2. Run the Streamlit Frontend
In a new terminal window (with the virtual environment activated), start Streamlit:
```bash
# From the project root directory
.venv\Scripts\streamlit run frontend/app.py
```
*(On macOS/Linux, replace `.venv\Scripts\` with `.venv/bin/`)*

The frontend will automatically open in your browser at **`http://localhost:8501`**.

---

## Git Operations Guide

To push this project to your remote repository (e.g., GitHub, GitLab, or Bitbucket), execute the following commands in your shell:

1. **Add remote repository URL:**
   ```bash
   git remote add origin <YOUR_REMOTE_REPOSITORY_URL>
   ```

2. **Rename default branch to main (optional but recommended):**
   ```bash
   git branch -M main
   ```

3. **Push to the remote repository:**
   ```bash
   git push -u origin main
   ```
