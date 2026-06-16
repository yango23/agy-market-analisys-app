import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.clients.coingecko import CoinGeckoClient
from backend.app.clients.cryptopanic import CryptoPanicClient
from backend.app.services.market import MarketService
from backend.app.services.alerts import AlertService
from backend.app.workers.updates import BackgroundWorker
from backend.app.api.routes import router as api_router, set_alert_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("backend.main")

# Initialize global services and clients
coingecko_client = CoinGeckoClient()
# Optionally retrieve CryptoPanic API token from environment variables
cryptopanic_token = os.getenv("CRYPTOPANIC_API_TOKEN")
cryptopanic_client = CryptoPanicClient(api_token=cryptopanic_token)

market_service = MarketService()
alert_service = AlertService()

# Set up API route connection to AlertService
set_alert_service(alert_service)

# Set up background worker
worker = BackgroundWorker(
    coingecko=coingecko_client,
    cryptopanic=cryptopanic_client,
    market_service=market_service,
    alert_service=alert_service
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
    version="1.0.0",
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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Aetheris Crypto Terminal API",
        "supported_tickers": worker.tickers,
        "coingecko_cache_status": "loaded" if GLOBAL_MARKET_CACHE else "empty"
    }

from backend.app.workers.updates import GLOBAL_MARKET_CACHE
