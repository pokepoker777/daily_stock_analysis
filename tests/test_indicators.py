# -*- coding: utf-8 -*-
"""Unit tests for advanced technical indicators module."""

import unittest

import numpy as np
import pandas as pd

from src.indicators import (
    AdvancedIndicatorResult,
    analyze_advanced_indicators,
    calc_atr,
    calc_bollinger_bands,
    calc_cci,
    calc_kdj,
    calc_obv,
    calc_williams_r,
)


def _make_ohlcv(n: int = 60, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    base = 10.0
    closes = [base]
    for _ in range(n - 1):
        closes.append(closes[-1] * (1 + rng.randn() * 0.02 + 0.002))
    closes = np.array(closes)
    return pd.DataFrame({
        "date": dates,
        "open": closes * (1 + rng.uniform(-0.01, 0.01, n)),
        "high": closes * (1 + rng.uniform(0.0, 0.02, n)),
        "low": closes * (1 - rng.uniform(0.0, 0.02, n)),
        "close": closes,
        "volume": rng.randint(100000, 5000000, n),
    })


class TestBollingerBands(unittest.TestCase):
    def test_columns_added(self):
        df = _make_ohlcv()
        result = calc_bollinger_bands(df)
        for col in ["BOLL_MID", "BOLL_UPPER", "BOLL_LOWER", "BOLL_WIDTH"]:
            self.assertIn(col, result.columns)

    def test_upper_above_lower(self):
        df = _make_ohlcv()
        result = calc_bollinger_bands(df).dropna()
        self.assertTrue((result["BOLL_UPPER"] >= result["BOLL_LOWER"]).all())

    def test_mid_between_bands(self):
        df = _make_ohlcv()
        result = calc_bollinger_bands(df).dropna()
        self.assertTrue((result["BOLL_MID"] <= result["BOLL_UPPER"]).all())
        self.assertTrue((result["BOLL_MID"] >= result["BOLL_LOWER"]).all())


class TestATR(unittest.TestCase):
    def test_columns_added(self):
        df = _make_ohlcv()
        result = calc_atr(df)
        self.assertIn("ATR", result.columns)
        self.assertIn("ATR_PCT", result.columns)

    def test_atr_positive(self):
        df = _make_ohlcv()
        result = calc_atr(df).dropna()
        self.assertTrue((result["ATR"] >= 0).all())


class TestOBV(unittest.TestCase):
    def test_columns_added(self):
        df = _make_ohlcv()
        result = calc_obv(df)
        self.assertIn("OBV", result.columns)
        self.assertIn("OBV_MA5", result.columns)

    def test_obv_length(self):
        df = _make_ohlcv(30)
        result = calc_obv(df)
        self.assertEqual(len(result), 30)


class TestKDJ(unittest.TestCase):
    def test_columns_added(self):
        df = _make_ohlcv()
        result = calc_kdj(df)
        for col in ["KDJ_K", "KDJ_D", "KDJ_J"]:
            self.assertIn(col, result.columns)

    def test_k_d_in_range(self):
        df = _make_ohlcv()
        result = calc_kdj(df)
        # K and D should generally be 0-100 (J can exceed)
        self.assertTrue((result["KDJ_K"] >= 0).all())
        self.assertTrue((result["KDJ_K"] <= 100).all())
        self.assertTrue((result["KDJ_D"] >= 0).all())
        self.assertTrue((result["KDJ_D"] <= 100).all())


class TestWilliamsR(unittest.TestCase):
    def test_range(self):
        df = _make_ohlcv()
        result = calc_williams_r(df).dropna()
        self.assertTrue((result["WILLIAMS_R"] >= -100).all())
        self.assertTrue((result["WILLIAMS_R"] <= 0).all())


class TestCCI(unittest.TestCase):
    def test_column_added(self):
        df = _make_ohlcv()
        result = calc_cci(df)
        self.assertIn("CCI", result.columns)


class TestAnalyzeAdvancedIndicators(unittest.TestCase):
    def test_returns_result(self):
        df = _make_ohlcv(60)
        result = analyze_advanced_indicators(df)
        self.assertIsInstance(result, AdvancedIndicatorResult)
        self.assertGreaterEqual(result.advanced_score, 0)
        self.assertLessEqual(result.advanced_score, 100)

    def test_to_dict(self):
        df = _make_ohlcv(60)
        result = analyze_advanced_indicators(df)
        d = result.to_dict()
        self.assertIn("bollinger", d)
        self.assertIn("atr", d)
        self.assertIn("kdj", d)
        self.assertIn("advanced_score", d)

    def test_to_prompt_text(self):
        df = _make_ohlcv(60)
        result = analyze_advanced_indicators(df)
        text = result.to_prompt_text()
        self.assertIn("Advanced Technical Indicators", text)
        self.assertIn("BOLL", text)

    def test_insufficient_data(self):
        df = _make_ohlcv(10)
        result = analyze_advanced_indicators(df)
        # With only 10 bars, should return mostly empty result
        self.assertEqual(result.advanced_score, 0)

    def test_empty_dataframe(self):
        result = analyze_advanced_indicators(pd.DataFrame())
        self.assertEqual(result.advanced_score, 0)


if __name__ == "__main__":
    unittest.main()
