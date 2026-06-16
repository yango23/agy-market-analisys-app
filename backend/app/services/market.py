import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class MarketService:
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """
        Calculates Relative Strength Index (RSI).
        """
        if len(prices) <= period:
            return [50.0] * len(prices)
            
        series = pd.Series(prices)
        delta = series.diff()
        
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # Wilder's Smoothing Method
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, 0.00001)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0).tolist()

    def calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """
        Calculates Moving Average Convergence Divergence (MACD).
        Returns Dict with keys: macd_line, signal_line, histogram
        """
        if len(prices) < slow_period:
            zeros = [0.0] * len(prices)
            return {"macd_line": zeros, "signal_line": zeros, "histogram": zeros}
            
        series = pd.Series(prices)
        
        ema_fast = series.ewm(span=fast_period, adjust=False).mean()
        ema_slow = series.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd_line": macd_line.fillna(0.0).tolist(),
            "signal_line": signal_line.fillna(0.0).tolist(),
            "histogram": histogram.fillna(0.0).tolist()
        }

    def calculate_support_resistance(self, ohlc_data: List[List[float]], window_size: int = 5) -> Dict[str, Any]:
        """
        Calculates support and resistance levels using:
        1. Classical Pivot Points (from the last period / recent window)
        2. Local Min/Max Peaks (Fractals) across the historical period
        
        ohlc_data format: list of [timestamp, open, high, low, close]
        """
        if not ohlc_data or len(ohlc_data) < window_size * 2:
            return {"support": [], "resistance": [], "pivot_points": {}}
            
        df = pd.DataFrame(ohlc_data, columns=["timestamp", "open", "high", "low", "close"])
        
        # 1. Classical Pivot Points (based on the latest full candle or last window candles)
        # We take the aggregated High, Low, and Close of the last 5 periods (e.g. recent trends)
        recent_df = df.iloc[-window_size:]
        high = recent_df["high"].max()
        low = recent_df["low"].min()
        close = recent_df["close"].iloc[-1]
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        pivot_levels = {
            "PP": round(pivot, 4),
            "R1": round(r1, 4),
            "S1": round(s1, 4),
            "R2": round(r2, 4),
            "S2": round(s2, 4),
            "R3": round(r3, 4),
            "S3": round(s3, 4)
        }
        
        # 2. Local Min/Max Peaks (Fractals)
        supports = []
        resistances = []
        
        # Find local peaks
        for i in range(window_size, len(df) - window_size):
            is_support = True
            is_resistance = True
            
            current_low = df.iloc[i]["low"]
            current_high = df.iloc[i]["high"]
            
            for j in range(i - window_size, i + window_size + 1):
                if i == j:
                    continue
                if df.iloc[j]["low"] < current_low:
                    is_support = False
                if df.iloc[j]["high"] > current_high:
                    is_resistance = False
                    
            if is_support:
                supports.append(float(current_low))
            if is_resistance:
                resistances.append(float(current_high))
                
        # Group similar levels using simple clustering (histograms/binning) to find strong zones
        def cluster_levels(levels: List[float], tolerance_pct: float = 0.015) -> List[float]:
            if not levels:
                return []
            sorted_levels = sorted(levels)
            clustered = []
            
            # Simple greedy clustering
            current_cluster = [sorted_levels[0]]
            for lvl in sorted_levels[1:]:
                # If level is within tolerance_pct from the cluster mean
                mean = np.mean(current_cluster)
                if (lvl - mean) / mean <= tolerance_pct:
                    current_cluster.append(lvl)
                else:
                    clustered.append(float(np.mean(current_cluster)))
                    current_cluster = [lvl]
            clustered.append(float(np.mean(current_cluster)))
            
            # Sort by frequency or proximity (we just return sorted levels)
            return sorted(clustered)
            
        final_supports = cluster_levels(supports)
        final_resistances = cluster_levels(resistances)
        
        # Limit to top 4 strongest levels
        # Filter levels close to the current price
        current_price = close
        final_supports = sorted([s for s in final_supports if s < current_price], reverse=True)[:4]
        final_resistances = sorted([r for r in final_resistances if r > current_price])[:4]
        
        return {
            "supports": [round(s, 4) for s in final_supports],
            "resistances": [round(r, 4) for r in final_resistances],
            "pivot_points": pivot_levels
        }
