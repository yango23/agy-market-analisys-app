import unittest
from backend.app.services.market import MarketService
from backend.app.services.alerts import AlertService

class TestMarketService(unittest.TestCase):
    def setUp(self):
        self.market = MarketService()
        # Create dummy price trend: 30 days of flat prices, then a jump
        self.dummy_prices = [100.0] * 20 + [105.0, 110.0, 115.0, 120.0, 125.0]

    def test_rsi_calculation(self):
        rsi = self.market.calculate_rsi(self.dummy_prices, period=14)
        self.assertEqual(len(rsi), len(self.dummy_prices))
        # Last value should be high (overbought trend)
        self.assertGreater(rsi[-1], 50.0)

    def test_macd_calculation(self):
        macd = self.market.calculate_macd(self.dummy_prices, 12, 26, 9)
        self.assertIn("macd_line", macd)
        self.assertIn("signal_line", macd)
        self.assertIn("histogram", macd)
        self.assertEqual(len(macd["macd_line"]), len(self.dummy_prices))

    def test_support_resistance_calculation(self):
        # 10 candles where low is 90 and high is 110, last close is 100
        ohlc = [[i, 100.0, 110.0, 90.0, 100.0] for i in range(20)]
        levels = self.market.calculate_support_resistance(ohlc, window_size=3)
        
        self.assertIn("supports", levels)
        self.assertIn("resistances", levels)
        self.assertIn("pivot_points", levels)
        
        # S1, R1, PP should be calculated
        pp = levels["pivot_points"]
        self.assertIn("PP", pp)
        self.assertIn("R1", pp)
        self.assertIn("S1", pp)


class TestAlertService(unittest.TestCase):
    def setUp(self):
        self.alerts = AlertService()
        self.alerts.clear_all_alerts() # clear defaults
        
    def test_create_and_delete_alert(self):
        alert = self.alerts.create_alert("BTC", "price", "above", 80000.0)
        self.assertEqual(alert["ticker"], "BTC")
        self.assertEqual(alert["metric"], "price")
        
        all_alerts = self.alerts.get_all_alerts()
        self.assertEqual(len(all_alerts), 1)
        
        deleted = self.alerts.delete_alert(alert["id"])
        self.assertTrue(deleted)
        self.assertEqual(len(self.alerts.get_all_alerts()), 0)

    def test_alert_rules_evaluation(self):
        alert_price_above = self.alerts.create_alert("BTC", "price", "above", 65000.0)
        alert_price_below = self.alerts.create_alert("BTC", "price", "below", 50000.0)
        
        # Test trigger above
        triggers = self.alerts.evaluate_rules("BTC", current_price=66000.0, current_rsi=50.0)
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["alert_id"], alert_price_above["id"])
        self.assertEqual(alert_price_above["status"], "triggered")
        
        # Test log entry
        logs = self.alerts.get_trigger_logs()
        self.assertEqual(len(logs), 1)
        self.assertIn("reached 66000.0", logs[0]["message"])
        
        # Verify triggered alert does not trigger again
        triggers_again = self.alerts.evaluate_rules("BTC", current_price=67000.0, current_rsi=50.0)
        self.assertEqual(len(triggers_again), 0)


if __name__ == "__main__":
    unittest.main()
