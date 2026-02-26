# -*- coding: utf-8 -*-
"""
===================================
Advanced Technical Indicators Module
===================================

Supplements the existing MA/MACD/RSI indicators in stock_analyzer.py
with additional industry-standard indicators used by quantitative
trading systems.

New indicators:
1. Bollinger Bands (BOLL) — volatility channel
2. Average True Range (ATR) — volatility measure
3. On-Balance Volume (OBV) — volume-price momentum
4. KDJ / Stochastic Oscillator — overbought/oversold
5. Williams %R — momentum reversal
6. CCI (Commodity Channel Index) — trend deviation

All functions accept a pandas DataFrame with standard OHLCV columns
and return the DataFrame with new indicator columns appended.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================
# Indicator calculation functions
# ============================================================

def calc_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.

    Args:
        df: DataFrame with 'close' column
        period: Moving average period (default 20)
        num_std: Number of standard deviations (default 2.0)

    Returns:
        DataFrame with BOLL_MID, BOLL_UPPER, BOLL_LOWER, BOLL_WIDTH columns
    """
    df = df.copy()
    df["BOLL_MID"] = df["close"].rolling(window=period).mean()
    rolling_std = df["close"].rolling(window=period).std()
    df["BOLL_UPPER"] = df["BOLL_MID"] + num_std * rolling_std
    df["BOLL_LOWER"] = df["BOLL_MID"] - num_std * rolling_std
    # Bandwidth: (upper - lower) / mid * 100, measures volatility
    df["BOLL_WIDTH"] = ((df["BOLL_UPPER"] - df["BOLL_LOWER"]) / df["BOLL_MID"] * 100).fillna(0)
    return df


def calc_atr(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR).

    ATR measures market volatility. Higher ATR = more volatile.
    Used for dynamic stop-loss placement (e.g., 2x ATR trailing stop).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)

    Returns:
        DataFrame with ATR and ATR_PCT (ATR as % of close) columns
    """
    df = df.copy()
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    # True Range = max(H-L, |H-Cp|, |L-Cp|)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR = EMA of True Range
    df["ATR"] = df["TR"].ewm(span=period, adjust=False).mean()

    # ATR as percentage of close (for cross-stock comparison)
    df["ATR_PCT"] = (df["ATR"] / df["close"] * 100).fillna(0)

    return df


def calc_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate On-Balance Volume (OBV).

    OBV is a cumulative volume indicator:
    - Price up: add volume
    - Price down: subtract volume
    - Price unchanged: no change

    OBV divergence from price signals potential reversals.

    Returns:
        DataFrame with OBV and OBV_MA5 columns
    """
    df = df.copy()
    close_diff = df["close"].diff()
    volume = df["volume"]

    obv_direction = np.where(close_diff > 0, 1, np.where(close_diff < 0, -1, 0))
    df["OBV"] = (volume * obv_direction).cumsum()
    df["OBV_MA5"] = df["OBV"].rolling(window=5).mean()

    return df


def calc_kdj(
    df: pd.DataFrame,
    k_period: int = 9,
    d_period: int = 3,
    j_smooth: int = 3,
) -> pd.DataFrame:
    """
    Calculate KDJ (Stochastic Oscillator, Chinese variant).

    K = 2/3 * prev_K + 1/3 * RSV
    D = 2/3 * prev_D + 1/3 * K
    J = 3*K - 2*D

    Signals:
    - J > 100: overbought
    - J < 0: oversold
    - K crosses above D: buy signal
    - K crosses below D: sell signal

    Returns:
        DataFrame with KDJ_K, KDJ_D, KDJ_J columns
    """
    df = df.copy()

    # RSV (Raw Stochastic Value)
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()

    rsv = ((df["close"] - low_min) / (high_max - low_min) * 100).fillna(50)

    # K, D smoothing (SMA-like with 2/3 decay)
    k_values = [50.0]  # Initial K = 50
    d_values = [50.0]  # Initial D = 50

    for i in range(1, len(rsv)):
        r = rsv.iloc[i]
        k = 2 / 3 * k_values[-1] + 1 / 3 * r
        d = 2 / 3 * d_values[-1] + 1 / 3 * k
        k_values.append(k)
        d_values.append(d)

    df["KDJ_K"] = k_values
    df["KDJ_D"] = d_values
    df["KDJ_J"] = 3 * df["KDJ_K"] - 2 * df["KDJ_D"]

    return df


def calc_williams_r(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.DataFrame:
    """
    Calculate Williams %R.

    Range: -100 to 0
    - Above -20: overbought
    - Below -80: oversold

    Returns:
        DataFrame with WILLIAMS_R column
    """
    df = df.copy()
    high_max = df["high"].rolling(window=period).max()
    low_min = df["low"].rolling(window=period).min()

    df["WILLIAMS_R"] = ((high_max - df["close"]) / (high_max - low_min) * -100).fillna(-50)

    return df


def calc_cci(
    df: pd.DataFrame,
    period: int = 20,
) -> pd.DataFrame:
    """
    Calculate Commodity Channel Index (CCI).

    CCI = (TP - SMA(TP)) / (0.015 * Mean Deviation)
    where TP = (High + Low + Close) / 3

    Signals:
    - CCI > +100: strong uptrend
    - CCI < -100: strong downtrend

    Returns:
        DataFrame with CCI column
    """
    df = df.copy()
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma_tp = tp.rolling(window=period).mean()
    mean_dev = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)

    df["CCI"] = ((tp - sma_tp) / (0.015 * mean_dev)).fillna(0)

    return df


# ============================================================
# Analysis result dataclass
# ============================================================

@dataclass
class AdvancedIndicatorResult:
    """Aggregated advanced indicator analysis."""

    # Bollinger Bands
    boll_upper: float = 0.0
    boll_mid: float = 0.0
    boll_lower: float = 0.0
    boll_width: float = 0.0
    boll_position: str = ""  # "above_upper" / "near_upper" / "mid" / "near_lower" / "below_lower"

    # ATR
    atr: float = 0.0
    atr_pct: float = 0.0
    volatility_level: str = ""  # "low" / "normal" / "high" / "extreme"
    suggested_stop_loss_pct: float = 0.0  # 2x ATR as % of price

    # OBV
    obv_trend: str = ""  # "bullish_divergence" / "bearish_divergence" / "confirming" / "neutral"

    # KDJ
    kdj_k: float = 0.0
    kdj_d: float = 0.0
    kdj_j: float = 0.0
    kdj_signal: str = ""  # "golden_cross" / "death_cross" / "overbought" / "oversold" / "neutral"

    # Williams %R
    williams_r: float = 0.0
    williams_signal: str = ""

    # CCI
    cci: float = 0.0
    cci_signal: str = ""

    # Composite
    advanced_score: int = 0  # 0-100 composite from advanced indicators
    advanced_signals: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bollinger": {
                "upper": round(self.boll_upper, 2),
                "mid": round(self.boll_mid, 2),
                "lower": round(self.boll_lower, 2),
                "width": round(self.boll_width, 2),
                "position": self.boll_position,
            },
            "atr": {
                "value": round(self.atr, 4),
                "pct": round(self.atr_pct, 2),
                "volatility": self.volatility_level,
                "suggested_stop_pct": round(self.suggested_stop_loss_pct, 2),
            },
            "obv_trend": self.obv_trend,
            "kdj": {
                "k": round(self.kdj_k, 2),
                "d": round(self.kdj_d, 2),
                "j": round(self.kdj_j, 2),
                "signal": self.kdj_signal,
            },
            "williams_r": {
                "value": round(self.williams_r, 2),
                "signal": self.williams_signal,
            },
            "cci": {
                "value": round(self.cci, 2),
                "signal": self.cci_signal,
            },
            "advanced_score": self.advanced_score,
            "advanced_signals": self.advanced_signals,
        }

    def to_prompt_text(self) -> str:
        """Format for injection into AI analysis prompt."""
        lines = [
            "### Advanced Technical Indicators",
            f"| Indicator | Value | Signal |",
            f"|-----------|-------|--------|",
            f"| BOLL Upper | {self.boll_upper:.2f} | Position: {self.boll_position} |",
            f"| BOLL Mid   | {self.boll_mid:.2f} | Width: {self.boll_width:.1f}% |",
            f"| BOLL Lower | {self.boll_lower:.2f} | |",
            f"| ATR        | {self.atr:.4f} ({self.atr_pct:.1f}%) | Volatility: {self.volatility_level} |",
            f"| Suggested Stop | {self.suggested_stop_loss_pct:.1f}% | Based on 2x ATR |",
            f"| OBV        | — | {self.obv_trend} |",
            f"| KDJ K/D/J  | {self.kdj_k:.1f}/{self.kdj_d:.1f}/{self.kdj_j:.1f} | {self.kdj_signal} |",
            f"| Williams %R | {self.williams_r:.1f} | {self.williams_signal} |",
            f"| CCI        | {self.cci:.1f} | {self.cci_signal} |",
            f"| **Adv Score** | **{self.advanced_score}/100** | |",
        ]
        return "\n".join(lines)


# ============================================================
# Composite analysis
# ============================================================

def analyze_advanced_indicators(
    df: pd.DataFrame,
    current_price: Optional[float] = None,
) -> AdvancedIndicatorResult:
    """
    Run all advanced indicators and produce a composite analysis.

    Args:
        df: DataFrame with standard OHLCV columns (date, open, high, low, close, volume)
        current_price: Current price (if None, uses last close)

    Returns:
        AdvancedIndicatorResult with all indicator values and signals
    """
    result = AdvancedIndicatorResult()

    if df is None or df.empty or len(df) < 26:
        logger.warning("Insufficient data for advanced indicator analysis")
        return result

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    if current_price is None:
        current_price = float(df["close"].iloc[-1])

    score = 0
    signals = []

    # --- Bollinger Bands ---
    try:
        df = calc_bollinger_bands(df)
        latest = df.iloc[-1]
        result.boll_upper = float(latest["BOLL_UPPER"])
        result.boll_mid = float(latest["BOLL_MID"])
        result.boll_lower = float(latest["BOLL_LOWER"])
        result.boll_width = float(latest["BOLL_WIDTH"])

        # Position analysis
        if current_price > result.boll_upper:
            result.boll_position = "above_upper"
            signals.append("⚠️ Price above BOLL upper — potential overbought")
        elif current_price > result.boll_mid + (result.boll_upper - result.boll_mid) * 0.7:
            result.boll_position = "near_upper"
            score += 5
        elif current_price < result.boll_lower:
            result.boll_position = "below_lower"
            score += 15
            signals.append("✅ Price below BOLL lower — potential oversold bounce")
        elif current_price < result.boll_mid - (result.boll_mid - result.boll_lower) * 0.7:
            result.boll_position = "near_lower"
            score += 12
            signals.append("✅ Near BOLL lower band — support zone")
        else:
            result.boll_position = "mid"
            score += 8

        # Squeeze detection (narrow bands = breakout imminent)
        if result.boll_width < 5:
            signals.append("⚡ BOLL squeeze — volatility contraction, breakout imminent")
    except Exception as e:
        logger.debug(f"Bollinger Bands calculation failed: {e}")

    # --- ATR ---
    try:
        df = calc_atr(df)
        latest = df.iloc[-1]
        result.atr = float(latest["ATR"])
        result.atr_pct = float(latest["ATR_PCT"])

        # Suggested stop-loss: 2x ATR as percentage
        result.suggested_stop_loss_pct = round(result.atr_pct * 2, 2)

        # Volatility classification
        if result.atr_pct < 1.5:
            result.volatility_level = "low"
            score += 8
        elif result.atr_pct < 3.0:
            result.volatility_level = "normal"
            score += 6
        elif result.atr_pct < 5.0:
            result.volatility_level = "high"
            score += 3
            signals.append("⚠️ High volatility — widen stop-loss")
        else:
            result.volatility_level = "extreme"
            score += 0
            signals.append("🚨 Extreme volatility — reduce position size")
    except Exception as e:
        logger.debug(f"ATR calculation failed: {e}")

    # --- OBV ---
    try:
        df = calc_obv(df)
        # Check OBV vs price divergence (last 10 bars)
        if len(df) >= 10:
            recent = df.iloc[-10:]
            price_trend = recent["close"].iloc[-1] - recent["close"].iloc[0]
            obv_trend = recent["OBV"].iloc[-1] - recent["OBV"].iloc[0]

            if price_trend > 0 and obv_trend < 0:
                result.obv_trend = "bearish_divergence"
                signals.append("⚠️ OBV bearish divergence — volume not confirming price rise")
            elif price_trend < 0 and obv_trend > 0:
                result.obv_trend = "bullish_divergence"
                score += 12
                signals.append("✅ OBV bullish divergence — accumulation during decline")
            elif (price_trend > 0 and obv_trend > 0) or (price_trend < 0 and obv_trend < 0):
                result.obv_trend = "confirming"
                score += 8
            else:
                result.obv_trend = "neutral"
                score += 5
    except Exception as e:
        logger.debug(f"OBV calculation failed: {e}")

    # --- KDJ ---
    try:
        df = calc_kdj(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        result.kdj_k = float(latest["KDJ_K"])
        result.kdj_d = float(latest["KDJ_D"])
        result.kdj_j = float(latest["KDJ_J"])

        # Cross detection
        k_cross_up = prev["KDJ_K"] <= prev["KDJ_D"] and result.kdj_k > result.kdj_d
        k_cross_down = prev["KDJ_K"] >= prev["KDJ_D"] and result.kdj_k < result.kdj_d

        if result.kdj_j > 100:
            result.kdj_signal = "overbought"
            signals.append(f"⚠️ KDJ J={result.kdj_j:.0f} > 100 — overbought")
        elif result.kdj_j < 0:
            result.kdj_signal = "oversold"
            score += 12
            signals.append(f"✅ KDJ J={result.kdj_j:.0f} < 0 — oversold, bounce opportunity")
        elif k_cross_up:
            result.kdj_signal = "golden_cross"
            score += 10
            signals.append("✅ KDJ golden cross — K above D")
        elif k_cross_down:
            result.kdj_signal = "death_cross"
            signals.append("⚠️ KDJ death cross — K below D")
        else:
            result.kdj_signal = "neutral"
            score += 5
    except Exception as e:
        logger.debug(f"KDJ calculation failed: {e}")

    # --- Williams %R ---
    try:
        df = calc_williams_r(df)
        latest = df.iloc[-1]
        result.williams_r = float(latest["WILLIAMS_R"])

        if result.williams_r > -20:
            result.williams_signal = "overbought"
            signals.append(f"⚠️ Williams %R={result.williams_r:.0f} — overbought zone")
        elif result.williams_r < -80:
            result.williams_signal = "oversold"
            score += 8
            signals.append(f"✅ Williams %R={result.williams_r:.0f} — oversold zone")
        else:
            result.williams_signal = "neutral"
            score += 4
    except Exception as e:
        logger.debug(f"Williams %R calculation failed: {e}")

    # --- CCI ---
    try:
        df = calc_cci(df)
        latest = df.iloc[-1]
        result.cci = float(latest["CCI"])

        if result.cci > 100:
            result.cci_signal = "strong_uptrend"
            score += 8
            signals.append(f"✅ CCI={result.cci:.0f} > 100 — strong uptrend")
        elif result.cci < -100:
            result.cci_signal = "strong_downtrend"
            signals.append(f"⚠️ CCI={result.cci:.0f} < -100 — strong downtrend")
        else:
            result.cci_signal = "neutral"
            score += 4
    except Exception as e:
        logger.debug(f"CCI calculation failed: {e}")

    result.advanced_score = min(100, score)
    result.advanced_signals = signals

    return result
