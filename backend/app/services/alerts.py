import os
import sqlite3
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, db_path: str = "backend/data/alerts.db"):
        self.db_path = db_path
        
        # Ensure data folder exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize Database Tables
        self._init_db()

    def _get_connection(self):
        # Return a new connection. This is thread-safe for async/background operations.
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # returns dict-like objects
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create Tickers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            
            # Create Alerts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    value REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    triggered_at TEXT
                )
            """)
            
            # Create Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trigger_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    value REAL NOT NULL,
                    current_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            
            conn.commit()
            
        # Pre-populate tables if empty
        self._prepopulate_defaults()

    def _prepopulate_defaults(self):
        # 1. Pre-populate Tickers
        tickers = self.get_all_tickers()
        if not tickers:
            default_tickers = [
                {"symbol": "BTC", "name": "Bitcoin"},
                {"symbol": "ETH", "name": "Ethereum"},
                {"symbol": "SOL", "name": "Solana"},
                {"symbol": "MATIC", "name": "Polygon"},
                {"symbol": "TON", "name": "The Open Network"}
            ]
            for t in default_tickers:
                self.add_ticker(t["symbol"], t["name"])
            logger.info("Prepopulated default tickers database.")

        # 2. Pre-populate Alerts
        alerts = self.get_all_alerts()
        if not alerts:
            default_alerts = [
                {"ticker": "BTC", "metric": "price", "condition": "above", "value": 75000.0},
                {"ticker": "BTC", "metric": "rsi", "condition": "below", "value": 30.0},
                {"ticker": "BTC", "metric": "rsi", "condition": "above", "value": 70.0},
                {"ticker": "ETH", "metric": "price", "condition": "above", "value": 4000.0},
                {"ticker": "ETH", "metric": "rsi", "condition": "below", "value": 30.0},
                {"ticker": "SOL", "metric": "rsi", "condition": "above", "value": 80.0}
            ]
            for a in default_alerts:
                self.create_alert(
                    ticker=a["ticker"],
                    metric=a["metric"],
                    condition=a["condition"],
                    value=a["value"]
                )
            logger.info("Prepopulated default alert rules database.")

    # --- TICKERS CRUD ---
    def get_all_tickers(self) -> List[Dict[str, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickers ORDER BY symbol ASC")
            rows = cursor.fetchall()
            return [{"symbol": row["symbol"], "name": row["name"]} for row in rows]

    def add_ticker(self, symbol: str, name: str) -> bool:
        symbol_upper = symbol.upper()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tickers (symbol, name) VALUES (?, ?)",
                    (symbol_upper, name)
                )
                conn.commit()
                logger.info(f"Ticker added to DB: {symbol_upper} ({name})")
                return True
        except sqlite3.IntegrityError:
            # Ticker already exists
            return False

    def delete_ticker(self, symbol: str) -> bool:
        symbol_upper = symbol.upper()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("SELECT 1 FROM tickers WHERE symbol = ?", (symbol_upper,))
            if not cursor.fetchone():
                return False
                
            # Delete ticker and all its active alerts
            cursor.execute("DELETE FROM tickers WHERE symbol = ?", (symbol_upper,))
            cursor.execute("DELETE FROM alerts WHERE ticker = ?", (symbol_upper,))
            conn.commit()
            logger.info(f"Ticker and associated alerts deleted: {symbol_upper}")
            return True

    # --- ALERTS CRUD ---
    def create_alert(self, ticker: str, metric: str, condition: str, value: float) -> Dict[str, Any]:
        alert_id = str(uuid.uuid4())
        alert = {
            "id": alert_id,
            "ticker": ticker.upper(),
            "metric": metric.lower(),
            "condition": condition.lower(),
            "value": float(value),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts (id, ticker, metric, condition, value, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["id"], alert["ticker"], alert["metric"], 
                    alert["condition"], alert["value"], alert["status"], 
                    alert["created_at"]
                )
            )
            conn.commit()
            
        logger.info(f"Alert rule created and saved to SQLite: {alert}")
        return alert

    def get_all_alerts(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if ticker:
                cursor.execute("SELECT * FROM alerts WHERE ticker = ?", (ticker.upper(),))
            else:
                cursor.execute("SELECT * FROM alerts")
                
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_alert(self, alert_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM alerts WHERE id = ?", (alert_id,))
            if not cursor.fetchone():
                return False
                
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            conn.commit()
            return True

    def clear_all_alerts(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts")
            conn.commit()

    # --- TRIGGER LOGS ---
    def get_trigger_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM trigger_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_trigger_logs(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trigger_logs")
            conn.commit()

    # --- EVALUATE STATE ---
    def evaluate_rules(self, ticker: str, current_price: float, current_rsi: float) -> List[Dict[str, Any]]:
        """
        Evaluates active rules in database against live price & RSI.
        Saves triggers to trigger_logs and updates alert status to 'triggered'.
        """
        ticker_upper = ticker.upper()
        triggered_now = []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM alerts WHERE ticker = ? AND status = 'active'",
                (ticker_upper,)
            )
            active_rules = cursor.fetchall()
            
            for row in active_rules:
                alert = dict(row)
                metric_val = current_price if alert["metric"] == "price" else current_rsi
                is_triggered = False
                
                if alert["condition"] == "above" and metric_val >= alert["value"]:
                    is_triggered = True
                elif alert["condition"] == "below" and metric_val <= alert["value"]:
                    is_triggered = True
                    
                if is_triggered:
                    triggered_at = datetime.now().isoformat()
                    # 1. Update Alert Status in DB
                    cursor.execute(
                        "UPDATE alerts SET status = 'triggered', triggered_at = ? WHERE id = ?",
                        (triggered_at, alert["id"])
                    )
                    
                    # 2. Insert into Logs Table in DB
                    message = f"ALERT: {alert['ticker']} {alert['metric']} reached {round(metric_val, 2)} (Target: {alert['condition']} {alert['value']})"
                    cursor.execute(
                        """
                        INSERT INTO trigger_logs (alert_id, ticker, metric, condition, value, current_value, timestamp, message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            alert["id"], alert["ticker"], alert["metric"],
                            alert["condition"], alert["value"], round(metric_val, 2),
                            triggered_at, message
                        )
                    )
                    
                    log_entry = {
                        "alert_id": alert["id"],
                        "ticker": alert["ticker"],
                        "metric": alert["metric"],
                        "condition": alert["condition"],
                        "value": alert["value"],
                        "current_value": round(metric_val, 2),
                        "timestamp": triggered_at,
                        "message": message
                    }
                    
                    print(f"\n[TRIGGERED ALERT] >>> {message} <<<\n")
                    logger.warning(f"Alert triggered: {message}")
                    triggered_now.append(log_entry)
                    
            conn.commit()
            
        return triggered_now
