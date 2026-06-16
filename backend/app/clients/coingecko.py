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

# Circulating supply approximations for fallback market cap calculations (Binance data)
SUPPLY_MAP = {
    "BTC": 19700000,
    "ETH": 120000000,
    "SOL": 460000000,
    "MATIC": 9900000000,
    "TON": 2500000000
}

class CoinGeckoClient:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.binance_base_url = "https://api.binance.com/api/v3"
        
        # In-memory fallback caches
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.ohlc_cache: Dict[str, List[List[float]]] = {}

    async def get_market_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches current price, 24h volume, market cap, and 24h change.
        Falls back to Binance API if CoinGecko returns 429 rate limit or errors.
        """
        ticker_upper = ticker.upper()
        coin_id = TICKER_MAP.get(ticker_upper, ticker.lower())
        
        url = f"{self.base_url}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        result = {
                            "price": float(coin_data.get("usd", 0.0)),
                            "market_cap": float(coin_data.get("usd_market_cap", 0.0)),
                            "volume_24h": float(coin_data.get("usd_24h_volume", 0.0)),
                            "change_24h": float(coin_data.get("usd_24h_change", 0.0))
                        }
                        self.price_cache[ticker_upper] = result
                        return result
                
                logger.warning(f"CoinGecko simple price returned status {response.status_code}. Initiating Binance fallback...")
                
        except Exception as e:
            logger.error(f"Error calling CoinGecko simple price for {ticker}: {e}. Initiating Binance fallback...")

        # Fallback to Binance API
        return await self._fetch_binance_market_data(ticker_upper)

    async def _fetch_binance_market_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch market metrics from Binance public ticker API.
        """
        binance_symbol = f"{ticker}USDT"
        url = f"{self.binance_base_url}/ticker/24hr"
        params = {"symbol": binance_symbol}
        
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    price = float(data.get("lastPrice", 0.0))
                    change = float(data.get("priceChangePercent", 0.0))
                    volume = float(data.get("quoteVolume", 0.0)) # Volume in USDT/USD
                    
                    # Approximate market cap using hardcoded circulating supply
                    supply = SUPPLY_MAP.get(ticker, 1000000000)
                    market_cap = price * supply
                    
                    result = {
                        "price": price,
                        "market_cap": market_cap,
                        "volume_24h": volume,
                        "change_24h": change
                    }
                    self.price_cache[ticker] = result
                    logger.info(f"Binance fallback successful for {ticker} simple price.")
                    return result
                    
                logger.warning(f"Binance fallback simple price returned status {response.status_code}.")
        except Exception as e:
            logger.error(f"Failed to fetch fallback simple price from Binance for {ticker}: {e}")
            
        # If both failed, use local cache or return zeros
        if ticker in self.price_cache:
            logger.info(f"Using local price cache for {ticker}.")
            return self.price_cache[ticker]
            
        return {"price": 0.0, "market_cap": 0.0, "volume_24h": 0.0, "change_24h": 0.0}

    async def get_historical_ohlc(self, ticker: str, days: int = 30) -> List[List[float]]:
        """
        Fetches historical OHLC data. Falls back to Binance Klines if CoinGecko is rate-limited.
        """
        ticker_upper = ticker.upper()
        coin_id = TICKER_MAP.get(ticker_upper, ticker.lower())
        cache_key = f"{ticker_upper}_{days}"
        
        # Valid days for CoinGecko
        valid_days = [1, 7, 14, 30, 90, 180, 365]
        if days not in valid_days:
            days = 30
            
        url = f"{self.base_url}/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days
        }
        
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    self.ohlc_cache[cache_key] = data
                    return data
                
                logger.warning(f"CoinGecko OHLC returned status {response.status_code}. Initiating Binance Klines fallback...")
                
        except Exception as e:
            logger.error(f"Error calling CoinGecko OHLC for {ticker}: {e}. Initiating Binance Klines fallback...")
            
        # Fallback to Binance Klines
        return await self._fetch_binance_ohlc(ticker_upper, days)

    async def _fetch_binance_ohlc(self, ticker: str, days: int) -> List[List[float]]:
        """
        Fetch historical candles (klines) from Binance.
        """
        binance_symbol = f"{ticker}USDT"
        url = f"{self.binance_base_url}/klines"
        
        # Map days to limit and interval
        # CoinGecko days=30 yields daily or 4-hourly data.
        # We'll fetch daily (1d) candles with limit same as days
        interval = "1d"
        limit = days
        
        if days == 1:
            interval = "30m"
            limit = 48
        elif days == 7:
            interval = "2h"
            limit = 84
            
        params = {
            "symbol": binance_symbol,
            "interval": interval,
            "limit": limit
        }
        
        cache_key = f"{ticker}_{days}"
        
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Binance Klines structure:
                    # [ [ open_time, open, high, low, close, volume, close_time ... ] ]
                    # We map this to CoinGecko OHLC format:
                    # [ [ timestamp_sec, open, high, low, close ] ]
                    ohlc = []
                    for k in data:
                        ohlc.append([
                            float(k[0]) / 1000, # Unix timestamp in seconds
                            float(k[1]),       # Open
                            float(k[2]),       # High
                            float(k[3]),       # Low
                            float(k[4])        # Close
                        ])
                    
                    self.ohlc_cache[cache_key] = ohlc
                    logger.info(f"Binance Klines fallback successful for {ticker} ({len(ohlc)} periods).")
                    return ohlc
                    
                logger.warning(f"Binance Klines fallback returned status {response.status_code}.")
        except Exception as e:
            logger.error(f"Failed to fetch fallback Klines from Binance for {ticker}: {e}")
            
        # Use cache if both failed
        if cache_key in self.ohlc_cache:
            logger.info(f"Using local OHLC cache for {ticker}.")
            return self.ohlc_cache[cache_key]
            
        return []
