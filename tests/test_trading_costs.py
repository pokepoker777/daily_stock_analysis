# -*- coding: utf-8 -*-
"""Unit tests for the backtest trading cost model."""

import unittest
from dataclasses import dataclass
from datetime import date, timedelta

from src.core.backtest_engine import BacktestEngine, EvaluationConfig, TradingCostConfig


@dataclass
class Bar:
    date: date
    open: float
    high: float
    low: float
    close: float


class TestTradingCostConfig(unittest.TestCase):
    """Test TradingCostConfig calculations."""

    def test_default_round_trip_cost(self):
        costs = TradingCostConfig()
        # buy: 0.025% + 0.05% = 0.075%
        # sell: 0.025% + 0.05% + 0.05% = 0.125%
        # total: 0.2% round trip
        expected = (0.00025 + 0.0005 + 0.00025 + 0.0005 + 0.0005) * 100
        self.assertAlmostEqual(costs.round_trip_cost_pct, expected, places=4)

    def test_apply_buy_cost_increases_price(self):
        costs = TradingCostConfig()
        price = 100.0
        effective = costs.apply_buy_cost(price)
        self.assertGreater(effective, price)

    def test_apply_sell_cost_decreases_price(self):
        costs = TradingCostConfig()
        price = 100.0
        effective = costs.apply_sell_cost(price)
        self.assertLess(effective, price)

    def test_custom_cost_config(self):
        costs = TradingCostConfig(
            commission_rate=0.001,   # 0.1%
            stamp_tax_rate=0.001,    # 0.1%
            slippage_rate=0.001,     # 0.1%
        )
        # buy: 0.1% + 0.1% = 0.2%
        # sell: 0.1% + 0.1% + 0.1% = 0.3%
        # total: 0.5%
        self.assertAlmostEqual(costs.round_trip_cost_pct, 0.5, places=4)

    def test_zero_cost_config(self):
        costs = TradingCostConfig(
            commission_rate=0.0,
            stamp_tax_rate=0.0,
            slippage_rate=0.0,
        )
        self.assertAlmostEqual(costs.round_trip_cost_pct, 0.0, places=4)
        self.assertEqual(costs.apply_buy_cost(100.0), 100.0)
        self.assertEqual(costs.apply_sell_cost(100.0), 100.0)


class TestBacktestWithCosts(unittest.TestCase):
    """Test that evaluate_single returns net return after costs."""

    def _make_bars(self, start_price: float, end_price: float, days: int = 5) -> list:
        base_date = date(2025, 1, 1)
        bars = []
        for i in range(days):
            # Linear interpolation
            frac = (i + 1) / days
            p = start_price + (end_price - start_price) * frac
            bars.append(Bar(
                date=base_date + timedelta(days=i + 1),
                open=p * 0.999,
                high=p * 1.01,
                low=p * 0.99,
                close=p,
            ))
        return bars

    def test_net_return_less_than_gross(self):
        """Net return should always be less than gross return for a profitable trade."""
        bars = self._make_bars(10.0, 11.0, days=5)
        config = EvaluationConfig(eval_window_days=5)
        result = BacktestEngine.evaluate_single(
            operation_advice="买入",
            analysis_date=date(2025, 1, 1),
            start_price=10.0,
            forward_bars=bars,
            stop_loss=None,
            take_profit=None,
            config=config,
        )
        self.assertEqual(result["eval_status"], "completed")
        self.assertIsNotNone(result["simulated_return_pct"])
        self.assertIsNotNone(result["simulated_return_net_pct"])
        # Net < Gross because costs reduce profit
        self.assertLess(result["simulated_return_net_pct"], result["simulated_return_pct"])

    def test_net_return_more_negative_on_loss(self):
        """On a losing trade, net return should be even more negative than gross."""
        bars = self._make_bars(10.0, 9.0, days=5)
        config = EvaluationConfig(eval_window_days=5)
        result = BacktestEngine.evaluate_single(
            operation_advice="买入",
            analysis_date=date(2025, 1, 1),
            start_price=10.0,
            forward_bars=bars,
            stop_loss=None,
            take_profit=None,
            config=config,
        )
        self.assertLess(result["simulated_return_net_pct"], result["simulated_return_pct"])

    def test_cash_position_zero_net_return(self):
        """Cash position should have zero net return."""
        bars = self._make_bars(10.0, 11.0, days=5)
        config = EvaluationConfig(eval_window_days=5)
        result = BacktestEngine.evaluate_single(
            operation_advice="观望",
            analysis_date=date(2025, 1, 1),
            start_price=10.0,
            forward_bars=bars,
            stop_loss=None,
            take_profit=None,
            config=config,
        )
        self.assertEqual(result["simulated_return_pct"], 0.0)
        self.assertEqual(result["simulated_return_net_pct"], 0.0)

    def test_round_trip_cost_in_result(self):
        """Result should include the round-trip cost percentage."""
        bars = self._make_bars(10.0, 11.0, days=5)
        config = EvaluationConfig(eval_window_days=5)
        result = BacktestEngine.evaluate_single(
            operation_advice="买入",
            analysis_date=date(2025, 1, 1),
            start_price=10.0,
            forward_bars=bars,
            stop_loss=None,
            take_profit=None,
            config=config,
        )
        self.assertIsNotNone(result["round_trip_cost_pct"])
        self.assertGreater(result["round_trip_cost_pct"], 0)

    def test_zero_cost_net_equals_gross(self):
        """With zero costs, net return should equal gross return."""
        bars = self._make_bars(10.0, 11.0, days=5)
        config = EvaluationConfig(
            eval_window_days=5,
            trading_costs=TradingCostConfig(
                commission_rate=0.0,
                stamp_tax_rate=0.0,
                slippage_rate=0.0,
            ),
        )
        result = BacktestEngine.evaluate_single(
            operation_advice="买入",
            analysis_date=date(2025, 1, 1),
            start_price=10.0,
            forward_bars=bars,
            stop_loss=None,
            take_profit=None,
            config=config,
        )
        self.assertAlmostEqual(
            result["simulated_return_net_pct"],
            result["simulated_return_pct"],
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
