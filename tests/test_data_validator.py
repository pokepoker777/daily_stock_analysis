# -*- coding: utf-8 -*-
"""Unit tests for the data validation pipeline."""

import unittest

import numpy as np
import pandas as pd

from src.data_validator import (
    DataValidator,
    Severity,
    ValidationReport,
    cross_validate_sources,
    validate_dataframe,
)


def _make_valid_df(n: int = 30) -> pd.DataFrame:
    """Generate a valid OHLCV DataFrame."""
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    rng = np.random.RandomState(42)
    closes = 10.0 + np.cumsum(rng.randn(n) * 0.1)
    closes = np.maximum(closes, 1.0)  # ensure positive
    return pd.DataFrame({
        "date": dates,
        "open": closes * (1 + rng.uniform(-0.005, 0.005, n)),
        "high": closes * (1 + rng.uniform(0.0, 0.015, n)),
        "low": closes * (1 - rng.uniform(0.0, 0.015, n)),
        "close": closes,
        "volume": rng.randint(100000, 5000000, n),
    })


class TestSchemaValidation(unittest.TestCase):
    def test_valid_df_passes(self):
        df = _make_valid_df()
        report = validate_dataframe(df, stock_code="000001")
        self.assertTrue(report.is_usable)
        self.assertEqual(report.critical_count, 0)

    def test_missing_columns_critical(self):
        df = pd.DataFrame({"date": ["2025-01-01"], "close": [10.0]})
        report = validate_dataframe(df)
        self.assertTrue(report.has_critical)
        self.assertIn("Missing required columns", report.critical_summary)

    def test_none_df_critical(self):
        report = validate_dataframe(None)
        self.assertTrue(report.has_critical)

    def test_empty_df_critical(self):
        report = validate_dataframe(pd.DataFrame())
        self.assertTrue(report.has_critical)


class TestTemporalValidation(unittest.TestCase):
    def test_duplicate_dates_warned(self):
        df = _make_valid_df(10)
        df.loc[5, "date"] = df.loc[4, "date"]  # duplicate
        report = validate_dataframe(df)
        date_issues = [i for i in report.issues if i.field == "date" and "duplicate" in i.message]
        self.assertTrue(len(date_issues) > 0)


class TestPriceValidation(unittest.TestCase):
    def test_negative_price_critical(self):
        df = _make_valid_df(10)
        df.loc[3, "close"] = -5.0
        report = validate_dataframe(df)
        self.assertTrue(report.has_critical)

    def test_zero_price_critical(self):
        df = _make_valid_df(10)
        df.loc[2, "open"] = 0.0
        report = validate_dataframe(df)
        self.assertTrue(report.has_critical)


class TestVolumeValidation(unittest.TestCase):
    def test_zero_volume_warned(self):
        df = _make_valid_df(10)
        df.loc[3, "volume"] = 0
        report = validate_dataframe(df)
        vol_issues = [i for i in report.issues if i.field == "volume" and "zero" in i.message]
        self.assertTrue(len(vol_issues) > 0)


class TestMissingValues(unittest.TestCase):
    def test_nan_in_close_warned(self):
        df = _make_valid_df(10)
        df.loc[5, "close"] = np.nan
        report = validate_dataframe(df)
        nan_issues = [i for i in report.issues if "NaN" in i.message]
        self.assertTrue(len(nan_issues) > 0)

    def test_inf_in_volume_critical(self):
        df = _make_valid_df(10)
        df.loc[3, "volume"] = np.inf
        report = validate_dataframe(df)
        inf_issues = [i for i in report.issues if "Inf" in i.message]
        self.assertTrue(len(inf_issues) > 0)
        self.assertTrue(report.has_critical)


class TestCrossValidation(unittest.TestCase):
    def test_matching_sources(self):
        df_a = _make_valid_df(10)
        df_b = df_a.copy()
        report = cross_validate_sources(df_a, df_b, "src_a", "src_b")
        self.assertFalse(report.has_critical)
        # Should have an INFO message about matching
        info_issues = [i for i in report.issues if i.severity == Severity.INFO]
        self.assertTrue(len(info_issues) > 0)

    def test_divergent_sources(self):
        df_a = _make_valid_df(10)
        df_b = df_a.copy()
        # Introduce 5% price divergence
        df_b["close"] = df_b["close"] * 1.05
        report = cross_validate_sources(df_a, df_b, "src_a", "src_b", "000001")
        warn_issues = [i for i in report.issues if i.severity == Severity.WARNING and "divergence" in i.message]
        self.assertTrue(len(warn_issues) > 0)

    def test_empty_source(self):
        df_a = _make_valid_df(10)
        report = cross_validate_sources(df_a, pd.DataFrame(), "src_a", "src_b")
        self.assertEqual(report.row_count, 0)


class TestReportProperties(unittest.TestCase):
    def test_to_dict(self):
        df = _make_valid_df(10)
        report = validate_dataframe(df, stock_code="600519", source="akshare")
        d = report.to_dict()
        self.assertEqual(d["stock_code"], "600519")
        self.assertEqual(d["source"], "akshare")
        self.assertIn("is_usable", d)
        self.assertIn("issues", d)


if __name__ == "__main__":
    unittest.main()
