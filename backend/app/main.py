import os
import json
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.clients.coingecko import CoinGeckoClient
from backend.app.clients.cryptopanic import CryptoPanicClient
from backend.app.services.market import MarketService
from backend.app.services.alerts import AlertService
from backend.app.workers.updates import BackgroundWorker, GLOBAL_MARKET_CACHE
from backend.app.api.routes import router as api_router, set_alert_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("backend.main")

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket broadcast: {e}")

manager = ConnectionManager()

async def on_alerts_triggered_callback(triggered_alerts: List[Dict[str, Any]]):
    """
    Callback executed by the BackgroundWorker when alert rules are met.
    Broadcasts the triggered alerts to all connected WebSocket clients.
    """
    if not triggered_alerts:
        return
    
    logger.info(f"Broadcasting {len(triggered_alerts)} triggered alerts to WebSockets...")
    message = json.dumps(triggered_alerts)
    await manager.broadcast(message)

# Initialize global services and clients
coingecko_client = CoinGeckoClient()
cryptopanic_token = os.getenv("CRYPTOPANIC_API_TOKEN")
cryptopanic_client = CryptoPanicClient(api_token=cryptopanic_token)

market_service = MarketService()
alert_service = AlertService()

# Set up API route connection to AlertService
set_alert_service(alert_service)

# Set up background worker (inject WebSocket broadcast callback)
worker = BackgroundWorker(
    coingecko=coingecko_client,
    cryptopanic=cryptopanic_client,
    market_service=market_service,
    alert_service=alert_service,
    on_alert_triggered=on_alerts_triggered_callback
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background tasks worker
    logger.info("Initializing services and background updates worker...")
    await worker.start()
    yield
    # Shutdown: Stop background tasks worker
    logger.info("Shutting down background updates worker...")
    await worker.stop()

# Initialize FastAPI App
app = FastAPI(
    title="Aetheris Crypto Terminal API",
    description="Backend API serving real-time indicators, S/R levels, news feeds, and alert notifications.",
    version="1.1.0",
    lifespan=lifespan
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# WebSocket Endpoint for Real-time Alert Notifications
@app.websocket("/api/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection, listen for close events
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Aetheris Crypto Terminal API",
        "supported_tickers": [t["symbol"] for t in alert_service.get_all_tickers()],
        "coingecko_cache_status": "loaded" if GLOBAL_MARKET_CACHE else "empty",
        "websocket_clients": len(manager.active_connections)
    }
