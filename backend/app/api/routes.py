from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from backend.app.workers.updates import GLOBAL_MARKET_CACHE
from backend.app.services.alerts import AlertService

router = APIRouter()

# AlertService dependency reference
alert_service: Optional[AlertService] = None

def set_alert_service(service: AlertService):
    global alert_service
    alert_service = service

# --- Schema Definitions ---
class AlertCreateRequest(BaseModel):
    ticker: str = Field(..., description="Crypto ticker symbol, e.g. BTC, ETH")
    metric: str = Field(..., description="Metric to track, either 'price' or 'rsi'")
    condition: str = Field(..., description="Condition, either 'above' or 'below'")
    value: float = Field(..., description="Threshold value")

class TickerCreateRequest(BaseModel):
    symbol: str = Field(..., description="Crypto ticker symbol, e.g. XRP, LINK")
    name: str = Field(..., description="Descriptive name, e.g. Ripple, Chainlink")

# --- Routes ---

# Tickers Management
@router.get("/tickers")
async def get_tickers():
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    return alert_service.get_all_tickers()

@router.post("/tickers")
async def add_ticker(req: TickerCreateRequest):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    
    symbol_upper = req.symbol.upper().strip()
    if not symbol_upper:
        raise HTTPException(status_code=400, detail="Invalid symbol name.")
        
    success = alert_service.add_ticker(symbol_upper, req.name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Ticker {symbol_upper} already exists.")
    return {"status": "success", "message": f"Ticker {symbol_upper} successfully added to database."}

@router.delete("/tickers/{symbol}")
async def delete_ticker(symbol: str):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    
    symbol_upper = symbol.upper().strip()
    success = alert_service.delete_ticker(symbol_upper)
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol_upper} not found in database.")
    return {"status": "success", "message": f"Ticker {symbol_upper} and its alerts deleted."}

# Market data
@router.get("/market/{ticker}")
async def get_market_data(ticker: str):
    ticker_upper = ticker.upper()
    if ticker_upper not in GLOBAL_MARKET_CACHE:
        raise HTTPException(
            status_code=404, 
            detail=f"Data for {ticker_upper} not loaded yet or not supported. Supported: {list(GLOBAL_MARKET_CACHE.keys())}"
        )
    return GLOBAL_MARKET_CACHE[ticker_upper]

@router.get("/news/{ticker}")
async def get_news_data(ticker: str):
    ticker_upper = ticker.upper()
    if ticker_upper not in GLOBAL_MARKET_CACHE:
        raise HTTPException(status_code=404, detail=f"News for {ticker_upper} not found.")
    return GLOBAL_MARKET_CACHE[ticker_upper].get("news", [])

# Alerts management
@router.get("/alerts")
async def get_alerts(ticker: Optional[str] = None):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    return alert_service.get_all_alerts(ticker)

@router.post("/alerts")
async def create_alert(req: AlertCreateRequest):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    
    # Validation
    if req.metric.lower() not in ["price", "rsi"]:
        raise HTTPException(status_code=400, detail="Invalid metric. Supported: 'price', 'rsi'")
    if req.condition.lower() not in ["above", "below"]:
        raise HTTPException(status_code=400, detail="Invalid condition. Supported: 'above', 'below'")
        
    alert = alert_service.create_alert(
        ticker=req.ticker,
        metric=req.metric,
        condition=req.condition,
        value=req.value
    )
    return alert

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    deleted = alert_service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"status": "success", "message": f"Alert {alert_id} deleted."}

@router.delete("/alerts")
async def clear_all_alerts():
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    alert_service.clear_all_alerts()
    return {"status": "success", "message": "All alert rules deleted."}

# Logs management
@router.get("/alerts/logs")
async def get_alert_logs(limit: int = 50):
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    return alert_service.get_trigger_logs(limit)

@router.delete("/alerts/logs")
async def clear_alert_logs():
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not initialized.")
    alert_service.clear_trigger_logs()
    return {"status": "success", "message": "Trigger logs cleared."}
