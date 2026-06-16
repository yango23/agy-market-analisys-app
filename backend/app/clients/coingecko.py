import logging
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

TICKER_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "MATIC": "matic-network",
    "TON": "the-open-network"
}

class CoinGeckoClient:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        # CoinGecko public API can be heavily rate-limited (429). We'll add memory-cache to fall back on.
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.ohlc_cache: Dict[str, List[List[float]]] = {}

    async def get_market_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches current price, 24h volume, market cap, and 24h change.
        """
        coin_id = TICKER_MAP.get(ticker.upper())
        if not coin_id:
            logger.warning(f"Ticker {ticker} not found in map. Defaulting to id same as ticker.")
            coin_id = ticker.lower()

        url = f"{self.base_url}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        result = {
                            "price": coin_data.get("usd", 0.0),
                            "market_cap": coin_data.get("usd_market_cap", 0.0),
                            "volume_24h": coin_data.get("usd_24h_volume", 0.0),
                            "change_24h": coin_data.get("usd_24h_change", 0.0)
                        }
                        self.price_cache[coin_id] = result
                        return result
                
                # Handle rate limits or errors
                logger.warning(f"CoinGecko API returned status {response.status_code} for simple price. Using cache.")
                if coin_id in self.price_cache:
                    return self.price_cache[coin_id]
                
        except Exception as e:
            logger.error(f"Error fetching market data from CoinGecko for {ticker}: {e}")
            if coin_id in self.price_cache:
                return self.price_cache[coin_id]
                
        # Return fallback zeros if no cache exists
        return {"price": 0.0, "market_cap": 0.0, "volume_24h": 0.0, "change_24h": 0.0}

    async def get_historical_ohlc(self, ticker: str, days: int = 30) -> List[List[float]]:
        """
        Fetches historical OHLC data (Days options: 1, 7, 14, 30, 90, 180, 365).
        Returns list of [timestamp, open, high, low, close]
        """
        coin_id = TICKER_MAP.get(ticker.upper()) or ticker.lower()
        
        # Days parameter must be valid for CoinGecko
        valid_days = [1, 7, 14, 30, 90, 180, 365]
        if days not in valid_days:
            days = 30
            
        url = f"{self.base_url}/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        cache_key = f"{coin_id}_{days}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    self.ohlc_cache[cache_key] = data
                    return data
                
                logger.warning(f"CoinGecko API returned status {response.status_code} for OHLC. Using cache.")
                if cache_key in self.ohlc_cache:
                    return self.ohlc_cache[cache_key]
                    
        except Exception as e:
            logger.error(f"Error fetching historical OHLC from CoinGecko for {ticker}: {e}")
            if cache_key in self.ohlc_cache:
                return self.ohlc_cache[cache_key]
                
        return []
