import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from backend.app.clients.coingecko import CoinGeckoClient
from backend.app.clients.cryptopanic import CryptoPanicClient
from backend.app.services.market import MarketService
from backend.app.services.alerts import AlertService

logger = logging.getLogger(__name__)

# Global cache to share market data between background worker and FastAPI routes
# This prevents hitting CoinGecko API rate limits on every user refresh
GLOBAL_MARKET_CACHE: Dict[str, Dict[str, Any]] = {}

class BackgroundWorker:
    def __init__(self, coingecko: CoinGeckoClient, cryptopanic: CryptoPanicClient, market_service: MarketService, alert_service: AlertService):
        self.coingecko = coingecko
        self.cryptopanic = cryptopanic
        self.market = market_service
        self.alerts = alert_service
        self.is_running = False
        self.tickers = ["BTC", "ETH", "SOL", "MATIC", "TON"]
        self.poll_interval = 30 # seconds

    async def start(self):
        self.is_running = True
        logger.info("Starting background worker loop...")
        asyncio.create_task(self._loop())

    async def stop(self):
        self.is_running = False
        logger.info("Stopping background worker loop...")

    async def _loop(self):
        # Warmup cache first
        await self.tick()
        
        while self.is_running:
            try:
                await asyncio.sleep(self.poll_interval)
                await self.tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background worker tick: {e}", exc_info=True)

    async def tick(self):
        logger.info(f"Background worker tick started at {datetime.now()}")
        
        for ticker in self.tickers:
            try:
                # 1. Fetch live metrics (Price, volume, Cap)
                live_data = await self.coingecko.get_market_data(ticker)
                
                # 2. Fetch historical OHLC (last 30 days)
                ohlc = await self.coingecko.get_historical_ohlc(ticker, days=30)
                
                if not ohlc:
                    logger.warning(f"Could not retrieve historical OHLC for {ticker}. Skipping indicators.")
                    continue
                
                # 3. Calculate indicators (RSI, MACD)
                closes = [candle[4] for candle in ohlc]
                rsi_vals = self.market.calculate_rsi(closes)
                macd_data = self.market.calculate_macd(closes)
                
                # 4. Calculate Support/Resistance zones
                levels = self.market.calculate_support_resistance(ohlc)
                
                latest_rsi = rsi_vals[-1] if rsi_vals else 50.0
                latest_macd = macd_data["macd_line"][-1] if macd_data["macd_line"] else 0.0
                latest_signal = macd_data["signal_line"][-1] if macd_data["signal_line"] else 0.0
                latest_hist = macd_data["histogram"][-1] if macd_data["histogram"] else 0.0
                
                # 5. Evaluate alert rules
                newly_triggered = self.alerts.evaluate_rules(
                    ticker=ticker,
                    current_price=live_data["price"],
                    current_rsi=latest_rsi
                )
                
                # 6. Fetch news (CryptoPanic)
                news = await self.cryptopanic.get_news(ticker)
                
                # 7. Write to Global Shared State
                GLOBAL_MARKET_CACHE[ticker.upper()] = {
                    "ticker": ticker.upper(),
                    "price": live_data["price"],
                    "market_cap": live_data["market_cap"],
                    "volume_24h": live_data["volume_24h"],
                    "change_24h": live_data["change_24h"],
                    "ohlc": ohlc,
                    "rsi": rsi_vals,
                    "macd": macd_data,
                    "support_resistance": levels,
                    "news": news,
                    "last_updated": datetime.now().isoformat()
                }
                
                logger.info(f"Updated cache and evaluated rules for {ticker} (Price: {live_data['price']}, RSI: {round(latest_rsi, 2)})")
                
            except Exception as e:
                logger.error(f"Failed to fetch updates for ticker {ticker}: {e}", exc_info=True)
                
        logger.info("Background worker tick completed.")
