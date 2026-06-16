import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        # Memory database for active trigger rules
        # In a production system, this would be SQLite or PostgreSQL
        self.alerts: Dict[str, Dict[str, Any]] = {}
        # Prepopulate with some default trigger alerts so it does something immediately
        self._prepopulate_defaults()
        
        # Log of triggered alerts
        self.trigger_log: List[Dict[str, Any]] = []

    def _prepopulate_defaults(self):
        default_alerts = [
            {"ticker": "BTC", "metric": "price", "condition": "above", "value": 75000.0},
            {"ticker": "BTC", "metric": "rsi", "condition": "below", "value": 30.0},
            {"ticker": "BTC", "metric": "rsi", "condition": "above", "value": 70.0},
            {"ticker": "ETH", "metric": "price", "condition": "above", "value": 4000.0},
            {"ticker": "ETH", "metric": "rsi", "condition": "below", "value": 30.0},
            {"ticker": "SOL", "metric": "rsi", "condition": "above", "value": 80.0}
        ]
        for alert in default_alerts:
            self.create_alert(
                ticker=alert["ticker"],
                metric=alert["metric"],
                condition=alert["condition"],
                value=alert["value"]
            )

    def create_alert(self, ticker: str, metric: str, condition: str, value: float) -> Dict[str, Any]:
        alert_id = str(uuid.uuid4())
        alert = {
            "id": alert_id,
            "ticker": ticker.upper(),
            "metric": metric.lower(),       # "price", "rsi"
            "condition": condition.lower(), # "above", "below"
            "value": float(value),
            "status": "active",             # "active", "triggered"
            "created_at": datetime.now().isoformat()
        }
        self.alerts[alert_id] = alert
        logger.info(f"Created alert rule: {alert}")
        return alert

    def get_all_alerts(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        rules = list(self.alerts.values())
        if ticker:
            rules = [r for r in rules if r["ticker"] == ticker.upper()]
        return rules

    def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted alert rule: {alert_id}")
            return True
        return False

    def clear_all_alerts(self) -> None:
        self.alerts.clear()
        logger.info("Cleared all alert rules.")

    def get_trigger_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.trigger_log[-limit:][::-1] # return newest first

    def clear_trigger_logs(self) -> None:
        self.trigger_log.clear()

    def evaluate_rules(self, ticker: str, current_price: float, current_rsi: float) -> List[Dict[str, Any]]:
        """
        Evaluates the active trigger rules against the current price and RSI values.
        Returns a list of newly triggered alerts.
        """
        triggered_now = []
        
        for alert_id, alert in self.alerts.items():
            if alert["status"] != "active":
                continue
            if alert["ticker"] != ticker.upper():
                continue
                
            metric_val = current_price if alert["metric"] == "price" else current_rsi
            is_triggered = False
            
            if alert["condition"] == "above":
                if metric_val >= alert["value"]:
                    is_triggered = True
            elif alert["condition"] == "below":
                if metric_val <= alert["value"]:
                    is_triggered = True
                    
            if is_triggered:
                alert["status"] = "triggered"
                alert["triggered_at"] = datetime.now().isoformat()
                
                log_entry = {
                    "alert_id": alert["id"],
                    "ticker": alert["ticker"],
                    "metric": alert["metric"],
                    "condition": alert["condition"],
                    "value": alert["value"],
                    "current_value": round(metric_val, 2),
                    "timestamp": alert["triggered_at"],
                    "message": f"ALERT: {alert['ticker']} {alert['metric']} reached {round(metric_val, 2)} (Target: {alert['condition']} {alert['value']})"
                }
                
                # Print to backend console as requested
                print(f"\n[TRIGGERED ALERT] >>> {log_entry['message']} <<<\n")
                logger.warning(f"Alert triggered: {log_entry['message']}")
                
                self.trigger_log.append(log_entry)
                triggered_now.append(log_entry)
                
        return triggered_now
