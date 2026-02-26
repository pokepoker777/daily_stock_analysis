# -*- coding: utf-8 -*-
"""
===================================
Data Validation Pipeline
===================================

Cross-source data consistency checks and anomaly detection.
Ensures that raw OHLCV data from multiple providers is clean and
trustworthy before it enters the AI analysis pipeline.

Validation layers:
1. Schema validation — required columns, types, ranges
2. Temporal integrity — date continuity, no future dates
3. Price sanity — OHLC relationship, limit-up/down bounds
4. Volume anomaly detection — zero-volume, extreme spikes
5. Cross-source reconciliation — compare two sources, flag divergence

Usage:
    from src.data_validator import DataValidator, validate_dataframe
    issues = validate_dataframe(df, stock_code="600519")
    if issues.has_critical:
        logger.error(f"Data rejected: {issues.critical_summary}")
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# A-share daily price limit (10% for main board, 20% for ChiNext/STAR)
PRICE_LIMIT_MAIN = 0.10
PRICE_LIMIT_CHINEXT = 0.20

# Volume spike threshold (vs 20-day average)
VOLUME_SPIKE_THRESHOLD = 10.0

# Cross-source price divergence threshold (%)
CROSS_SOURCE_PRICE_TOLERANCE = 0.02  # 2%


class Severity(str, Enum):
    """Validation issue severity."""
    CRITICAL = "critical"   # Data should be rejected
    WARNING = "warning"     # Data usable but flagged
    INFO = "info"           # Informational


@dataclass
class ValidationIssue:
    """A single data validation issue."""
    severity: Severity
    field: str
    message: str
    row_index: Optional[int] = None
    value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "field": self.field,
            "message": self.message,
            "row": self.row_index,
            "value": str(self.value) if self.value is not None else None,
        }


@dataclass
class ValidationReport:
    """Aggregated validation report for a dataset."""
    stock_code: str = ""
    source: str = ""
    row_count: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(i.severity == Severity.CRITICAL for i in self.issues)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def critical_summary(self) -> str:
        crits = [i for i in self.issues if i.severity == Severity.CRITICAL]
        if not crits:
            return "No critical issues"
        return "; ".join(i.message for i in crits[:5])

    @property
    def is_usable(self) -> bool:
        """Data is usable if no critical issues exist."""
        return not self.has_critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stock_code": self.stock_code,
            "source": self.source,
            "row_count": self.row_count,
            "is_usable": self.is_usable,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues[:50]],
        }


class DataValidator:
    """
    Multi-layer data validation pipeline.

    Validates a pandas DataFrame of OHLCV data against A-share market rules.
    """

    REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}

    def validate(
        self,
        df: pd.DataFrame,
        stock_code: str = "",
        source: str = "",
    ) -> ValidationReport:
        """
        Run all validation checks on a DataFrame.

        Args:
            df: OHLCV DataFrame
            stock_code: Stock code for context
            source: Data source name

        Returns:
            ValidationReport with all issues found
        """
        report = ValidationReport(
            stock_code=stock_code,
            source=source,
            row_count=len(df) if df is not None else 0,
        )

        if df is None or df.empty:
            report.issues.append(ValidationIssue(
                severity=Severity.CRITICAL,
                field="dataframe",
                message="DataFrame is None or empty",
            ))
            return report

        # Layer 1: Schema validation
        self._validate_schema(df, report)
        if report.has_critical:
            return report  # Can't proceed without required columns

        # Layer 2: Temporal integrity
        self._validate_temporal(df, report)

        # Layer 3: Price sanity
        self._validate_prices(df, stock_code, report)

        # Layer 4: Volume anomalies
        self._validate_volume(df, report)

        # Layer 5: NaN/Inf checks
        self._validate_missing(df, report)

        return report

    def _validate_schema(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Check required columns and data types."""
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            report.issues.append(ValidationIssue(
                severity=Severity.CRITICAL,
                field="schema",
                message=f"Missing required columns: {missing}",
            ))
            return

        # Type checks for numeric columns
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors="raise")
                except (ValueError, TypeError):
                    report.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        field=col,
                        message=f"Column '{col}' contains non-numeric values",
                    ))

    def _validate_temporal(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Check date continuity and no future dates."""
        if "date" not in df.columns:
            return

        try:
            dates = pd.to_datetime(df["date"])
        except Exception:
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="date",
                message="Cannot parse date column",
            ))
            return

        # Check for future dates
        today = pd.Timestamp(date.today())
        future_mask = dates > today
        if future_mask.any():
            count = future_mask.sum()
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="date",
                message=f"{count} rows have future dates",
            ))

        # Check for duplicates
        dup_count = dates.duplicated().sum()
        if dup_count > 0:
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="date",
                message=f"{dup_count} duplicate dates found",
            ))

        # Check if sorted
        if not dates.is_monotonic_increasing and not dates.is_monotonic_decreasing:
            report.issues.append(ValidationIssue(
                severity=Severity.INFO,
                field="date",
                message="Dates are not monotonically sorted",
            ))

    def _validate_prices(self, df: pd.DataFrame, stock_code: str, report: ValidationReport) -> None:
        """Validate OHLC price relationships and limit-up/down bounds."""
        for col in ["open", "high", "low", "close"]:
            if col not in df.columns:
                return

        # OHLC relationship: High >= max(Open, Close), Low <= min(Open, Close)
        invalid_high = df["high"] < df[["open", "close"]].max(axis=1) - 0.001
        if invalid_high.any():
            count = invalid_high.sum()
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="high",
                message=f"{count} rows where high < max(open, close)",
            ))

        invalid_low = df["low"] > df[["open", "close"]].min(axis=1) + 0.001
        if invalid_low.any():
            count = invalid_low.sum()
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="low",
                message=f"{count} rows where low > min(open, close)",
            ))

        # Negative prices
        for col in ["open", "high", "low", "close"]:
            neg_count = (df[col] <= 0).sum()
            if neg_count > 0:
                report.issues.append(ValidationIssue(
                    severity=Severity.CRITICAL,
                    field=col,
                    message=f"{neg_count} rows with non-positive {col} price",
                ))

        # Daily return limit check (soft — some stocks have 20% limits)
        if len(df) >= 2:
            is_chinext = stock_code.startswith("3") or stock_code.startswith("68")
            limit = PRICE_LIMIT_CHINEXT if is_chinext else PRICE_LIMIT_MAIN
            # Add 5% buffer for ST stocks / special situations
            limit_with_buffer = limit + 0.05

            returns = df["close"].pct_change().abs()
            extreme = returns > limit_with_buffer
            if extreme.any():
                count = extreme.sum()
                report.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    field="close",
                    message=f"{count} rows exceed {limit_with_buffer*100:.0f}% daily return limit",
                ))

    def _validate_volume(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Check for zero-volume days and extreme volume spikes."""
        if "volume" not in df.columns:
            return

        # Zero volume (non-trading days that shouldn't be in the data)
        zero_vol = (df["volume"] == 0).sum()
        if zero_vol > 0:
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="volume",
                message=f"{zero_vol} rows with zero volume (suspension?)",
            ))

        # Volume spikes (> 10x 20-day average)
        if len(df) >= 20:
            vol_ma20 = df["volume"].rolling(window=20).mean()
            spike_mask = df["volume"] > vol_ma20 * VOLUME_SPIKE_THRESHOLD
            spike_count = spike_mask.sum()
            if spike_count > 0:
                report.issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    field="volume",
                    message=f"{spike_count} volume spikes (>{VOLUME_SPIKE_THRESHOLD}x 20d avg)",
                ))

    def _validate_missing(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Check for NaN and Inf values in numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                sev = Severity.WARNING if nan_count < len(df) * 0.1 else Severity.CRITICAL
                report.issues.append(ValidationIssue(
                    severity=sev,
                    field=col,
                    message=f"{nan_count} NaN values in {col}",
                ))

            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                report.issues.append(ValidationIssue(
                    severity=Severity.CRITICAL,
                    field=col,
                    message=f"{inf_count} Inf values in {col}",
                ))


def cross_validate_sources(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    source_a: str = "source_a",
    source_b: str = "source_b",
    stock_code: str = "",
) -> ValidationReport:
    """
    Compare data from two different sources for the same stock.

    Flags rows where close prices diverge by more than CROSS_SOURCE_PRICE_TOLERANCE.

    Args:
        df_a: DataFrame from source A
        df_b: DataFrame from source B
        source_a: Name of source A
        source_b: Name of source B
        stock_code: Stock code

    Returns:
        ValidationReport with divergence issues
    """
    report = ValidationReport(
        stock_code=stock_code,
        source=f"{source_a} vs {source_b}",
    )

    if df_a is None or df_b is None or df_a.empty or df_b.empty:
        report.issues.append(ValidationIssue(
            severity=Severity.WARNING,
            field="cross_validation",
            message="One or both DataFrames are empty",
        ))
        return report

    # Merge on date
    try:
        a = df_a[["date", "close"]].copy().rename(columns={"close": "close_a"})
        b = df_b[["date", "close"]].copy().rename(columns={"close": "close_b"})

        a["date"] = pd.to_datetime(a["date"])
        b["date"] = pd.to_datetime(b["date"])

        merged = pd.merge(a, b, on="date", how="inner")
        report.row_count = len(merged)

        if merged.empty:
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="date",
                message="No overlapping dates between sources",
            ))
            return report

        # Compute divergence
        merged["divergence"] = (
            (merged["close_a"] - merged["close_b"]).abs() / merged["close_a"]
        )

        divergent = merged[merged["divergence"] > CROSS_SOURCE_PRICE_TOLERANCE]
        if len(divergent) > 0:
            max_div = divergent["divergence"].max()
            report.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                field="close",
                message=(
                    f"{len(divergent)}/{len(merged)} dates have close price divergence "
                    f">{CROSS_SOURCE_PRICE_TOLERANCE*100:.0f}% between {source_a} and {source_b} "
                    f"(max: {max_div*100:.2f}%)"
                ),
            ))
        else:
            report.issues.append(ValidationIssue(
                severity=Severity.INFO,
                field="close",
                message=f"All {len(merged)} dates match within {CROSS_SOURCE_PRICE_TOLERANCE*100:.0f}% tolerance",
            ))

    except Exception as e:
        report.issues.append(ValidationIssue(
            severity=Severity.WARNING,
            field="cross_validation",
            message=f"Cross-validation error: {e}",
        ))

    return report


# Convenience function
def validate_dataframe(
    df: pd.DataFrame,
    stock_code: str = "",
    source: str = "",
) -> ValidationReport:
    """Validate a single DataFrame. Returns a ValidationReport."""
    return DataValidator().validate(df, stock_code=stock_code, source=source)
